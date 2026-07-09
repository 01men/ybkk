# 05-self-test-report.md — V2 自测报告（AIOS-003 verify 棒）

> 时点：2026-07-09 12:30 +08:00（verify 棒重跑更新）
> 测试人：orchestrator（verify 棒）
> 范围：apps/ingest + apps/ontology + apps/api + apps/flow_engine + apps/web

---

## 1. 单元测试（verify 棒重跑）

verify 棒用 `scripts/v2_verify_runner.py` 跑全测试（沙箱无 pytest-asyncio，但 runner 已适配 pytest 8+ 的 FixtureFunctionDefinition + sync/async 自动判别）。

### 1.1 apps/ingest 单测（6 用例）

| # | 用例 | 验证 | 结果 |
|---|---|---|---|
| 1 | `test_excel_parser_basic` | openpyxl 解析，列类型推断 | ✅ |
| 2 | `test_excel_parser_empty_sheet` | 空 sheet 处理 | ✅ |
| 3 | `test_markdown_parser_sections` | # 章节切分 + list item 抽取 | ✅ |
| 4 | `test_markdown_parser_no_standards` | 无标准候选返回空 | ✅ |
| 5 | `test_meeting_parser_local` | whisper 跳过 + 阿里云 stub | ✅ |
| 6 | `test_pdf_parser_invalid` | 非 PDF 字节抛错 | ✅ |

### 1.2 apps/ontology 单测（9 用例）

| # | 用例 | 验证 | 结果 |
|---|---|---|---|
| 1 | `test_node_count` | NODES = 10 | ✅ |
| 2 | `test_relationship_count` | RELATIONSHIPS = 12 | ✅ |
| 3 | `test_all_kinds_referenced` | 关系引用的 kind 都在 NODES | ✅ |
| 4 | `test_init_cypher_has_indexes` | CREATE INDEX + CONSTRAINT 完整 | ✅ |
| 5 | `test_auto_map_materials` | Material 字段映射 | ✅ |
| 6 | `test_auto_map_supplier` | Supplier 字段映射 | ✅ |
| 7 | `test_auto_map_warehouse` | Warehouse 字段映射 | ✅ |
| 8 | `test_auto_map_empty` | 空列表返回空 | ✅ |
| 9 | `test_auto_map_no_match` | 无匹配返回空 | ✅ |

### 1.3 apps/flow_engine 单测（15 用例，V2 新增）

| # | 用例 | 验证 | 结果 |
|---|---|---|---|
| 1 | `test_extract_json_plain` | 纯 JSON 抽取 | ✅ |
| 2 | `test_extract_json_markdown_fence` | ``` ```json``` ``` 围栏 | ✅ |
| 3 | `test_extract_json_embedded` | 文本中嵌入 JSON | ✅ |
| 4 | `test_extract_json_invalid` | 非法输入返回空 dict | ✅ |
| 5 | `test_build_full_prompt_includes_context` | context JSON 拼接 | ✅ |
| 6 | `test_gen_call_id_stable` | 同输入同 ID | ✅ |
| 7 | `test_gen_call_id_differs_on_change` | 不同输入不同 ID | ✅ |
| 8 | `test_get_template_known_keys` | 3 个内置模板存在 | ✅ |
| 9 | `test_get_template_unknown_falls_back` | 未知 key 走兜底 | ✅ |
| 10 | `test_llm_judge_decision_true` | 正常 decision=true 路径（mock httpx） | ✅ |
| 11 | `test_llm_judge_decision_false` | decision=false 路径 | ✅ |
| 12 | `test_llm_judge_missing_keys_downgrades_confidence` | expected_schema 缺失降权 | ✅ |
| 13 | `test_llm_judge_invalid_json_safe_default` | 垃圾响应不抛错 | ✅ |
| 14 | `test_llm_judge_http_error_safe_default` | LLM 不可用时保守 False | ✅ |
| 15 | `test_llm_judge_markdown_fence_response` | 围栏响应也能解 | ✅ |

