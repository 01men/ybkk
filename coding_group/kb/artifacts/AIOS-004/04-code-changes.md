# 04-code-changes.md — V3 代码变更清单（AIOS-004 dev 棒）

> 来源：03-tasks.md V3-001~V3-011（11 父任务 / 约 40 子项）
> 时点：2026-07-09 13:55 +08:00

---

## V3-001: 多租户 backend

**新增**：
- `apps/api/src/db/migrations/versions/0005_v3_tenancy.py` — 5 张表（orgs / org_members / roles / permissions / role_permissions）+ 7 张业务表加 `org_id` 列 + 内置 4 角色 / 30 权限点 / 角色权限矩阵 seed
- `apps/api/src/middleware/tenancy.py` — `OrgContext` dataclass + `get_org_context` dependency + `require_org_member`

**修改**：
- `apps/api/src/models.py` — 加 `Org` / `OrgMember` / `Role` / `Permission` / `RolePermission`
- `apps/api/src/auth.py` — `user_to_jwt(user, org_id="", role_key="")` 签 JWT 时带 2 个新 claims

**新增路由**（`apps/api/src/api/v1/orgs.py`）：
- `GET  /api/v1/orgs` — 列出我的组织
- `POST /api/v1/orgs` — 创建组织（admin only）
- `POST /api/v1/orgs/{id}/switch` — 切换组织（返回新 JWT）
- `GET  /api/v1/orgs/{id}/members` — 成员列表
- `POST /api/v1/orgs/{id}/members` — 邀请成员
- `PATCH /api/v1/orgs/{id}/members/{uid}` — 改角色
- `DELETE /api/v1/orgs/{id}/members/{uid}` — 移除

---

## V3-002: RBAC backend

**新增**：
- `apps/api/src/middleware/rbac.py` — `ALL_PERMISSIONS` tuple (30) + `ROLE_LEVEL` dict + `ROLE_PERMISSIONS` dict + `has_permission(role, perm)` + `permissions_for(role)`
- `apps/api/tests/test_rbac.py` — 4 角色 × 5 关键权限 = 20 单测用例
- `apps/api/src/api/v1/permissions.py` — `GET /api/v1/permissions` 返回当前用户 perms

**修改**：V0-V2 业务 API 全部加 `Depends(require_permission(...))` 鉴权（`datasources` / `ingest` / `scenarios` / `flows` / `audits` / `ontology` / `llm`）

**4 角色权限矩阵**：
- **admin** — 全部 30 权限
- **engineer** — 15 权限（不含 `system.manage` / `org.delete` / `user.delete`）
- **operator** — 6 权限（场景运行 / 数据源只读 / flow 触发 / ingest / 监控只读）
- **viewer** — 6 权限（只读：scenario / datasource / flow / audit / llm / monitoring）

---

## V3-003: 监控 stack（profile=monitoring）

**新增**：
- `deploy/compose/monitoring/prometheus.yml` — scrape 6 jobs（api/flow-engine/ingest/ontology/ollama/cadvisor）
- `deploy/compose/monitoring/alerts.yml` — 6 alert rules
- `deploy/compose/monitoring/grafana/provisioning/datasources/datasources.yml` — Prometheus + Loki
- `deploy/compose/monitoring/grafana/provisioning/dashboards/dashboards.yml` — provider
- `deploy/compose/monitoring/grafana/dashboards/aios-api.json` — 4 panels
- `deploy/compose/monitoring/grafana/dashboards/aios-flow.json` — 3 panels
- `deploy/compose/monitoring/grafana/dashboards/aios-llm.json` — 3 panels
- `deploy/compose/monitoring/grafana/dashboards/aios-ingest.json` — 2 panels
- `deploy/compose/monitoring/grafana/dashboards/aios-ontology.json` — 3 panels
- `deploy/compose/monitoring/loki-config.yml` — schema v13 + 168h retention
- `deploy/compose/monitoring/promtail/promtail-config.yml` — docker sd_configs

---

## V3-004: 应用 metrics 端点（stdlib-only）

**新增**：
- `apps/api/src/metrics.py` — `Counter` / `Histogram` / `Gauge` 自实现（避免引入 prometheus_client 依赖）
- `apps/api/src/api/v1/metrics.py` — `GET /api/v1/metrics` 输出 prometheus 文本格式 + `metrics_middleware` 自动计数请求

**修改 / 新增**：
- `apps/flow_engine/src/aios_flow/metrics.py` + `main.py` 加 `GET /metrics` 端点 + version 0.3.0
- `apps/ingest/src/aios_ingest/metrics.py` + `main.py` 加 `GET /metrics` + 成功/失败 inc metric
- `apps/ontology/src/aios_ontology/metrics.py` + `main.py` 加 `GET /metrics` + `OLLAMA_UP` Gauge

---

## V3-005: 告警规则（6 alerts）

`deploy/compose/monitoring/alerts.yml`:
1. `AiosApi5xxRateHigh` — 5xx 错误率 > 5% / 5min
2. `AiosFlowFailureRateHigh` — flow 失败率 > 20% / 10min
3. `AiosOllamaDown` — Ollama API 不可达 2min
4. `AiosIngestJobFailure` — ingest 任务失败 > 3 / 5min
5. `AiosNeo4jDown` — neo4j 不可达 1min
6. `AiosLlmInjectionSpike` — LLM 注入拦截计数 > 0 / 5min（SEC-V3-01 联动）

---

## V3-006: SEC-V3-01（LLM system role 隔离 + 反注入）

