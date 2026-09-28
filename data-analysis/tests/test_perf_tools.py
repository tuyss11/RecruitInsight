from __future__ import annotations

import csv
import io
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SRC_PATH = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_PATH))

from generate_perf_data import (  # noqa: E402
    PERF_RANDOM_SEED,
    SKILLS,
    generate_rows,
    write_perf_csv,
)
from apply_perf_indexes import index_names, load_statements  # noqa: E402
from import_perf_jobs import (  # noqa: E402
    load_perf_database_config,
    validate_perf_database_name,
)


class NonClosingStringIO(io.StringIO):
    def close(self) -> None:
        pass


class GeneratePerfDataTest(unittest.TestCase):
    def test_generation_is_reproducible(self) -> None:
        self.assertEqual(generate_rows(20, PERF_RANDOM_SEED), generate_rows(20, PERF_RANDOM_SEED))

    def test_generated_rows_are_clearly_simulated(self) -> None:
        rows = generate_rows(20)
        self.assertTrue(all(row["company"].startswith("性能测试公司") for row in rows))
        self.assertTrue(all("模拟压力测试数据" in row["description"] for row in rows))
        self.assertTrue(
            all(set(row["skills"].split("|")).issubset(set(SKILLS)) for row in rows)
        )

    def test_generated_csv_matches_import_contract(self) -> None:
        output = NonClosingStringIO()
        with patch.object(Path, "mkdir"), patch.object(Path, "open", return_value=output):
            write_perf_csv(generate_rows(12), Path("perf.csv"))
        output.seek(0)
        parsed = list(csv.DictReader(output))
        self.assertEqual(len(parsed), 12)
        self.assertEqual(parsed[0]["source_id"], "perf-000001")

    def test_job_count_must_be_positive(self) -> None:
        with self.assertRaises(ValueError):
            generate_rows(0)


class PerfDatabaseSafetyTest(unittest.TestCase):
    def test_expected_database_is_allowed(self) -> None:
        self.assertEqual(
            validate_perf_database_name("recruit_insight_perf"),
            "recruit_insight_perf",
        )

    def test_normal_database_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_perf_database_name("recruit_insight")

    def test_prompted_credentials_are_scoped_to_perf_database(self) -> None:
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("builtins.input", return_value="perf_user"),
            patch("getpass.getpass", return_value="secret"),
        ):
            config = load_perf_database_config(prompt_credentials=True)

        self.assertEqual(config.name, "recruit_insight_perf")
        self.assertEqual(config.username, "perf_user")
        self.assertEqual(config.password, "secret")


class IndexMigrationTest(unittest.TestCase):
    def test_migration_contains_only_reviewed_indexes(self) -> None:
        statements = load_statements()
        self.assertEqual(len(statements), 3)
        self.assertTrue(all("CREATE INDEX" in statement for statement in statements))
        self.assertFalse(any("USE recruit_insight" in statement for statement in statements))
        self.assertEqual(
            index_names(statements),
            [
                "idx_job_city_category_publish",
                "idx_job_city_publish",
                "idx_job_category_publish",
            ],
        )
        self.assertIn("salary_min, salary_max", statements[-1])


if __name__ == "__main__":
    unittest.main()
