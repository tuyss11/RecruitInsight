# RecruitInsight 性能优化设计

## 1. 为什么不用 59 条数据测试数据库性能

正常演示数据库 `recruit_insight` 必须保持 59 条模拟岗位，用于 Dashboard 和 API 回归。这个数据量通常全部位于内存，优化器也可能合理选择全表扫描，无法反映索引对扫描范围、排序和深分页的作用。因此本阶段建立独立的 `recruit_insight_perf`，所有记录均明确标记为“程序生成的模拟压力测试数据”。

## 2. 性能数据生成与导入

`data-analysis/src/generate_perf_data.py` 使用固定种子 `20260928` 生成可复现 CSV，包含 10 个城市、6 个类别、18 个既有标准技能、合理薪资范围及约 10% 未知薪资。公司名均为 `性能测试公司0001` 一类虚构名称，描述中也包含模拟数据声明。

生成文件位于 `dataset/perf/jobs_perf.csv`，已被 Git 忽略。独立 importer 只允许数据库名 `recruit_insight_perf`，会拒绝正常库名称：

```powershell
python data-analysis/src/generate_perf_data.py
python data-analysis/src/import_perf_jobs.py --prompt-credentials
```

实际导入数量：

- `job`：30,000
- `skill`：18
- `job_skill`：119,971

性能库字符集为 `utf8mb4`，排序规则为 `utf8mb4_0900_ai_ci`。终端密码输入不回显、不写入文件；仓库不包含数据库凭据。

## 3. Benchmark 方法

`benchmark_queries.py` 测试项目实际使用的分页、分页 COUNT、技能 Top 10、城市/薪资分组以及前导通配符关键词查询。每条 SQL 预热 3 次并正式执行 10 次，记录 min/median/max，同时保存标准 `EXPLAIN` 和 MySQL 8 `EXPLAIN ANALYZE`。

```powershell
python data-analysis/src/benchmark_queries.py --label before --prompt-credentials
python data-analysis/src/apply_perf_indexes.py --prompt-credentials
python data-analysis/src/benchmark_queries.py --label after --prompt-credentials
```

完整结果和解释见 `docs/performance-before-after.md`。

## 4. 基线索引与问题

优化前只有：

- `job.PRIMARY(id)`
- `job.uk_job_source_id(source_id)`
- `skill.PRIMARY(id)` 与 `uk_skill_name(name)`
- `job_skill.PRIMARY(job_id, skill_id)` 与 `idx_job_skill_skill_id(skill_id)`

A/B/C/D 的 job 查询均为全表扫描；分页查询还需 filesort。F 为类别筛选扫描全部 30,000 个岗位。E 已正确利用关系表和主键索引，因此没有重复创建关系表索引。

## 5. 最终索引

迁移文件为 `sql/007_add_query_indexes.sql`，最终只保留 3 个业务索引：

1. `idx_job_city_category_publish(city, category, publish_date DESC, id DESC)`：服务 city + category 分页及分页 COUNT；等值列在前、排序列在后。
2. `idx_job_city_publish(city, publish_date DESC, id DESC)`：单 city 分页不能跨过第一个索引中的 category 保持排序，因此需要独立顺序；同时为城市 GROUP BY 提供 covering scan。
3. `idx_job_category_publish(category, publish_date DESC, id DESC, salary_min, salary_max)`：前三列服务单 category 分页与类别技能统计，末尾薪资列使 salary GROUP BY 成为 covering scan。

没有增加大量单列或重复索引。代价是额外磁盘空间以及 INSERT/UPDATE 时维护 3 棵 B-Tree；这是针对已验证读查询的明确权衡。

最终索引可幂等应用到保持 59 条数据的正常数据库；该助手只创建缺少的索引，不删除表或数据：

```powershell
python data-analysis/src/apply_normal_indexes.py --prompt-credentials
```

## 6. LIKE 限制

`title LIKE '%Java%'` 的开头是通配符，普通 B-Tree 无法定位连续前缀范围。实测优化前后均扫描全部 30,000 行且使用 filesort，所以没有添加无效的 title B-Tree 索引。未来可按真实需求评估 MySQL FULLTEXT 或 Elasticsearch，当前阶段不做过度设计。

