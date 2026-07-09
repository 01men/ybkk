# 02-design-doc.md — V2 技术设计（AIOS-003 design 棒）

> 设计范围：V2 多源 + 本体 + LLM 接入
> 时点：2026-07-09 10:12 +08:00

---

## 1. 架构变更

### 1.1 新增服务

| 服务 | 技术栈 | 端口 | 容器名 |
|---|---|---|---|
| `apps/ingest` | FastAPI + Worker (Dramatiq/RQ) | 8082 | aios-ingest |
| `apps/ontology` | FastAPI + Neo4j driver | 8083 | aios-ontology |
| `ollama`（可选）| 本地 LLM runtime | 11434 | aios-ollama |

> 私有化部署下，`qwen` 容器跑 Qwen2.5-72B；V2 改用更轻的 Qwen2.5-7B（Ollama 镜像可装）

### 1.2 复用服务

- `apps/api`（8080）— 上传 API 走这里
- `apps/flow_engine`（8081）— 场景执行
- `aios-postgres`（5432）— 业务库
- `aios-neo4j`（7474/7687）— 本体图（已有，扩 schema）
- `aios-minio`（9000）— 文件存储（新增 bucket：ingest）

### 1.3 docker-compose 扩展示意图

```yaml
# 新增
ingest:
  build: ./apps/ingest
  command: python -m aios_ingest.worker
  depends_on: [api, neo4j, minio]

ontology:
  build: ./apps/ontology
  command: python -m aios_ontology.worker
  depends_on: [neo4j, api]

ollama:
  image: ollama/ollama:latest
  ports: ["11434:11434"]
  volumes: [ollama-data:/root/.ollama]
  # 预拉模型：docker exec ollama ollama pull qwen2.5:7b
```

## 2. 本体 Schema（Neo4j）

### 2.1 节点类型（10 类）

```cypher
// 业务对象
(:Material {external_id, code, name, spec, unit, safety_stock, current_stock})
(:Supplier {external_id, code, name, contact, rating})
(:Warehouse {external_id, code, name, location, capacity})
(:Equipment {external_id, code, name, model, status, last_maintenance_at})
(:Order {external_id, code, type, status, created_at})

// 流程
(:Process {external_id, code, name, version, steps_json})
(:ProcessStep {external_id, code, name, sequence, duration_min, responsible_role})

// 标准 / 规则
(:DeliveryStandard {external_id, key, kind, expr_json, scope_json, source})
(:BusinessRule {external_id, content, confidence, source: meeting|document|llm_inferred})

// 关系端
(:Role {external_id, code, name, scope})
```

### 2.2 关系类型（12 类）

```cypher
(:Material)-[:SUPPLIED_BY]->(:Supplier)
(:Material)-[:STORED_IN]->(:Warehouse)
(:Equipment)-[:MAINTAINED_BY]->(:Role)
(:Process)-[:HAS_STEP]->(:ProcessStep)
(:ProcessStep)-[:NEXT]->(:ProcessStep)
(:Order)-[:USES_MATERIAL]->(:Material)
(:Order)-[:PRODUCED_BY]->(:Equipment)
(:DeliveryStandard)-[:APPLIES_TO]->(:Process)
(:DeliveryStandard)-[:OWNED_BY]->(:Role)
(:BusinessRule)-[:DEFINES]->(:DeliveryStandard)
(:BusinessRule)-[:OWNED_BY]->(:Role)
(:Material)-[:CRITICAL_TO]->(:Process)
```

> V2 注：`BusinessRule.source` 字段（meeting|document|llm_inferred）记录规则来源，不再单建 Meeting 节点。

### 2.3 索引

```cypher
CREATE INDEX material_external_id IF NOT EXISTS FOR (n:Material) ON (n.external_id)
CREATE INDEX supplier_external_id IF NOT EXISTS FOR (n:Supplier) ON (n.external_id)
// ... 每类节点都建
```

## 3. 多源摄取架构

### 3.1 接入层

```python
class BaseIngester(Protocol):
    async def parse(self, file: bytes) -> ParsedDocument: ...
    async def extract_entities(self, doc: ParsedDocument) -> list[Entity]: ...
    async def extract_relations(self, doc: ParsedDocument) -> list[Relation]: ...
```

### 3.2 4 个 Ingester

| Ingester | 依赖 | 输出 |
|---|---|---|
| `ExcelIngester` | openpyxl | 表格 → 行 → Material/Supplier |
| `PDFIngester` | unstructured[pdf] | 段落 + 表格 → Process / Step |
| `MeetingIngester` | whisper.cpp / 阿里云 ASR | 转写文本 → BusinessRule |
| `MarkdownIngester` | markdown-it-py | 段落 → DeliveryStandard 候选 |

### 3.3 上传 API

```python
POST /api/v1/ingest/upload
  multipart: file=<binary>
  body: { kind: "excel" | "pdf" | "meeting" | "doc" }
  → 返回 { ingest_id, status: "processing" }

GET /api/v1/ingest/{ingest_id}
  → 返回 { status, parsed_count, entities_count, relations_count, errors }
```

### 3.4 处理流

```
upload → MinIO 存原文 → Redis 队列 → ingest worker
   ↓
parse → extract → 写 Neo4j → 写 audit_log → 更新 ingest 状态
```

## 4. 字段映射规则

### 4.1 规则格式

```yaml
# mapping.yaml
mappings:
  - source: mysql://erp_db/materials
    target: Material
    field_map:
      code: material_code
      name: material_name
      spec: spec
      safety_stock: safety_stock_threshold
      current_stock: current_qty
    unit: unit_field
    relations:
      supplier: -> Supplier(code=supplier_code)
      warehouse: -> Warehouse(code=warehouse_code)
```

