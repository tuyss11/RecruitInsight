# GitHub Readiness Checklist

公开发布前检查（本阶段只准备，不创建远程仓库、不 push）：

- [x] 工作树将在本阶段文档 commit 后保持干净
- [x] Git 跟踪文件与 Git 历史未发现真实密码
- [x] 未跟踪 `.env`
- [x] 未跟踪 `application-local.yml`
- [x] 未跟踪 Redis dump
- [x] 未跟踪生成的 30,000 条 perf CSV
- [x] 未跟踪 `node_modules`、`target`、`dist`、IDE 缓存和 Python 缓存
- [x] README 已按公开作品集结构整理
- [x] Dashboard 截图完成
- [x] Architecture Mermaid 图完成
- [x] Data Pipeline Mermaid 图完成
- [x] ER Mermaid 图完成
- [x] Python、Maven、npm build instructions 已验证
- [x] 正常模拟数据声明明确
- [x] 性能测试数据声明明确
- [ ] License 已决定（当前待仓库所有者选择 MIT 或 Apache-2.0）
- [x] 图片经视觉检查，无账号、密码、通知或桌面隐私信息

## Security Audit Notes

- 关键词审计覆盖 `password`、`passwd`、`DB_PASSWORD`、`secret`、`token`、`api_key`、`access_key`。
- 命中内容均为环境变量名、示例占位符、数据类字段或安全说明。
- Git 历史中未发现 `.env`、`application-local.yml`、私钥、token 文件或真实凭据值。
- 未跟踪大型性能 CSV；Git 历史中没有超过 5 MB 的 blob。
- 仓库当前未配置 remote，本阶段不会自动创建 GitHub 仓库或 push。