## 7. Redis 与 Spring Cache

本机 Redis 使用 WSL 2、Ubuntu 24.04 LTS 和 Redis 官方 `packages.redis.io` APT 仓库安装，Redis 8.10.2 只用于本地开发。安全配置保持：

```text
bind 127.0.0.1 -::1
port 6379
protected-mode yes
```

没有配置密码，也没有监听 `0.0.0.0`。Windows Spring Boot 通过 `localhost:6379` 访问 WSL Redis。连接地址来自 `REDIS_HOST`、`REDIS_PORT`，仓库中没有 Redis 密码。

当前 WSL 2.7 环境会在没有 Windows 客户端会话时自动停止发行版。进行本地开发时，先打开并保持一个 Ubuntu 会话；systemd 会启动已启用的 Redis 服务：

```powershell
wsl -d Ubuntu-24.04
```

如果 Redis 未运行，在 Ubuntu 中执行 `sudo systemctl start redis-server`。没有通过改成 `0.0.0.0` 或关闭 protected mode 来绕过 WSL 生命周期问题。

后端通过 Spring Cache abstraction 缓存 Statistics Service，不在 Controller 中直接操作 `RedisTemplate`。缓存接口：

- `/api/statistics/overview`
- `/api/statistics/skills`
- `/api/statistics/cities`
- `/api/statistics/categories`
- `/api/statistics/salary`

`/api/jobs` 不缓存，因为分页、关键词、城市、类别和公司组合会形成较大的参数空间，而且已有针对主要筛选/排序的数据库索引。

## 8. Cache Key、TTL 与序列化

实际 key 示例：

```text
statistics:overview
statistics:skills:all:10
statistics:skills:后端开发:10
statistics:skills:数据分析:10
statistics:cities
statistics:categories
statistics:salary
```

skills key 同时包含标准化后的 category 和 limit，避免不同参数互相覆盖。TTL 为 10 分钟（600 秒），实际 Redis TTL 命令已验证返回 600 并随时间下降。

value 使用 JSON 序列化，并通过受限的类型白名单保存 DTO/List 类型信息。实际完成了写入 Redis、从缓存反序列化并再次返回 HTTP JSON 的回归，避免 Java 默认二进制序列化的可读性和版本问题。

## 9. Miss、Hit 与故障行为

验证流程只删除 `statistics:*` 中的目标 key，没有使用 `FLUSHALL`：

- 第一次 overview 请求为 miss：MyBatis 日志出现统计 SQL，响应为 59 条岗位，Redis 写入 `statistics:overview`。
- 第二次相同请求为 hit：响应内容一致，MyBatis 不再输出对应统计 SQL。
- 三组 skills 参数生成三个不同 key；各自第二次请求均不再执行 SQL。
- cities、categories、salary 同样完成 miss/hit 验证。
- `/api/jobs` 每次仍执行分页 COUNT 与查询，确认未进入缓存。

Redis 暂停时，连接在 2 秒超时后由自定义 `CacheErrorHandler` 记录警告，统计接口继续查询 MySQL 并返回 59 条数据；没有为本地项目引入复杂高可用架构。

## 10. 一致性限制

Python importer 直接写 MySQL，不会立即通知 Spring Cache。当前采用 TTL 最终一致性：统计结果最多可能延迟约 10 分钟更新。未来可在导入成功后调用明确的缓存失效机制或发送失效事件，但当前不为此引入消息队列。

## 11. 参考资料

- [Spring Boot Cache](https://docs.spring.io/spring-boot/reference/io/caching.html)
- [Spring Cache annotations](https://docs.spring.io/spring-framework/reference/integration/cache/annotations.html)
- [Spring Data Redis JSON serializer](https://docs.spring.io/spring-data/redis/reference/api/java/org/springframework/data/redis/serializer/GenericJacksonJsonRedisSerializer.html)
- [Redis 官方 Linux APT 安装](https://redis.io/docs/latest/operate/oss_and_stack/install/install-stack/)
