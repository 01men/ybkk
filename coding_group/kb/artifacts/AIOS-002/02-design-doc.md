# 02-design-doc.md — V1 技术设计（AIOS-002 design 棒）

> 设计范围：V1 核心闭环 = 前端控制台 + Temporal 场景编排 + FlowRun + E2E。
> 时点：2026-07-09 09:45 +08:00。

---

## 1. 架构变更

### 1.1 新增服务

| 服务 | 技术栈 | 端口 | 容器名 |
|---|---|---|---|
| `apps/web` | Next.js 14 (App Router) + Ant Design Pro + TypeScript | 3000 | aios-web |
| `apps/flow_engine` | FastAPI + Temporal Python SDK worker | 8081 | aios-flow-engine |
| `temporal` | Temporal Server (单节点) | 7233 | aios-temporal |
| `temporal-ui` | Temporal Web UI（可选） | 8088 | aios-temporal-ui |
| `postgres-temporal` | PostgreSQL 16（Temporal 元数据，独立库）| 5433 | aios-postgres-temporal |

> Temporal 用独立 PG 实例（不与业务库混）→ 业务故障不影响 Temporal 心跳。

### 1.2 复用服务（V0 资产 100% 复用）

- `apps/api` (8080) — 数据源 / 场景 / 流程 / 审计 API
- `aios-postgres` (5432) — 业务库
- `aios-neo4j` (7474/7687) — 本体图（V1 暂不接 V2）
- `aios-minio` (9000/9001) — 对象存储
- `aios-redis` (6379) — 缓存

### 1.3 docker-compose 扩展示意图

```yaml
# 新增
temporal:
  image: temporalio/auto-setup:1.24
  ports: ["7233:7233"]
  environment:
    - DB=postgresql
    - POSTGRES_USER=temporal
    - POSTGRES_PWD=temporal
    - POSTGRES_SEEDS=postgres-temporal
  depends_on: [postgres-temporal]

postgres-temporal:
  image: postgres:16
  environment:
    - POSTGRES_USER=temporal
    - POSTGRES_PASSWORD=temporal
    - POSTGRES_DB=temporal
  volumes: [temporal_pg:/var/lib/postgresql/data]

flow-engine:
  build: ./apps/flow_engine
  command: python -m aios_flow.worker
  environment:
    - TEMPORAL_HOST=temporal:7233
    - AIOS_API_URL=http://api:8080
  depends_on: [temporal, api]

web:
  build: ./apps/web
  ports: ["3000:3000"]
  environment:
    - AIOS_API_URL=http://api:8080
  depends_on: [api]
```

## 2. 数据模型（V1 增量）

### 2.1 flows 表（V0 已存在，V1 补字段）

```sql
-- V0 已有：id, key, scenario_id, datasource_id, status, created_at
-- V1 新增：
ALTER TABLE flows ADD COLUMN trigger_type VARCHAR(32);       -- manual | schedule | ontology_event
ALTER TABLE flows ADD COLUMN trigger_config JSONB;           -- schedule: {cron: "0 8 * * *"} | manual: null | ontology_event: {watch_field: "..."}
ALTER TABLE flows ADD COLUMN temporal_workflow_id VARCHAR(128);  -- Temporal 端 workflow_id
```

### 2.2 flow_runs 表（V0 已存在，V1 补字段）

```sql
-- V0 已有：id, flow_id, status, started_at, finished_at
-- V1 新增：
ALTER TABLE flow_runs ADD COLUMN trigger_type VARCHAR(32);
ALTER TABLE flow_runs ADD COLUMN temporal_run_id VARCHAR(128);
ALTER TABLE flow_runs ADD COLUMN step_results JSONB;        -- [{step_id, status, output, error}]
ALTER TABLE flow_runs ADD COLUMN actor VARCHAR(128);
```

