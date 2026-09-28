"""Benchmark the SQL patterns used by RecruitInsight against the perf database."""

from __future__ import annotations

import argparse
import json
import statistics
import time
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from pymysql.connections import Connection

from import_jobs import connect_database
from import_perf_jobs import (
    DEFAULT_PERF_DATABASE,
    load_perf_database_config,
    validate_perf_database_name,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WARMUPS = 3
DEFAULT_REPETITIONS = 10


@dataclass(frozen=True)
class QueryCase:
    code: str
    name: str
    sql: str
    params: tuple[Any, ...]


QUERY_CASES = [
    QueryCase(
        "A",
        "city + category deep pagination",
        """SELECT id, source_id, title, company, city, category, education,
                  salary_min, salary_max, salary_months, publish_date
           FROM job
           WHERE city = %s AND category = %s
           ORDER BY publish_date DESC, id DESC
           LIMIT 20 OFFSET 200""",
        ("上海", "后端开发"),
    ),
    QueryCase(
        "B",
        "single city pagination",
        """SELECT id, source_id, title, company, city, category, education,
                  salary_min, salary_max, salary_months, publish_date
           FROM job
           WHERE city = %s
           ORDER BY publish_date DESC, id DESC
           LIMIT 20""",
        ("上海",),
    ),
    QueryCase(
        "C",
        "single category pagination",
        """SELECT id, source_id, title, company, city, category, education,
                  salary_min, salary_max, salary_months, publish_date
           FROM job
           WHERE category = %s
           ORDER BY publish_date DESC, id DESC
           LIMIT 20""",
        ("后端开发",),
    ),
    QueryCase(
        "D",
        "city + category pagination count",
        "SELECT COUNT(*) FROM job WHERE city = %s AND category = %s",
        ("上海", "后端开发"),
    ),
    QueryCase(
        "E",
        "skills Top 10",
        """SELECT s.name, COUNT(*) AS job_count
           FROM job_skill js
           INNER JOIN skill s ON s.id = js.skill_id
           INNER JOIN job j ON j.id = js.job_id
           GROUP BY s.id, s.name
           ORDER BY job_count DESC, s.name ASC
           LIMIT 10""",
        (),
    ),
    QueryCase(
        "F",
        "category skills Top 10",
        """SELECT s.name, COUNT(*) AS job_count
           FROM job_skill js
           INNER JOIN skill s ON s.id = js.skill_id
           INNER JOIN job j ON j.id = js.job_id
           WHERE j.category = %s
           GROUP BY s.id, s.name
           ORDER BY job_count DESC, s.name ASC
           LIMIT 10""",
        ("后端开发",),
    ),
    QueryCase(
        "G",
        "cities GROUP BY",
        """SELECT city, COUNT(*) AS job_count
           FROM job
           GROUP BY city
           ORDER BY job_count DESC, city ASC""",
        (),
    ),
    QueryCase(
        "H",
        "salary GROUP BY",
        """SELECT category,
                  COUNT(*) AS job_count,
                  CAST(ROUND(AVG(salary_min), 0) AS SIGNED) AS average_salary_min,
                  CAST(ROUND(AVG(salary_max), 0) AS SIGNED) AS average_salary_max,
                  CAST(ROUND(AVG((salary_min + salary_max) / 2.0), 0) AS SIGNED)
                      AS average_salary_mid
           FROM job
           WHERE salary_min IS NOT NULL AND salary_max IS NOT NULL
           GROUP BY category
           ORDER BY job_count DESC, category ASC""",
        (),
    ),
    QueryCase(
        "I",
        "leading-wildcard title search",
        """SELECT id, source_id, title, company, city, category, education,
                  salary_min, salary_max, salary_months, publish_date
           FROM job
           WHERE title LIKE %s
           ORDER BY publish_date DESC, id DESC
           LIMIT 20""",
        ("%Java%",),
    ),
]


def json_default(value: Any) -> str:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def inventory_indexes(connection: Connection) -> list[dict[str, Any]]:
    with connection.cursor() as cursor:
        cursor.execute(
            """SELECT table_name, index_name, non_unique, seq_in_index, column_name
               FROM information_schema.statistics
               WHERE table_schema = DATABASE()
                 AND table_name IN ('job', 'skill', 'job_skill')
               ORDER BY table_name, index_name, seq_in_index"""
        )
        return list(cursor.fetchall())


def table_counts(connection: Connection) -> dict[str, int]:
    counts: dict[str, int] = {}
    with connection.cursor() as cursor:
        for table_name in ("job", "skill", "job_skill"):
            cursor.execute(f"SELECT COUNT(*) AS row_count FROM {table_name}")
            counts[table_name] = int(cursor.fetchone()["row_count"])
    return counts


def explain(connection: Connection, case: QueryCase) -> tuple[list[dict[str, Any]], list[str]]:
    with connection.cursor() as cursor:
        cursor.execute(f"EXPLAIN {case.sql}", case.params)
        estimated = list(cursor.fetchall())
        cursor.execute(f"EXPLAIN ANALYZE {case.sql}", case.params)
        analyzed = [str(next(iter(row.values()))) for row in cursor.fetchall()]
    return estimated, analyzed


def measure(
    connection: Connection,
    case: QueryCase,
    warmups: int,
    repetitions: int,
) -> dict[str, Any]:
    with connection.cursor() as cursor:
        for _ in range(warmups):
            cursor.execute(case.sql, case.params)
            cursor.fetchall()

        timings: list[float] = []
        row_count = 0
        for _ in range(repetitions):
            started = time.perf_counter_ns()
            cursor.execute(case.sql, case.params)
            rows = cursor.fetchall()
            elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
            timings.append(elapsed_ms)
            row_count = len(rows)

    estimated, analyzed = explain(connection, case)
    return {
        "code": case.code,
        "name": case.name,
        "sql": " ".join(case.sql.split()),
        "params": list(case.params),
        "returned_rows": row_count,
        "timing_ms": {
            "min": round(min(timings), 4),
            "median": round(statistics.median(timings), 4),
            "max": round(max(timings), 4),
            "samples": [round(value, 4) for value in timings],
        },
        "explain": estimated,
        "explain_analyze": analyzed,
    }


def benchmark(
    connection: Connection,
    label: str,
    warmups: int = DEFAULT_WARMUPS,
    repetitions: int = DEFAULT_REPETITIONS,
) -> dict[str, Any]:
    with connection.cursor() as cursor:
        cursor.execute("SELECT VERSION() AS version")
        server_version = cursor.fetchone()["version"]

    return {
        "label": label,
        "dataset_notice": "Programmatically generated simulated performance-test data",
        "measured_at_utc": datetime.now(timezone.utc).isoformat(),
        "database": DEFAULT_PERF_DATABASE,
        "mysql_version": server_version,
        "warmups": warmups,
        "repetitions": repetitions,
        "table_counts": table_counts(connection),
        "indexes": inventory_indexes(connection),
        "queries": [measure(connection, case, warmups, repetitions) for case in QUERY_CASES],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", required=True, choices=["before", "after"])
    parser.add_argument("--warmups", type=int, default=DEFAULT_WARMUPS)
    parser.add_argument("--repetitions", type=int, default=DEFAULT_REPETITIONS)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--prompt-credentials",
        action="store_true",
        help="prompt for missing MySQL credentials without echoing the password",
    )
    args = parser.parse_args()
    if args.warmups < 0 or args.repetitions < 1:
        parser.error("warmups must be non-negative and repetitions must be positive")

    database_name = validate_perf_database_name(DEFAULT_PERF_DATABASE)
    config = load_perf_database_config(args.prompt_credentials)
    connection = connect_database(config)
    try:
        result = benchmark(connection, args.label, args.warmups, args.repetitions)
    finally:
        connection.close()

    output = args.output or (
        PROJECT_ROOT / "docs" / "benchmark-results" / f"{args.label}.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, default=json_default),
        encoding="utf-8",
    )

    print(f"Dataset: {result['dataset_notice']}")
    print(f"Rows: {result['table_counts']}")
    for query in result["queries"]:
        timing = query["timing_ms"]
        print(
            f"{query['code']} {query['name']}: "
            f"min={timing['min']:.4f} ms, median={timing['median']:.4f} ms, "
            f"max={timing['max']:.4f} ms"
        )
    print(f"Result: {output.resolve()}")


if __name__ == "__main__":
    main()
