# 9 阶段接力赛：工作流定义

> 这一章回答一个问题：一个需求从「我说一句话」到「线上跑起来」，到底分几步走。

---

## 一、9 阶段全景图

```
[初始化]
   ↓
[需求理解]      ← 弹人工关卡「需求确认」
   ↓
[方案设计]      ← 弹人工关卡「方案确认」（高风险必弹）
   ↓
[分支准备]
   ↓
[开发实施]      ← 5 道门禁全过后进入下一棒
   ↓
[集成验证]      ← 含 E2E（前置到代码审查之前）
   ↓
[代码审查]      ← 4 维度收口，阻塞项 = 0 才进验收
   ↓
[验收]          ← 重跑 5 道门禁 + 写交付报告
   ↓
[交付收尾]      ← 触发 MCP（GitHub / Deploy / Notify）
```

---

## 二、每一阶段的硬定义

> 任何阶段的存在都对应一类历史教训。强行合并的下场是「代码审查过了 → 接口测试挂了 → 全白做」。

每一阶段都过这两道筛：

> ① 它是否有独立的失败模式？
> ② 它失败时回退的位置是否不一样？

两个都是「是」→ 必须独立。否则就合。

### 阶段 1：初始化
- **谁跑**：orchestrator
- **输入**：用户原始目标（一句话）
- **做**：分配 `req-id`、创建制品目录、写 `state.json`、拍门禁基线（如果还没拍）
- **产出**：`kb/artifacts/<req-id>/00-product-brief.md`、`state.json`、`.gates-state.json`
- **通过条件**：制品目录就绪、基线已存在
- **失败回退**：无（这是最初阶段）

### 阶段 2：需求理解
- **谁跑**：requirements-analyst
- **必读 Skill**：`prd-template` → `prd-quality-check` → `impact-radius-analysis`
- **产出**：`01-requirement-doc.md`
- **通过条件**：5 维评分每维 ≥ 60、总分 ≥ 60
- **失败回退**：补问用户（最多 3 个问题）/ 改写文档

### 阶段 3：需求确认（人工关卡）
- **触发**：需求理解产出后必弹
- **弹什么**：「这是需求理解，10 秒看完 → 确认继续 / 我要改 / 重做」
- **通过**：进入方案设计
- **失败**：打回需求理解

### 阶段 4：方案设计
- **谁跑**：solution-architect
- **必读 Skill**：`design-doc-template` → `coding-conventions` → `scope-overflow-check`
- **产出**：`02-design-doc.md`、`03-tasks.md`
- **通过条件**：每个任务可独立验证；风险自评完整；不超出需求范围
- **失败回退**：打回方案设计

### 阶段 5：方案确认（人工关卡，条件触发）
- **触发**：`risk_level == high` 或 `crosses_module_boundary` 或 `auth_change` 或 `data_migration`
- **弹什么**：「这是方案，30 秒看完 → 确认继续 / 降级 / 重做」
- **通过**：进入分支准备
- **失败**：打回方案设计

### 阶段 6：分支准备
- **谁跑**：orchestrator（跑 `scripts/gates/gate-prepare-branch.sh`）
- **做**：在涉及的子模块仓库创建特性分支 `feat/REQ-<id>-<slug>`
- **产出**：分支名列表写到 `state.json`
- **通过条件**：分支创建成功
- **失败回退**：重试一次，仍失败 → 阻塞项

### 阶段 7：开发实施
- **谁跑**：developer
- **必读 Skill**：`coding-conventions` → `testing-specs` → `deployment-checklist` → `security-rules`
- **必读制品**：01/02/03 + 上一环节 `04-code-changes.md`
- **产出**：`04-code-changes.md` + 单测 + E2E 代码 + `05-self-test-report.md`
- **通过条件**：5 道门禁全过 + 基线对比 delta 为空
- **失败回退**：打回开发（developer 自己改）

### 阶段 8：集成验证
- **谁跑**：orchestrator 触发 developer 跑 E2E 在 staging
- **关键**：这一阶段**前置到代码审查之前**（文章里的关键决策：开发 Agent 也写测试，前置是为了不把便宜的锅甩给贵的代码审查）
- **通过条件**：E2E 全过 + 截图归档
- **失败回退**：打回开发

### 阶段 9：代码审查
- **谁跑**：reviewer
- **必读 Skill**：`scope-overflow-check` → `security-rules` → `coding-conventions` → `frontend-quality`（前端时）→ `feedback-loop-rules`
- **4 维度**：方案一致性 / 验收覆盖 / 质量基线 / 前端增量
- **产出**：`06-review-report.md`
- **通过条件**：阻塞项 = 0；软门禁告警允许有但需明确写
- **失败回退**：打回开发（带阻塞项清单）

