# 工具栈基线

> 第一份从 `02-tooling-checklist.md` 选完填好；每次有变动 commit 一行 `YYYY-MM-DD: <变更>`。
> 本文件由 solution-architect 在 `AIOS-001` 方案棒初始化（之前是占位符）。

## 选型

| 类目 | 选择 | 备注 |
|---|---|---|
| 主模型 | Claude Sonnet 4.5 | 跑开发 / 需求 / 方案 |
| 审查模型 | Claude Opus 4 | 跑审查 |
| IDE / Agent 客户端 | Claude Code | 仓库已用 .claude 规范 |
| 仓库 | GitHub | https://github.com/01men/ybkk |
| 部署 | 自建 K8s / Docker Compose（私有化） | 客户内网部署，不上公有云 |
| 数据库（业务） | PostgreSQL 16（平台自有库） + 客户既有关系型 DB（只读） | 双库策略 |
| 对象存储（业务） | MinIO（私有化部署） | 替代公有 OSS；存客户上传的 Excel/PDF/会议纪要 |
| 本体图存储 | Neo4j 5（私有化部署） | 装本体对象图专用，社区版够用 |
| 缓存 | Redis 7 | 场景模板 / 标准缓存 / 限流 |
| LLM 接入 | 自部署 Qwen2.5-72B（私有化） + 预留 OpenAI/Claude 接口（私有化网关） | 客户数据不出网 |
| OCR / 文档抽取 | PaddleOCR（中文）+ Unstructured（PDF/DOCX） | 离线友好 |
| ETL / 数据元识别 | SQLAlchemy + sqlglot（跨方言） | 支持 MySQL/PostgreSQL/SQL Server/Oracle |
| 工作流引擎 | Temporal（私有化） | 流程执行 / 重试 / 状态机 |
| 消息总线 | NATS（私有化） | 内部事件 / webhook 出站 |
| 监控 | Prometheus + Grafana + Loki（私有化） | 监控 / 日志 / 告警 |
| 通知 | 飞书 / 钉钉 / 企业微信（出站 webhook） | 客户选配 |
| 支付（业务） | 无 | 私有化产品，按许可授权 |
| 邮件 | 无 | 私有化场景不常用邮件 |
| 前端 | Next.js 14（App Router） + TypeScript + Ant Design Pro | 私有化部署 / 服务端组件 |
| 后端 | Python 3.11 + FastAPI + Pydantic v2 | AI 生态成熟 |
| 包管理（前端） | pnpm | |
| 包管理（后端） | uv | |
| 容器化 | Docker + Docker Compose（一键私有化） + Helm（K8s 可选） | |
| CI | GitHub Actions（私有 runner，按需） | 默认本地跑门禁 |

## 更新记录

- 2026-07-08：solution-architect 在 AIOS-001 方案棒初始化技术栈（之前是占位符）
- YYYY-MM-DD（V1）：占位符骨架