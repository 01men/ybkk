# 02-design-doc.md — 技术方案
req-id: AIOS-001
based-on: 01-requirement-doc.md
created: 2026-07-08
author: solution-architect
version: 1

---

## 1. 方案摘要（200 字内）

元冰可可 AIOS 私有化部署版：Next.js 14 控制台 + Python 3.11 FastAPI 后端 + Neo4j 本体图 + Temporal 流程引擎 + 多源数据接入层（关系型 DB / Excel / PDF / 会议纪要）。核心链路 = 数据元接入 → 本体图构建 → 场景模板匹配 → 自主流程执行 → 全链路审计。零写入客户系统承诺通过「数据源只读账号 + 平台自有库 + 网关层出口白名单」三层保障。一键私有化（Docker Compose），30 分钟上桌，5 个离散制造场景模板内置。

---

## 2. 架构变更

### 2.1 新增模块

| 模块 | 路径 | 职责 |
|---|---|---|
| `apps/web`（前端） | `src/web/` | Next.js 14 控制台；数据源管理 / 本体图浏览 / 场景库 / 流程编排 / 审计页 |
| `apps/api`（后端） | `src/api/` | FastAPI；8 个核心接口 + 业务编排层 |
| `apps/ingest`（摄取 worker） | `src/ingest/` | 文件 / 数据库 / 文档解析；产出本体候选 |
| `apps/ontology`（本体服务） | `src/ontology/` | Neo4j 适配；对象图 CRUD；语义推断 |
| `apps/flow-engine`（流程引擎） | `src/flow_engine/` | Temporal worker；执行场景模板 |
| `packages/standards`（标准库） | `src/standards/` | 内置 5 个离散制造场景模板 + 标准定义 DSL |
| `packages/audit`（审计库） | `src/audit/` | 不可变日志 append-only |
| `deploy/compose`（部署） | `deploy/` | Docker Compose 一键部署；含 PostgreSQL / Neo4j / Redis / MinIO / NATS / Temporal |

### 2.2 修改模块

无（仓库原本无业务代码）。脚手架路径（`coding_group/`）保持只读。

### 2.3 数据模型变更（新增 8 张表 / Neo4j 节点）

参见 `01-requirement-doc.md` §6 影响半径。本方案中**字段级定义**：

```
datasources (id, type, connection_json_encrypted, status, created_at, last_check_at)
ontology_entities (id, kind, label, attrs_json, source_ref, updated_at) — Neo4j
ontology_relations (id, from_id, to_id, rel_type, weight, source_ref) — Neo4j
delivery_standards (id, key, name, kind, expr_json, scope_json, built_in, tenant_id, updated_at)
scenarios (id, key, name, industry, default_standard_keys, flow_template_json, built_in)
flows (id, scenario_id, datasource_bindings_json, standard_overrides_json, status, created_at)
flow_runs (id, flow_id, triggered_at, finished_at, status, output_json, audit_ref)
audit_log (id, ts, actor, action, datasource_id, standard_ref, flow_id, run_id, payload_json)
  -- append-only, 触发器禁止 UPDATE / DELETE
```

### 2.4 接口契约变更

8 个核心接口已在 PRD §6 列出。**字段级细化**：

```
POST /api/v1/datasources
  req: { type: "mysql"|"postgres"|"sqlserver"|"oracle",
         connection: { host, port, db, user, password, ssl?, read_only_account_ack: true } }
  res: { id, status: "connected"|"failed",
         tables_discovered, fields_inferred, ontology_entities_added }

POST /api/v1/ingest/files
  req: { kind: "xlsx"|"pdf"|"docx"|"txt",
         source: "bom"|"process"|"meeting"|"other",
         file_ref: "<minio_key>" }
  res: { ingest_id, entities_extracted, standards_extracted, errors[] }

POST /api/v1/flows
  req: { scenario_id, datasource_bindings: {<field>: <datasource_id>.<table>.<column>},
          standard_overrides: {<standard_key>: <value>} }
  res: { flow_id, status, field_mapping: [{target_field, source_ref, transform}] }
```

---

## 3. 关键技术决策

### 决策 1：本体图存储选 Neo4j 而非 PostgreSQL + JSONB

