# 03-tasks.md — 任务清单（AIOS-001）

> 任务清单，每条**可勾可验**。依据 `02-design-doc.md` 与 `01-requirement-doc.md`。
> 完成定义：单测 + E2E 全过 + 5 道门禁全过（参见 `coding_group/AGENTS.md` §2）。

---

## 阶段 0：脚手架与基线（必须先做）

- [ ] **TASK-000**：基线门禁拍快照
  - 涉及文件：`coding_group/assets/scripts/gate-baseline.sh` 输出 → `coding_group/kb/gates/baseline.json`
  - 验证方式：执行 `bash coding_group/assets/scripts/gate-baseline.sh --snapshot` 退出码 0；`baseline.json` 存在
  - 估算：1 人时
  - 依赖：无

---

## 阶段 1：仓库与 monorepo 骨架

- [ ] **TASK-001**：建 monorepo 骨架（pnpm workspaces + Turbo）
  - 涉及文件：`package.json`、根 `pnpm-workspace.yaml`、`turbo.json`、`.gitignore`、`.editorconfig`
  - 验证方式：`pnpm install` 成功；`pnpm -r list` 列出所有子包
  - 估算：2 人时
  - 依赖：TASK-000

- [ ] **TASK-002**：建 Docker Compose 一键部署骨架
  - 涉及文件：`deploy/compose/docker-compose.yml`、`install.sh`、`backup.sh`、`.env.example`
  - 验证方式：`docker compose config` 校验通过；`install.sh` 在干净机器可启动（占位镜像先打）
  - 估算：4 人时
  - 依赖：TASK-001

- [ ] **TASK-003**：建前后端空工程
  - 涉及文件：`apps/web/`（Next.js 14）、`apps/api/`（FastAPI 空骨架）、`apps/ingest/`、`apps/ontology/`、`apps/flow_engine/`、`packages/standards/`、`packages/audit/`、`packages/llm-gateway/`
  - 验证方式：`pnpm dev` 启前端；`uv run fastapi dev apps/api/src/main.py` 启后端；各自 200
  - 估算：4 人时
  - 依赖：TASK-001

---

## 阶段 2：核心数据层（先建库，验收先过）

- [ ] **TASK-010**：PostgreSQL schema 与 migration
  - 涉及文件：`apps/api/src/db/migrations/versions/0001_init.py`（含 datasources / delivery_standards / scenarios / flows / flow_runs / audit_log）
  - 验证方式：`uv run alembic upgrade head` 成功；`audit_log` 表触发器禁止 UPDATE/DELETE 通过测试
  - 估算：3 人时
  - 依赖：TASK-003

- [ ] **TASK-011**：Neo4j 初始化与对象图 schema
  - 涉及文件：`apps/ontology/src/neo4j/init.cypher`、`apps/ontology/src/models/entities.py`
  - 验证方式：手动跑 init.cypher 成功；5 类核心节点（Device/Material/Process/Person/Customer）constraint 创建成功
  - 估算：2 人时
  - 依赖：TASK-010

- [ ] **TASK-012**：Pydantic 模型（DTO + ORM）
  - 涉及文件：`apps/api/src/models/`（按表对应）
  - 验证方式：单测覆盖每个 model 的序列化 / 反序列化
  - 估算：3 人时
  - 依赖：TASK-010

- [ ] **TASK-013**：FastAPI 错误类型统一
  - 涉及文件：`apps/api/src/errors.py`、`apps/api/src/middleware/error_handler.py`
  - 验证方式：单测覆盖 E_DS_AUTH / E_DS_TIMEOUT 等错误码返回契约
  - 估算：2 人时
  - 依赖：TASK-012

---

## 阶段 3：数据元接入（4 类）

