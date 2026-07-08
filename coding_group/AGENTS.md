# AGENTS.md — 仓库工程纪律（强制）

> 这是你产品仓库的"家法"。每个 Agent 进去这个仓库的第一件事就是读完这一份。
> 占位符（`<...>`）第一次提交前替换成你的真实信息。

---

## 0. 启动顺序（所有 Agent 必读）

进入这个仓库后，按下面顺序做事，不要跳：

1. 读 `kb/AGENTS.md`（展开版规约）
2. 读 `kb/tooling.md`（工具栈基线）
3. 读 `kb/skills/` 下与你当前阶段相关的 Skill
4. 检查 `kb/changelog.md` 最近 5 条
5. 看 `kb/artifacts/` 当前是否还有未完成的需求，如有，先交接 / 接管
6. 检查 `.gates-state.json` 看门禁是否处于通过态

---

## 1. 角色边界（最强纪律）

- **下游 Agent 不可直接修改上游产物**。需要改时只能提阻塞项，由总控打回上游。
- 跨阶段协调由总控（orchestrator）负责。Agent 之间不直接对话。
- 任何职责范围之外的产物（如「方案 Agent 写了代码」「开发 Agent 改 PRD」），立即停止并通过阻塞项上报。

---

## 2. 工程规则

- 提交前必须 5 道门禁全过。详见 `scripts/gates/`。
- 覆盖率阈值：核心模块 ≥ 80%，其他 ≥ 60%。
- 所有 PR 必须有 review-report 引用。
- 制品必须落到 `kb/artifacts/<req-id>/`，不要散落到其他位置。

---

## 3. 沟通风格

- 用中文回答；技术名词英文。
- 不用 emoji 装饰决策。
- 看到不清楚的，宁可提问不要猜。

---

## 4. 元信息（替换占位符）

- 产品名: <PRODUCT_NAME>
- 仓库: <REPO_URL>
- 部署: <DEPLOY_URL>
- 维护者: <YOUR_NAME>
- 工具栈基线: 见 `kb/tooling.md`
- 最近更新: <YYYY-MM-DD>

---

## 5. 必读清单（按阶段）

| 当前阶段 | 必读 Skill |
|---|---|
| 需求理解 | `prd-template` → `prd-quality-check` → `impact-radius-analysis` |
| 方案设计 | `design-doc-template` → `coding-conventions` → `scope-overflow-check` |
| 开发实施 | `coding-conventions` → `testing-specs` → `deployment-checklist` → `security-rules` |
| 代码审查 | `scope-overflow-check` → `security-rules` → `coding-conventions` → `frontend-quality` → `feedback-loop-rules` |
| 验收/交付 | `deployment-checklist` → `feedback-loop-rules` |

---

## 6. 反馈循环纪律（最关键）

- Rule 越多，AI 解释空间越大。所有"能判定的事"都下沉成脚本。
- 「完成」以最近一份 `.gates-state.json` 为准。门禁挂 = 没完成，不存在中间态。
- 基线对比：`delta = new_failures - baseline_failures`，只有 delta 才阻断。
- 连续打回 ≥ 3 次 → 触发熔断暂停。

---

## 7. 制品约定

`kb/artifacts/<req-id>/` 下放每一棒产物：

| 阶段 | 必写 | 禁止动 |
|---|---|---|
| 初始化 | `00-product-brief.md`、`state.json` | — |
| 需求理解 | `01-requirement-doc.md` | 任何 Agent 都可读，**只有 requirements-analyst 可写** |
| 方案设计 | `02-design-doc.md`、`03-tasks.md` | **只有 solution-architect 可写** |
| 开发 | `04-code-changes.md`、`05-self-test-report.md` | **只有 developer 可写** |
| 审查 | `06-review-report.md` | **只有 reviewer 可写** |
| 验收 | `07-delivery-report.md` | 只有 orchestrator 可写 |
| 阻塞项 | `blockers/*.md` | 任何 Agent 可读；写必须遵守 `feedback-loop-rules` §6 schema |
