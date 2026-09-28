# 招聘模拟数据统计 SQL

> 以下查询只分析 RecruitInsight 项目中的模拟岗位数据，不代表真实招聘市场。

## 热门技能

```sql
SELECT s.name,
       COUNT(*) AS job_count
FROM job_skill js
JOIN skill s ON s.id = js.skill_id
JOIN job j ON j.id = js.job_id
WHERE j.category = ?
GROUP BY s.id, s.name
ORDER BY job_count DESC, s.name ASC
LIMIT ?;
```

`job_skill` 将岗位与技能关联，两个 JOIN 用于取得技能名称和可选的岗位类别。`GROUP BY` 将同名技能归组，`COUNT(*)` 计算要求该技能的岗位数，`ORDER BY` 先按岗位数降序、再按技能名升序稳定排序。类别和数量均使用参数化查询。

## 城市岗位数量

```sql
SELECT city,
       COUNT(*) AS job_count
FROM job
GROUP BY city
ORDER BY job_count DESC, city ASC;
```

`GROUP BY city` 为每个城市建立分组，`COUNT(*)` 统计组内岗位，排序规则保证数量相同时结果稳定。“未知”城市不会被隐式过滤。

## 类别岗位数量

```sql
SELECT category,
       COUNT(*) AS job_count
FROM job
GROUP BY category
ORDER BY job_count DESC, category ASC;
```

数据库负责类别分组和计数。Service 使用这些计数计算各类别占全部岗位的百分比，并四舍五入到两位小数。

## 类别月薪统计

```sql
SELECT category,
       COUNT(*) AS job_count,
       CAST(ROUND(AVG(salary_min), 0) AS SIGNED) AS average_salary_min,
       CAST(ROUND(AVG(salary_max), 0) AS SIGNED) AS average_salary_max,
       CAST(ROUND(AVG((salary_min + salary_max) / 2.0), 0) AS SIGNED)
           AS average_salary_mid
FROM job
WHERE salary_min IS NOT NULL
  AND salary_max IS NOT NULL
GROUP BY category
ORDER BY job_count DESC, category ASC;
```

`WHERE` 明确限定上下界都已知的岗位，使 `COUNT(*)` 与三个 `AVG` 使用完全相同的数据集合。虽然 MySQL 的 `AVG` 本身会忽略 NULL，显式条件仍能避免岗位数量与平均值口径不一致。结果按月薪人民币元四舍五入为整数，不使用 `salary_months` 计算年薪。