**结论：30/30 全部通过。**

---

## 2. 静态分析

### 2.1 Python AST parse

```
apps/api/src/api/v1/ingest.py           OK
apps/api/src/api/v1/ontology.py         OK
apps/api/src/api/v1/llm.py              OK
apps/api/src/main.py                    OK
apps/api/src/models.py                  OK
apps/flow_engine/src/aios_flow/activities/llm_judge.py   OK
apps/flow_engine/src/aios_flow/workflows/generic.py      OK
apps/flow_engine/tests/test_llm_judge.py                 OK
apps/ingest/src/aios_ingest/parser/markdown.py           OK
apps/ingest/src/aios_ingest/parser/excel.py             OK
apps/ontology/src/aios_ontology/schema.py                OK
```

### 2.2 YAML validate

```
deploy/compose/docker-compose.yml       OK (YAML safe_load 成功)
```

### 2.3 Bug 修复（verify 棒发现）

| Bug | 文件 | 修复 |
|---|---|---|
| `BusinessRule → Meeting` 引用了未定义的节点 | `apps/ontology/src/aios_ontology/schema.py` | 改成 `BusinessRule → OWNED_BY → Role`，RELATIONSHIPS 维持 12 个 |
| `llm_judge` 只 catch `httpx.HTTPError`，任何异常会抛 | `apps/flow_engine/src/aios_flow/activities/llm_judge.py` | 改为 `except Exception`，更稳健 |
| Markdown list item 内容没进 section content | `apps/ingest/src/aios_ingest/parser/markdown.py` | 加 `list_item_open/close` 跟踪，给 inline 加 `- ` 前缀 |
| Runner fixture 识别错（`getattr(obj, "__class__.__name__")` 取空） | `scripts/v2_verify_runner.py` | 改成 `type(obj).__name__` |

---

## 3. 集成点检查

| 集成点 | 验证 | 状态 |
|---|---|---|
| API → ingest service | `apps/api/src/api/v1/ingest.py` 调 `http://ingest:8082/ingest` | ✅ |
| API → ontology service | 调 `http://ontology:8083/ingest/extract` + `upsert` | ✅ |
| API → LLM | 调 `http://ollama:11434/api/generate` | ✅ |
| flow_engine → LLM | `llm_judge_activity` 调 `os.getenv("AIOS_LLM_URL")` | ✅ |
| docker-compose 健康检查 | ingest 8082 / ontology 8083 / ollama 11434 | ✅ |
| 前端 → 后端 | `/api/backend/ingest/...` 经 Next.js rewrite → api:8000 | ✅ |

---

## 4. 已知问题 / 留尾

| 编号 | 描述 | 处理 |
|---|---|---|
| ISS-01 | LLM 不可用时返回 `decision=False` 保守默认（流程不阻断） | 留 V3 接多 provider fallback |
| ISS-02 | 字段映射只支持简单 fuzzy match，复杂 Excel 需用户手动调 | V2 接受（设计 §10 风险 4） |
| ISS-03 | `ingest/extract` prompt 抽取依赖 Ollama 可用；离线时不写本体 | 接受（设计 §11 风险 5） |
| ISS-04 | Neo4j iframe 在生产环境需 reverse proxy / 鉴权 | V3 加 |
| ISS-05 | E2E 5 spec 写了但 verify 阶段沙箱无 node 完整环境，未实跑 | 留客户机器跑 |

---

## 5. 自测结论

- **单测**：30/30 通过（6 ingest + 9 ontology + 15 flow_engine）
- **静态分析**：所有关键 Python / YAML 文件 parse OK
- **集成点**：6 个跨服务调用路径全部对得上
- **Bug 修复**：4 个（schema / llm_judge 容错 / markdown list / runner fixture）
- **阻塞项**：0
- **可进入 ship 棒**
