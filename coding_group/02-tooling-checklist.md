# 工具栈与账号准备清单

> 你不需要懂编程，所以这一章列得**很死**——照抄，不会错。

---

## 三层划分：必选 / 强烈推荐 / 按业务选

### ✅ 必选（没有就跑不起来）

| 类型 | 具体要什么 | 为什么 | 大约花多少钱 |
|---|---|---|---|
| 大模型订阅 | **Claude Pro / Max**（首选）或 **OpenAI GPT Plus / Team** | 跑团队的算力来源 | Claude Max $200/月，Pro $20/月；GPT Plus $20/月 |
| 一个 IDE | **Claude Code**（CLI 工具）或 **Cursor** | 这是你的"团队总部" | Claude Code 包含在 Claude 订阅里；Cursor Pro $20/月 |
| 一个 Git 仓库 | **GitHub**（推荐）或 Gitee | 代码和制品的家 | 私有仓库免费 |

> **模型怎么选？** 现在（2026 年 7 月）Claude Sonnet 4 / Opus 4 系列在工程化编码任务上稳定度最高。如果你只用 GPT-5 / DeepSeek 系列，记得把审查阶段提到 Opus 级别，开发用 Sonnet 级别。配置方法见 `04-agents.md`。

### 🟡 强烈推荐（至少挑一个）

| 类型 | 具体要什么 | 为什么 | 大约花多少钱 |
|---|---|---|---|
| 部署平台 | **Vercel**（首选，10 分钟搞定）<br>或 Cloudflare Pages / Netlify | 第 9 阶段自动部署 | 免费档够个人项目 |
| 通知通道 | **飞书 / 企微 / Slack webhook** 任一 | 交付收尾时提醒你"做完了" | 完全免费 |
| 域管理（可选） | 阿里云 / 腾讯云 / Cloudflare | 给产品绑定正式域名 | 国内几十块/年，Cloudflare 完全免费 |

> **部署平台怎么选？**
> - 你做**前端 / Next.js / 纯静态**：**Vercel**（首选）或 Cloudflare Pages
> - 你做**全栈 Node / Python / Go**：**Vercel** 也行（支持 serverless），或 **阿里云函数计算**、**腾讯云轻量**
> - 你做**纯后端 / API**：**Fly.io**（免费档有）、**Railway**、**阿里云 ECS**

### 🟢 按业务选（缺就跑对应那块业务）

| 业务类型 | 需要的能力 | 推荐产品（挑一个） | 大约花多少钱 |
|---|---|---|---|
| 用户系统 | 数据库 + 鉴权 | **Supabase**（最省事）/ Neon DB + Clerk / 阿里云 RDS | Supabase 免费档够用 |
| 文件/图片 | 对象存储 | **Cloudflare R2**（10GB 免费）/ 阿里云 OSS / 腾讯云 COS | R2 完全免出流量费 |
| 支付 | 接入支付宝 / 微信 / Stripe | 按地区选 | 按交易抽成 |
| AI 能力 | Embedding / 多模态 / TTS | 你主要用 Claude / GPT 不需要额外买；如果你要专门的 embedding / TTS 再补 | 按调用量 |
| 邮件 | 发注册验证码 / 通知 | **Resend**（免费 100 封/天）/ SendGrid / 阿里云邮件推送 | 免费档够早期 |
| 定时任务 | 跑 cron | 部署平台的 cron + GitHub Actions | 几乎免费 |

---

## 需要申请的 API Key 和凭据

照抄这张表。第一列填名字，第二列填实际拿到的值（**不要把 key 本身直接写在这里**——填到仓库的 `.env.example` 和云端的 secret 里）。

```
# 大模型
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
# 看你用哪个填哪个

# 部署（路径 B 才需要，Vercel 自动 OAuth 一般不需要这个）
VERCEL_TOKEN=
CLOUDFLARE_API_TOKEN=

# 数据库（按你选）
DATABASE_URL=
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

# 对象存储（按你选）
R2_ACCOUNT_ID=
R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=

# 邮件（按你选）
RESEND_API_KEY=

# 通知
FEISHU_WEBHOOK_URL=
WECOM_WEBHOOK_URL=
SLACK_WEBHOOK_URL=

# 支付（按你选）
STRIPE_SECRET_KEY=
ALIPAY_APP_ID=
WECHAT_PAY_MCH_ID=
```

> ⚠️ **不要把真实的 API key 写进仓库或 git 历史**。最稳的做法：把 key 配在部署平台的 Project Settings → Environment Variables 里；本地开发用 `.env` 文件并加进 `.gitignore`。

---

## 国内特殊准备（如果你在国内）

| 事项 | 怎么搞 |
|---|---|
| Claude / OpenAI 访问 | 需要可用的网络代理 + 信用卡 |
| 国内替代方案 | 把"主模型"换成 **DeepSeek-V3** 或 **Kimi K2** 或 **GLM-4.5**（API 兼容 OpenAI 接口），把"审查"阶段用更强的模型 |
| 部署平台 | 国内优先 **阿里云函数计算 / 腾讯云轻量 / Vercel 通过自有域名映射** |
| 通知 | **飞书**（最普及）+ **企微**（企业场景） |
| 支付 | 微信支付（个体工商户可申请）+ 支付宝（个人可申请当面付） |
| ICP 备案 | 国内域名必须备案；用香港或美国节点就不用 |
| 对象存储 / 数据库 | 阿里云 / 腾讯云，OSS / COS / RDS |

> **方案 A（用我）的注意**：你跟我对话时主要告诉我"我已经买了 Claude Max"、"我的代码托管在 GitHub"、"我部署在 Vercel"，剩下的我用 MCP 接进来。你不用自己去申请一堆 API Key。

---

## 把工具栈清单填好之后

把它存到仓库的 `kb/tooling.md`（不存在就创建），每次有变化更新一份。这是团队的"基线知识"，跟代码一起 commit 进去。

格式：

```markdown
# 工具栈基线

| 类目 | 选择 | 备注 |
|---|---|---|
| 主模型 | Claude Sonnet 4.5 | 跑开发和需求 |
| 审查模型 | Claude Opus 4 | 跑审查和方案 |
| IDE | Claude Code | |
| 部署 | Vercel | |
| 数据库 | Supabase | |
| 对象存储 | Cloudflare R2 | |
| 通知 | 飞书 | |
| 监控（可选） | Sentry | |

更新记录：
- 2026-07-08：V1 建立
- YYYY-MM-DD：<变更理由 + 影响面>
```

---

## 你接下来要做什么

1. 把 ✅ 的 3 项买好（Claude 订阅 + GitHub 账号 + IDE）
2. 按你做的产品类型挑 🟡 里的一项
3. 按业务类型挑 🟢 里的若干项
4. **如果你用 Mavis（路径 A），把这份清单发给我，我帮你接好；如果你用路径 B**，自己去 Vercel / Supabase 注册，并把 key 存到 `.env`
