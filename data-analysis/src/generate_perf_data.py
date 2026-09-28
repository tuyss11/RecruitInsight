"""Generate reproducible simulated recruitment data for local performance tests."""

from __future__ import annotations

import argparse
import csv
import random
from datetime import date, timedelta
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "dataset" / "perf" / "jobs_perf.csv"
DEFAULT_JOB_COUNT = 30_000
PERF_RANDOM_SEED = 20260928
REFERENCE_DATE = date(2026, 9, 28)

CITIES = ["北京", "上海", "深圳", "杭州", "广州", "成都", "西安", "南京", "武汉", "苏州"]
CATEGORIES = ["后端开发", "数据分析", "数据开发", "算法", "测试", "其他"]
EDUCATION_LEVELS = ["不限", "大专", "本科", "本科及以上", "硕士", "硕士及以上"]
SKILLS = [
    "Docker", "Excel", "Git", "Hive", "Java", "Linux", "MySQL", "NumPy",
    "Pandas", "PostgreSQL", "Power BI", "Python", "Redis", "Spark", "Spring",
    "Spring Boot", "SQL", "Tableau",
]

CATEGORY_TITLES = {
    "后端开发": ["Java后端工程师", "Python后端工程师", "服务端研发工程师", "Spring Boot开发工程师"],
    "数据分析": ["数据分析师", "商业分析师", "BI数据分析师", "数据分析专员"],
    "数据开发": ["数据开发工程师", "数仓ETL工程师", "大数据开发工程师", "数据平台工程师"],
    "算法": ["算法工程师", "机器学习工程师", "推荐算法工程师", "算法研究员"],
    "测试": ["测试开发工程师", "软件测试工程师", "自动化测试工程师", "QA工程师"],
    "其他": ["数据产品专员", "技术支持工程师", "项目助理", "数据运营专员"],
}

CATEGORY_SKILLS = {
    "后端开发": ["Java", "Spring", "Spring Boot", "MySQL", "Redis", "Linux", "Docker", "Git"],
    "数据分析": ["Python", "SQL", "Excel", "Pandas", "NumPy", "Power BI", "Tableau"],
    "数据开发": ["Python", "SQL", "Hive", "Spark", "Linux", "Docker", "MySQL", "PostgreSQL"],
    "算法": ["Python", "NumPy", "Pandas", "SQL", "Linux", "Git", "Docker"],
    "测试": ["Python", "Java", "SQL", "Linux", "Git", "Docker"],
    "其他": ["Excel", "SQL", "Python", "Power BI", "Tableau", "Git"],
}

SALARY_RANGES = {
    "后端开发": (10_000, 28_000, 4_000, 12_000),
    "数据分析": (7_000, 20_000, 3_000, 9_000),
    "数据开发": (11_000, 30_000, 5_000, 13_000),
    "算法": (14_000, 36_000, 6_000, 16_000),
    "测试": (8_000, 22_000, 3_000, 9_000),
    "其他": (6_000, 18_000, 2_000, 7_000),
}

FIELDNAMES = [
    "source_id", "title", "company", "city", "category", "education",
    "salary_min", "salary_max", "salary_months", "description", "publish_date", "skills",
]


def _salary(rng: random.Random, category: str) -> tuple[int | None, int | None, int | None]:
    if rng.random() < 0.10:
        return None, None, None
    minimum_low, minimum_high, spread_low, spread_high = SALARY_RANGES[category]
    minimum = rng.randrange(minimum_low, minimum_high + 1, 1_000)
    maximum = minimum + rng.randrange(spread_low, spread_high + 1, 1_000)
    return minimum, maximum, rng.choice([12, 12, 12, 13, 14, 16])


def _skills(rng: random.Random, category: str) -> list[str]:
    preferred = CATEGORY_SKILLS[category]
    selected = set(rng.sample(preferred, k=rng.randint(2, min(4, len(preferred)))))
    remaining = [skill for skill in SKILLS if skill not in selected]
    selected.update(rng.sample(remaining, k=rng.randint(0, 2)))
    return [skill for skill in SKILLS if skill in selected]


def generate_rows(job_count: int, seed: int = PERF_RANDOM_SEED) -> list[dict[str, Any]]:
    if job_count < 1:
        raise ValueError("job_count must be positive")

    rng = random.Random(seed)
    rows: list[dict[str, Any]] = []
    for index in range(1, job_count + 1):
        category = rng.choices(CATEGORIES, weights=[30, 20, 15, 12, 13, 10], k=1)[0]
        skills = _skills(rng, category)
        salary_min, salary_max, salary_months = _salary(rng, category)
        publish_date = REFERENCE_DATE - timedelta(days=rng.randint(0, 729))
        rows.append({
            "source_id": f"perf-{index:06d}",
            "title": rng.choice(CATEGORY_TITLES[category]),
            "company": f"性能测试公司{rng.randint(1, 1200):04d}",
            "city": rng.choice(CITIES),
            "category": category,
            "education": rng.choice(EDUCATION_LEVELS),
            "salary_min": salary_min,
            "salary_max": salary_max,
            "salary_months": salary_months,
            "description": f"程序生成的模拟压力测试数据；岗位类别：{category}；技能：{'、'.join(skills)}。",
            "publish_date": publish_date.isoformat(),
            "skills": "|".join(skills),
        })
    return rows


def write_perf_csv(rows: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=DEFAULT_JOB_COUNT)
    parser.add_argument("--seed", type=int, default=PERF_RANDOM_SEED)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()

    rows = generate_rows(args.count, args.seed)
    write_perf_csv(rows, args.output)
    print("Dataset type: programmatically generated simulated performance-test data")
    print(f"Random seed: {args.seed}")
    print(f"Jobs generated: {len(rows)}")
    print(f"Output: {args.output.resolve()}")


if __name__ == "__main__":
    main()
