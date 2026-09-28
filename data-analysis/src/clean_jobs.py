"""Clean the simulated RecruitInsight recruitment dataset."""

from __future__ import annotations

import re
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import NamedTuple

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_PATH = PROJECT_ROOT / "dataset" / "raw" / "jobs_raw_sample.csv"
PROCESSED_DATA_PATH = PROJECT_ROOT / "dataset" / "processed" / "jobs_cleaned.csv"
REPORT_PATH = PROJECT_ROOT / "docs" / "data-cleaning-report.md"

WORKING_DAYS_PER_MONTH = Decimal("21.75")
DEFAULT_SALARY_MONTHS = 12

CATEGORY_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("数据开发", ("数据开发", "etl", "数仓", "数据仓库")),
    ("数据分析", ("数据分析", "商业分析", "bi")),
    ("算法", ("算法", "机器学习", "推荐")),
    ("测试", ("测试", "qa")),
    (
        "后端开发",
        (
            "java",
            "后端",
            "服务端",
            "spring",
            "python开发",
            "python后端",
            "python服务端",
        ),
    ),
)

SKILL_PATTERNS: tuple[tuple[str, str], ...] = (
    ("Java", r"(?<![A-Za-z])java(?![A-Za-z])"),
    ("Python", r"(?<![A-Za-z])python(?![A-Za-z])"),
    ("SQL", r"(?<![A-Za-z])sql(?![A-Za-z])"),
    ("MySQL", r"(?<![A-Za-z])mysql(?![A-Za-z])"),
    ("PostgreSQL", r"(?<![A-Za-z])postgresql(?![A-Za-z])"),
    ("Spring Boot", r"(?<![A-Za-z])spring\s*boot(?![A-Za-z])"),
    ("Spring", r"(?<![A-Za-z])spring(?!\s*boot)(?![A-Za-z])"),
    ("Redis", r"(?<![A-Za-z])redis(?![A-Za-z])"),
    ("Linux", r"(?<![A-Za-z])linux(?![A-Za-z])"),
    ("Git", r"(?<![A-Za-z])git(?![A-Za-z])"),
    ("Docker", r"(?<![A-Za-z])docker(?![A-Za-z])"),
    ("Pandas", r"(?<![A-Za-z])pandas(?![A-Za-z])"),
    ("NumPy", r"(?<![A-Za-z])numpy(?![A-Za-z])"),
    ("Excel", r"(?<![A-Za-z])excel(?![A-Za-z])"),
    ("Tableau", r"(?<![A-Za-z])tableau(?![A-Za-z])"),
    ("Power BI", r"(?<![A-Za-z])power\s*bi(?![A-Za-z])"),
    ("Hive", r"(?<![A-Za-z])hive(?![A-Za-z])"),
    ("Spark", r"(?<![A-Za-z])spark(?![A-Za-z])"),
)

OUTPUT_COLUMNS = [
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
]


class SalaryResult(NamedTuple):
    salary_min: int | None
    salary_max: int | None
    salary_months: int | None


def normalize_text(value: object, default: str | None = None) -> str | None:
    """Trim text and collapse internal whitespace without inventing content."""
    if value is None or pd.isna(value):
        return default
    normalized = re.sub(r"\s+", " ", str(value)).strip()
    return normalized if normalized else default


def normalize_city(value: object) -> str:
    """Normalize known city variants while preserving unknown city names."""
    city = normalize_text(value, "未知")
    assert city is not None

    compact_city = re.sub(r"\s+", "", city)
    for canonical in ("北京", "上海", "深圳", "杭州", "广州"):
        if compact_city == canonical or compact_city.startswith(
            (f"{canonical}市", f"{canonical}·", f"{canonical}-", f"{canonical}—")
        ):
            return canonical
    return city


def classify_job_category(title: object) -> str:
    """Classify a title using an ordered and maintainable keyword mapping."""
    normalized_title = (normalize_text(title, "") or "").casefold()
    for category, keywords in CATEGORY_KEYWORDS:
        if any(keyword.casefold() in normalized_title for keyword in keywords):
            return category
    return "其他"


