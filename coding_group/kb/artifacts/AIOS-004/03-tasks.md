# 03-tasks.md — V3 任务清单（AIOS-004 design 棒）

> 来源：02-design-doc.md
> 时点：2026-07-09 13:22 +08:00

---

## V3-001：多租户 backend

- [ ] migration 0005_v3_tenancy — orgs + org_members + 业务表加 org_id
- [ ] apps/api/src/models.py — Org / OrgMember 模型
- [ ] apps/api/src/auth.py — JWT claims 加 `org_id` + `role_key`
- [ ] apps/api/src/middleware/tenancy.py — OrgContext + require_org_member
- [ ] apps/api/src/api/v1/orgs.py — org CRUD + 成员管理 + 切换
- [ ] 验证：2 个 org 用户互相不可见对方数据

## V3-002：RBAC backend

- [ ] migration 内置 4 角色 + 30 权限点
- [ ] apps/api/src/middleware/rbac.py — require_permission
- [ ] V0-V2 业务 API 全加 `Depends(require_permission(...))`
- [ ] apps/api/src/api/v1/permissions.py — 权限点查询
- [ ] 单测：4 角色 × 5 关键权限 = 20 用例
- [ ] 验证：无权限调 API 返回 403

## V3-003：监控（profile=monitoring）

- [ ] deploy/compose/monitoring/prometheus.yml
- [ ] deploy/compose/monitoring/grafana/provisioning/datasources.yml
- [ ] deploy/compose/monitoring/grafana/provisioning/dashboards.yml
- [ ] deploy/compose/monitoring/loki-config.yml
- [ ] deploy/compose/monitoring/promtail-config.yml
- [ ] deploy/compose/monitoring/dashboards/*.json（5 个 dashboard JSON）
- [ ] docker-compose 加 5 个 service（profile=monitoring）

## V3-004：应用 metrics 端点

- [ ] apps/api/src/api/v1/metrics.py — `GET /metrics` (prometheus_client)
- [ ] apps/api/src/main.py — Instrumentator 中间件
- [ ] apps/flow_engine 加 /metrics
- [ ] apps/ingest 加 /metrics
- [ ] apps/ontology 加 /metrics
- [ ] 5 类指标：api_request / flow_run / llm_call / ingest_job / ontology_node

## V3-005：告警规则

- [ ] deploy/compose/monitoring/alerts.yml — 5 条 alert rules
- [ ] prometheus.yml 引用 alerts.yml
- [ ] 验证：模拟 5xx 触发 alert（K6 脚本或手测）

## V3-006：SEC-V3-01（LLM system role 隔离）

- [ ] llm_judge.py 拆 system_prompt + user_prompt
- [ ] system_prompt 固定文案（角色 + JSON schema + 反注入）
- [ ] 反注入关键词检测（IGNORE / DISREGARD / YOU_ARE_NOW 等）
- [ ] 命中时 confidence=0 + log warning
- [ ] 单测：3 条 injection 攻击 + 1 条合法
- [ ] flow_engine 改 generic.py 传 system_prompt

## V3-007：OPS-V3-02（Ollama auto pull）

- [ ] apps/ollama/Dockerfile（V3 NEW）
- [ ] apps/ollama/entrypoint.sh
- [ ] deploy/compose/docker-compose.yml 改 ollama image
- [ ] install.sh 加 `ollama list | grep qwen2.5:7b` 等待
- [ ] 验证：首次启动日志有 `qwen2.5:7b pulled successfully`

## V3-008：前端 — 组织切换 + 用户管理 + 监控

- [ ] apps/web/src/app/orgs/page.tsx — 列出我的组织
- [ ] apps/web/src/app/orgs/new/page.tsx — 建组织
- [ ] apps/web/src/app/orgs/[id]/page.tsx — 成员管理
- [ ] apps/web/src/app/monitoring/page.tsx — 嵌入 Grafana iframe
- [ ] console-shell 顶部加 org 切换下拉
- [ ] 权限隐藏：viewer 看不到 ingest/ontology 菜单

## V3-009：5 道门禁 V3 补丁

- [ ] gate-baseline — V3 baseline json
- [ ] gate-lint — 加 ruff S 系列（bandit）
- [ ] gate-deploy-test — 加 prometheus / grafana / ollama qwen pull health
- [ ] 验证：5 门禁脚本跑通

## V3-010：5 个 V3 E2E

- [ ] 11-org-switch.spec.ts — 建 2 个 org + 切换 + 数据隔离
- [ ] 12-rbac.spec.ts — viewer 看不到 ingest 菜单 / 调 API 403
- [ ] 13-monitoring.spec.ts — Grafana 页可访问 + 5 dashboard 标题
- [ ] 14-llm-system-role.spec.ts — llm-usage 测 system prompt 隔离
- [ ] 15-ollama-pull.spec.ts — 测 ollama qwen2.5:7b 已拉（health 200）

## V3-011：docker-compose V3 升级

- [ ] 加 prometheus / grafana / loki / promtail / cadvisor
- [ ] 加 `apps/api` metrics 端口（8080 内部 `/metrics`）
- [ ] 加 `apps/ollama` 独立 image
- [ ] profile=monitoring 默认不起，需 `docker compose --profile monitoring up -d`

---

**任务勾选统计**：11 个父任务，约 40 子项
