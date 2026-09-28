"""Rebuild and import the isolated RecruitInsight performance-test database."""

from __future__ import annotations

import argparse
import getpass
import os
import re
from dataclasses import replace
from pathlib import Path
from typing import Any, Iterable

import pymysql
from pymysql.connections import Connection
from pymysql.cursors import DictCursor

from import_jobs import (
    DatabaseConfig,
    load_cleaned_jobs,
    nullable_date,
    nullable_integer,
    split_skills,
    sql_value,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PERF_DATA_PATH = PROJECT_ROOT / "dataset" / "perf" / "jobs_perf.csv"
DEFAULT_PERF_DATABASE = "recruit_insight_perf"
BATCH_SIZE = 1_000

JOB_INSERT_SQL = """
INSERT INTO job (
    source_id, title, company, city, category, education,
    salary_min, salary_max, salary_months, description, publish_date
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

SCHEMA_STATEMENTS = [
    """
    CREATE TABLE job (
        id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
        source_id VARCHAR(64) NOT NULL COMMENT '模拟压力测试记录 ID',
        title VARCHAR(100) NOT NULL COMMENT '岗位名称',
        company VARCHAR(150) NOT NULL COMMENT '虚构公司名称',
        city VARCHAR(50) NOT NULL COMMENT '城市',
        category VARCHAR(50) NOT NULL COMMENT '岗位类别',
        education VARCHAR(50) NOT NULL DEFAULT '不限' COMMENT '学历要求',
        salary_min INT UNSIGNED NULL COMMENT '最低月薪（元）',
        salary_max INT UNSIGNED NULL COMMENT '最高月薪（元）',
        salary_months TINYINT UNSIGNED NULL COMMENT '一年发薪月数',
        description TEXT NULL COMMENT '模拟岗位描述',
        publish_date DATE NULL COMMENT '发布日期',
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        PRIMARY KEY (id),
        UNIQUE KEY uk_job_source_id (source_id),
        CONSTRAINT chk_job_salary_range
            CHECK (salary_min IS NULL OR salary_max IS NULL OR salary_max >= salary_min)
    ) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
      COMMENT='程序生成的模拟压力测试岗位'
    """,
    """
    CREATE TABLE skill (
        id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
        name VARCHAR(100) NOT NULL COMMENT '规范化技能名称',
        PRIMARY KEY (id),
        UNIQUE KEY uk_skill_name (name)
    ) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
      COMMENT='性能测试技能字典'
    """,
    """
    CREATE TABLE job_skill (
        job_id BIGINT UNSIGNED NOT NULL COMMENT '岗位 ID',
        skill_id BIGINT UNSIGNED NOT NULL COMMENT '技能 ID',
        PRIMARY KEY (job_id, skill_id),
        KEY idx_job_skill_skill_id (skill_id),
        CONSTRAINT fk_perf_job_skill_job
            FOREIGN KEY (job_id) REFERENCES job (id) ON DELETE CASCADE,
        CONSTRAINT fk_perf_job_skill_skill
            FOREIGN KEY (skill_id) REFERENCES skill (id)
    ) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
      COMMENT='性能测试岗位与技能关系'
    """,
]


def validate_perf_database_name(name: str) -> str:
    if name != DEFAULT_PERF_DATABASE or not re.fullmatch(r"[a-z0-9_]+", name):
        raise ValueError(f"Performance import only permits database {DEFAULT_PERF_DATABASE!r}")
    return name


def batched(values: list[Any], size: int = BATCH_SIZE) -> Iterable[list[Any]]:
    for start in range(0, len(values), size):
        yield values[start:start + size]


def connect_server(config: DatabaseConfig) -> Connection:
    return pymysql.connect(
        host=config.host,
        port=config.port,
        user=config.username,
        password=config.password,
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=True,
    )


def load_database_config(
        database_name: str,
        prompt_credentials: bool = False,
) -> DatabaseConfig:
    """Load credentials without ever reading or printing a local Spring config file."""
    try:
        base_config = DatabaseConfig.from_environment()
    except RuntimeError:
        if not prompt_credentials:
            raise

        username = input("MySQL username: ").strip()
        if not username:
            raise RuntimeError("MySQL username must not be empty")
        password = getpass.getpass("MySQL password (input hidden): ")
        try:
            port = int(os.getenv("DB_PORT", "3306"))
        except ValueError as error:
            raise RuntimeError("DB_PORT must be an integer") from error
        base_config = DatabaseConfig(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=port,
            name=database_name,
            username=username,
            password=password,
        )

    return replace(base_config, name=database_name)


def load_perf_database_config(prompt_credentials: bool = False) -> DatabaseConfig:
    return load_database_config(DEFAULT_PERF_DATABASE, prompt_credentials)


def rebuild_perf_schema(connection: Connection, database_name: str) -> None:
    database_name = validate_perf_database_name(database_name)
    with connection.cursor() as cursor:
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{database_name}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci"
        )
    connection.select_db(database_name)
    with connection.cursor() as cursor:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        cursor.execute("DROP TABLE IF EXISTS job_skill")
        cursor.execute("DROP TABLE IF EXISTS skill")
        cursor.execute("DROP TABLE IF EXISTS job")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        for statement in SCHEMA_STATEMENTS:
            cursor.execute(statement)


def import_perf_jobs(connection: Connection, data_path: Path = PERF_DATA_PATH) -> dict[str, int]:
    dataframe = load_cleaned_jobs(data_path)
    jobs: list[tuple[Any, ...]] = []
    skills_by_source: dict[str, list[str]] = {}
    for row in dataframe.itertuples(index=False):
        source_id = str(row.source_id).strip()
        skills_by_source[source_id] = split_skills(row.skills)
        jobs.append((
            source_id,
            sql_value(row.title),
            sql_value(row.company),
            sql_value(row.city),
            sql_value(row.category),
            sql_value(row.education),
            nullable_integer(row.salary_min),
            nullable_integer(row.salary_max),
            nullable_integer(row.salary_months),
            sql_value(row.description),
            nullable_date(row.publish_date),
        ))

    connection.autocommit(False)
    try:
        with connection.cursor() as cursor:
            for job_batch in batched(jobs):
                cursor.executemany(JOB_INSERT_SQL, job_batch)

            cursor.execute("SELECT id, source_id FROM job")
            job_ids = {item["source_id"]: int(item["id"]) for item in cursor.fetchall()}

            skill_names = sorted({skill for values in skills_by_source.values() for skill in values})
            cursor.executemany("INSERT INTO skill (name) VALUES (%s)", [(name,) for name in skill_names])
            cursor.execute("SELECT id, name FROM skill")
            skill_ids = {item["name"]: int(item["id"]) for item in cursor.fetchall()}

            relations = [
                (job_ids[source_id], skill_ids[skill])
                for source_id, values in skills_by_source.items()
                for skill in values
            ]
            for relation_batch in batched(relations):
                cursor.executemany(
                    "INSERT INTO job_skill (job_id, skill_id) VALUES (%s, %s)",
                    relation_batch,
                )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.autocommit(True)

    return {"jobs": len(jobs), "skills": len(skill_names), "job_skill": len(relations)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--prompt-credentials",
        action="store_true",
        help="prompt for missing MySQL credentials without echoing the password",
    )
    args = parser.parse_args()
    database_name = validate_perf_database_name(
        os.getenv("PERF_DB_NAME", DEFAULT_PERF_DATABASE)
    )
    config = replace(
        load_perf_database_config(args.prompt_credentials),
        name=database_name,
    )
    connection = connect_server(config)
    try:
        rebuild_perf_schema(connection, config.name)
        result = import_perf_jobs(connection)
    finally:
        connection.close()

    print("Dataset type: programmatically generated simulated performance-test data")
    print(f"Database: {config.name}")
    print(f"Jobs: {result['jobs']}")
    print(f"Skills: {result['skills']}")
    print(f"Job-skill relations: {result['job_skill']}")


if __name__ == "__main__":
    main()