def _monthly_amount(value: str) -> int:
    return int((Decimal(value) * 1000).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _daily_to_monthly(value: str) -> int:
    return int(
        (Decimal(value) * WORKING_DAYS_PER_MONTH).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
    )


def parse_salary(value: object) -> SalaryResult:
    """Convert supported salary text to monthly RMB without fabricating values."""
    salary = normalize_text(value)
    if salary is None or salary.casefold() in {"面议", "薪资面议"}:
        return SalaryResult(None, None, None)

    compact_salary = re.sub(r"\s+", "", salary).replace("—", "-").replace("–", "-")

    monthly_match = re.fullmatch(
        r"(\d+(?:\.\d+)?)[kK]?-(\d+(?:\.\d+)?)[kK](?:[·xX*]?(\d+)薪)?",
        compact_salary,
    )
    if monthly_match:
        minimum, maximum, months = monthly_match.groups()
        return SalaryResult(
            _monthly_amount(minimum),
            _monthly_amount(maximum),
            int(months) if months else DEFAULT_SALARY_MONTHS,
        )

    daily_range_match = re.fullmatch(
        r"(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)(?:元)?/天", compact_salary
    )
    if daily_range_match:
        minimum, maximum = daily_range_match.groups()
        return SalaryResult(
            _daily_to_monthly(minimum),
            _daily_to_monthly(maximum),
            DEFAULT_SALARY_MONTHS,
        )

    daily_single_match = re.fullmatch(r"(\d+(?:\.\d+)?)(?:元)?/天", compact_salary)
    if daily_single_match:
        amount = _daily_to_monthly(daily_single_match.group(1))
        return SalaryResult(amount, amount, DEFAULT_SALARY_MONTHS)

    return SalaryResult(None, None, None)


def extract_skills(title: object, description: object = "") -> str:
    """Extract canonical skill names once, in stable dictionary order."""
    text = " ".join(
        part for part in (normalize_text(title, ""), normalize_text(description, "")) if part
    )
    skills = [
        skill
        for skill, pattern in SKILL_PATTERNS
        if re.search(pattern, text, flags=re.IGNORECASE)
    ]
    return "|".join(skills)


def clean_dataframe(raw_df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    """Apply all cleaning rules and return both clean data and quality metrics."""
    required_columns = {
        "source_id",
        "title",
        "company",
        "city",
        "education",
        "salary",
        "description",
        "publish_date",
    }
    missing_columns = required_columns.difference(raw_df.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing_columns))}")

    cleaned = raw_df.copy()
    raw_rows = len(cleaned)

    cleaned["source_id"] = cleaned["source_id"].map(lambda value: normalize_text(value, ""))
    cleaned["title"] = cleaned["title"].map(lambda value: normalize_text(value))
    missing_title_mask = cleaned["title"].isna()
    rows_dropped_missing_title = int(missing_title_mask.sum())
    cleaned = cleaned.loc[~missing_title_mask].copy()

    cleaned["company"] = cleaned["company"].map(
        lambda value: normalize_text(value, "未知公司")
    )
    cleaned["city"] = cleaned["city"].map(normalize_city)
    cleaned["education"] = cleaned["education"].map(
        lambda value: normalize_text(value, "不限")
    )
    cleaned["description"] = cleaned["description"].map(
        lambda value: normalize_text(value, "")
    )
    cleaned["publish_date"] = pd.to_datetime(
        cleaned["publish_date"], errors="coerce"
    ).dt.strftime("%Y-%m-%d")
    cleaned["publish_date"] = cleaned["publish_date"].fillna("")

    cleaned["category"] = cleaned["title"].map(classify_job_category)
    salary_results = cleaned["salary"].map(parse_salary)
    cleaned["salary_min"] = pd.array(
        [result.salary_min for result in salary_results], dtype="Int64"
    )
    cleaned["salary_max"] = pd.array(
        [result.salary_max for result in salary_results], dtype="Int64"
    )
    cleaned["salary_months"] = pd.array(
        [result.salary_months for result in salary_results], dtype="Int64"
    )
    cleaned["skills"] = cleaned.apply(
        lambda row: extract_skills(row["title"], row["description"]), axis=1
    )

    deduplication_key = ["title", "company", "city", "publish_date"]
    before_deduplication = len(cleaned)
    cleaned = cleaned.drop_duplicates(subset=deduplication_key, keep="first").copy()
    duplicate_rows_removed = before_deduplication - len(cleaned)

    cleaned = cleaned[OUTPUT_COLUMNS].reset_index(drop=True)
    salary_parsed = int(cleaned["salary_min"].notna().sum())
    report: dict[str, object] = {
        "raw_rows": raw_rows,
        "duplicate_rows_removed": duplicate_rows_removed,
        "rows_dropped_missing_title": rows_dropped_missing_title,
        "clean_rows": len(cleaned),
        "salary_parsed": salary_parsed,
        "salary_missing_unparsed": len(cleaned) - salary_parsed,
        "category_distribution": cleaned["category"].value_counts().to_dict(),
        "city_count": int(cleaned["city"].nunique()),
    }
    return cleaned, report


