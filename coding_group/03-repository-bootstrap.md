# 仓库脚手架：建一个 Agent 友好的产品仓库

> 这一章回答一个问题：一个「被 Agent 团队高效工作」的仓库，长什么样。

---

## 一、目录结构（全貌）

```
<your-product>/
├── AGENTS.md                       # 仓库级「家法」，所有 AI 进来第一件事是读它
├── README.md
├── package.json                    # 或 pyproject.toml / go.mod，按你的栈
├── src/                            # 业务代码
│   └── (按你自己的约定)
├── tests/
│   ├── unit/                       # 单元测试
│   └── e2e/                        # 端到端测试
├── scripts/
│   └── gates/                      # 5 道门禁脚本（见 07-scripts.md）
│       ├── gate-coverage.sh
│       ├── gate-lint.sh
│       ├── gate-deploy-test.sh
│       ├── gate-e2e.sh
│       └── gate-baseline.sh
├── kb/                             # 知识库（**项目级**，必须 commit 进去）
│   ├── AGENTS.md                   # 仓库级规约的展开版
│   ├── tooling.md                  # 工具栈基线
│   ├── skills/                     # 11 个 Skill 的 SKILL.md 索引
│   │   ├── prd-quality-check/SKILL.md
│   │   ├── impact-radius-analysis/SKILL.md
│   │   └── (... 共 11 个)
│   ├── gates/
│   │   └── baseline.json           # 门禁基线快照
│   ├── artifacts/                  # 每个需求的制品落在这里（按需求 ID 分目录）
│   │   └── <req-id>/
│   │       ├── 00-product-brief.md
│   │       ├── 01-requirement-doc.md
│   │       ├── 02-design-doc.md
│   │       ├── 03-tasks.md
│   │       ├── 04-code-changes.md
│   │       ├── 05-self-test-report.md
│   │       ├── 06-review-report.md
│   │       └── 07-delivery-report.md
│   └── changelog.md                # 体系演进日志
└── .gitignore
```

### 关键原则

