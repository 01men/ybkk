# 08-ship-log.md — V3 发货记录（AIOS-004 ship 棒）

> 发货人：orchestrator
> 时点：2026-07-09 14:10 +08:00
> GitHub: https://github.com/01men/ybkk

---

## 1. Git

| 项 | 值 |
|---|---|
| Commit | `9e17bd7` |
| Branch | `main` |
| Push | ✅ `cae95f5..9e17bd7 main -> main` |
| 变更范围 | 52 files changed, 3438 insertions(+), 156 deletions(-) |
| SSH | ed25519 key `ybkk_github_global_ed25519`（V1 已配置） |

## 2. 制品清单（推送内容）

### 多租户 backend (V3-001)
- `apps/api/src/db/migrations/versions/0005_v3_tenancy.py` (NEW)
- `apps/api/src/middleware/tenancy.py` (NEW)
- `apps/api/src/models.py` (M) + `apps/api/src/auth.py` (M)

### RBAC (V3-002)
- `apps/api/src/middleware/rbac.py` (NEW)
- `apps/api/tests/test_rbac.py` (NEW — 20 关键矩阵)
- V0-V2 业务 API 加 `Depends(require_permission(...))`

### 监控 (V3-003 + V3-004 + V3-005)
- `deploy/compose/monitoring/prometheus.yml` (NEW)
- `deploy/compose/monitoring/alerts.yml` (NEW)
- `deploy/compose/monitoring/grafana/provisioning/{datasources,dashboards}.yml` (NEW)
- `deploy/compose/monitoring/grafana/dashboards/aios-{api,flow,llm,ingest,ontology}.json` (NEW × 5)
- `deploy/compose/monitoring/loki-config.yml` (NEW)
- `deploy/compose/monitoring/promtail/promtail-config.yml` (NEW)
- 4 服务 metrics: `apps/{api,flow_engine,ingest,ontology}/.../metrics.py` (NEW)

### SEC-V3-01 (V3-006)
- `apps/flow_engine/src/aios_flow/activities/llm_judge.py` (M — 大改)
- `apps/flow_engine/src/aios_flow/workflows/generic.py` (M)
- `apps/flow_engine/tests/test_llm_judge.py` (M — 大改 5 反注入测试)

### OPS-V3-02 (V3-007)
- `apps/ollama/Dockerfile` (NEW)
- `apps/ollama/entrypoint.sh` (NEW — 含 bug fix)

### 前端 (V3-008)
- `apps/web/src/app/orgs/page.tsx` (NEW)
- `apps/web/src/app/orgs/[id]/page.tsx` (NEW)
- `apps/web/src/app/monitoring/page.tsx` (NEW)
- `apps/web/src/app/console-shell.tsx` (M — RBAC perm 过滤 + org Select)

### 门禁 (V3-009)
- `coding_group/assets/scripts/gate-lint.sh` (M — ruff S 系列)
- `coding_group/assets/scripts/gate-deploy-test.sh` (M — 3 V3 健康检查)

### E2E (V3-010)
- `apps/web/e2e/11-org-switch.spec.ts` (NEW)
- `apps/web/e2e/12-rbac.spec.ts` (NEW)
- `apps/web/e2e/13-monitoring.spec.ts` (NEW)
- `apps/web/e2e/14-llm-system-role.spec.ts` (NEW)
- `apps/web/e2e/15-ollama-pull.spec.ts` (NEW)

### Compose (V3-011)
- `deploy/compose/docker-compose.yml` (M — AIOS_VERSION 0.4.0 + 5 monitoring service)

### 制品 (STAGE 7-8)
- `coding_group/kb/artifacts/AIOS-004/{00~07 + state.json}` (NEW × 9)

## 3. 部署建议

```bash
# 客户机器（Linux 8C16G）
cd /opt/ybkk
git clone https://github.com/01men/ybkk.git
cd ybkk/deploy/compose
cp .env.example .env  # 改 POSTGRES_PASSWORD / MINIO_ROOT_PASSWORD / JWT_SECRET / GRAFANA_ADMIN_PASSWORD
./install.sh          # 拉镜像 + 起容器

# 监控（profile=monitoring 默认不起，需要时启动）
docker compose --profile monitoring up -d
# 访问：
#   Grafana http://localhost:3001 (admin / GRAFANA_ADMIN_PASSWORD)
#   Prometheus http://localhost:9090
#   Loki http://localhost:3100
#   cadvisor http://localhost:8080
```

## 4. 门禁实跑（客户机器）

```bash
cd /opt/ybkk
bash coding_group/assets/scripts/gate-baseline.sh --snapshot
bash coding_group/assets/scripts/gate-baseline.sh status
bash coding_group/assets/scripts/gate-coverage.sh
bash coding_group/assets/scripts/gate-lint.sh
bash coding_group/assets/scripts/gate-deploy-test.sh
bash coding_group/assets/scripts/gate-e2e.sh
```

V3 预期：
- baseline = 空 failures（与现状一致）
- coverage = ≥ 80% (RBAC / LLM judge 关键矩阵)
- lint = ruff + S 系列 PASS
- deploy-test = api + ingest + ontology + ollama + prometheus + grafana + qwen2.5:7b 7 health OK
- e2e = 15 spec（V0~V3 共）全过

## 5. 版本

- AIOS_VERSION: `0.4.0`
- OLLAMA 默认模型: `qwen2.5:7b`
- Grafana 仪表盘: 5 个
- Prometheus alerts: 6 条
- 反注入关键词: 10 个
- RBAC 角色: 4（admin/engineer/operator/viewer）
- 权限点: 30
- 多租户表: 5（orgs/org_members/roles/permissions/role_permissions）

## 6. V4 留尾（非阻塞）

1. 反注入升级到正则 word boundary（防 substring 误伤）
2. JWT 强制重新签发（去掉「空组织」兼容分支）
3. Grafana datasource 加 `extra_hosts: ["host.docker.internal:host-gateway"]`（客户非 swarm 环境）
4. `/auth/me` 后端返回 `perms` 字段（前端去掉 system.manage 兜底）
5. RBAC 中给 admin 加 `org.delete` 测试
6. internal API 加 mTLS（V1 沿用的「仅 docker 网络隔离」升一档）

## 7. 结束语

V3 (AIOS-004) 11 任务全部完成，9 阶段状态机跑通。
GitHub 主分支已同步 commit `9e17bd7`。

V0 → V1 → V2 → V3 四棒连推，元冰可可 AIOS 完成 4 阶段演进：

| 版本 | 主题 | 任务数 | commits |
|---|---|---|---|
| V0 (AIOS-001) | 脚手架 | 8 | `6d30217` |
| V1 (AIOS-002) | web + temporal + e2e | 12 | `b6603a2` |
| V2 (AIOS-003) | ingest + ontology + LLM | 11 | `42fdc50` |
| V3 (AIOS-004) | 多租户 + RBAC + 监控 + SEC/OPS | 11 | `9e17bd7` |

> 元冰可可 AIOS 已具备私有化交付基础：5 服务 + 5 内置场景 + 4 角色 RBAC + 完整监控告警 + 反 prompt injection + Ollama 自部署。客户机器实跑 5 道门禁后即可上线。