- **备选**：PostgreSQL + JSONB（更通用，运维栈少一个组件）
- **取舍**：本体场景天然图结构（设备-工序-物料-人员-客户多跳关系）；Neo4j Cypher 比 SQL JOIN + JSONB 路径查询好维护；社区版够用；运维复杂度 +1 但收益 >> 成本。**采纳 Neo4j**。

### 决策 2：流程引擎选 Temporal 而非自研 DAG / Airflow

- **备选**：自研 DAG（轻）/ Airflow（重）
- **取舍**：私有化部署必须高可靠 / 可重试 / 可观测；Temporal 是工业级工作流标准；自研要写至少 3 个月。**采纳 Temporal**。

### 决策 3：LLM 自部署 Qwen2.5-72B 而非走公有 API

- **备选**：OpenAI / Claude / DeepSeek 公有 API
- **取舍**：私有化承诺「数据不出厂」+ 行业合规要求 → 必须自部署；Qwen2.5-72B 中文 + 推理能力对制造业文本抽取足够。**采纳自部署**，但保留 OpenAI/Claude 网关抽象层（`packages/llm-gateway`），方便客户切换。

### 决策 4：前端 Next.js 14 App Router + Ant Design Pro

- **备选**：Vue 3 + Element Plus / React + 自研组件
- **取舍**：Ant Design Pro 私有化场景组件齐全（表格 / 流程编辑器 / 表单设计器 / 监控大屏）；Next.js 14 服务端组件减少 JS 包大小，私有化首屏快。**采纳 Next.js + Antd Pro**。

### 决策 5：前端 / 后端 monorepo 而非拆仓

- **备选**：拆 web / api / ingest 三个仓库
- **取舍**：私有化部署必须一套 Compose 起；monorepo 保证版本一致；Turbo 加速构建。**采纳 monorepo（pnpm workspaces + Turbo）**。

### 决策 6：场景模板用 DSL（YAML）描述而非 JSON / 代码

- **备选**：纯 JSON / TypeScript 代码
- **取舍**：业务配置人员（非程序员）需修改标准；YAML 可读性 + 自带注释；校验走 JSON Schema。**采纳 YAML + JSON Schema**。

---

## 4. 数据流

### 4.1 数据元接入 → 本体图

```
[客户管理员] → POST /api/v1/datasources
  → FastAPI 校验 + 入 datasources 表（密码 KMS 加密）
  → ingest worker 拉表元数据（information_schema）
  → sqlglot 解析 + 类型推断
  → LLM-gateway 推断业务含义（设备 / 物料 / 工序 / 人员 / 客户）
  → ontology 服务 UPSERT Neo4j 节点 + 关系
  → 异步返回：{tables_discovered, fields_inferred, entities_added}
```

### 4.2 文件摄取 → 交付标准

```
[配置人员] → POST /api/v1/ingest/files  (上传到 MinIO 拿 ref)
  → 文件路由：xlsx→pandas+openpyxl / pdf→PaddleOCR+Unstructured / docx→Unstructured
  → LLM-gateway 抽取 {entities, standards, action_items}
  → ontology UPSERT 实体；delivery_standards UPSERT 标准
  → 审计写一条 audit_log
```

### 4.3 场景模板加载 → 流程执行

```
[运营总监] → POST /api/v1/flows  (scenario_id + 数据源绑定 + 标准覆盖)
  → 加载 scenarios.flow_template_json
  → 校验字段映射（datasource_bindings 必须能解析到具体 column）
  → 创建 Temporal Workflow：监听 ontology 事件 / 定时触发
  → 首次触发：跑一遍 → 写 flow_runs + audit_log
  → 持续监听：本体图属性变化 → 触发条件命中 → 跑 workflow → 通知出站
```

---

## 5. 失败模式

