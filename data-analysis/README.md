# 招聘模拟数据清洗 Pipeline

本目录使用 Pandas 将带有常见质量问题的模拟招聘 CSV 清洗为结构统一的数据集。所有记录均为模拟测试数据，不来自真实招聘网站。

## 运行

从项目根目录执行：

```powershell
python data-analysis/src/clean_jobs.py
```

输入文件为 `dataset/raw/jobs_raw_sample.csv`，输出文件为 `dataset/processed/jobs_cleaned.csv`。脚本通过自身位置计算项目根目录，不依赖 Shell 当前目录。

## 测试

```powershell
python -m unittest discover -s data-analysis/tests -v
```

## 主要规则

- 缺失岗位名称的记录删除；其他文本字段按规则补齐。
- 城市统一常见的“市”和城区后缀写法。
- 薪资统一为人民币月薪，日薪按每月 21.75 个工作日折算。
- 月薪范围与一年发薪月数分开保存。
- 业务去重键为 `title + company + city + publish_date`，用于识别同一公司、同一城市、同一天发布的同名岗位。
- 技能采用固定词典、大小写无关匹配和规范名称输出。
