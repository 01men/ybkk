# 03-tasks.md — V1 任务清单（AIOS-002 design 棒）

> 来源：[02-design-doc.md](file:///d:/项目/元冰可项目/ybkk/coding_group/kb/artifacts/AIOS-002/02-design-doc.md) §10。
> 时点：2026-07-09 09:47 +08:00。
> 原则：每条任务可验证、可勾选。

---

## V1-001：apps/web 工程启动

- [ ] 初始化 Next.js 14 (App Router) + TypeScript
- [ ] 装 antd / @ant-design/pro-components / @tanstack/react-query / zustand / axios
- [ ] 全局 ConfigProvider + 中文 locale
- [ ] `npm run dev` 起在 3000 端口
- [ ] 验证：访问 `http://localhost:3000` 看到 antd 欢迎页

## V1-002：登录页 + JWT 中间件

- [ ] `app/login/page.tsx` — 用户名/密码表单 + 调 `/api/v1/auth/login`
- [ ] 登录成功 → JWT 存 httpOnly cookie
- [ ] `app/api/_auth.ts` — `getCurrentUser()` 读 cookie 调后端 `/auth/me`
- [ ] 未登录访问任意页 → 跳 `/login`
- [ ] 后端 `apps/api/src/middleware/auth.py` + `apps/api/src/api/v1/auth.py`
- [ ] 验证：未登录访问 `/datasources` → 跳 `/login`；登录后跳回

## V1-003：数据源管理页（list + new）

- [ ] `app/datasources/page.tsx` — ProTable 列 datasources
- [ ] `app/datasources/new/page.tsx` — ProForm 提交 POST `/api/v1/datasources`
- [ ] 成功 → 跳列表 + toast
- [ ] 失败 → 表单显示 error 字段
- [ ] 验证：接入一个测试 MySQL，列表 status=CONNECTED；故意错密码，status=FAILED

## V1-004：场景模板页

- [ ] `app/scenarios/page.tsx` — 5 卡片，列出内置 5 场景
- [ ] `app/scenarios/[key]/page.tsx` — 详情：流模板 DAG 图（用 @ant-design/graphs 或 react-flow）+ 默认标准
- [ ] 「激活」按钮 → 选数据源 + trigger 类型 → 调 POST `/api/v1/flows` 创建 Flow
- [ ] 验证：5 卡片全显示；点库存预警 → 看 DAG；激活 → flow 创建成功

## V1-005：流程列表 + 详情页

- [ ] `app/flows/page.tsx` — ProTable 列 flows
- [ ] `app/flows/[id]/page.tsx` — 详情 + 触发按钮 + 跳 runs
- [ ] `app/flows/[id]/runs/page.tsx` — ProTable 列 flow_runs
- [ ] 验证：流程列表显示所有 flow；点详情 → 触发 → flow_runs 多一行 running → succeeded

## V1-006：审计日志页

- [ ] `app/audits/page.tsx` — ProTable 列 audit_log
- [ ] 「校验链完整性」按钮 → 调 `verifyChain` → 显示 valid / broken at N
- [ ] 验证：审计页显示登录 / 接数据源 / 触发 / 跑完所有操作；链校验返回 valid

## V1-007：apps/flow_engine 服务骨架

- [ ] `apps/flow_engine/pyproject.toml` — FastAPI + temporalio + httpx + apscheduler
- [ ] `apps/flow_engine/src/main.py` — FastAPI app（管理 API：列出 / 重跑 / 取消 workflow）
- [ ] `apps/flow_engine/src/worker.py` — Temporal Worker 注册
- [ ] docker-compose 加 `flow-engine` + `temporal` + `postgres-temporal` 服务
- [ ] 验证：docker-compose up → flow-engine 起来连上 temporal

## V1-008：5 场景 Temporal Workflow

- [ ] `apps/flow_engine/src/workflows/generic.py` — GenericScenarioWorkflow（5 场景共用）
- [ ] `apps/flow_engine/src/activities/steps.py` — execute_step 支持 11 个标准
  - inventory_low_stock / notify_purchase / create_replenish_ticket
  - equipment_maintenance_due / create_maintenance_ticket / notify_maintenance
  - quality_inspection_sample / quality_judge_pass / tag_quality_result
  - production_collect_constraints / production_schedule_optimize / notify_schedule
  - inbound_qty_anomaly / inbound_quality_anomaly / create_8d_report / notify_supplier
- [ ] `apps/flow_engine/src/activities/db.py` — 通过后端 API 查 ontology 字段
- [ ] `apps/flow_engine/src/activities/notify.py` — V1 console.log 占位
- [ ] 验证：手动触发一个 Flow，worker 跑 3 step 全 succeeded，flow_runs 状态更新

## V1-009：3 类触发器

- [ ] `apps/flow_engine/src/triggers/manual.py` — 接收 API 调用 → 启动 workflow
- [ ] `apps/flow_engine/src/triggers/schedule.py` — APScheduler 每分钟扫 cron 匹配
- [ ] `apps/flow_engine/src/triggers/ontology_event.py` — V2 占位（V1 不接）
- [ ] 验证：手动 trigger 成功；schedule trigger 等到 cron 命中（V1 测试用每分钟跑一次）

## V1-010：5 道门禁补丁

- [ ] `coverage-python.sh` 加 `apps/flow_engine/` 扫描
- [ ] `coverage-node.sh` 加 `apps/web/` 扫描
- [ ] `gate-e2e.sh` 加 Playwright 调用
- [ ] `gate-deploy-test.sh` 加 `temporal` + `flow-engine` 健康检查
- [ ] 验证：客户机器跑 `bash gate.ps1 all` 全 PASS

## V1-011：5 场景 E2E（Playwright）

- [ ] `apps/web/e2e/01-datasource.spec.ts` — 登录 → 接 MySQL 测试库
- [ ] `apps/web/e2e/02-scenario-activate.spec.ts` — 激活「库存预警」
- [ ] `apps/web/e2e/03-flow-trigger.spec.ts` — 手动触发 → 等 succeeded
- [ ] `apps/web/e2e/04-flow-run-view.spec.ts` — 看 FlowRun 详情
- [ ] `apps/web/e2e/05-audit-chain.spec.ts` — 看审计 + 校验链 valid
- [ ] 验证：`pnpm playwright test` 5 spec 全 pass

## V1-012：install.sh 加 setup-default-admin

- [ ] 启动后自动创建 admin 用户（密码随机生成 → 打印给客户）
- [ ] 提示客户首次登录后改密码
- [ ] 验证：fresh install → admin 可登录；改密码后旧密码失败

---

## 任务勾选统计

- 12 个父任务
- 估时：~5~7 人日（密集实施）
- 完成数：0/12（启动时）