- [ ] **TASK-020**：关系型 DB 接入
  - 涉及文件：`apps/api/src/services/datasource_service.py`、`apps/api/src/api/v1/datasources.py`、`apps/ingest/src/extractors/sql_extractor.py`
  - 验证方式：单测覆盖 MySQL/PostgreSQL/SQL Server/Oracle 4 种方言的表/字段抽取；E2E 跑通「添加 MySQL → 返回 tables_discovered」
  - 估算：8 人时
  - 依赖：TASK-013

- [ ] **TASK-021**：Excel 摄取（xlsx）
  - 涉及文件：`apps/ingest/src/extractors/xlsx_extractor.py`、`apps/api/src/api/v1/ingest.py`
  - 验证方式：单测覆盖 5 种典型 Excel（BOM / 工艺 / 库存 / 客户 / 设备台账）；E2E 上传 50MB Excel ≤ 30s
  - 估算：4 人时
  - 依赖：TASK-020

- [ ] **TASK-022**：PDF / DOCX 文档抽取
  - 涉及文件：`apps/ingest/src/extractors/pdf_extractor.py`、`apps/ingest/src/extractors/docx_extractor.py`
  - 验证方式：单测覆盖 PaddleOCR + Unstructured 路径；E2E 上传 200MB PDF ≤ 5min
  - 估算：6 人时
  - 依赖：TASK-021

- [ ] **TASK-023**：会议纪要抽取（txt / 录音转写）
  - 涉及文件：`apps/ingest/src/extractors/meeting_extractor.py`
  - 验证方式：单测覆盖「决议 / 行动项 / 责任归属」三段抽取；E2E 粘贴 1k 字会议纪要 ≤ 2min
  - 估算：4 人时
  - 依赖：TASK-022

---

## 阶段 4：本体图 + LLM 网关

- [ ] **TASK-030**：LLM 网关抽象层
  - 涉及文件：`packages/llm-gateway/src/gateway.py`（Qwen2.5-72B 本地 + OpenAI/Claude 适配）
  - 验证方式：单测覆盖两个 provider 的请求 / 响应 / 重试 / fallback
  - 估算：4 人时
  - 依赖：TASK-003

- [ ] **TASK-031**：本体推断服务
  - 涉及文件：`apps/ontology/src/services/infer_service.py`（设备 / 物料 / 工序 / 人员 / 客户 5 类）
  - 验证方式：单测覆盖 5 类推断；置信度 < 0.6 进 staging；E2E 加一个 MySQL → 本体图出现 5 类节点
  - 估算：8 人时
  - 依赖：TASK-030、TASK-020

- [ ] **TASK-032**：本体图 CRUD + Cypher 封装
  - 涉及文件：`apps/ontology/src/repositories/neo4j_repo.py`
  - 验证方式：单测覆盖 5 类节点 + 关系 CRUD；Cypher 强制带 LIMIT（lint 校验）
  - 估算：4 人时
  - 依赖：TASK-011

---

## 阶段 5：场景模板与标准库

- [ ] **TASK-040**：标准 DSL（YAML + JSON Schema）
  - 涉及文件：`packages/standards/src/dsl/standard.py`、`packages/standards/src/schemas/standard.schema.json`
  - 验证方式：单测覆盖 DSL 解析 / 校验 / 序列化；JSON Schema 校验 5 个内置标准
  - 估算：3 人时
  - 依赖：TASK-003

- [ ] **TASK-041**：内置 5 个离散制造场景模板
  - 涉及文件：`packages/standards/src/scenarios/inventory_alert.yaml`、`equipment_maintenance.yaml`、`quality_inspection.yaml`、`production_scheduling.yaml`、`inbound_anomaly.yaml`
  - 验证方式：每个 YAML 通过 JSON Schema 校验；单测覆盖每场景的核心字段；文档（`packages/standards/docs/*.md`）写清每个场景适用条件
  - 估算：10 人时
  - 依赖：TASK-040

- [ ] **TASK-042**：场景模板加载 API
  - 涉及文件：`apps/api/src/api/v1/scenarios.py`、`apps/api/src/services/scenario_service.py`
  - 验证方式：单测覆盖 GET /api/v1/scenarios 返回 5 个内置场景；E2E 选择「库存预警」→ 创建 flow 成功
  - 估算：3 人时
  - 依赖：TASK-041

