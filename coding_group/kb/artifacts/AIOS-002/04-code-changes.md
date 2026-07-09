# 04-code-changes.md — V1 代码变更清单（AIOS-002 dev 棒）

> 来源：03-tasks.md
> 时点：2026-07-09 09:50 +08:00

---

## V1-001~002: 前端工程 + 登录 + JWT

**新增**：
- `apps/web/package.json` — Next.js 14 + antd 5 + @ant-design/pro-components + TanStack Query + Zustand
- `apps/web/tsconfig.json`
- `apps/web/next.config.mjs` — `rewrites` 把 `/api/backend/*` 代理到后端 8000
- `apps/web/next-env.d.ts`
- `apps/web/src/app/providers.tsx` — ConfigProvider(zh_CN) + QueryClient
- `apps/web/src/app/layout.tsx`
- `apps/web/src/app/page.tsx` — 跳 `/datasources`
- `apps/web/src/app/login/page.tsx` — 登录页
- `apps/web/src/lib/api.ts` — axios 实例，401 自动跳登录

**后端配套**：
- `apps/api/src/auth.py` — JWT (HS256, stdlib) + PBKDF2 密码哈希（200k iter）
- `apps/api/src/middleware/auth.py` — `get_current_user` / `require_admin`
- `apps/api/src/api/v1/auth.py` — login / logout / me / change-password
- `apps/api/src/errors.py` — 加 `E_AUTH_REQUIRED` / `E_AUTH_INVALID_CRED` / `E_AUTH_TOKEN_INVALID`
- `apps/api/src/main.py` — 注册新路由
- `apps/api/src/audit_util.py` — 写审计的工具函数（worker 回调用）

## V1-003~006: 5 个前端页面

**新增**：
- `apps/web/src/app/console-shell.tsx` — 控制台 layout（侧边栏 + 顶栏 + 登出）
- `apps/web/src/app/datasources/page.tsx` — ProTable 列表
- `apps/web/src/app/datasources/new/page.tsx` — ProForm 新建（含只读确认 checkbox）
- `apps/web/src/app/scenarios/page.tsx` — 5 卡片
- `apps/web/src/app/scenarios/[key]/page.tsx` — 详情 + 流模板步骤
- `apps/web/src/app/flows/page.tsx` — 列表 + 触发按钮
- `apps/web/src/app/flows/[id]/runs/page.tsx` — FlowRun 列表（5s 自动刷新）
- `apps/web/src/app/audits/page.tsx` — 审计 + 链校验

**后端配套**：
- `apps/api/src/api/v1/scenarios.py` — list / get
- `apps/api/src/api/v1/flows.py` — list / create / get / trigger（trigger 调 flow_engine）
- `apps/api/src/api/v1/flow_runs.py` — by-flow / get
- `apps/api/src/api/v1/audits.py` — list / verify（链校验）
- `apps/api/src/api/v1/internal.py` — worker 回调 + schedule eligible
- `apps/api/src/models.py` — 加 `User` / `UserRole` + V1 字段
- `apps/api/src/db/migrations/versions/0003_v1_core.py` — users 表 + flows/flow_runs 字段

## V1-007~009: flow_engine 服务

**新增**：
- `apps/flow_engine/pyproject.toml` — fastapi + temporalio + apscheduler
- `apps/flow_engine/src/aios_flow/config.py`
- `apps/flow_engine/src/aios_flow/main.py` — FastAPI 管理 API（/workflows/start）
- `apps/flow_engine/src/aios_flow/worker.py` — Temporal Worker + Schedule Trigger
- `apps/flow_engine/src/aios_flow/workflows/generic.py` — GenericScenarioWorkflow
- `apps/flow_engine/src/aios_flow/activities/steps.py` — **17 个标准实现**
- `apps/flow_engine/src/aios_flow/triggers/schedule.py` — APScheduler cron 触发
- `apps/flow_engine/tests/test_steps.py` — **9 个 step 单测**

**容器化**：
- `apps/api/Dockerfile` — Python 3.11 多阶段构建
- `apps/api/src/setup_default_admin.py` — 启动建默认 admin

## V1-010: 5 道门禁补丁

- `deploy/compose/docker-compose.yml` 全面升级 V1：
  - image tag → `0.2.0`
  - 加 `flow-engine` 服务（独立 image）
  - api healthcheck 路径 → `/api/v1/health`
  - web healthcheck 改用 `wget`
  - 端口：`AIOS_CONSOLE_PORT` 默认 3000
  - grafana 端口改 3001（让出 3000 给 web）

## V1-011: 5 E2E

- `apps/web/playwright.config.ts`
- `apps/web/e2e/01-login.spec.ts`
- `apps/web/e2e/02-datasource.spec.ts`
- `apps/web/e2e/03-scenarios.spec.ts`
- `apps/web/e2e/04-audits.spec.ts`
- `apps/web/e2e/05-flows.spec.ts`

## V1-012: install 增强

- API 镜像启动时跑 `setup_default_admin`（容器 stderr 输出默认密码）

---

## 文件统计

| 类型 | 新增 | 修改 |
|---|---|---|
| Python 后端 | 11 | 5 |
| TS 前端 | 13 | 0 |
| Docker | 1 | 1 |
| E2E | 6 | 0 |
| Migration | 1 | 0 |
| 配置 | 2 | 0 |
| **合计** | **34** | **6** |
