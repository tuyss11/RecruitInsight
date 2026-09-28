from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd


SRC_PATH = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_PATH))

from import_jobs import (  # noqa: E402
    load_cleaned_jobs,
    nullable_date,
    nullable_integer,
    split_skills,
    sql_value,
)


class SqlValueTest(unittest.TestCase):
    def test_pandas_na_becomes_none(self) -> None:
        self.assertIsNone(sql_value(pd.NA))

    def test_nan_becomes_none(self) -> None:
        self.assertIsNone(sql_value(float("nan")))

    def test_nullable_integer(self) -> None:
        self.assertEqual(nullable_integer(12000.0), 12000)
        self.assertIsNone(nullable_integer(pd.NA))

    def test_nullable_date(self) -> None:
        self.assertEqual(nullable_date("2026-09-28").isoformat(), "2026-09-28")
        self.assertIsNone(nullable_date(pd.NA))


class SplitSkillsTest(unittest.TestCase):
    def test_split_deduplicates_and_preserves_order(self) -> None:
        self.assertEqual(
            split_skills("Java|Spring Boot|MySQL|Java"),
            ["Java", "Spring Boot", "MySQL"],
        )

    def test_missing_skills_become_empty_list(self) -> None:
        self.assertEqual(split_skills(pd.NA), [])


class LoadCleanedJobsTest(unittest.TestCase):
    def test_project_dataset_has_unique_source_ids(self) -> None:
        dataframe = load_cleaned_jobs()
        self.assertEqual(len(dataframe), 59)
        self.assertFalse(dataframe["source_id"].duplicated().any())


if __name__ == "__main__":
    unittest.main()