- **业务代码和知识库分离**：`src/`、`tests/` 是被改动的代码；`kb/` 是规约、Skill、制品，是被查阅不被改动的（制品除外）。
- **制品按需求 ID 单建目录**：`kb/artifacts/<req-id>/` 每一棒交出来的东西都在这。出了事翻这一个目录就够。
- **门禁脚本在 scripts/gates/**：能被 AI 调、能被 Git hooks 调、能被 CI 调，三处都能调。

---

## 二、`AGENTS.md` —— 仓库「家法」（Agent 必读）

这是最重要的一个文件。所有 Agent 进入这个仓库，第一件事**必须**读完这份 `AGENTS.md`。文章开头那句「下游不可改上游产物」就写在这里。

把它放在仓库根目录，命名空间跟其他框架一致（Claude Code 也认这个文件名）：

```markdown
# AGENTS.md — 仓库工程纪律（强制）

## 0. 启动顺序（所有 Agent 必读）

进入这个仓库后，按下面顺序做事，不要跳：

1. 读 `kb/AGENTS.md`（这是展开版）
2. 读 `kb/tooling.md`（工具栈基线）
3. 读 `kb/skills/` 下与你当前阶段相关的 Skill
4. 检查 `kb/changelog.md` 最近 5 条
5. 看 `kb/artifacts/` 当前是否还有未完成的需求，如有，先交接 / 接管
6. 检查 `.gates-state.json` 看门禁是否处于通过态

## 1. 角色边界（最强纪律）

- **下游 Agent 不可直接修改上游产物**。需要改时只能提阻塞项，由总控打回上游。
- 跨阶段协调由总控（orchestrator）负责。Agent 之间不直接对话。
- 任何职责范围之外的产物（如「方案 Agent 写了代码」「开发 Agent 改 PRD」），立即停止并通过阻塞项上报。

## 2. 工程规则

- 提交前必须 5 道门禁全过。详见 `scripts/gates/`。
- 覆盖率阈值：核心模块 ≥ 80%，其他 ≥ 60%。
- 所有 PR 必须有 review-report 引用。
- 制品必须落到 `kb/artifacts/<req-id>/`，不要散落到其他位置。

## 3. 沟通风格

- 用中文回答；技术名词英文。
- 不用 emoji 装饰决策。
- 看到不清楚的，宁可提问不要猜。

## 4. 元信息

- 产品名：<PRODUCT_NAME>
- 仓库：<REPO_URL>
- 部署：<DEPLOY_URL>
- 维护者：<YOUR_NAME>
- 最近更新：YYYY-MM-DD
```

---

## 三、`kb/AGENTS.md` —— 仓库规约展开版

这一份比根目录的 `AGENTS.md` 更长，写「为什么是这个约束」「约束的边界」：

```markdown
# kb/AGENTS.md — 仓库规约展开版

## 1. 工作流：9 阶段接力赛

[整段引用 06-workflow.md 的状态机定义]

## 2. 门禁：5 道硬/软门禁的判定

[整段引用 07-scripts.md 的门禁定义]

## 3. Skill 加载纪律

哪个阶段加载哪个 Skill，**写在 05-skills.md 的「Skill 加载表」里**，不靠 Agent 自己记忆。

## 4. 提交规范

- commit message 格式：`<type>(<req-id>): <desc>`
- type ∈ {feat, fix, refactor, docs, test, chore}
- 例：`feat(REQ-001): 实现用户登录页`

## 5. 制品规范

- 每棒产物的文件命名固定（见 `kb/artifacts/<req-id>/` 模板）
- 任何 Agent 写产物前，必须先创建该目录

## 6. 失败 / 阻塞

- 任何超出范围的修改 → 阻塞项文档 `[BLOCKER]`
- 阻塞项以文件形式提交到 `kb/artifacts/<req-id>/blockers/`
```

---

## 四、`kb/tooling.md` —— 工具栈基线

在 [02-tooling-checklist.md](02-tooling-checklist.md) 末尾的模板已经写得很清楚，原样进 `kb/tooling.md`。

每次新增 / 替换工具栈，要在这里 commit 一行 `YYYY-MM-DD: <变更>`。

---

## 五、Skill 的安装方式（具体到 Claude Code）

Claude Code 把 `kb/skills/<skill-name>/SKILL.md` 当作一个 Skill 加载。

每个 Skill 文件第一行必须是 YAML frontmatter：

```yaml
---
name: <skill-name>
description: <一行说清这个 Skill 干啥的，Claude Code 会用这个决定要不要加载它>
---
```

下面是其中一个 Skill 的样板示例，详见 `assets/skills/` 下 11 个文件。

---

## 六、`.gitignore` 必备项

```gitignore
# 运行时
.env
.env.*
!.env.example
node_modules/
dist/
build/
.next/

# 测试覆盖率
coverage/
*.lcov

# IDE
.vscode/
.idea/
.DS_Store

# Agent 工作产物（不是 KB 制品，**不要 commit**）
.gates-state.json
.run/
```

---

## 七、第一次 commit 推荐做这 5 件事

1. 跑 `git init`、`git add .`、`git commit -m "chore: bootstrap agent-friendly scaffold"`
2. 在 GitHub 仓库 Settings → Branches → Protected branches 启用 `main` 分支的保护
3. 装 GitHub Actions / GitLab CI（路径 B 才需要）
4. 跑一次 `scripts/gates/gate-baseline.sh --snapshot`，让基线落进 `kb/gates/baseline.json`
5. 把这一份 commit 进 main 分支

走完这 5 步，再让 Agent 团队进这个仓库。

---

## 下一步

- 想知道 4 个 Agent 各司其职 → [04-agents.md](04-agents.md)
- 想知道 11 个 Skill 都长啥样 → [05-skills.md](05-skills.md)
