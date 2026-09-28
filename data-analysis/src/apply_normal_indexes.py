"""Apply reviewed query indexes to the normal RecruitInsight database."""

from __future__ import annotations

import argparse

from apply_perf_indexes import index_names, load_statements
from import_jobs import connect_database
from import_perf_jobs import load_database_config


NORMAL_DATABASE = "recruit_insight"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--prompt-credentials",
        action="store_true",
        help="prompt for missing MySQL credentials without echoing the password",
    )
    args = parser.parse_args()

    config = load_database_config(NORMAL_DATABASE, args.prompt_credentials)
    statements = load_statements()
    reviewed_names = index_names(statements)
    connection = connect_database(config)
    applied: list[str] = []
    skipped: list[str] = []
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT DATABASE() AS database_name")
            selected_database = cursor.fetchone()["database_name"]
            if selected_database != NORMAL_DATABASE:
                raise RuntimeError("Refusing to update a database other than recruit_insight")
            cursor.execute(
                """SELECT DISTINCT INDEX_NAME AS reviewed_index_name
                   FROM information_schema.statistics
                   WHERE table_schema = DATABASE() AND table_name = 'job'"""
            )
            existing_names = {row["reviewed_index_name"] for row in cursor.fetchall()}
            for index_name, statement in zip(reviewed_names, statements, strict=True):
                if index_name in existing_names:
                    skipped.append(index_name)
                    continue
                cursor.execute(statement)
                applied.append(index_name)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    print(f"Database: {selected_database}")
    print(f"Indexes applied: {len(applied)} ({', '.join(applied) or 'none'})")
    print(f"Indexes already present: {len(skipped)} ({', '.join(skipped) or 'none'})")


if __name__ == "__main__":
    main()
