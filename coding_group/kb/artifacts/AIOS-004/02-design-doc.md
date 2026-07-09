# 02-design-doc.md — V3 技术设计（AIOS-004 design 棒）

> 时点：2026-07-09 13:18 +08:00
> 设计范围：多租户 + RBAC + 监控告警 + SEC/OPS V2 留尾

---

## 1. 架构变更

### 1.1 复用 V0-V2

- 100% 复用 V0 数据层、错误体系、审计
- 100% 复用 V1 JWT + PBKDF2 鉴权
- 100% 复用 V2 4 类 parser / 本体 / LLM judge

### 1.2 新增服务

| 服务 | 镜像 | 端口 | 容器名 | profile |
|---|---|---|---|---|
| `prometheus` | prom/prometheus | 9090 | aios-prometheus | monitoring |
| `grafana` | grafana/grafana | 3001 | aios-grafana | monitoring |
| `loki` | grafana/loki | 3100 | aios-loki | monitoring |
| `promtail` | grafana/promtail | — | aios-promtail | monitoring |
| `cadvisor` | gcr.io/cadvisor/cadvisor | 8080 | aios-cadvisor | monitoring |

> profile=monitoring 不启动也不影响主流程；install.sh 提示用户选拉起。

### 1.3 后端包结构

```
apps/api/
├── src/
│   ├── auth.py                       # V1 + 加 org_id / role claims
│   ├── middleware/
│   │   ├── auth.py                   # V1 get_current_user
│   │   ├── tenancy.py                # V3 NEW: 注入 org_id 上下文
│   │   └── rbac.py                   # V3 NEW: require_permission
│   ├── api/v1/
│   │   ├── orgs.py                   # V3 NEW: CRUD org + 成员管理
│   │   ├── users.py                  # V3 NEW: 邀请 + 角色绑定
│   │   ├── metrics.py                # V3 NEW: /metrics (prometheus)
│   │   └── ... (V0/V1/V2 路由全保留 + Depends 加 tenancy/rbac)
│   └── models.py                     # + Org / OrgMember / Role / Permission
```

```
apps/flow_engine/
└── src/aios_flow/
    ├── main.py                       # + /metrics
    └── worker.py                     # + prometheus metrics

apps/ingest/src/aios_ingest/main.py  # + /metrics
apps/ontology/src/aios_ontology/main.py  # + /metrics
```

## 2. 数据模型（V3 增量）

### 2.1 新表（migration 0005_v3_tenancy）

```sql
CREATE TABLE orgs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(128) NOT NULL,
    slug VARCHAR(64) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE org_members (
    org_id UUID REFERENCES orgs(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role_key VARCHAR(32) NOT NULL,  -- admin | engineer | operator | viewer
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (org_id, user_id)
);

CREATE TABLE roles (
    key VARCHAR(32) PRIMARY KEY,    -- admin | engineer | operator | viewer
    label VARCHAR(64) NOT NULL,
    level INT NOT NULL               -- 4 / 3 / 2 / 1
);

CREATE TABLE permissions (
    key VARCHAR(64) PRIMARY KEY
);

CREATE TABLE role_permissions (
    role_key VARCHAR(32) REFERENCES roles(key),
    perm_key VARCHAR(64) REFERENCES permissions(key),
    PRIMARY KEY (role_key, perm_key)
);
```

### 2.2 业务表加 org_id

```sql
-- migration 0005: 给 V0-V2 的所有业务表加 org_id
ALTER TABLE datasources ADD COLUMN org_id UUID REFERENCES orgs(id);
ALTER TABLE scenarios ADD COLUMN org_id UUID REFERENCES orgs(id);
ALTER TABLE flows ADD COLUMN org_id UUID REFERENCES orgs(id);
ALTER TABLE flow_runs ADD COLUMN org_id UUID REFERENCES orgs(id);
ALTER TABLE audit_logs ADD COLUMN org_id UUID REFERENCES orgs(id);
ALTER TABLE ingest_jobs ADD COLUMN org_id UUID REFERENCES orgs(id);
ALTER TABLE llm_calls ADD COLUMN org_id UUID REFERENCES orgs(id);

-- 索引
CREATE INDEX idx_datasources_org ON datasources(org_id);
-- ... (每个业务表 1 个)
```

## 3. API 设计（V3 新增）

| Method | Path | 用途 | 鉴权 |
|---|---|---|---|
| POST | `/api/v1/orgs` | 建组织 | admin (无 org) |
| GET | `/api/v1/orgs` | 列出我所属组织 | JWT |
| POST | `/api/v1/orgs/{id}/members` | 邀请用户加入组织 | admin |
| GET | `/api/v1/orgs/{id}/members` | 列出成员 | member |
| PATCH | `/api/v1/orgs/{id}/members/{user_id}` | 改角色 | admin |
| DELETE | `/api/v1/orgs/{id}/members/{user_id}` | 移除 | admin |
| POST | `/api/v1/orgs/{id}/switch` | 切换当前 org_id（返回新 token）| member |
| GET | `/api/v1/permissions` | 列出所有权限点 | admin |
| GET | `/api/v1/metrics` | Prometheus scrape | 无（内网）|

