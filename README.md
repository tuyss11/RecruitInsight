# RecruitInsight

RecruitInsight 是一个用于学习和作品展示的招聘数据分析平台。当前阶段只实现后端 MVP：通过 Spring Boot、MyBatis-Plus 和 MySQL 跑通岗位列表查询链路。

## 当前范围

- 后端：Java 21、Spring Boot、Maven、MyBatis-Plus、MySQL
- API：`GET /api/jobs`
- 数据库：`recruit_insight`
- 数据表：`job`

前端与 Python 数据分析暂不开发。

## 本地数据库配置

默认配置从环境变量读取数据库凭据：

- `DB_USERNAME`：本地 MySQL 用户名
- `DB_PASSWORD`：本地 MySQL 密码

也可以复制 `backend/src/main/resources/application-local.example.yml` 为
`application-local.yml`，在副本中填写本地凭据，并使用 `local` profile 启动。
`application-local.yml` 已被 `.gitignore` 忽略，不应提交到 Git。

## 初始化数据库

按顺序执行 `sql` 目录中的脚本：

1. `000_create_database.sql`
2. `001_create_job_table.sql`
3. `002_insert_job_test_data.sql`
4. `003_insert_more_job_test_data.sql`

这些脚本不包含数据库密码。测试数据中的公司均为明确的示例名称。

## 编译与启动

进入 `backend` 目录后执行：

```powershell
mvn clean compile
mvn spring-boot:run '-Dspring-boot.run.profiles=local'
```

应用启动后访问：

```text
http://localhost:8080/api/jobs
```

## 岗位分页查询

`GET /api/jobs` 支持以下可选参数：

| 参数 | 默认值 | 规则 |
| --- | --- | --- |
| `page` | `1` | 必须大于等于 1 |
| `size` | `10` | 必须在 1 到 100 之间 |
| `keyword` | 无 | 岗位名称模糊匹配 |
| `city` | 无 | 城市精确匹配 |
| `category` | 无 | 岗位类别精确匹配 |
| `company` | 无 | 公司名称模糊匹配 |

所有筛选条件可以组合使用，组合时采用 AND 逻辑。例如：

```text
http://localhost:8080/api/jobs?page=1&size=10&keyword=Java&city=上海
```