---

## 阶段 6：流程引擎

- [ ] **TASK-050**：Temporal worker 启动
  - 涉及文件：`apps/flow_engine/src/worker.py`、`apps/flow_engine/src/activities/`
  - 验证方式：Temporal worker 在 Docker Compose 中启动成功；hello-world workflow 跑通
  - 估算：4 人时
  - 依赖：TASK-002

- [ ] **TASK-051**：场景 → Temporal workflow 编排
  - 涉及文件：`apps/flow_engine/src/workflows/scenario_workflow.py`、`apps/flow_engine/src/activities/standard_eval.py`
  - 验证方式：单测覆盖「监听 ontology 事件 → 触发条件命中 → 执行 workflow → 通知出站」；E2E 模拟「库存量 < 安全库存」→ 5s 内钉钉通知发出
  - 估算：8 人时
  - 依赖：TASK-050、TASK-042

- [ ] **TASK-052**：流程执行历史 + 审计关联
  - 涉及文件：`apps/api/src/api/v1/flows.py`、`apps/api/src/services/flow_run_service.py`
  - 验证方式：单测覆盖 flow_runs 写入；E2E 跑一个 workflow → 审计页能查到
  - 估算：4 人时
  - 依赖：TASK-051

---

## 阶段 7：审计与安全

- [ ] **TASK-060**：审计日志 append-only + hash 链
  - 涉及文件：`packages/audit/src/writer.py`、`apps/api/src/db/migrations/versions/0002_audit_triggers.py`
  - 验证方式：单测覆盖 hash 链校验；尝试 UPDATE/DELETE audit_log 失败（数据库层拒绝）
  - 估算：4 人时
  - 依赖：TASK-010

- [ ] **TASK-061**：数据源凭证 KMS 加密
  - 涉及文件：`apps/api/src/services/secret_service.py`、`apps/api/src/config/kms.yaml`
  - 验证方式：单测覆盖加密 / 解密；DB 中 connection_json 是密文；解密后连接成功
  - 估算：4 人时
  - 依赖：TASK-020

- [ ] **TASK-062**：「回写检测」定时脚本
  - 涉及文件：`apps/api/src/scripts/writeback_detector.py`
  - 验证方式：脚本以只读账号重连所有数据源；运行 100 次 DML 操作 → 全部失败（因只读账号权限不足）
  - 估算：3 人时
  - 依赖：TASK-061

- [ ] **TASK-063**：JWT + RBAC
  - 涉及文件：`apps/api/src/middleware/auth.py`、`apps/api/src/services/rbac_service.py`
  - 验证方式：单测覆盖 admin / config / viewer 三角色权限矩阵；未授权请求 401；越权请求 403
  - 估算：4 人时
  - 依赖：TASK-013

---

## 阶段 8：前端控制台

- [ ] **TASK-070**：控制台骨架 + 登录
  - 涉及文件：`apps/web/src/app/(auth)/login/page.tsx`、`apps/web/src/app/layout.tsx`、`apps/web/src/middleware.ts`
  - 验证方式：E2E 登录 → 跳转首页 → 控制台 200
  - 估算：4 人时
  - 依赖：TASK-063

- [ ] **TASK-071**：数据源管理页
  - 涉及文件：`apps/web/src/app/(console)/datasources/page.tsx`、`apps/web/src/components/datasource-form.tsx`
  - 验证方式：E2E 添加 MySQL → 看到连接结果 + tables_discovered 摘要
  - 估算：4 人时
  - 依赖：TASK-070、TASK-020

- [ ] **TASK-072**：本体图浏览页（Neo4j 可视化）
  - 涉及文件：`apps/web/src/app/(console)/ontology/page.tsx`、`apps/web/src/components/ontology-graph.tsx`（用 react-force-graph-2d）
  - 验证方式：E2E 进入本体页 → 看到 5 类节点图谱
  - 估算：6 人时
  - 依赖：TASK-071、TASK-031