> 所有 V0-V2 业务 API（datasources/flows/ingest/ontology/llm）都要在 `Depends` 链上加 `tenancy` + `rbac`。

## 4. RBAC 设计

### 4.1 4 角色

| 角色 | level | 权限点 |
|---|---|---|
| admin | 4 | 全部 |
| engineer | 3 | datasource.*, scenario.*, flow.*, ontology.*, llm.test, ingest.execute, audit.read |
| operator | 2 | datasource.read, scenario.read, flow.execute, ingest.execute, ontology.read |
| viewer | 1 | *.read |

### 4.2 中间件

```python
def require_permission(perm: str):
    async def _dep(user: CurrentUser = Depends(get_current_user),
                   org: OrgContext = Depends(require_org_member)):
        if not has_perm(user, org, perm):
            raise HTTPException(403, f"missing permission: {perm}")
        return user, org
    return _dep
```

## 5. 监控设计

### 5.1 指标

| 名称 | 类型 | labels | 位置 |
|---|---|---|---|
| `aios_api_request_total` | Counter | method, path, status | API |
| `aios_api_request_duration_seconds` | Histogram | method, path | API |
| `aios_flow_run_total` | Counter | flow_id, status | flow_engine |
| `aios_flow_step_duration_seconds` | Histogram | step_id | flow_engine |
| `aios_llm_call_total` | Counter | provider, model | API + flow_engine |
| `aios_llm_call_duration_seconds` | Histogram | provider | API + flow_engine |
| `aios_ingest_job_total` | Counter | kind, status | ingest |
| `aios_ontology_node_total` | Gauge | kind | ontology |
| `aios_ollama_up` | Gauge | — | ontology |

### 5.2 告警规则（prometheus）

5 条 alerts，详见 03-tasks.md V3-005。

### 5.3 Grafana 仪表盘

5 个 dashboard：API / Flow / LLM / Ingest / Ontology

每个 dashboard 4-6 个 panel（rate / histogram / gauge / 错误率 / 资源）。

## 6. SEC-V3-01 设计

### 6.1 LLM judge 拆 system / user

```python
@dataclass
class LLMJudgeInput:
    system_prompt: str  # 固定：角色 + JSON schema + 反 prompt injection
    user_prompt: str    # 业务上下文（data 段，不解析为指令）
    context: dict
    expected_schema: list[str]
```

### 6.2 反 prompt injection 关键词

`IGNORE_PREV`, `DISREGARD`, `YOU_ARE_NOW`, `NEW_INSTRUCTIONS`, `SYSTEM`, `###` 等等。
命中 → confidence 强制 0 + decision 强制 False + log warning。

## 7. OPS-V3-02 设计

### 7.1 ollama 容器改造

```dockerfile
FROM ollama/ollama:latest
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
```

```bash
#!/bin/bash
# entrypoint.sh
ollama serve &
OLLAMA_PID=$!
# 等待 ollama ready
for i in {1..30}; do
  if curl -sf http://localhost:11434/api/tags > /dev/null; then break; fi
  sleep 1
done
# pull 默认模型
ollama pull qwen2.5:7b
wait $OLLAMA_PID
```

### 7.2 install.sh

- `docker compose --profile monitoring up -d` 选拉起
- `docker exec aios_ollama_1 ollama list` 输出 `qwen2.5:7b` 才视为成功

## 8. 5 道门禁 V3 补丁

| 门禁 | V3 改动 |
|---|---|
| gate-baseline | 加 V3 baseline（orgs / metrics / ollama_pull 失败 list） |
| gate-coverage | 已自动 find 多包，V3 多 4 个包 |
| gate-lint | ruff 加 S 安全规则（`bandit` 风格） |
| gate-deploy-test | 加 prometheus / grafana / ollama qwen pull health |
| gate-e2e | V3 + 5 spec |

## 9. 风险与对策

| 风险 | 对策 |
|---|---|
| 多租户数据泄露 | 强类型 OrgContext 上下文 + 中间件 + e2e 验证 |
| Prometheus 拉起慢 | profile=monitoring 按需启动 |
| 反 prompt injection 误伤合法 context | 关键词走 soft match + log review |
| 5 道门禁在客户机器性能差异 | 加 timeout 单独告警 |

## 10. 包含 / 不包含

### 包含
- 多租户（orgs + members + 中间件 + 切换 token）
- RBAC（4 角色 + 30+ 权限 + 中间件 + 前端权限隐藏）
- 监控（Prometheus + Grafana + Loki + cadvisor + 5 dashboard + 5 alerts）
- 4 服务 metrics 端点
- SEC-V3-01（LLM system role 隔离）
- OPS-V3-02（Ollama auto pull）
- 5 个 V3 E2E
- 5 道门禁 V3 补丁
- 前端：组织切换 + 用户管理 + 监控页 + 权限隐藏

### 不包含
- ASR 自训练（V4）
- 本体在线学习（V4）
- 移动端（V4）
- 复杂 BI 报表（V4）
- 多 LLM provider failover（V4）
