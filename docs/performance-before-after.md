# MySQL 性能优化前后对比

## 测试口径

- 数据库：`recruit_insight_perf`
- MySQL：8.4.9
- 数据性质：程序生成的模拟压力测试数据，不是真实招聘数据
- 数据量：`job` 30,000、`skill` 18、`job_skill` 119,971
- 随机种子：`20260928`
- 每条 SQL：预热 3 次，正式测量 10 次
- 主要指标：10 次正式测量的 median；同时保留 min/max
- 前后使用相同数据、SQL、参数和本机环境

59 条正常演示数据不足以形成可信的索引结论，因此所有数据库性能数字均来自隔离的性能数据库。原始机器可读结果见 `docs/benchmark-results/before.json` 与 `after.json`。

## 查询集合

| 编号 | 项目实际查询模式 |
| --- | --- |
| A | city + category 深分页，按 `publish_date DESC, id DESC` 排序 |
| B | 单 city 分页与排序 |
| C | 单 category 分页与排序 |
| D | city + category 的分页 COUNT |
| E | 全量 Skills Top 10 |
| F | category 下 Skills Top 10 |
| G | cities GROUP BY |
| H | salary GROUP BY |
| I | `title LIKE '%Java%'` 分页与排序 |

## 真实性能结果

时间单位为毫秒，格式为 `min / median / max`。提升率按 `(before median - after median) / before median` 计算；负值表示本轮实测变慢。

| Query | Before | After | Median 提升率 |
| --- | ---: | ---: | ---: |
| A | 8.5276 / 9.4676 / 11.2285 | 0.7131 / 0.8431 / 10.3479 | 91.09% |
| B | 7.9086 / 8.4480 / 10.2523 | 0.4127 / 0.4586 / 0.8302 | 94.57% |
| C | 8.8329 / 9.8742 / 14.7316 | 0.3739 / 0.4049 / 0.4762 | 95.90% |
| D | 4.7411 / 4.9188 / 5.8031 | 0.3044 / 0.3456 / 0.4158 | 92.97% |
| E | 146.0456 / 156.8076 / 161.6568 | 156.7055 / 167.4717 / 185.1609 | -6.80% |
| F | 45.6329 / 47.2603 / 50.3578 | 45.6426 / 51.0752 / 60.5636 | -8.07% |
| G | 9.6724 / 10.1635 / 14.7124 | 3.5035 / 3.6256 / 5.4452 | 64.33% |
| H | 18.6905 / 21.0575 / 22.5245 | 8.1515 / 8.6212 / 11.3859 | 59.06% |
| I | 9.0329 / 9.2824 / 11.9590 | 9.2539 / 10.2279 / 12.2196 | -10.19% |

本地亚毫秒级查询容易出现调度与缓存噪声，例如 A 的 after 最大值有一次 10.3479 ms 离群值，因此结论以 median 和执行计划共同判断，不使用单次最好结果。

## EXPLAIN / EXPLAIN ANALYZE 关键变化

### 明显提升

- A：从 `type=ALL`、扫描约 29,571 行并 `Using filesort`，变为使用 `idx_job_city_category_publish` 的 `ref` 查找；估算匹配 928 行，`EXPLAIN ANALYZE` 只读取满足 OFFSET/LIMIT 所需的 220 行。
- B：从全表扫描与 filesort，变为 `idx_job_city_publish` range scan；`EXPLAIN ANALYZE` 读取 20 行后即可停止。
- C：从全表扫描与 filesort，变为 `idx_job_category_publish` ref lookup；读取 20 行后停止。
- D：从全表扫描约 30,000 行，变为对 city/category 组合索引的 covering lookup，共计数 928 行。
- G：仍需读取 30,000 条索引记录，但从表扫描 + 临时聚合变为 city-leading covering index scan 和流式分组，median 降低 64.33%。
- H：最终 category 索引追加 `salary_min`、`salary_max` 覆盖列，`EXPLAIN ANALYZE` 显示 covering index scan；虽然仍读取 30,000 条索引记录并过滤出 26,986 条有效薪资记录，但避免回表，median 降低 59.06%。

### 提升不明显或出现波动

- E：原有 `idx_job_skill_skill_id`、`job_skill` 主键和 `job` 主键已经被正确使用。查询仍需处理 119,971 条关系并做临时聚合与排序，新 job 索引没有减少该工作量；本轮 median 波动为 -6.80%。
- F：job 访问从全表扫描变为 category covering lookup，但仍需处理该类别的 8,850 个岗位和 35,333 条关系并聚合；端到端 median 本轮为 -8.07%，不能宣称加速。
- I：执行计划前后均为 `type=ALL`、约 29,571 估算行、`Using where; Using filesort`；-10.19% 属于未减少工作量情况下的本地波动。

## `LIKE '%Java%'` 结论

前导通配符使普通 B-Tree 无法从字符串左侧定位搜索范围，因此没有为了好看的数字添加 `title` 普通索引。当前 30,000 条模拟数据规模无需引入 Elasticsearch。未来只有在全文检索需求和数据规模实际增长时，再评估 MySQL FULLTEXT 或 Elasticsearch。

## 缓存基准（正常 59 条演示库）

`GET /api/statistics/overview` 使用 localhost 做 10 组成对测量；每组先删除目标 key 测 miss，再立即请求相同接口测 hit：

| 场景 | min | median | max |
| --- | ---: | ---: | ---: |
| Cache Miss | 5.4353 ms | 18.6485 ms | 25.9837 ms |
| Cache Hit | 3.0006 ms | 8.6194 ms | 23.9471 ms |

实际 `TTL statistics:overview` 返回 Redis 整数 600。正常库只有 59 条数据，命中与未命中的差异有限，这是预期结果，不应解释为巨大性能收益。原始样本见 `docs/benchmark-results/cache-normal.json`。