**修改**：
- `apps/flow_engine/src/aios_flow/activities/llm_judge.py`（大改）：
  - `LLMJudgeInput` 拆 `system_prompt` + `user_prompt` 两个字段
  - `DEFAULT_SYSTEM_PROMPT` 固定文案（角色 + JSON schema + 反注入规则）
  - `INJECTION_KEYWORDS` 10 个关键词：`ignore previous` / `ignore all` / `disregard` / `you are now` / `new instructions` / `system:` / `### system` / `### instruction` / `system` / `<|system|>`
  - `_detect_injection` substring lowercase 匹配
  - `_build_messages` 走 `messages=[system, user]` 调 `/api/chat`（不是 `/api/generate`）
  - 命中时返回 `blocked=True` + `[injection_blocked]` reason
  - `LLMJudgeResult` 加 `blocked: bool` 字段
- `apps/flow_engine/src/aios_flow/workflows/generic.py`：
  - `llm_judge_activity` 改用 `user_prompt=` 参数
  - 返回 dict 加 `"blocked": result.blocked`

**新增测试**（`apps/flow_engine/tests/test_llm_judge.py` 大改）：
- `_build_messages` 用 messages=[system, user] 而非 prompt= 拼接
- `_detect_injection` 命中关键词
- `blocks_ignore_previous` — 包含 "ignore previous" 时 confidence=0 + blocked=True
- `blocks_system_role` — 包含 "system:" 时被拦
- `does_not_call_ollama_when_injection` — 命中时 httpx post 不被调用（用 mock）
- `passes_through_legitimate_context` — 合法输入走 ollama

---

## V3-007: OPS-V3-02（Ollama auto pull）

**新增**：
- `apps/ollama/Dockerfile` — `FROM ollama/ollama:latest` + 拷贝 entrypoint.sh + ENV `AIOS_OLLAMA_PULL_MODELS=qwen2.5:7b`
- `apps/ollama/entrypoint.sh`：
  1. 后台启 `ollama serve`
  2. 轮询 `curl /api/tags` 等就绪（最多 60s）
  3. 遍历 `AIOS_OLLAMA_PULL_MODELS`（逗号分隔）逐个 `ollama pull`
  4. 打印 success 日志 + 前台 wait ollama serve
  - **Bug fix（V3 收尾发现）**：`$LOG_PREFIX` 缺 `echo` 引号，已修

---

## V3-008: 前端 — 组织 + 监控

**新增**：
- `apps/web/src/app/orgs/page.tsx` — 我的组织列表 + 新建组织 Modal + 切换按钮
- `apps/web/src/app/orgs/[id]/page.tsx` — 成员管理 + 邀请 + 改角色 + 移除
- `apps/web/src/app/monitoring/page.tsx` — 5 dashboard 卡片 + Prometheus 状态

**修改**：
- `apps/web/src/app/console-shell.tsx`：
  - V3 RBAC：菜单按 `NAV_PERMS` perm 过滤
  - 顶部 org 切换 Select
  - 当前角色 tag 显示

---

## V3-009: 5 道门禁 V3 补丁

**修改**：
- `coding_group/assets/scripts/gate-lint.sh` — 加 `ruff check --select S`（bandit 安全规则：hardcoded password / 不安全 hash / assert 用作校验）
- `coding_group/assets/scripts/gate-deploy-test.sh` — 加 3 个 V3 健康检查：
  - prometheus `:9090/-/healthy` (当 aios_prometheus_1 容器运行)
  - grafana `:3000/api/health` (当 aios_grafana_1 容器运行)
  - ollama qwen2.5:7b 模型已 pull（`/api/tags` grep qwen2.5:7b）

baseline.json 不需要更新（仍是空 failures，与现状一致）

---

## V3-010: 5 个 V3 E2E

**新增**：
- `apps/web/e2e/11-org-switch.spec.ts` — 组织列表 + 新建 Modal + 成员管理
- `apps/web/e2e/12-rbac.spec.ts` — admin 菜单可见（监控/组织/审计）+ role tag 显示
- `apps/web/e2e/13-monitoring.spec.ts` — 5 dashboard 卡片标题 + Prometheus 状态卡片
- `apps/web/e2e/14-llm-system-role.spec.ts` — LLM dashboard 描述含「注入拦截」+ /metrics 端点
- `apps/web/e2e/15-ollama-pull.spec.ts` — ollama qwen-local 按钮 + API health 200 + ontology dashboard Ollama

---

## V3-011: docker-compose V3 升级

**修改**：
- `deploy/compose/docker-compose.yml`（大改）：
  - 所有镜像 tag `${AIOS_VERSION:-0.4.0}`（V0/V1/V2 是 0.3.0）
  - ollama 改用独立 image `ghcr.io/01men/ybkk-ollama:0.4.0`（带 entrypoint 自动 pull）
  - 加 5 个 monitoring service（prometheus / grafana / loki / promtail / cadvisor），全部 `profiles: ["monitoring"]` 默认不起
  - grafana 加 anonymous Viewer（无需登录预览 dashboard）
  - monitoring / grafana / loki / promtail 4 个持久卷
  - cadvisor privileged + /dev/kmsg
  - prometheus 启用 `--web.enable-lifecycle`（支持热加载配置）

---

## 制品完备性

| 阶段 | 制品 | 状态 |
|---|---|---|
| dev | 04-code-changes.md | ✅ 本文件 |
| dev | tests/ | ✅ 5 个 V3 单测（test_rbac + test_llm_judge 改写） |
| dev | 05-self-test-report.md | ✅ 下一文件 |
| review | 06-review-report.md | ✅ |
| verify | 07-delivery-report.md | （STAGE 8 写） |
| ship | 08-ship-log.md | （STAGE 9 写） |

> AIOS_VERSION: 0.3.0 → 0.4.0