- [ ] **TASK-073**：场景库 + 流程编排
  - 涉及文件：`apps/web/src/app/(console)/scenarios/page.tsx`、`apps/web/src/app/(console)/flows/page.tsx`、`apps/web/src/components/flow-builder.tsx`
  - 验证方式：E2E 选「库存预警」→ 绑定数据源 → 修改阈值 → 创建 flow 成功
  - 估算：8 人时
  - 依赖：TASK-072、TASK-051

- [ ] **TASK-074**：审计页 + 导出
  - 涉及文件：`apps/web/src/app/(console)/audit/page.tsx`、`apps/web/src/components/audit-export.tsx`
  - 验证方式：E2E 查 30 天审计 → 查到一个 run → 导出 PDF 报告成功
  - 估算：4 人时
  - 依赖：TASK-060、TASK-073

---

## 阶段 9：部署与运维

- [ ] **TASK-080**：install.sh / backup.sh / upgrade.sh 完善
  - 涉及文件：`deploy/compose/install.sh`、`deploy/compose/backup.sh`、`deploy/compose/upgrade.sh`
  - 验证方式：在干净 Ubuntu 22.04 / 8C16G 上 `install.sh` ≤ 30min；备份还原 OK
  - 估算：4 人时
  - 依赖：TASK-002

- [ ] **TASK-081**：Prometheus + Grafana + Loki 接入
  - 涉及文件：`deploy/compose/prometheus.yml`、`deploy/compose/grafana/dashboards/aios.json`
  - 验证方式：Grafana 大屏可访问；指标 / 日志采集正常
  - 估算：3 人时
  - 依赖：TASK-080

- [ ] **TASK-082**：私有化部署 E2E（验收路径 5）
  - 涉及文件：`tests/e2e/private_install/`
  - 验证方式：在干净机器跑完整路径 5 通过
  - 估算：3 人时
  - 依赖：TASK-081

---

## 门禁与门禁门关

- [ ] **TASK-090**：5 道门禁跑通
  - 涉及文件：`coding_group/assets/scripts/gate-*.sh` 配置
  - 验证方式：5 道门禁按序跑全部 PASSED；`.gates-state.json` 写入
  - 估算：2 人时
  - 依赖：TASK-082

- [ ] **TASK-091**：基线对比通过
  - 涉及文件：`coding_group/kb/gates/baseline.json`
  - 验证方式：`new_failures - baseline_failures = ∅`
  - 估算：1 人时
  - 依赖：TASK-090

---

## 总览

- 任务总数：**30**（TASK-000 ~ TASK-091）
- 总估算：**~120 人时**
- 关键路径：TASK-001 → TASK-003 → TASK-010 → TASK-020 → TASK-031 → TASK-051 → TASK-073 → TASK-090 → TASK-091
- 最大风险：TASK-031（本体推断）、TASK-051（场景编排）、TASK-073（流程编辑器）

---

## 交接给开发 Agent（developer）

请按阶段 0 → 9 顺序推进。**每完成一个阶段**：

1. 跑对应阶段的所有单测 + E2E（`pnpm test` / `pytest` / `playwright test`）
2. 跑 `gate-coverage.sh` + `gate-lint.sh`（前两道门禁）
3. 在 `04-code-changes.md` 记录本阶段 commit 列表
4. 把更新后的 `.gates-state.json` 摘要写到 `05-self-test-report.md`

**禁止**：
- 跳阶段（如直接做 TASK-051 不做 TASK-031）
- 加 PRD 没提的功能（scope-overflow-check 会抓）
- 改 PRD / 方案（下游不能改上游）

**遇到阻塞**：
- 上游问题 → 写 `blockers/01-dev-blocked-by-design.md`
- 设计本身问题 → 写 `blockers/02-dev-design-clarify.md`
- 不要在对话里问，写制品。