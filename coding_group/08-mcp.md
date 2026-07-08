# 3 个 MCP：让 AI 在受控边界内动外部系统

> MCP (Model Context Protocol) = AI 拿到的不是"通用 HTTP 工具"，而是"专门对接这个系统的窄接口"。这一章把 3 个 MCP 是什么、怎么接、怎么用讲清楚。

---

## 三个 MCP 各自管什么

| MCP | 干什么 | 用在哪个阶段 | 触发频次 |
|---|---|---|---|
| **GitHub MCP** | 创建 PR / 推 commit / 关联分支 / 拉 review 评论 | 初始化 + 交付收尾 | 每需求 2~4 次 |
| **Deploy MCP** | 触发 staging / 触发生产部署 / 拿回部署 URL / 健康检查 | 验证 + 交付 | 每需求 1~2 次 |
| **Notify MCP** | 发飞书 / 企微 / Slack 通知（带 PR + 部署 URL + reviewer） | 交付收尾 | 每需求 1 次 |

---

## 三个 MCP 的设计原则（文章里的真金白银）

1. **读多写少**：能读的尽量多接。TAPD 详情 / 仓库既有 MR / 部署历史——这些是 AI 判断"要不要做"的上下文。写的方法要严格挑选。

2. **写操作必须有清晰触发点**：3 个 MCP 的写操作只在「初始化」「交付收尾」两个阶段触发。其他阶段一概只读。

3. **MCP 调用全部留痕**：每次写操作都要在制品里留一条记录（含：调的方法 / 入参 / 返回 / 时间戳）。

4. **写操作必须幂等**：「关联 git 分支」必须按 (仓库, 分支) 二元组判重，重复关联直接跳过。否则交付收尾阶段重跑就灌一堆重复内容。

5. **失败软降级**：MCP 失败只警告，不阻断。一次发通知失败不算大事，下一轮自然补发。

---

## GitHub MCP

### 提供的最小方法集

```typescript
// 读
gh_read_repo_structure(path: string): TreeNode[]
gh_list_open_prs(): PR[]
gh_read_pr_comments(pr_id: string): Comment[]
gh_read_file(path: string, ref?: string): string

// 写（只在初始化 / 交付时调用）
gh_create_branch(base: string, new_branch: string, repo?: string): void  // 幂等
gh_commit_files(branch: string, files: File[], message: string): void     // 幂等
gh_create_pr(head: string, base: string, title: string, body: string, reviewers?: string[]): PR
gh_add_pr_comment(pr_id: string, body: string): void
gh_request_review(pr_id: string, reviewers: string[]): void
gh_merge_pr(pr_id: string, method: 'squash' | 'rebase' | 'merge'): void
```

### 关键提醒

- PR body 用模板，含：任务清单勾选、5 道门禁结果、reviewer 报告链接
- 推荐 reviewer 自动从 CODEOWNERS + 历史作者拿
- 合并必须 squash + 等 CI 全过

---

## Deploy MCP

### 提供的最小方法集

```typescript
// 读
deploy_get_latest_deployments(environment: 'staging' | 'production'): Deployment[]
deploy_get_health(environment: 'staging' | 'production'): HealthStatus

// 写
deploy_trigger(environment: 'staging' | 'production', version?: string): Deployment  // 幂等：同版本跳过
deploy_rollback(environment: 'staging' | 'production', to_version: string): void
```

### 部署平台适配（路径 B 才需要，路径 A 用 Mavis 内置）

| 平台 | 实现 |
|---|---|
| Vercel | `npx vercel --target=staging` + `vercel ls` |
| Cloudflare Pages | `wrangler pages deploy` + `wrangler pages deployment list` |
| Netlify | `netlify deploy --prod` + `netlify status` |
| 阿里云 | 阿里云 CLI + 容器镜像服务 API |
| Fly.io | `fly deploy` + `fly status` |

### 关键提醒

- 部署写到环境变量 `DEPLOY_STAGING_URL`、`DEPLOY_PRODUCTION_URL`
- 健康检查超时 60 秒；超时回退走 `deploy_rollback`
- 部署后必须等 `health.ok == true` 才视为"完成"

---

## Notify MCP

### 提供的最小方法集

```typescript
notify_feishu(webhook_url: string, payload: FeishuPayload): void
notify_wecom(webhook_url: string, payload: WecomPayload): void
notify_slack(webhook_url: string, payload: SlackPayload): void
notify_email(to: string, subject: string, body: string): void
```

### 飞书示例 payload

```json
{
  "msg_type": "interactive",
  "card": {
    "header": {
      "title": {"tag": "plain_text", "content": "✅ REQ-001 已上线"}
    },
    "elements": [
      {
        "tag": "div",
        "text": {"tag": "plain_text", "content": "需求：用户登录\nPR: https://github.com/...\n部署: https://...\nReviewer: ..."}
      }
    ]
  }
}
```

### 关键提醒

- 飞书 webhook 在群机器人里加（群设置 → 群机器人 → 添加机器人 → 自定义 webhook）
- Webhook URL **不要进 git**，放进部署平台 secret 或本地 `.env`
- 通知失败不阻断交付，但记录到制品

---

## MCP 在 Harness 里的位置（再强调）

> **MCP 不是 Harness 的主体**。Harness 的主体是：
> - Workflow（流程）
> - Skill（操作手册）
> - Agent（角色）
> - Scripts（门禁）
> - Rule（家法）
>
> MCP 只是**外接能力**——让 AI 能动外部系统。

如果开发闭环本身不稳，接 MCP 只会让 bug 影响范围扩大到外部系统。所以：

- 路径 A：你把 MCP 配置交给我（说「用 GitHub MCP」、「用飞书 MCP」），我接
- 路径 B：你自己配置（下面有最简实现）

---

## 路径 B 的最简实现（不是完整 MCP，是直接调用封装）

如果你用 Claude Code，不需要完整的 MCP server。直接在 `assets/prompts/orchestrator.md` 加这些调起配置：

```
.claude/
├── mcp/
│   ├── github.json            # GitHub MCP 配置
│   ├── deploy.json            # Deploy MCP 配置
│   └── notify.json            # Notify MCP 配置
└── commands/
    └── (各种 slash command)
```

`.claude/mcp/github.json` 示例：

```json
{
  "name": "github",
  "type": "mcp",
  "command": "node",
  "args": [".claude/mcp/servers/github-server.js"],
  "env": {
    "GITHUB_TOKEN": "${GITHUB_TOKEN}"
  }
}
```

> 完整 MCP server 实现略——但 Claude Code 也有更简单的：用 `gh` CLI 直接调，包装一层 shell 函数。

---

## 你接下来要做什么

按路径 A 走：你只需要告诉我「飞书 webhook URL 是 X」、「Vercel token 在 Y」，我接。
按路径 B 走：自己按上面贴 github.json 的格式配，或者直接 `gh` CLI 包一层。

---

## 下一步

- 想看「出问题了怎么排查」→ [09-runbook.md](09-runbook.md)
- 想看「体系怎么跟着产品长大」→ [10-evolve.md](10-evolve.md)
