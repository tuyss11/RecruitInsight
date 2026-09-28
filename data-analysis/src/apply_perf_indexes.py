"""Apply the reviewed query indexes to the isolated performance database."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from import_jobs import connect_database
from import_perf_jobs import load_perf_database_config


PROJECT_ROOT = Path(__file__).resolve().parents[2]
INDEX_SQL_PATH = PROJECT_ROOT / "sql" / "007_add_query_indexes.sql"


def load_statements(path: Path = INDEX_SQL_PATH) -> list[str]:
    sql_lines = [
        line for line in path.read_text(encoding="utf-8").splitlines()
        if not line.lstrip().startswith("--")
    ]
    return [statement.strip() for statement in "\n".join(sql_lines).split(";")
            if statement.strip()]


def index_names(statements: list[str]) -> list[str]:
    names: list[str] = []
    for statement in statements:
        match = re.match(r"CREATE\s+INDEX\s+([a-zA-Z0-9_]+)", statement, re.IGNORECASE)
        if match is None:
            raise ValueError("Index migration may only contain CREATE INDEX statements")
        names.append(match.group(1))
    return names


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--prompt-credentials",
        action="store_true",
        help="prompt for missing MySQL credentials without echoing the password",
    )
    args = parser.parse_args()

    config = load_perf_database_config(args.prompt_credentials)
    statements = load_statements()
    reviewed_names = index_names(statements)
    connection = connect_database(config)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT DATABASE() AS database_name")
            selected_database = cursor.fetchone()["database_name"]
            if selected_database != "recruit_insight_perf":
                raise RuntimeError("Refusing to add performance indexes outside recruit_insight_perf")
            cursor.execute(
                """SELECT DISTINCT INDEX_NAME AS reviewed_index_name
                   FROM information_schema.statistics
                   WHERE table_schema = DATABASE() AND table_name = 'job'"""
            )
            existing_names = {row["reviewed_index_name"] for row in cursor.fetchall()}
            for index_name in reviewed_names:
                if index_name in existing_names:
                    cursor.execute(f"DROP INDEX `{index_name}` ON job")
            for statement in statements:
                cursor.execute(statement)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    print(f"Database: {selected_database}")
    print(f"Indexes applied: {len(statements)}")
    print(f"Source: {INDEX_SQL_PATH.resolve()}")


if __name__ == "__main__":
    main()
