"""Import the cleaned simulated jobs into the normalized MySQL schema."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
import pymysql
from pymysql.connections import Connection
from pymysql.cursors import DictCursor


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CLEANED_DATA_PATH = PROJECT_ROOT / "dataset" / "processed" / "jobs_cleaned.csv"

REQUIRED_COLUMNS = {
    "source_id",
    "title",
    "company",
    "city",
    "category",
    "education",
    "salary_min",
    "salary_max",
    "salary_months",
    "description",
    "skills",
    "publish_date",
}

JOB_UPSERT_SQL = """
INSERT INTO job (
    source_id,
    title,
    company,
    city,
    category,
    education,
    salary_min,
    salary_max,
    salary_months,
    description,
    publish_date
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE
    id = LAST_INSERT_ID(id),
    title = VALUES(title),
    company = VALUES(company),
    city = VALUES(city),
    category = VALUES(category),
    education = VALUES(education),
    salary_min = VALUES(salary_min),
    salary_max = VALUES(salary_max),
    salary_months = VALUES(salary_months),
    description = VALUES(description),
    publish_date = VALUES(publish_date)
"""

SKILL_UPSERT_SQL = """
INSERT INTO skill (name)
VALUES (%s)
ON DUPLICATE KEY UPDATE
    id = LAST_INSERT_ID(id),
    name = VALUES(name)
"""


@dataclass(frozen=True)
class DatabaseConfig:
    host: str
    port: int
    name: str
    username: str
    password: str

    @classmethod
    def from_environment(cls) -> "DatabaseConfig":
        username = os.getenv("DB_USERNAME")
        password = os.getenv("DB_PASSWORD")
        if not username or password is None:
            raise RuntimeError(
                "DB_USERNAME and DB_PASSWORD must be provided as environment variables"
            )

        port_text = os.getenv("DB_PORT", "3306")
        try:
            port = int(port_text)
        except ValueError as error:
            raise RuntimeError("DB_PORT must be an integer") from error

        return cls(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=port,
            name=os.getenv("DB_NAME", "recruit_insight"),
            username=username,
            password=password,
        )


@dataclass(frozen=True)
class ImportResult:
    jobs_inserted: int
    jobs_updated: int
    skills: int
    job_skill_relations: int


def sql_value(value: Any) -> Any:
    """Convert Pandas missing/scalar values into DB-API compatible values."""
    if value is None or pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.date()
    if hasattr(value, "item") and not isinstance(value, (str, bytes)):
        return value.item()
    return value


def nullable_integer(value: Any) -> int | None:
    converted = sql_value(value)
    return None if converted is None else int(converted)


def nullable_date(value: Any) -> date | None:
    converted = sql_value(value)
    if converted is None:
        return None
    parsed = pd.to_datetime(converted, errors="coerce")
    return None if pd.isna(parsed) else parsed.date()


def split_skills(value: Any) -> list[str]:
    converted = sql_value(value)
    if converted is None:
        return []
    return list(dict.fromkeys(part.strip() for part in str(converted).split("|") if part.strip()))


def load_cleaned_jobs(path: Path = CLEANED_DATA_PATH) -> pd.DataFrame:
    dataframe = pd.read_csv(path, encoding="utf-8-sig", dtype={"source_id": "string"})
    missing_columns = REQUIRED_COLUMNS.difference(dataframe.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing_columns))}")
    if dataframe["source_id"].isna().any() or (dataframe["source_id"].str.strip() == "").any():
        raise ValueError("Every cleaned job must have a source_id")
    if dataframe["source_id"].duplicated().any():
        raise ValueError("source_id must be unique in the cleaned CSV")
    return dataframe


def connect_database(config: DatabaseConfig) -> Connection:
    return pymysql.connect(
        host=config.host,
        port=config.port,
        user=config.username,
        password=config.password,
        database=config.name,
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=False,
    )


def import_jobs(dataframe: pd.DataFrame, connection: Connection) -> ImportResult:
    """Upsert jobs and rebuild their normalized skill links in one transaction."""
    jobs_inserted = 0
    jobs_updated = 0

    try:
        connection.begin()
        with connection.cursor() as cursor:
            for _, row in dataframe.iterrows():
                source_id = str(row["source_id"]).strip()
                cursor.execute("SELECT id FROM job WHERE source_id = %s", (source_id,))
                existing_job = cursor.fetchone()

                cursor.execute(
                    JOB_UPSERT_SQL,
                    (
                        source_id,
                        sql_value(row["title"]),
                        sql_value(row["company"]),
                        sql_value(row["city"]),
                        sql_value(row["category"]),
                        sql_value(row["education"]),
                        nullable_integer(row["salary_min"]),
                        nullable_integer(row["salary_max"]),
                        nullable_integer(row["salary_months"]),
                        sql_value(row["description"]),
                        nullable_date(row["publish_date"]),
                    ),
                )
                job_id = int(cursor.lastrowid)

                if existing_job is None:
                    jobs_inserted += 1
                else:
                    jobs_updated += 1

                cursor.execute("DELETE FROM job_skill WHERE job_id = %s", (job_id,))
                for skill_name in split_skills(row["skills"]):
                    cursor.execute(SKILL_UPSERT_SQL, (skill_name,))
                    skill_id = int(cursor.lastrowid)
                    cursor.execute(
                        "INSERT IGNORE INTO job_skill (job_id, skill_id) VALUES (%s, %s)",
                        (job_id, skill_id),
                    )

            cursor.execute(
                """
                DELETE s
                FROM skill s
                LEFT JOIN job_skill js ON js.skill_id = s.id
                WHERE js.skill_id IS NULL
                """
            )
            cursor.execute("SELECT COUNT(*) AS count FROM skill")
            skill_count = int(cursor.fetchone()["count"])
            cursor.execute("SELECT COUNT(*) AS count FROM job_skill")
            relation_count = int(cursor.fetchone()["count"])

        connection.commit()
    except Exception:
        connection.rollback()
        raise

    return ImportResult(
        jobs_inserted=jobs_inserted,
        jobs_updated=jobs_updated,
        skills=skill_count,
        job_skill_relations=relation_count,
    )


def main() -> None:
    config = DatabaseConfig.from_environment()
    dataframe = load_cleaned_jobs()
    connection = connect_database(config)
    try:
        result = import_jobs(dataframe, connection)
    finally:
        connection.close()

    print(f"Jobs inserted: {result.jobs_inserted}")
    print(f"Jobs updated: {result.jobs_updated}")
    print(f"Skills: {result.skills}")
    print(f"Job-skill relations: {result.job_skill_relations}")


if __name__ == "__main__":
    main()