| 场景 | 兜底 |
|---|---|
| 数据源连接失败 | 返回明确错误码（E_DS_AUTH / E_DS_TIMEOUT / E_DS_NO_PERMISSION）；不抛 500；UI 显示修复指引 |
| 本体图推断置信度低（< 0.6） | 标记 `needs_human_review`，不写入 Neo4j 主图；进 `staging` 区让配置员确认 |
| 文件 OCR 失败 / 抽取为空 | 返回 ingest_id + errors[]；UI 引导重传或手工标注 |
| LLM 网关调用失败 / 超时 | 重试 3 次（指数退避）；失败后回退到规则抽取；写 `audit_log` 标记 `llm_fallback=true` |
| Temporal workflow 崩溃 | Temporal 自带持久化；恢复后从最近 check-point 继续 |
| Neo4j 不可达 | 读路径降级到 PostgreSQL 缓存视图；写路径返回 503 + 重试 |
| 客户数据源 schema 变更 | 周期间扫描 + diff → 触发 ontology 重建 job；不阻塞主链路 |
| 私有化部署硬件不够 | `install.sh` 检测（CPU / 内存 / 磁盘）→ 不够则拒绝启动并给推荐配置 |
| 审计日志膨胀 | 日志按月分区；超过 90 天归档到 MinIO 冷存储；保留 7 年（合规） |
| 出站 webhook 失败 | 重试 5 次；失败进死信队列；UI 提示用户重发 |

---

## 6. 安全考量

| 项 | 方案 |
|---|---|
| 鉴权 | JWT（HS256）+ Refresh Token；前端 httpOnly cookie；平台 RBAC（admin / config / viewer） |
| 数据源凭证 | 平台 KMS 加密落库；运行时解密 → 只读账号访问；**绝不**写回客户库（验证：定时跑「回写检测脚本」） |
| 数据脱敏 | 抽取的本体图与标准默认**只存摘要与字段名**，原值按需 lazy load；PII 字段标记 + UI 端 mask |
| 限额 | 数据源接入限 50 个 / 租户；文件上传 ≤ 200MB；LLM 调用限速 60 req/min |
| 审计日志 | append-only（PostgreSQL 触发器禁 UPDATE / DELETE）；每日 hash 链校验；导出可签字 |
| 网络隔离 | 平台只暴露 443（控制台）+ 内部 RPC；LLM 网关 / 数据源都在内网 |
| 私钥管理 | HashiCorp Vault（私有化部署）或本地 KMS（轻量模式） |
| 漏洞扫描 | CI 跑 Trivy + Bandit + npm audit；任一 high 阻断发布 |

---

## 7. 性能考量

| 项 | 指标 |
|---|---|
| 控制台首屏（私有化内网） | LCP ≤ 1.5s（Antd Pro + Next.js 服务端组件） |
| 数据源接入 → 本体图生成 | ≤ 5 分钟（100 张表以内） |
| 单文件摄取（50MB Excel） | ≤ 30s |
| 场景模板加载 → 流程创建 | ≤ 60s |
| 单 workflow 触发 → 下游动作 | ≤ 5s |
| 审计页查询（30 天） | ≤ 2s（已建索引 `(tenant_id, ts DESC)`） |
| 并发（单租户） | 100 并发 workflow；2000 QPS 控制台 API |

**慢路径识别**：
- LLM 抽取（瓶颈）→ 限速 + 缓存常见 schema 抽取结果
- Neo4j 全图遍历（防爆）→ 分页 + Cypher 强制带 LIMIT
- PostgreSQL 审计大表 → 按 ts 范围分区

---

## 8. 测试策略

### 单测（覆盖率硬指标）

| 模块 | 阈值 |
|---|---|
| `apps/api/services/` | ≥ 80%（核心业务） |
| `apps/ingest/` | ≥ 80% |
| `apps/ontology/` | ≥ 80% |
| `apps/flow_engine/` | ≥ 80% |
| `packages/standards/` | ≥ 80% |
| 前端组件 | ≥ 60% |
| 工具类 | ≥ 80% |

### E2E（Playwright + pytest-temportal）

- 路径 1：管理员注册 → 添加 MySQL 数据源 → 看到本体图
- 路径 2：上传 BOM Excel → 加载「库存预警」场景 → 修改阈值 → 触发预警通知
- 路径 3：上传 PDF 流程规范 → 抽取标准 → 编辑 → 应用到设备保养流程
- 路径 4：审计页查询 → 找到对应 run → 导出 PDF 报告
- 路径 5：`install.sh` 跑完 → 访问控制台 → 完成一个端到端 demo

### 安全扫描

- Trivy（容器镜像）
- Bandit（Python）
- npm audit / pnpm audit
- 凭据扫描（gitleaks）
- SQL 注入（自动 fuzz：所有 SQLAlchemy 调用过安全 lint）

### 性能测试（k6）

- 数据源接入 100 张表 ≤ 5min
- 100 并发 workflow 触发 → 全链路 ≤ 5s P95

---

## 9. 部署策略

