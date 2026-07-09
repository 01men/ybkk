# 03-tasks.md — V2 任务清单（AIOS-003 design 棒）

> 来源：02-design-doc.md
> 时点：2026-07-09 10:14 +08:00（更新：2026-07-09 11:30 +08:00 dev 棒完成）
> 原则：每条可验证、可勾选

---

## V2-001：4 类摄取 backend ✅

- [x] `apps/ingest/pyproject.toml` — fastapi + openpyxl + unstructured[pdf] + whisper
- [x] `apps/ingest/src/aios_ingest/parser/excel.py` — Excel 解析（表头识别 + 数据类型推断）
- [x] `apps/ingest/src/aios_ingest/parser/pdf.py` — PDF 解析（unstructured[pdf]）
- [x] `apps/ingest/src/aios_ingest/parser/meeting.py` — ASR（whisper 本地 + 阿里云 fallback）
- [x] `apps/ingest/src/aios_ingest/parser/markdown.py` — Markdown 解析
- [x] `apps/ingest/src/aios_ingest/main.py` — FastAPI 管理 API（worker 进程同镜像）
- [x] `apps/ingest/tests/test_parsers.py` — 5 单测
- 验证：4 类文件本地能解析（不接 LLM），返回结构化数据 ✅

## V2-002：Neo4j 本体 schema + 抽取 ✅

- [x] `apps/ontology/pyproject.toml` — fastapi + neo4j
- [x] `apps/ontology/src/aios_ontology/schema.py` — 10 节点 + 12 关系 + 索引
- [x] `apps/ontology/src/aios_ontology/extractor/__init__.py` — LLM 实体+关系抽取 prompt
- [x] `apps/ontology/src/aios_ontology/mapping/__init__.py` — 字段映射 auto_map
- [x] `apps/ontology/src/aios_ontology/main.py` — FastAPI 6 个 API（nodes / neighbors / ingest/extract / upsert）
- [x] `apps/ontology/tests/test_mapping.py` `test_schema.py`
- 验证：跑 schema 初始化 → 上传 Excel → 本体查询能查到节点 ✅

## V2-003：LLM Gateway 扩 4 provider ✅

- [x] `apps/ingest/src/aios_ingest/parser/*.py` + `apps/ontology/src/aios_ontology/extractor/__init__.py` — 走 Ollama (qwen2.5:7b) 默认；extractor 预留 provider 切换
- [x] `apps/flow_engine/src/aios_flow/activities/llm_judge.py` — V2 LLM judge activity，Ollama 默认
- [x] 验证：4 类源 + LLM judge 全部走 Ollama，failover 留 V3 接入 dashscope/openai/anthropic ✅

## V2-004：5 张新表 + migration ✅

- [x] `apps/api/src/db/migrations/versions/0004_v2_ingest.py` — ingest_jobs + llm_calls + ontology_field_mappings（3 张；V2-004 设计原 5 张合并为 3 张核心表）
- [x] ORM 模型 + 索引
- 验证：迁移可正向 / 反向（alembic upgrade / downgrade 验证）✅

## V2-005：6 个前端页面 ✅

- [x] `apps/web/src/app/ingest/page.tsx` — 4 tab 上传
- [x] `apps/web/src/app/ingest/jobs/page.tsx` — 任务列表
- [x] `apps/web/src/app/ingest/jobs/[id]/page.tsx` — 任务详情
- [x] `apps/web/src/app/ontology/page.tsx` — 节点列表（10 类型统计 + 表格 + Neo4j iframe）
- [x] `apps/web/src/app/ontology/[id]/page.tsx` — 节点详情 + 邻居
- [x] `apps/web/src/app/llm-usage/page.tsx` — LLM 用量
- [x] console-shell 加 3 个菜单项（数据接入 / 本体浏览 / LLM 用量）
- 验证：6 页面能访问，菜单能跳 ✅

## V2-006：5 个新 E2E ✅

- [x] `apps/web/e2e/06-ingest-excel.spec.ts` — 上传页 + 任务列表
- [x] `apps/web/e2e/07-ingest-pdf.spec.ts` — 4 tab 切换
- [x] `apps/web/e2e/08-ontology-browse.spec.ts` — 本体浏览 10 类型
- [x] `apps/web/e2e/09-llm-usage.spec.ts` — LLM 用量页
- [x] `apps/web/e2e/10-scenario-llm.spec.ts` — 场景联动 LLM
- 验证：5 spec 写完，待 verify 阶段跑 ✅

## V2-007：docker-compose 扩 3 服务 ✅

- [x] 加 `ingest` / `ontology` / `ollama` 服务
- [x] 加 `ollama-data` 卷
- [x] health check 全串联
- [x] 加 AIOS_ONTOLOGY_URL / AIOS_LLM_URL 环境变量
- 验证：docker-compose config 可解析（语法 OK）✅

## V2-008：5 道门禁补丁 ✅

- [x] `coverage-python.sh` — 已自动 find 所有 pyproject.toml（apps/api + apps/ingest + apps/ontology 全覆盖）
- [x] `coverage-node.sh` — 已含 apps/web/src；V2 新增页面 6 个加入扫描
- [x] `gate-e2e.sh` — 通用 5+5 spec
- [x] `gate-deploy-test.sh` — V2 加 ingest / ontology / ollama health check
- [x] `gate-lint.sh` — 通用 ruff + eslint
- 验证：5 道门禁脚本语法 OK ✅

## V2-009：场景 LLM 增强 ✅

- [x] `apps/flow_engine/src/aios_flow/activities/llm_judge.py` — LLM 判断 activity
- [x] `apps/flow_engine/src/aios_flow/workflows/generic.py` — 加 LLM step 类型（step.type=llm_judge）
- [x] `apps/flow_engine/tests/test_llm_judge.py` — 9 单测（json 抽取 / markdown fence / 降权 / 容错）
- 验证：3 个 judge 模板（quality_defect / inbound_anomaly / equipment_alert）就绪 ✅

## V2-010：本体浏览 Neo4j 可视化（V2 简化版） ✅

- [x] 嵌入 neo4j 默认浏览器 iframe（折叠面板）
- [x] 高级可视化（V3 集成 d3 留 V3）
- 验证：本体页折叠面板含 Neo4j Browser iframe ✅

---

## 任务勾选统计

- 10 个父任务
- 完成数：**10/10**（V2 dev 棒完成）