### 4.2 推断流程

1. 用户上传 Excel + 选模板
2. 系统读列名 → 查 mapping 候选
3. 没匹配 → 调 LLM 提建议（带置信度）→ 用户确认
4. 保存 mapping → 后续同模板自动匹配

## 5. LLM Gateway（V2 扩 4 provider）

### 5.1 接口

```python
class LLMGateway(Protocol):
    async def chat(self, messages: list[Message], **opts) -> LLMResponse: ...
    async def extract(self, schema: dict, text: str) -> dict: ...  # JSON mode
```

### 5.2 Fallback 链路

```
Qwen Local (默认) → DashScope → OpenAI → Anthropic
```

每个 provider 失败自动降级；token 用量按 provider 单独统计。

### 5.3 Prompt 模板库

```
prompts/
├── entity_extraction.json    # 实体抽取（含 few-shot）
├── relation_extraction.json  # 关系抽取
├── business_rule_extract.json # 从会议抽取业务规则
├── field_mapping_suggest.json # 字段映射建议
└── scenario_judge.json        # 场景内 LLM 判断
```

## 6. 数据库扩展

### 2.3 新表 `ingest_jobs`

```sql
CREATE TABLE ingest_jobs (
    id UUID PRIMARY KEY,
    kind VARCHAR(32) NOT NULL,  -- excel | pdf | meeting | doc
    filename VARCHAR(512) NOT NULL,
    minio_path VARCHAR(512) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    -- pending | processing | succeeded | failed
    parsed_count INTEGER DEFAULT 0,
    entities_count INTEGER DEFAULT 0,
    relations_count INTEGER DEFAULT 0,
    error TEXT,
    created_by VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    finished_at TIMESTAMPTZ
);
```

### 2.4 新表 `llm_calls`

```sql
CREATE TABLE llm_calls (
    id UUID PRIMARY KEY,
    provider VARCHAR(32) NOT NULL,
    model VARCHAR(64) NOT NULL,
    prompt_hash VARCHAR(64) NOT NULL,
    response_hash VARCHAR(64) NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    cost_usd NUMERIC(10, 6),
    duration_ms INTEGER,
    actor VARCHAR(64) NOT NULL,
    flow_id VARCHAR(64),
    run_id VARCHAR(64),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 2.5 新表 `ontology_field_mappings`

```sql
CREATE TABLE ontology_field_mappings (
    id UUID PRIMARY KEY,
    template_name VARCHAR(128) NOT NULL,
    source_type VARCHAR(32) NOT NULL,  -- excel | mysql | pdf
    target_kind VARCHAR(32) NOT NULL,
    field_map JSONB NOT NULL,
    relations JSONB,
    confidence NUMERIC(3, 2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## 7. API 设计（V2 新增）

| Method | Path | 用途 | 鉴权 |
|---|---|---|---|
| POST | `/api/v1/ingest/upload` | 上传文件 | JWT |
| GET | `/api/v1/ingest/jobs` | 列出任务 | JWT |
| GET | `/api/v1/ingest/jobs/{id}` | 任务详情 | JWT |
| GET | `/api/v1/ontology/nodes` | 列出节点（按 kind）| JWT |
| GET | `/api/v1/ontology/nodes/{id}` | 节点详情 | JWT |
| GET | `/api/v1/ontology/nodes/{id}/neighbors` | 邻居 | JWT |
| POST | `/api/v1/ontology/query` | Cypher 查询（受控）| JWT |
| GET | `/api/v1/llm/usage` | LLM 用量统计 | JWT |
| POST | `/api/v1/llm/test` | 测试 LLM 连通 | JWT |

## 8. 前端新增

| 页面 | 路径 | 用途 |
|---|---|---|
| 数据接入 | `/ingest` | 4 tab 上传 |
| 任务列表 | `/ingest/jobs` | 历史任务 |
| 任务详情 | `/ingest/jobs/[id]` | 进度 + 解析结果 |
| 本体浏览 | `/ontology` | 节点列表 |
| 节点详情 | `/ontology/[id]` | 节点 + 邻居 |
| LLM 用量 | `/llm-usage` | 统计 + 成本 |

## 9. 5 道门禁（V2 补丁）

- `coverage-python.sh` 加 `apps/ingest/` / `apps/ontology/` 扫描
- `gate-lint.sh` 加 Python ruff（已含） + TS eslint
- `gate-e2e.sh` 加 5 个新 E2E（4 个摄取 + 1 个本体浏览）

## 10. 包含 / 不包含

### 包含

- 4 个 Ingester（Excel / PDF / 会议 / Markdown）
- Neo4j schema + 实体/关系抽取（LLM 驱动）+ 字段映射
- LLM gateway 4 provider + fallback
- 6 个新表
- 6 个新前端页面
- ingest worker（异步处理）
- 5 个新 E2E

### 不包含

- 多租户 / RBAC 完整版（V3）
- 监控告警（V3）
- ASR 自训练（V2 用现成）
- 本体在线学习（V3）

## 11. 风险与对策

| 风险 | 对策 |
|---|---|
| PDF 复杂表格解析失败 | V2 接受 80% 准确率；失败时显示「请提供 Excel 版本」 |
| ASR 慢（30s/min）| 异步处理 + 进度回调 + 客户端 polling |
| Neo4j 性能 | 加 label + external_id 联合索引 |
| LLM 幻觉 | 关键决策加 schema 验证 + 置信度字段 |
| 字段映射歧义 | 强制要求 mapping，不允许 LLM 猜 |
