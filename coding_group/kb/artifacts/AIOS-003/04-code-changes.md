# 04-code-changes.md — V2 代码变更清单（AIOS-003 dev 棒）

> 时点：2026-07-09 11:35 +08:00
> 范围：apps/ingest / apps/ontology / apps/api / apps/flow_engine / apps/web / deploy/compose
> 与 02-design-doc.md / 03-tasks.md 一一对应

---

## 1. 新增包 / 服务

### 1.1 `apps/ingest` (V2 新增)

```
apps/ingest/
├── pyproject.toml
├── Dockerfile                              # Python 3.11 多阶段
├── src/aios_ingest/
│   ├── __init__.py
│   ├── config.py                           # settings (env)
│   ├── main.py                             # FastAPI app (health + 管理 API)
│   ├── worker.py                           # entrypoint
│   └── parser/
│       ├── __init__.py                     # BaseParser + ParsedDocument
│       ├── excel.py                        # ExcelParser (openpyxl)
│       ├── pdf.py                          # PdfParser (unstructured + pypdf fallback)
│       ├── meeting.py                      # MeetingParser (whisper + 阿里云 stub)
│       └── markdown.py                     # MarkdownParser (markdown-it-py)
└── tests/
    └── test_parsers.py                     # 5 单测
```

### 1.2 `apps/ontology` (V2 新增)

```
apps/ontology/
├── pyproject.toml
├── Dockerfile
├── src/aios_ontology/
│   ├── __init__.py
│   ├── config.py
│   ├── main.py                             # 6 API: nodes/list/get/neighbors + ingest/extract + upsert
│   ├── worker.py
│   ├── schema.py                           # 10 节点 + 12 关系 + 索引（init_constraints）
│   ├── extractor/__init__.py               # LLM 实体+关系抽取 prompt + _llm_call
│   └── mapping/__init__.py                 # auto_map（简单 fuzzy match）
└── tests/
    ├── test_mapping.py
    └── test_schema.py
```

---

## 2. 后端变更 `apps/api`

### 2.1 新增文件

- `apps/api/src/api/v1/ingest.py` — 上传 / 任务列表 / 任务详情（V2）
- `apps/api/src/api/v1/ontology.py` — 本体节点列表 / 详情 / 邻居（V2 透传到 ontology 服务）
- `apps/api/src/api/v1/llm.py` — LLM 用量统计 / 测试连通（V2）

### 2.2 修改文件

- `apps/api/src/models.py` — 加 IngestJob / LLMCall / OntologyFieldMapping 三个 ORM 模型
- `apps/api/src/main.py` — 升级到 0.3.0，注册 ingest/ontology/llm 三个 router

### 2.3 数据库

- `apps/api/src/db/migrations/versions/0004_v2_ingest.py` — V2 迁移：
  - `ingest_jobs (id, kind, filename, minio_path, status, parsed_count, entities_count, relations_count, error, created_by, created_at, finished_at)`
  - `llm_calls (id, provider, model, prompt_hash, response_hash, input_tokens, output_tokens, cost_usd, duration_ms, actor, flow_id, run_id, created_at)`
  - `ontology_field_mappings (id, template_name, source_type, target_kind, field_map, relations, confidence, created_at)`
  - 索引：status / created_at / provider

---

## 3. flow_engine 变更 `apps/flow_engine`

### 3.1 新增文件

- `apps/flow_engine/src/aios_flow/activities/llm_judge.py` — LLM judge activity：
  - LLMJudgeInput / LLMJudgeResult dataclass
  - `_extract_json`（兼容 markdown fence / 嵌入 / 整段）
  - `_build_full_prompt`（拼模板 + context）
  - `_llm_call`（调 Ollama /api/generate）
  - `llm_judge()` 核心实现
  - `JUDGE_TEMPLATES` 3 个内置模板：quality_defect / inbound_anomaly / equipment_alert
- `apps/flow_engine/tests/test_llm_judge.py` — 9 单测

### 3.2 修改文件

- `apps/flow_engine/src/aios_flow/workflows/generic.py` —
  - 加 `llm_judge_activity` 包装（@activity.defn name="llm_judge"）
  - GenericScenarioWorkflow 主循环加 `step.type == "llm_judge"` 分支

