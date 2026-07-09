# kb/AGENTS.md — 仓库规约展开版

> 这份是仓库根 `AGENTS.md` 的展开版。所有 Agent 读完根 `AGENTS.md` 后，**必须**接着读这一份。
> 它只补充根 `AGENTS.md` 没覆盖到的细节，不重复声明纪律（纪律以根 `AGENTS.md` 为准）。

---

## 1. 工具栈基线

详见同目录 `tooling.md`。任何 Agent 不得擅自替换其中的：

- 覆盖率工具（参见 `coding_group/assets/scripts/plugins/`）
- 5 道门禁脚本（参见 `coding_group/assets/scripts/`）
- MCP 工具集（参见 `coding_group/08-mcp.md`）

---

## 2. Skill 索引

`coding_group/assets/skills/` 下共 11 个 Skill，每个 SKILL.md 都规定：

- 触发条件（什么阶段 / 什么症状必须读它）
- 输入契约（需要先有什么制品）
- 输出契约（必须产出什么制品 / 阻塞项）
- 反模式（哪些写法禁止）

按阶段必读清单见根 `AGENTS.md` §5。

---

## 3. 制品目录权限矩阵

根 `AGENTS.md` §7 给出了「谁能写谁不能改」的简化版，本节给出完整版：

| 制品路径 | 读 | 写 | 备注 |
|---|---|---|---|
| `00-product-brief.md` | 全员 | orchestrator（初始化棒） | 任何阶段不得修改；变动只能开新需求 |
| `state.json` | 全员 | orchestrator | 状态机唯一可信源 |
| `01-requirement-doc.md` | 全员 | requirements-analyst | 下游 Agent 提阻塞项改之 |
| `02-design-doc.md` | 全员 | solution-architect | 同上 |
| `03-tasks.md` | 全员 | solution-architect | 同上 |
| `04-code-changes.md` | 全员 | developer | — |
| `05-self-test-report.md` | 全员 | developer | — |
| `06-review-report.md` | 全员 | reviewer | — |
| `07-delivery-report.md` | 全员 | orchestrator | — |
| `blockers/*.md` | 全员 | 任何 Agent | 必须遵守 `feedback-loop-rules` §6 schema |

---

## 4. 阻塞项协议

- 阻塞项文件路径：`coding_group/kb/artifacts/<req-id>/blockers/<stage>-<seq>.md`
- 提交阻塞项的 Agent 必须在制品末尾追加一条引用（不修改正文）
- orchestrator 在收到阻塞项后，按优先级裁决：阻断 / 提示 / 驳回

---

## 5. 门禁与基线

- 门禁运行入口：`coding_group/assets/scripts/gate-*.sh`
- 基线快照：`coding_group/kb/gates/baseline.json`
- 当前状态：`.gates-state.json`（仓库根，**不要**放进 kb/）
- 基线对比规则：仅 `new_failures - baseline_failures` 视为阻塞，历史失败不算

---

## 6. 演进与变更

- 任何对根 `AGENTS.md` 或本文件的修改，**必须**先在 `coding_group/kb/changelog.md` 留痕
- 修改门禁阈值 / 角色边界 / 制品约定的，必须经人工确认
- 自动化脚本与人工确认的边界，参见 `coding_group/10-evolve.md`