### 阶段 10：验收
- **谁跑**：orchestrator 触发
- **做**：重跑 5 道门禁 + 重读上游制品 + 看 reviewer 的软告警
- **产出**：`07-delivery-report.md`，含 verification 段
- **通过条件**：5 道门禁 idempotent 通过；reviewer 通过；关键指标监控就绪
- **失败回退**：打回开发 / 触发事故复盘

### 阶段 11：交付收尾（人工关卡 + MCP）
- **人工关卡**：「这是交付报告 + 5 道门禁结果 → 接受 / 打回」
- **接受后**调 3 个 MCP：
  - GitHub MCP：建 PR / 推 commit
  - Deploy MCP：触发生产部署
  - Notify MCP：飞书通知
- **产出**：线上 URL + PR URL + 飞书消息链接

> 上面 11 个数字 = 「9 阶段」+ 「分支准备和集成验证实际上是夹在其中的硬步骤」，加 2 个人工关卡 = 11 个节点。简化看就 9 阶段。

---

## 三、状态机（伪代码）

```python
state = initialize()
transitions = [
    ('init', 'analyze', confirm_user_intent),
    ('analyze', 'confirm-req', require_human_confirm),
    ('confirm-req', 'design', auto_if_confirmed),
    ('design', 'confirm-design', require_human_confirm_if_risky),
    ('confirm-design', 'branch', auto),
    ('branch', 'dev', auto),
    ('dev', 'integration', require_gates_pass),
    ('integration', 'review', require_e2e_pass),
    ('review', 'verify', require_blockers_zero),
    ('verify', 'ship', require_acceptance),
    ('ship', 'done', require_human_confirm),
]

while state != 'done':
    next_state, guard = next_transition(state)
    if guard(state):
        state = next_state
    elif state in ('analyze', 'design', 'dev', 'review'):
        # 允许自循环修改
        state = iterate(state)
    else:
        # 人工关卡熔断
        state = await_human(state)
```

完整实现：在 `.claude/skills/feedback-loop-rules/` 里写出可执行版本。

---

## 四、为什么是 9，不是 3 也不是 30

每一阶段都有独立的失败模式：

| 失败模式 | 阶段 |
|---|---|
| PRD 不清楚、目标歧义 | 需求理解 |
| 设计有 bug / 漏考虑 | 方案设计 |
| 代码写得不规范 | 开发 |
| 接口对不上 / E2E 失败 | 集成验证 |
| 越界 / 安全 / 验收缺失 | 代码审查 |
| 监控 / 部署缺一步 | 验收 |
| 用户没承认接受 | 交付收尾 |

**强行合并 = 让最贵的环节背最便宜的锅**。文章里把"集成测试从后置挪到前置"之后，开发打回次数从 1.8 降到 0.4 —— 因为"对不对"在写代码时已经能验证，不必让审查 Agent 反复去判定便宜的事实。

---

## 五、人工关卡的体感红线

> 「**不能让用户每分钟点一次以上**」——文章里的硬约束。

| 阶段 | 弹什么 | 用户花时 |
|---|---|---|
| 需求确认 | 5 行需求摘要 + 3 选项 | 10~30s |
| 方案确认（条件触发） | 30 秒看完 | 30~60s |
| 验收 | 交付摘要 + 接受 / 打回 | 10~30s |
| 熔断 | 撞 3 次打回时弹 | ≤ 1min |
| 交付收尾 | 部署完成通知 + 接受 | 5s |

> 任何让用户每分钟点一次以上的交互，**都算设计 bug**。

---

## 六、怎么应对边界情况

### 用户给的需求一句话之外没别的

`requirements-analyst` 必跑 `prd-quality-check`，5 维不达 60 就反问用户。**最多 3 个问题**——把优先级最高（最容易答的）排在前面：

1. 「这个产品的目标用户是谁？」
2. 「成功的标准是什么？（可观察，可验证）」
3. 「有什么是明确不要做的？」

### 用户中途改需求

不允许在制品中途改 PRD。要改：
- 旧需求归档（写 `kb/artifacts/<req-id>/archived.md`）
- 新开一个需求 ID 重新跑流程

### 跨产品多模块需求

「高风险 / 跨模块」 → 必弹方案确认。
orchestrator 主动把任务分到对应模块仓库（多仓情况），每个模块独立走开发 → 审查 → 部署，但共享一个 `req-id` 在制品目录。

### 失败连续发生

任一阶段连续被打回 ≥ 3 次 → 触发熔断暂停（见 `assets/skills/feedback-loop-rules/SKILL.md` §4）。

### 用户不愿意守纪律

不允许。半自动的体感红线一旦破坏，团队会绕过工具退回 Vibe Coding。**要么走流程，要么不开新需求**。

---

## 七、下一步

- 想知道 5 道门禁脚本实际怎么写 → [07-scripts.md](07-scripts.md)
- 想知道 MCP 怎么接 → [08-mcp.md](08-mcp.md)
