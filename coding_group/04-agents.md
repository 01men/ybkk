# 4 个 Agent + 1 个总控：怎么注册、怎么用

> 这一章回答一个问题：在 Claude Code 或 Cursor 里，怎么把这 4 个角色注册下来、然后让总控去调度。

---

## 一、角色一览

| 角色 | 中文名 | 干什么 | 必读 | 必写 | **不许做** |
|---|---|---|---|---|---|
| **orchestrator** | 总控 | 调度 4 个 Agent 接力、跑门禁、跑脚本、推 MCP、记制品 | `kb/AGENTS.md` + 当前制品 | `.orchestrator-state.json`、`.gates-state.json` | 自己写代码、自己出方案、自己审代码 |
| **requirements-analyst** | 需求分析 | 把一句目标 → 结构化需求理解 + 影响半径 | `kb/tooling.md` + `prd-quality-check` Skill + `impact-radius-analysis` Skill + `prd-template` Skill | `kb/artifacts/<req-id>/01-requirement-doc.md` | 写技术方案、改 PRD |
| **solution-architect** | 方案设计 | 把需求 → 可执行技术方案 + 任务清单 | 需求文档 + `design-doc-template` Skill + `coding-conventions` Skill | `02-design-doc.md` + `03-tasks.md` | 改需求理解文档、直接动代码 |
| **developer** | 开发实施 | 按方案写代码 + 单测 + E2E | 需求 + 方案 + `coding-conventions` Skill + `testing-specs` Skill + `deployment-checklist` Skill | `04-code-changes.md` + `tests/` 里的代码 + `05-self-test-report.md` | 超出方案范围、跳过门禁 |
| **reviewer** | 代码审查 | 从 4 维度收口 | 上游全部产物 + git diff + `scope-overflow-check` Skill + `security-rules` Skill + `frontend-quality` Skill | `06-review-report.md` | 改任何上游产物 |

> **「不许做」是最关键的列。** 这是角色边界。下游 Agent 总是想"顺手"做上游的事 —— 它会用「这是优化」「这里有必要」等表述。这时它必须停下来，写一份 `[BLOCKER]` 文档，由总控打回上游。

---

## 二、在 Claude Code 里注册（具体操作步骤）

假设你已经买了 Claude Max，打开 Claude Code CLI：

```bash
# 1. 进入你的产品仓库
cd <your-product>

# 2. 打开 settings.json (或者在 .claude 目录下)
mkdir -p .claude
ls -la .claude
```

Claude Code 把子 Agent 配置放在 `.claude/agents/<agent-name>/AGENT.md`（或 `CLAUDE.md`）。我们按这个约定布局：

```
<your-product>/
└── .claude/
    └── agents/
        ├── orchestrator/AGENT.md
        ├── requirements-analyst/AGENT.md
        ├── solution-architect/AGENT.md
        ├── developer/AGENT.md
        └── reviewer/AGENT.md
```

把 `assets/prompts/` 下 5 个 `.md` 文件分别复制到对应子目录：

```bash
mkdir -p .claude/agents/{orchestrator,requirements-analyst,solution-architect,developer,reviewer}
cp assets/prompts/orchestrator.md      .claude/agents/orchestrator/AGENT.md
cp assets/prompts/agent-requirements.md .claude/agents/requirements-analyst/AGENT.md
cp assets/prompts/agent-design.md        .claude/agents/solution-architect/AGENT.md
cp assets/prompts/agent-develop.md       .claude/agents/developer/AGENT.md
cp assets/prompts/agent-reviewer.md      .claude/agents/reviewer/AGENT.md
```

启动 Claude Code，让它「看见」这些 Agent：

```bash
# 在仓库根目录运行（要先 cd 进去）
claude
# 然后说：「列出当前可用的 Agent」
> /agents
# 应该能看到 5 个名字一字不差的 Agent
```

> 名字必须一字不差，因为工作流里靠名字唤起。详见 `06-workflow.md`。

---

## 三、如果是 Cursor

Cursor 的 Custom Agents 配置文件位置：

```
~/.cursor/agents/   或  .cursor/agents/
```

