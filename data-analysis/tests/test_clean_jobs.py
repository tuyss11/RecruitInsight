from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd


SRC_PATH = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_PATH))

from clean_jobs import (  # noqa: E402
    SalaryResult,
    classify_job_category,
    clean_dataframe,
    extract_skills,
    normalize_city,
    parse_salary,
)


class ParseSalaryTest(unittest.TestCase):
    def test_k_range(self) -> None:
        self.assertEqual(parse_salary("10-15K"), SalaryResult(10000, 15000, 12))

    def test_k_on_both_bounds(self) -> None:
        self.assertEqual(parse_salary("15K-25K"), SalaryResult(15000, 25000, 12))

    def test_extra_salary_months(self) -> None:
        self.assertEqual(
            parse_salary("15-25K·14薪"), SalaryResult(15000, 25000, 14)
        )

    def test_daily_range(self) -> None:
        self.assertEqual(
            parse_salary("300-400元/天"), SalaryResult(6525, 8700, 12)
        )

    def test_daily_single(self) -> None:
        self.assertEqual(parse_salary("200元/天"), SalaryResult(4350, 4350, 12))

    def test_negotiable(self) -> None:
        self.assertEqual(parse_salary("面议"), SalaryResult(None, None, None))

    def test_none(self) -> None:
        self.assertEqual(parse_salary(None), SalaryResult(None, None, None))

    def test_unrecognized(self) -> None:
        self.assertEqual(parse_salary("一万左右"), SalaryResult(None, None, None))


class NormalizeCityTest(unittest.TestCase):
    def test_beijing_municipality(self) -> None:
        self.assertEqual(normalize_city(" 北京市 "), "北京")

    def test_beijing_district(self) -> None:
        self.assertEqual(normalize_city("北京·海淀"), "北京")

    def test_shanghai_municipality(self) -> None:
        self.assertEqual(normalize_city("上海市"), "上海")

    def test_unknown_city_is_preserved(self) -> None:
        self.assertEqual(normalize_city("成都"), "成都")


class ExtractSkillsTest(unittest.TestCase):
    def test_case_and_aliases(self) -> None:
        self.assertEqual(
            extract_skills("JAVA开发", "熟悉 springboot、Mysql 和 redis"),
            "Java|MySQL|Spring Boot|Redis",
        )

    def test_power_bi_alias(self) -> None:
        self.assertEqual(extract_skills("数据分析", "使用 PowerBI 和 Excel"), "Excel|Power BI")

    def test_sql_is_not_extracted_from_mysql(self) -> None:
        self.assertEqual(extract_skills("开发工程师", "熟悉 MySQL"), "MySQL")

    def test_duplicate_skill_is_removed(self) -> None:
        self.assertEqual(extract_skills("Python实习生", "python Pandas pandas"), "Python|Pandas")


class ClassifyCategoryTest(unittest.TestCase):
    def test_backend(self) -> None:
        self.assertEqual(classify_job_category("Java后端实习生"), "后端开发")

    def test_data_analysis(self) -> None:
        self.assertEqual(classify_job_category("商业数据分析"), "数据分析")

    def test_data_engineering(self) -> None:
        self.assertEqual(classify_job_category("ETL数据开发工程师"), "数据开发")

    def test_algorithm(self) -> None:
        self.assertEqual(classify_job_category("推荐算法实习生"), "算法")

    def test_testing(self) -> None:
        self.assertEqual(classify_job_category("QA测试开发实习生"), "测试")

    def test_other(self) -> None:
        self.assertEqual(classify_job_category("产品运营"), "其他")


class CleanDataframeTest(unittest.TestCase):
    def test_missing_title_defaults_and_business_deduplication(self) -> None:
        raw_df = pd.DataFrame(
            [
                {
                    "source_id": "1",
                    "title": " Java实习生 ",
                    "company": None,
                    "city": "北京市",
                    "education": None,
                    "salary": "10-15K",
                    "description": None,
                    "publish_date": "2026-09-01",
                },
                {
                    "source_id": "2",
                    "title": "Java实习生",
                    "company": "未知公司",
                    "city": "北京",
                    "education": "本科",
                    "salary": "面议",
                    "description": "duplicate",
                    "publish_date": "2026-09-01",
                },
                {
                    "source_id": "3",
                    "title": " ",
                    "company": "示例智能",
                    "city": "上海",
                    "education": "本科",
                    "salary": "8-12K",
                    "description": "missing title",
                    "publish_date": "2026-09-02",
                },
            ]
        )

        cleaned, report = clean_dataframe(raw_df)

        self.assertEqual(len(cleaned), 1)
        self.assertEqual(report["duplicate_rows_removed"], 1)
        self.assertEqual(report["rows_dropped_missing_title"], 1)
        self.assertEqual(cleaned.loc[0, "company"], "未知公司")
        self.assertEqual(cleaned.loc[0, "city"], "北京")
        self.assertEqual(cleaned.loc[0, "education"], "不限")
        self.assertEqual(cleaned.loc[0, "description"], "")


if __name__ == "__main__":
    unittest.main()