def print_quality_report(report: dict[str, object]) -> None:
    print(f"Raw rows: {report['raw_rows']}")
    print(f"Duplicate rows removed: {report['duplicate_rows_removed']}")
    print(f"Rows dropped due to missing title: {report['rows_dropped_missing_title']}")
    print(f"Clean rows: {report['clean_rows']}")
    print(f"Salary parsed: {report['salary_parsed']}")
    print(f"Salary missing/unparsed: {report['salary_missing_unparsed']}")
    print("Category distribution:")
    for category, count in report["category_distribution"].items():
        print(f"  {category}: {count}")
    print(f"城市数量: {report['city_count']}")


def write_markdown_report(report: dict[str, object], path: Path) -> None:
    category_lines = "\n".join(
        f"- {category}：{count}"
        for category, count in report["category_distribution"].items()
    )
    salary_parsed = int(report["salary_parsed"])
    clean_rows = int(report["clean_rows"])
    success_rate = salary_parsed / clean_rows if clean_rows else 0
    content = f"""# 招聘模拟数据清洗报告

> 本报告中的岗位记录全部为模拟测试数据，不代表任何真实企业的招聘信息。

## 原始数据问题

样例数据包含岗位名和城市写法不统一、大小写差异、字段缺失、重复岗位，以及月薪、日薪、面议和无法解析等混合薪资格式。

## 清洗规则

- 缺失岗位名称的记录直接删除。
- 公司、城市、学历和描述分别使用“未知公司”“未知”“不限”和空字符串补齐。
- 城市统一北京、上海、深圳、杭州和广州的“市”、城区后缀写法；未知城市保留原值。
- 使用 `title + company + city + publish_date` 作为业务去重键。
- 薪资解析失败时保留缺失值，不用 0 代替。

## 薪资转换规则

- K 制月薪转换为人民币元，普通月薪按 12 薪记录。
- `N-MK·X薪` 的月薪范围和发薪月数分别保存。
- 日薪按照 `月薪 = 日薪 × 21.75` 折算，并四舍五入到整数元。
- 面议、空值和无法识别的格式保留为缺失值。

## 岗位分类规则

分类关键词按顺序配置为数据开发、数据分析、算法、测试、后端开发；未命中规则时归为“其他”。

## 技能抽取规则

从岗位名称与描述合并文本中按固定词典抽取技能，忽略英文大小写并统一常见别名；每项技能只保留一次，以 `|` 分隔。独立的 SQL 边界匹配避免从 MySQL 或 PostgreSQL 中重复抽取 SQL。

## 处理结果

- 原始记录数：{report['raw_rows']}
- 缺失岗位名称删除数：{report['rows_dropped_missing_title']}
- 重复记录删除数：{report['duplicate_rows_removed']}
- 清洗后记录数：{report['clean_rows']}
- 薪资解析成功数：{report['salary_parsed']}
- 薪资缺失或无法解析数：{report['salary_missing_unparsed']}
- 薪资解析成功率：{success_rate:.2%}
- 城市种类数：{report['city_count']}

### 类别分布

{category_lines}
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> None:
    raw_df = pd.read_csv(RAW_DATA_PATH, encoding="utf-8-sig", dtype="string")
    cleaned_df, report = clean_dataframe(raw_df)

    PROCESSED_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    cleaned_df.to_csv(PROCESSED_DATA_PATH, index=False, encoding="utf-8-sig")
    write_markdown_report(report, REPORT_PATH)
    print_quality_report(report)
    print(f"Output: {PROCESSED_DATA_PATH}")


if __name__ == "__main__":
    main()