布局一样：

```
.cursor/agents/<agent-name>/AGENT.md
```

`assets/prompts/` 下文件原样复制即可。

---

## 四、Orchestrator 怎么调度 4 个 Agent

Orchestrator 不应该让一个 Agent "在它的 turn 里把所有事做完"。它要做的是**接力赛**——

每一棒明确：
- 谁跑（哪个 Agent）
- 跑前必须看到什么（必读清单）
- 跑完交什么（产物文件）
- 怎么判过 / 不过（门禁脚本 or 阻塞项文档）
- 过了交给谁、不过打回谁

详见 `06-workflow.md` 的状态机。Orchestrator 的 master prompt 在 `assets/prompts/orchestrator.md`，**核心逻辑**是一段伪代码状态机。

---

## 五、Agent 间对话纪律

> **最强纪律（来自文章，又被我加强）：下游 Agent 不可直接修改上游产物。**

具体实现是**通讯靠文件**：

```
需求 Agent 写  →  kb/artifacts/<req-id>/01-requirement-doc.md
                    ↓
方案 Agent 读   ←  kb/artifacts/<req-id>/01-requirement-doc.md
方案 Agent 写  →  kb/artifacts/<req-id>/02-design-doc.md
                    ↓
开发 Agent 读   ←  kb/artifacts/<req-id>/02-design-doc.md
开发 Agent 写  →  kb/artifacts/<req-id>/04-code-changes.md
                    ↓
审查 Agent 读   ←  kb/artifacts/<req-id>/04-code-changes.md
审查 Agent 写  →  kb/artifacts/<req-id>/06-review-report.md
```

下游 Agent 想改上游文档怎么办？**写一份阻塞项**：

```
kb/artifacts/<req-id>/blockers/01-<stage>-blocked-by-requirement.md
```

格式见 `assets/skills/scope-overflow-check/SKILL.md` 第 6 节。

**Orchestrator 看到阻塞项 → 打回上游 Agent 改 → 跑完再回到当前棒。**

---

## 六、Prompt 草稿（详版）

完整的 5 个 Agent prompt 在 `assets/prompts/`：

- `assets/prompts/orchestrator.md`
- `assets/prompts/agent-requirements.md`
- `assets/prompts/agent-design.md`
- `assets/prompts/agent-develop.md`
- `assets/prompts/agent-reviewer.md`

每一份都是**直接可复制**的 master prompt。

---

## 七、常见的把 Agent 用歪的方式

> **下面是真实踩过的坑。** 你以后看到这些行为，要立刻停手修。

| 错误用法 | 错在哪 | 怎么改 |
|---|---|---|
| 把 5 个 Agent 合成 1 个，让它"自己想清楚" | 责任边界丢失、自审自过、token 爆炸 | 严守 4+1 结构 |
| 让 Agent "自己审自己的 PR" | 模型对自己产出没否决欲，永远过 | 必须开独立的 reviewer Agent |
| 改 prompt 只改参数不改 Skill | 同一需求每次跑出来不同 | 把规约沉淀成 Skill |
| 把团队约束写进 Memory | 换人就丢，个人与团队不一致 | 必须落到仓库 `kb/` |
| Agent 协作靠对话而不是靠文件 | 上游产物被覆盖时无法追溯 | 严守产物落 `kb/artifacts/<req-id>/` |

---

## 八、调试技巧

> 「Agent 不听话」基本是 4 类原因

1. **prompt 太长** → 把 prompt 里只在某一阶段用得到的部分抽到 Skill 里
2. **prompt 互相矛盾** → 把硬约束提到 AGENTS.md 里，每个 Agent 都强制读
3. **Skill 没被加载** → 在 prompt 里显式写「记得读 prd-quality-check」
4. **门禁脚本假阳性 / 假阴性** → 调整阈值（先看 `09-runbook.md`）

---

## 下一步

- 想看 11 个 Skill 都讲了什么 → [05-skills.md](05-skills.md)
- 想看 9 阶段流程具体怎么跑 → [06-workflow.md](06-workflow.md)
