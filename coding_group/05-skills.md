# 11 个 Skill：定位、触发词、加载矩阵

> 这一章回答：11 个 Skill 是什么、什么时候用、谁负责加载。

---

## 11 个 Skill 一览

| # | Skill 名 | 用途 | 主要加载方 | 加载时机 |
|---|---|---|---|---|
| 1 | `prd-quality-check` | 5 维评分 PRD 完整性 | requirements-analyst | 写完需求理解后 |
| 2 | `impact-radius-analysis` | 估算影响半径 | requirements-analyst | 同上 |
| 3 | `prd-template` | PRD 文档强制模板 | requirements-analyst | 开始写需求时 |
| 4 | `design-doc-template` | 设计文档强制模板 | solution-architect | 开始写方案时 |
| 5 | `coding-conventions` | 仓库代码规约总集 | developer / reviewer | 写代码前 / 审查时 |
| 6 | `testing-specs` | 测试规范 | developer | 写测试前 |
| 7 | `deployment-checklist` | 部署前清单 | developer / orchestrator | 验收前 / 交付时 |
| 8 | `scope-overflow-check` | 范围溢出自查 | developer / reviewer | 写完代码 / 审查时 |
| 9 | `security-rules` | 安全编码规约 | developer / reviewer | 写代码前 / 涉及鉴权数据 |
| 10 | `frontend-quality` | 前端审查清单 | reviewer（涉及前端） | 审查时（条件触发） |
| 11 | `feedback-loop-rules` | 反馈循环规则（基线、熔断、软门禁伤疤） | orchestrator / reviewer | 全流程 |

---

## Skill 加载矩阵（谁在什么棒加载哪些）

| 阶段 | 加载的 Skill | 加载顺序 |
|---|---|---|
| **需求理解** | `prd-template` → `prd-quality-check` → `impact-radius-analysis` | 必须 |
| **方案设计** | `design-doc-template` → `coding-conventions` → `scope-overflow-check` | 必须 |
| **开发实施** | `coding-conventions` → `testing-specs` → `deployment-checklist` → `security-rules`（涉鉴权时） | 必须 |
| **代码审查** | `scope-overflow-check` → `security-rules` → `coding-conventions` → `frontend-quality`（前端时）→ `feedback-loop-rules` | 必须 |
| **验收 / 交付** | `deployment-checklist` → `feedback-loop-rules` | 必须 |

> 在 `assets/prompts/` 的每个 Agent 的 master prompt 第 0 节已经写明该 Agent **必加载哪些 Skill**。这里给的是完整版矩阵，方便出问题时排查。

---

## Skill vs Rule 的边界（再强调一次）

文章里的硬纪律：

- **Rule**（自然语言约束）：写在 `AGENTS.md` 里，对应「态度」「软规范」
  - 例：「不要瞎改 PRD 没要求的功能」「写代码前先想清楚」「保持代码优雅」
  - 这些没法机器判定，所以留在 Rule

- **Skill**（文档式操作手册）：写在 `kb/skills/<name>/SKILL.md`，对应「操作」「硬规范」
  - 例：「所有 endpoint 入参必须用 Zod 校验」「覆盖率核心 ≥ 80%」
  - 这些要么机器可判定（→ 升级为门禁脚本）、要么是结构化操作流程（→ Skill）

> **凡是能在文档里讲清楚的"操作流程"就成 Skill，凡是只能讲"态度"的就成 Rule。**

---

## 怎么快速看 Skill 加载没

如果某个 Skill「Agent 没注意到」，99% 是这两个原因：

1. **prompt 没显式说要加载**
2. **Skill 文件位置不对**（Claude Code 严格要求 `kb/skills/<name>/SKILL.md`）

修法：见 `09-runbook.md` §5。

---

## 怎么更新 Skill

原则：**Skill 改动要写 changelog**。

```
1. 改 kb/skills/<name>/SKILL.md
2. 在 kb/changelog.md 加一行：
   ## YYYY-MM-DD: <skill 名> <一句话>
   - 改动: <段、理由>
   - 触发原因: <那次撞墙>
3. 跑一次基线对比，确保门禁脚本仍生效
4. 提交 commit: feat(skill): <name> <一句话>
```

---

## Skill 与门禁脚本的协作

很多 Skill 是「软规范」（写文档），但其中能机器判定的部分，**也会被门禁脚本强制执行**。

例如：

| Skill 段 | 对应的门禁脚本判定 |
|---|---|
| `coding-conventions` §3「错误处理」 | `gate-lint.sh` 中的自定义 ESLint / Flake8 规则 |
| `testing-specs` §「覆盖率门槛」 | `gate-coverage.sh` |
| `security-rules` §「依赖安全」 | `gate-lint.sh`（含 npm audit） |

Skill 是「告诉 Agent 怎么做」，门禁是「机器判定做得对不对」。**二者必须同时存在**——只有 Skill 没门禁，Agent 会偷懒；只有门禁没 Skill，Agent 不知道为什么挂。

---

## 下一步

- 想看 9 阶段接力赛具体怎么跑 → [06-workflow.md](06-workflow.md)
- 想知道 5 道门禁脚本长啥样 → [07-scripts.md](07-scripts.md)
