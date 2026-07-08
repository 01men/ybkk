# 工具栈基线

> 第一份从 `02-tooling-checklist.md` 选完填好；每次有变动 commit 一行 `YYYY-MM-DD: <变更>`。

## 选型（替换占位符）

| 类目 | 选择 | 备注 |
|---|---|---|
| 主模型 | `<Claude Sonnet 4.5 / DeepSeek-V3 / GPT-5 ...>` | 跑开发和需求 |
| 审查模型 | `<Claude Opus 4 / ...>` | 跑审查和方案 |
| IDE / Agent 客户端 | `<Claude Code / Cursor / Mavis>` | |
| 仓库 | `<GitHub / Gitee / GitLab>` | |
| 部署 | `<Vercel / Cloudflare Pages / 阿里云 / 腾讯云>` | |
| 数据库（按业务） | `<Supabase / Neon / 阿里云 RDS / 无>` | |
| 对象存储（按业务） | `<Cloudflare R2 / 阿里云 OSS / 腾讯云 COS / 无>` | |
| 邮件（按业务） | `<Resend / 阿里云邮件推送 / SendGrid / 无>` | |
| 通知 | `<飞书 / 企微 / Slack / 邮件>` | |
| 支付（按业务） | `<Stripe / 支付宝 / 微信支付 / 无>` | |
| 监控（可选） | `<Sentry / 自建 / 无>` | |

## 更新记录

- YYYY-MM-DD（今天）：V1 建立，初始工具栈选型