### 2.3 新表 `users`（V1 新增）

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(64) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,  -- bcrypt
    role VARCHAR(32) NOT NULL DEFAULT 'admin',  -- V1 简化为单角色
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
-- 默认用户 admin / changeme（install.sh 提示改）
```

## 3. API 设计（V1 新增）

| Method | Path | 用途 | 鉴权 |
|---|---|---|---|
| POST | `/api/v1/auth/login` | 登录返回 JWT | 无 |
| GET | `/api/v1/auth/me` | 当前用户 | JWT |
| GET | `/api/v1/flows` | 列出所有 Flow | JWT |
| POST | `/api/v1/flows` | 创建 Flow（绑定 scenario + datasource + trigger）| JWT |
| GET | `/api/v1/flows/{id}` | 详情 | JWT |
| POST | `/api/v1/flows/{id}/trigger` | 手动触发 | JWT |
| GET | `/api/v1/flows/{id}/runs` | 列出 FlowRun | JWT |
| GET | `/api/v1/flow-runs/{id}` | 详情（含 step_results）| JWT |
| GET | `/api/v1/audits` | 审计日志列表 + 链校验 | JWT |

> V0 已有路由全部保留；V1 加 `Depends(get_current_user)` 中间件。

## 4. 前端架构

### 4.1 路由

```
app/
├── layout.tsx              # 全局 layout（antd ConfigProvider + 主题）
├── page.tsx                # / → 重定向到 /datasources
├── login/page.tsx          # /login
├── datasources/page.tsx    # 数据源列表
├── datasources/new/page.tsx  # 数据源新建表单
├── scenarios/page.tsx      # 5 场景卡片
├── scenarios/[key]/page.tsx  # 场景详情 + DAG 图
├── flows/page.tsx          # 流程列表
├── flows/[id]/page.tsx     # 流程详情 + 触发
├── flows/[id]/runs/page.tsx  # FlowRun 列表
├── audits/page.tsx         # 审计日志
└── api/                    # BFF（可选；V1 直接调后端）
```

### 4.2 状态管理

- TanStack Query（React Query）— 服务端状态
- Zustand — 客户端状态（当前用户 / 主题）
- 不要 Redux（V1 体量不需要）

### 4.3 UI 组件

- Ant Design Pro 5.x（开箱即用的 ProTable / ProForm / ProCard）

## 5. Temporal Workflow 设计

### 5.1 通用场景 workflow

```python
@workflow.defn
class GenericScenarioWorkflow:
    @workflow.run
    async def run(self, input: ScenarioInput) -> ScenarioResult:
        # 1. 加载场景模板
        scenario = await workflow.execute_activity(
            load_scenario, input.scenario_key,
            start_to_close_timeout=timedelta(seconds=10),
        )
        # 2. 按流模板顺序执行每个 step
        results = []
        for step in scenario.flow_template:
            step_result = await workflow.execute_activity(
                execute_step,
                StepInput(flow_id=input.flow_id, step=step, prev_results=results),
                start_to_close_timeout=timedelta(seconds=300),
            )
            results.append(step_result)
        return ScenarioResult(flow_id=input.flow_id, steps=results)
```

### 5.2 触发器

| 触发器类型 | 实现 |
|---|---|
| manual | 前端调 `POST /api/v1/flows/{id}/trigger` → API 调 `temporal.start_workflow()` |
| schedule | APScheduler 跑在 flow_engine 进程里，每分钟扫一次，对 cron 匹配的 Flow 触发 |
| ontology_event | V2 实现（订阅 Neo4j 事件） |

### 5.3 step 执行

每个 step = 一个标准（DeliveryStandard）= 一段 Python 逻辑。V1 不接 LLM（V2 接），V1 用 if/else 跑标准：

```python
@activity.defn
async def execute_step(input: StepInput) -> StepResult:
    std = input.step.standard_key
    if std == "inventory_low_stock":
        # 查 material.current_stock < material.safety_stock
        # 返回 StepResult(matched=True, payload={...})
        ...
    elif std == "notify_purchase":
        # 调通知 API（V1 用 console.log 占位，V2 接飞书/钉钉/邮件）
        ...
```

## 6. 5 道门禁（V1 在客户机器实跑）

| 门禁 | V1 命令 | 预期结果 |
|---|---|---|
| gate-baseline | `bash coding_group/assets/scripts/gate-baseline.sh` | PASS |
| gate-coverage | `bash .../gate-coverage.sh` | core ≥ 80%，整体 ≥ 60% |
| gate-lint | `bash .../gate-lint.sh` | ruff + eslint 全过 |
| gate-deploy-test | `bash .../gate-deploy-test.sh` | docker-compose up + 健康检查 |
| gate-e2e | `bash .../gate-e2e.sh` | Playwright 5 场景全过 |

## 7. 5 道门禁实现补丁

V0 5 道门禁脚本已落库；V1 不改门禁，只改门禁调到的目标：

- `coverage-python.sh` — 加 `apps/flow_engine/` 扫描
- `coverage-node.sh` — 加 `apps/web/` 扫描
- `gate-e2e.sh` — 加 Playwright 5 场景

## 8. 与 V0 偏离

- 零偏离。V1 100% 复用 V0 数据层 + 错误体系 + 审计。

## 9. 风险与对策

| 风险 | 对策 |
|---|---|
| Temporal 单点 | 客户私有化部署：单节点足够；生产环境加 HA 留 V3 |
| Next.js 性能 | RSC + 静态生成，antd 按需 import |
| E2E 跑挂 | 拆 5 个独立 spec，CI 报告分别统计 |
| 5 道门禁在客户机器性能差异 | 脚本加 timeout；超时单独告警 |

## 10. 包含 / 不包含

### 包含

- Next.js 14 + 5 页面 + antd
- FastAPI + Temporal worker + 5 场景 workflow
- FlowRun 状态机 + 3 类触发器
- 5 场景 E2E
- 5 道门禁在客户机器实跑
- 安装脚本加 `setup-default-admin` 步骤

### 不包含

- LLM 接入（V2）
- 本体推断（V2）
- 多租户 / 细粒度 RBAC（V3）
- 监控告警（V3）