### 灰度计划

- v1 仅供内部 dogfood（`01men/ybkk` 自部署）
- v1.1 选 3 家种子客户内测（白名单）
- v1.2 通用 GA（按行业模板包扩展）

### 一键私有化

```
git clone https://github.com/01men/ybkk.git
cd ybkk/deploy/compose
./install.sh   # 检测硬件 → 拉镜像 → 起容器 → 初始化本体图空库
# 30 分钟内访问 https://<server-ip>:8443
```

支持：Docker Compose（默认）/ Kubernetes + Helm（可选，按客户基础设施）。

### 回滚

- 镜像层：保留最近 3 个 tag，helm 回滚 `helm rollback aios 1`
- 数据层：`backup.sh` 每 6h 一次 PG / Neo4j 全量；保留 7 天
- 配置层：所有配置走 Helm values / `.env`，git 化

### 监控指标

- 平台：API P95 / Temporal workflow 成功率 / Neo4j 查询 P95 / LLM 网关命中率
- 业务：场景模板运行次数 / 触发条件命中次数 / 异常率
- 客户体验：审计页查询耗时 / 数据源连接失败次数

告警：飞书 / 钉钉 / 邮件 webhook（按客户选配）。

---

## 10. 范围（明确边界）

### 包含

- 8 个核心 API + 4 类数据元接入（关系型 DB / Excel / PDF / 会议纪要）
- 本体图构建（5 类核心对象 + 关系自动推断）
- 5 个离散制造场景模板（库存预警 / 设备保养 / 质检抽检 / 排产优化 / 来料异常）
- 标准 DSL（YAML）+ 业务配置人员可视化编辑
- Temporal 流程引擎 + 全链路审计
- 一键私有化部署（Docker Compose）
- 控制台：数据源 / 本体图浏览 / 场景库 / 流程编排 / 审计页

### 不包含

- 流程制造行业模板（v2 加）
- SCADA / 时序库 / OPC-UA 接入（v2 加）
- SaaS 多租户（永久不做，专注私有化）
- 数字孪生 / 工艺仿真（不做）
- 出站 API 市场（不做）
- 对客户 ERP / MES / WMS 的写入能力（**永不**做，违反核心承诺）

---

## 11. 风险自评

| 风险类型 | 等级 | 兜底方案 |
|---|---|---|
| 范围溢出 | low | 全部任务在 `03-tasks.md` 中；scope-overflow-check 在 review 必跑 |
| 数据回退 | medium | `backup.sh` + Helm rollback；新表都有 down migration；audit_log append-only 不可回退（符合合规） |
| 接口破坏 | low | 内部接口；首版无外部调用方；OpenAPI spec 在 repo 里 |
| 鉴权穿透 | medium | RBAC + 数据源凭证 KMS；定时跑「回写检测」防越权 |
| 性能边界 | medium | 限速 + 缓存 + Neo4j LIMIT 强制 + LLM 抽取结果缓存 |
| 硬件要求 | medium | install.sh 预检；推荐 8C16G（最小）/ 16C32G（推荐）；不够则拒绝启动 |
| LLM 抽取准确度 | high | LLM 输出 + 规则回退；置信度 < 0.6 进 staging 人工确认 |
| 行业模板质量 | medium | 模板与种子客户共研；上线前 3 家验证；模板可由配置人员覆盖 |
| 跨模块协作 | high | 9 阶段流水线 + 5 道门禁 + 制品目录权限矩阵；reviewer 严抓 scope |

**高风险触发器**：LLM 抽取准确度 / 跨模块协作 → orchestrator 必弹方案确认关卡（PRD §6 已标记）+ 在交付报告 `requires_human_eyes: true`。

---

## 12. 与上游 PRD 的连接

- `01-requirement-doc.md` §3「用户故事」7 条 → 本方案 §10「包含」全部覆盖
- `01-requirement-doc.md` §4「验收标准」12 条 → 本方案 §8「E2E 路径」5 条 + §7「性能指标」7 项；剩余验收项在 `03-tasks.md` 中单测 / E2E 任务落实
- `01-requirement-doc.md` §5「非目标」9 条 → 本方案 §10「不包含」7 条 + 「永不写入客户库」红头承诺
- `01-requirement-doc.md` §6「影响半径」接口清单 → 本方案 §2.4 接口契约字段级对齐