---

## 4. 前端变更 `apps/web`

### 4.1 新增页面

- `apps/web/src/app/ingest/page.tsx` — 数据接入 4 tab 上传
- `apps/web/src/app/ingest/jobs/page.tsx` — 任务列表（5s 自动刷新）
- `apps/web/src/app/ingest/jobs/[id]/page.tsx` — 任务详情（自动轮询直到 succeeded/failed）
- `apps/web/src/app/ontology/page.tsx` — 节点列表（10 类型统计卡 + 表格 + Neo4j iframe 折叠面板）
- `apps/web/src/app/ontology/[id]/page.tsx` — 节点详情 + 邻居
- `apps/web/src/app/llm-usage/page.tsx` — LLM 用量（4 统计卡 + 分组表 + 连通性测试表单）

### 4.2 修改文件

- `apps/web/src/app/console-shell.tsx` — 加 CloudUploadOutlined / NodeIndexOutlined / RobotOutlined 三个菜单项

### 4.3 E2E

- `apps/web/e2e/06-ingest-excel.spec.ts` — 数据接入 4 tab + 任务列表 + 404
- `apps/web/e2e/07-ingest-pdf.spec.ts` — 4 tab 切换
- `apps/web/e2e/08-ontology-browse.spec.ts` — 10 类型卡 + Neo4j + 筛选
- `apps/web/e2e/09-llm-usage.spec.ts` — 4 统计 + 4 provider 按钮
- `apps/web/e2e/10-scenario-llm.spec.ts` — 场景 + LLM 联动 + 流程页

---

## 5. 部署变更 `deploy/compose`

- `deploy/compose/docker-compose.yml` — V2 升级：
  - `AIOS_VERSION` 默认 0.3.0
  - `web` / `api` / `qwen` / `flow-engine` image 升 0.3.0
  - `ingest` / `ontology` 改为独立 image（`ghcr.io/01men/ybkk-ingest` / `ghcr.io/01men/ybkk-ontology`）
  - 加 `ollama` 服务（port 11434，卷 ollama-data）
  - 加 `ollama-data` 卷
  - `api` 加 `AIOS_ONTOLOGY_URL=http://ontology:8083` + `AIOS_LLM_URL=http://ollama:11434` 环境变量
  - `flow-engine` 加 `AIOS_LLM_URL`
  - `ingest` / `ontology` / `flow-engine` 加 ollama depends_on
  - ingest / ontology 加 health check（8082 / 8083）

---

## 6. 门禁脚本变更 `coding_group/assets/scripts`

- `coding_group/assets/scripts/gate-deploy-test.sh` — V2 加 ingest / ontology / ollama 健康检查

> 其它门禁脚本（coverage-python / coverage-node / gate-e2e / gate-lint / gate-baseline）通过通用 find / 通用支持 V2 无需改动。

---

## 7. 变更规模

- 新增 Python 包：2（apps/ingest + apps/ontology）
- 新增 Python 文件：14
- 新增前端页面：6
- 新增前端文件：6 + console-shell 1 改
- 新增 E2E：5
- 新增 Docker 服务：1（ollama）+ 2 改（ingest / ontology 用独立 image）
- 新增 migration：1（0004_v2_ingest，3 张表）
- 门禁脚本改动：1

---

## 8. 与需求 / 设计 / 任务清单对齐

| 设计 § | 任务 § | 本制品 § |
|---|---|---|
| §1 架构变更 | V2-007 | §5 |
| §2 本体 Schema | V2-002 | §1.2 |
| §3 多源摄取 | V2-001 | §1.1 |
| §4 字段映射 | V2-002 | §1.2 mapping/ |
| §5 LLM Gateway | V2-003 / V2-009 | §1.1 + §3.1 |
| §6 数据库扩展 | V2-004 | §2.3 |
| §7 API 设计 | V2-005 / V2-009 | §2.1 + §2.2 + §3.2 |
| §8 前端 | V2-005 | §4.1 + §4.2 |
| §9 5 道门禁 | V2-008 | §6 |
| §10 包含 | V2-010 | §4.1 (ontology/page.tsx) |
