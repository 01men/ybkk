# 个人编程 Agent 团队搭建方案

> 你是产品经理 / 创始人 / 业务人员，不懂编程，只想"说一句需求，做一个产品"。
> 这套方案给你一套能照着搭、照着用、照着跑的工程化 Agent 团队。
> 基于一篇腾讯 TAB 团队的 Harness 实战文章，但你是个体开发者，已经按你的场景裁剪过。

---

## 30 秒看懂：这套方案到底在搭什么

把 AI 比作新来的资深实习生。它聪明、上进、什么都能聊两句，但它：

- 不会主动停一下问你"这块你到底想要啥"
- 看见 bug 会装作没看见，含糊过去
- 一兴奋就给你改你没让它改的地方
- 测试覆盖率它说写就"写完了"（其实很多没写）
- 跑完一个需求不会主动把工单、文档、提交流程都走一遍

**本方案 = 给这个实习生一套"工程纪律 + 协作剧本 + 自动门禁"**：

| 层次 | 解决什么 | 在你这边长什么样 |
|---|---|---|
| **Skill** | 它专心做好一件事，别每次都从零想起老套路 | 11 个 `SKILL.md` 文件，每个讲一类任务的"标准操作" |
| **Agent** | 谁负责什么阶段，免得一个 AI 啥都自己说了算还自审 | 4 个子 Agent：需求 / 设计 / 开发 / 审查，加 1 个总控 |
| **Workflow** | 一个需求怎么走完 9 个阶段，谁接谁的棒 | 一份状态机文档，每阶段有产物清单 + 打回规则 |
| **Scripts** | "写完了"必须机器说了算，不是 AI 口头说 | 5 道门禁脚本：覆盖率 / 静态扫描 / 部署冒烟 / E2E / 基线对比 |
| **MCP** | 让 AI 能在受控边界内动外部系统（GitHub、部署平台等） | 3 个 MCP：GitHub / 部署 / 通知 |
| **Rule** | 仓库级别的"家法" | 一份 `AGENTS.md`，声明工程纪律 |

**这套方案的一个判断：能写脚本判定的，绝对不让人和 AI 解释执行。**

---

## 两条使用路径

### 路径 A（推荐）：你跟我对话，我把全套跑起来
你给我一个目标，我（作为总控）协调多个 sub-agent 把需求拆解、方案设计、代码生成、测试、部署全部跑完。
> **你现在正在这条路。** 你只要说目标，我接管。

### 路径 B：你自己也能搭一套（拿到独立能力）
把本目录的 `assets/prompts/` 和 `assets/skills/` 复制到你自己的 Claude Code / Cursor 项目里，按 `04-agents.md` 配置 4 个子 Agent，按 `06-workflow.md` 跑 9 阶段流程。

> A 是直接吃到果子，B 是你会种树。两条不冲突，建议先用 A 出活儿，再上手 B 把体系沉淀下来。

---

## 文件导览

| 文档 | 你现在要做什么 |
|---|---|
| [00-30min-kickoff.md](00-30min-kickoff.md) | **先看这个。** 30 分钟走完最小启动 |
| [01-overview.md](01-overview.md) | 方案全景图，4 块拼图怎么勾 |
| [02-tooling-checklist.md](02-tooling-checklist.md) | 订阅 / API Key / 账号清单，照抄 |
| [03-repository-bootstrap.md](03-repository-bootstrap.md) | 新仓库的脚手架，含 `AGENTS.md` 模板 |
| [04-agents.md](04-agents.md) | 4 个 Agent 的角色定义 + 配置方法 |
| [05-skills.md](05-skills.md) | 11 个 Skill 的定位 + 索引 |
| [06-workflow.md](06-workflow.md) | 9 阶段流程 + 状态机 + 打回规则 |
| [07-scripts.md](07-scripts.md) | 5 道门禁脚本（直接可用） |
| [08-mcp.md](08-mcp.md) | 3 个 MCP 的配置 |
| [09-runbook.md](09-runbook.md) | 出问题怎么排查 |
| [10-evolve.md](10-evolve.md) | 体系怎么跟着你一起长大 |

可直接复制粘贴的资产在 `output/` 下，**41 个文件全部就位**：

**顶层（复制到仓库根）**：
- `AGENTS.md` — 仓库家法（开箱即用）
- `.env.example` — 环境变量模板
- `.gitignore` — 防止凭据、产物进 git

**5 个 Agent 的 master prompt**（`assets/prompts/`）：
- `orchestrator.md` — 总控（最核心）
- `agent-requirements.md` — 需求分析
- `agent-design.md` — 方案设计
- `agent-develop.md` — 开发实施
- `agent-reviewer.md` — 代码审查

**11 个 Skill**（`assets/skills/<name>/SKILL.md`）：
- `prd-quality-check/` `impact-radius-analysis/` `prd-template/`
- `design-doc-template/` `coding-conventions/` `testing-specs/`
- `deployment-checklist/` `scope-overflow-check/` `security-rules/`
- `frontend-quality/` `feedback-loop-rules/`

**8 个门禁脚本**（`assets/scripts/`）：
- `gate-baseline.sh`（核心，已经能跑）/ `gate-coverage.sh` / `gate-lint.sh` / `gate-deploy-test.sh` / `gate-e2e.sh`
- `plugins/coverage-node.sh` / `plugins/coverage-python.sh` / `plugins/coverage-go.sh`（按栈选一个）

**知识库模板**（`kb/`）：
- `tooling.md` — 工具栈基线（首次填一遍）
- `changelog.md` — 体系演进日志（不要停更）

---

## 你接下来要做什么

1. **打开 `00-30min-kickoff.md`**，跟着走 30 分钟。
2. 等最小启动跑通，你会第一次感受到"我说一句，团队跑到底"。
3. 之后再回到这份 README，按章节深挖细节、做 B 路径的独立化。
