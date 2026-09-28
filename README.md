# RecruitInsight

RecruitInsight 是一个用于学习和作品展示的招聘数据分析平台。当前已包含岗位查询后端和基于 Pandas 的模拟招聘数据清洗 Pipeline。

## 当前范围

- 后端：Java 21、Spring Boot、Maven、MyBatis-Plus、MySQL
- API：`GET /api/jobs`
- 数据库：`recruit_insight`
- 数据表：`job`
- 数据处理：Python 3.12、Pandas

前端暂不开发。当前 Python Pipeline 只处理模拟 CSV，不写入 MySQL。

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
5. `004_extend_job_table.sql`
6. `005_create_skill_tables.sql`
7. `006_prepare_clean_import.sql`

`002` 和 `003` 用于后端查询阶段的模拟数据；执行 `006` 会在正式导入清洗数据前清除这些旧记录。所有脚本都不包含数据库密码，测试数据中的公司均为明确的示例名称。

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

## Data Processing

当前数据处理与查询流程为：

```text
模拟 raw CSV
→ Pandas cleaning
→ processed CSV
→ PyMySQL importer
→ job / skill / job_skill
→ Spring Boot API
```

从项目根目录运行：

```powershell
python data-analysis/src/clean_jobs.py
```

输入：`dataset/raw/jobs_raw_sample.csv`

输出：`dataset/processed/jobs_cleaned.csv`

执行基础测试：

```powershell
python -m unittest discover -s data-analysis/tests -v
```

数据库导入程序为 `data-analysis/src/import_jobs.py`。连接信息从 `DB_HOST`、`DB_PORT`、`DB_NAME`、`DB_USERNAME` 和 `DB_PASSWORD` 环境变量读取，不能写入仓库。执行 migration 与本地模拟数据清理后运行：

```powershell
python data-analysis/src/import_jobs.py
```

岗位通过唯一 `source_id` 幂等更新，技能和岗位技能关系分别保存在 `skill` 与 `job_skill` 表中。数据库设计说明见 `docs/database-design.md`。

## Statistics API

以下接口基于项目当前的模拟数据集，由 MySQL 使用 `JOIN`、`GROUP BY`、`COUNT` 和 `AVG` 完成主要聚合：

```text
GET /api/statistics/overview
GET /api/statistics/skills
GET /api/statistics/skills?limit=5&category=后端开发
GET /api/statistics/cities
GET /api/statistics/categories
GET /api/statistics/salary
```

`skills` 的 `limit` 默认为 10，允许范围为 1～50，`category` 为可选精确筛选条件。薪资接口只统计月薪上下界均已知的岗位，结果单位为人民币元/月。核心查询及解释见 `docs/statistics-sql.md`。

所有当前分析结果均为项目模拟数据统计结果，不能解释为真实招聘市场结论。

## Frontend

前端采用 Vue 3、Vite、Axios 和 ECharts，实现单页招聘模拟数据分析 Dashboard，包括数据概览、热门技能、城市岗位、类别分布、月薪对比以及带后端分页的岗位查询。

开发时需要同时启动后端和前端：

Terminal 1：

```powershell
cd backend
mvn spring-boot:run '-Dspring-boot.run.profiles=local'
```

Terminal 2：

```powershell
cd frontend
npm install
npm run dev
```

浏览器访问 `http://127.0.0.1:5173`。Vite 开发服务器将 `/api` 请求代理到 `http://localhost:8080`，因此无需为开发环境在 Spring Boot 中开放全局 CORS。

生产构建：

```powershell
cd frontend
npm run build
```

`frontend/dist/` 为构建产物并已被 Git 忽略。Dashboard 中的所有数据仍为项目模拟数据，仅用于功能演示。

目前所有招聘记录均为模拟测试数据，不代表真实企业招聘信息，也不来自招聘网站爬取。
