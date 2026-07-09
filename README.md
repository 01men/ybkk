# 元冰可可 AIOS

面向离散制造企业的 AI 操作系统（私有化部署）。**不改造现有系统**，直读数据元 + 内置交付标准，自主构建 AI 业务流程，让企业拿到即可启动 AI 转型。

## 仓库结构

```
ybkk/
├── AGENTS.md                   # 仓库级家法
├── README.md                   # 本文件
├── package.json                # monorepo 根
├── pnpm-workspace.yaml
├── turbo.json
├── tsconfig.base.json
├── .prettierrc.json
├── .editorconfig
├── .gitignore
├── apps/                       # 业务应用
│   ├── web/                    # Next.js 14 控制台
│   ├── api/                    # FastAPI 后端
│   ├── ingest/                 # 摄取 worker（Excel/PDF/会议）
│   ├── ontology/               # Neo4j 本体图服务
│   └── flow_engine/            # Temporal 工作流引擎
├── packages/                   # 共享库
│   ├── standards/              # 场景模板 DSL + 内置模板
│   ├── audit/                  # 审计日志库
│   └── llm_gateway/            # LLM 抽象层
├── deploy/                     # 部署
│   └── compose/                # Docker Compose 一键部署
└── coding_group/               # Agent 团队 + 知识库
    ├── README.md
    ├── AGENTS.md 体系文档
    ├── assets/
    │   ├── prompts/            # 5 个 Agent prompt
    │   ├── skills/             # 11 个 Skill
    │   └── scripts/            # 5 道门禁脚本
    └── kb/
        ├── AGENTS.md
        ├── tooling.md
        ├── artifacts/AIOS-001/ # 当前需求制品
        └── changelog.md
```

## 快速开始（开发者）

```bash
# 1. 安装依赖
pnpm install

# 2. 起后端（需要 PostgreSQL / Neo4j / Redis / MinIO / NATS / Temporal）
# 推荐方式：私有化部署
bash deploy/compose/install.sh

# 3. 起前端
pnpm dev

# 4. 跑门禁
pnpm gate:baseline   # 第一次先拍基线
pnpm gate:all        # 跑 5 道门禁
```

## Agent 团队（按 AGENTS.md 9 阶段跑需求）

```bash
# 注册 5 个 Agent 到 Claude Code / Cursor
mkdir -p .claude/agents/{orchestrator,requirements-analyst,solution-architect,developer,reviewer}
cp coding_group/assets/prompts/orchestrator.md      .claude/agents/orchestrator/AGENT.md
cp coding_group/assets/prompts/agent-requirements.md .claude/agents/requirements-analyst/AGENT.md
cp coding_group/assets/prompts/agent-design.md        .claude/agents/solution-architect/AGENT.md
cp coding_group/assets/prompts/agent-develop.md       .claude/agents/developer/AGENT.md
cp coding_group/assets/prompts/agent-reviewer.md      .claude/agents/reviewer/AGENT.md

# 让总控跑一个需求
# 在仓库根目录：说「我要做 XXX」，orchestrator 接管
```

## 详细文档

| 想看什么 | 看哪里 |
|---|---|
| 仓库家法 | [AGENTS.md](./AGENTS.md) |
| 体系总览 | [coding_group/README.md](./coding_group/README.md) |
| 当前需求 PRD | [coding_group/kb/artifacts/AIOS-001/01-requirement-doc.md](./coding_group/kb/artifacts/AIOS-001/01-requirement-doc.md) |
| 当前需求方案 | [coding_group/kb/artifacts/AIOS-001/02-design-doc.md](./coding_group/kb/artifacts/AIOS-001/02-design-doc.md) |
| 当前需求任务 | [coding_group/kb/artifacts/AIOS-001/03-tasks.md](./coding_group/kb/artifacts/AIOS-001/03-tasks.md) |
| 工具栈 | [coding_group/kb/tooling.md](./coding_group/kb/tooling.md) |

## License

Proprietary. © 2026 元冰可可.