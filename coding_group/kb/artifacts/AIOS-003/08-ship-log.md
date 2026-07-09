# 08-ship-log.md — V2 交付日志（AIOS-003 ship 棒）

> 时点：2026-07-09 12:55 +08:00
> 交付人：orchestrator
> 状态：**SHIPPED**

---

## 1. Git 提交

| 字段 | 值 |
|---|---|
| Commit hash | `42fdc5018d1cf7ddfe117c7e9ccf5f4341e20b89` |
| 短 hash | `42fdc50` |
| 标题 | V2 (AIOS-003): 多源摄取 + 本体 + LLM 接入 |
| 作者 | xiaodao |
| 推送时间 | 2026-07-09 12:55 +08:00 |
| 推送方式 | SSH 22 + ed25519 (`ybkk_github_global_ed25519`) |
| Remote | github.com/01men/ybkk.git |
| Branch | main |

## 2. 上推内容

```
A  apps/api/src/api/v1/ingest.py
A  apps/api/src/api/v1/llm.py
A  apps/api/src/api/v1/ontology.py
A  apps/api/src/db/migrations/versions/0004_v2_ingest.py
M  apps/api/src/main.py                         (0.2.0 → 0.3.0 + 3 router)
M  apps/api/src/models.py                       (+ IngestJob/LLMCall/OntologyFieldMapping)
A  apps/flow_engine/src/aios_flow/activities/llm_judge.py
M  apps/flow_engine/src/aios_flow/workflows/generic.py    (+ llm_judge step type)
A  apps/flow_engine/tests/test_llm_judge.py     (15 用例)
A  apps/ingest/                                 (V2 全新包, 13 文件)
A  apps/ontology/                               (V2 全新包, 9 文件)
M  apps/web/src/app/console-shell.tsx           (+ 3 菜单)
A  apps/web/src/app/ingest/                     (3 页面)
A  apps/web/src/app/ontology/                   (2 页面)
A  apps/web/src/app/llm-usage/page.tsx
A  apps/web/e2e/06-10-*.spec.ts                 (5 V2 spec)
M  deploy/compose/docker-compose.yml            (V2 加 ollama + 独立 image)
M  coding_group/assets/scripts/gate-deploy-test.sh  (V2 加 3 health check)
A  coding_group/kb/artifacts/AIOS-003/         (9 制品)
A  scripts/v2_verify_runner.py
```

**总变更：~70 文件 / +3500 行**

## 3. 验证状态（推送时）

- 单测：30/30 通过（6 ingest + 9 ontology + 15 flow_engine）
- 静态分析：11 文件 AST parse OK
- YAML：docker-compose 解析 OK
- 集成点：6 跨服务调用路径全对
- Review：0 阻塞 / 4 V3 建议
- 5 道门禁：就位

## 4. V2 核心能力

| 能力 | 描述 |
|---|---|
| 多源摄取 | 4 类 parser：Excel / PDF / 会议 / Markdown |
| 本体图 | 10 节点 + 12 关系（Neo4j），LLM 实体+关系抽取 |
| 字段映射 | fuzzy match 自动映射 Material/Supplier/Warehouse |
| LLM judge | 3 模板（quality_defect / inbound_anomaly / equipment_alert） |
| LLM 容错 | HTTPError / Connection / JSON parse 失败时保守 False |
| 6 页面 | 数据接入 / 任务列表 / 任务详情 / 本体浏览 / 节点详情 / LLM 用量 |
| 5 E2E | 06-ingest-excel / 07-ingest-pdf / 08-ontology-browse / 09-llm-usage / 10-scenario-llm |
| Neo4j 可视化 | 折叠面板嵌入 Neo4j Browser iframe |
| Ollama 集成 | docker-compose 加 ollama 服务 + 数据卷 |

## 5. 部署指引（客户机器）

```bash
# 1. 拉 V2 镜像
docker compose -f deploy/compose/docker-compose.yml pull

# 2. 启动
cd deploy/compose && ./install.sh

# 3. 拉 LLM 模型（首次启动会自动起 ollama）
docker exec aios_ollama_1 ollama pull qwen2.5:7b

# 4. 访问控制台
open http://localhost:3000
# admin / admin123
```

## 6. V3 路线（已记录 backlog）

- SEC-V3-01：LLM prompt 加 system 角色隔离
- TS-V3-01：llm-usage 强类型收紧
- OPS-V3-01：Neo4j reverse proxy 鉴权
- OPS-V3-02：Ollama 启动自动 pull 模型（docker entrypoint）
- 多租户 / RBAC
- 监控告警（Prometheus + Grafana + Loki 已就位 profile=monitoring）
- ASR 自训练
- 本体在线学习

## 7. 仓库地址

- HTTPS：https://github.com/01men/ybkk
- SSH：git@github.com:01men/ybkk.git
- V2 commit：https://github.com/01men/ybkk/commit/42fdc50
