# 01-requirement-doc.md — 需求理解文档
req-id: AIOS-001
created: 2026-07-08
author: requirements-analyst
version: 1

---

## 1. 一句话目标

制造业企业（首版聚焦离散制造）部署元冰可可 AIOS 后，无需改造任何现有系统，平台自动读取企业内的关系型数据库、本体对象库、Excel、流程规范与会议内容，结合内置的「场景 × 职能」交付标准，自主构建可执行的 AI 业务流程，从而让企业拿到产品即可直接启动 AI 转型。

---

## 2. 目标用户与场景

- **主要用户**：
  - 离散制造企业（机械加工 / 装配 / 3C 电子）的 IT 负责人、运营总监、生产主管
  - **不**面向终端车间工人；面向「要推动 AI 转型」的中层决策者与一线配置者
- **触发场景**：
  - 企业已运行多年 ERP / MES / WMS / 钉钉 / 飞书 / 邮件系统，**不希望**为了 AI 转型而推倒重建
  - 业务部门提需求：质检、库存预警、排产优化、设备保养等场景希望尽快上 AI
  - FDE / 咨询公司调研周期长、费用高，企业希望自助完成业务链路构建
- **用户想要的**：
  - 「装上就能用」—— 提供数据源凭证即可，不需要开发改造
  - 「行业模板开箱即用」—— 离散制造的常见场景（首版至少 5 个）有现成交付标准
  - 「自主构建」—— 业务配置人员可自助组合数据元 + 交付标准 → 形成新流程，**不需要**写代码

---

## 3. 用户故事

- AS 制造业 IT 负责人 I WANT 在控制台里「添加一个 MySQL 数据源」并提供只读账号 SO THAT 平台 30 分钟内自动识别表 / 字段 / 业务含义，本体对象图随之更新
- AS 运营总监 I WANT 选择「库存预警」这个内置场景模板 SO THAT 平台基于企业现有库存表 + 安全库存规则自动生成预警流程，无需开发
- AS 生产主管 I WANT 在交付标准编辑器里把「设备保养」标准改成自家工厂的规则 SO THAT 平台按本地规范自动触发保养工单
- AS 数据源管理员 I WANT 平台只读访问数据库、绝不写入 SO THAT 我的核心业务数据不被破坏，零信任 / 可审计
- AS 审计员 I WANT 平台对每一次「数据元读取 → 交付标准匹配 → 流程触发」留痕 SO THAT AI 决策可解释、可追溯、满足合规
- AS 工厂厂长 I WANT 在本地服务器上完成整套平台部署 SO THAT 数据不出厂、满足私有化合规
- AS 配置人员 I WANT 把会议纪要 / 流程规范 PDF 直接拖入平台 SO THAT 平台抽取关键交付标准并入本体图，无需手工录入

---

## 4. 验收标准（可观察、可验证）

> 每条都按 Given/When/Then 风格写，可被 E2E 自动化。

- [ ] **数据源接入**：当用户填写 MySQL 连接信息并点击「连接」，系统在 60s 内返回「连接成功 + 已识别 N 张表 + 已推断 M 个字段语义」摘要；连接失败时返回明确错误码与原因
- [ ] **本体图生成**：当 ≥ 1 个数据源接入完成，平台在 5 分钟内自动构建本体对象图（设备 / 物料 / 工序 / 人员 / 客户 五类核心对象），并展示对象间关系可视化
- [ ] **Excel 摄取**：当用户上传 ≤ 50MB 的 .xlsx 文件并指定数据域（如「BOM」「工艺路线」），平台 30s 内抽取结构化数据并入本体图
- [ ] **流程规范摄取**：当用户上传 ≤ 200MB 的 PDF/Word 流程规范，平台 5 分钟内抽取关键交付标准条目（指标 / 阈值 / 责任人 / 触发条件）
- [ ] **会议内容摄取**：当用户粘贴或上传会议纪要文本（≥ 1k 字），平台 2 分钟内抽取「决议 / 行动项 / 责任归属」并归入本体图
- [ ] **场景模板加载**：当用户从「场景库」选择「库存预警」模板并绑定数据源，平台 60s 内生成可运行的预警流程并展示字段映射
- [ ] **交付标准编辑**：当用户在编辑器中修改某条标准的阈值并保存，平台在 30s 内重新计算所有引用该标准的流程的输出
- [ ] **流程自主执行**：当本体图中某个对象属性触发预设标准（如「库存量 < 安全库存」），平台在 5s 内调用既定的下游动作（发钉钉 / 写指定表 / 触发 webhook）
- [ ] **审计留痕**：当平台执行任一动作，全链路日志可在「审计页」查到（时间 / 数据源 / 标准引用 / 输出 / 关联用户）
- [ ] **私有化部署**：当用户在 1 台 8C16G Linux 服务器上执行 `install.sh`，30 分钟内完成全部组件启动并访问控制台；离线断网情况下仍可使用全部核心功能
- [ ] **零写入保证**：当数据源被标识为「只读」，平台任何自动化操作都不得回写该数据源；写入仅限平台自有库
- [ ] **场景模板覆盖**：首版内置 ≥ 5 个离散制造场景模板（库存预警 / 设备保养 / 质检抽检 / 排产优化 / 来料异常）

---

## 5. 非目标（明确不做）

- **不**改造企业现有 ERP / MES / WMS 系统（核心承诺）
- **不**做传统软件的「需求调研 → PRD → 开发 → 测试 → 上线」长链路（核心承诺：替代 FDE）
- **不**面向终端车间工人提供 UI（首版面向配置者与决策者）
- **不**覆盖流程制造行业（化工 / 钢铁 / 食品）—— 首版聚焦离散制造；后续通过模板包扩展
- **不**做 SaaS 多租户 —— 首版仅私有化部署
- **不**做 SCADA / 时序库 / OPC-UA 接入 —— 首版数据源限定关系型 DB + 本体对象库 + Excel + 文档；工业协议接入进 v2
- **不**做端到端的工艺仿真 / 数字孪生 —— 仅做数据驱动的业务链路编排
- **不**承诺自动写代码 / 生成新软件 —— 平台的产出是「AI 业务流程」，不是新软件模块
- **不**做对外开放的 API 市场 —— 首版接口仅供本平台组件间使用

---

## 6. 影响半径

```yaml
## 6. 影响半径
involves:
  modules: [frontend, backend, database, deploy, configs, tests, docs]
  endpoints_added:
    - method: POST
      path: /api/v1/datasources
      req: {type: string, connection: object}
      res: {id: string, status: string, tables_discovered: int}
    - method: GET
      path: /api/v1/datasources/{id}
      res: {id: string, type: string, status: string, ontology_snapshot: object}
    - method: POST
      path: /api/v1/ingest/files
      req: {kind: enum[xlsx,pdf,docx,txt], source: enum[bom,process,meeting,other], file_ref: string}
      res: {ingest_id: string, entities_extracted: int, standards_extracted: int}
    - method: POST
      path: /api/v1/ontology/rebuild
      req: {scope: enum[full,partial], datasource_ids: string[]}
      res: {job_id: string}
    - method: GET
      path: /api/v1/scenarios
      res: {scenarios: [{id: string, name: string, industry: string, default_standards: string[]}]}
    - method: POST
      path: /api/v1/flows
      req: {scenario_id: string, datasource_bindings: object[], standard_overrides: object}
      res: {flow_id: string, status: string, field_mapping: object}
    - method: GET
      path: /api/v1/flows/{id}/runs
      res: {runs: [{run_id: string, triggered_at: timestamp, output: object, audit_ref: string}]}
    - method: GET
      path: /api/v1/audit
      req: {from: timestamp, to: timestamp, actor: string, flow_id: string}
      res: {entries: [{audit_id, ts, datasource, standard_ref, output, actor}]}
  endpoints_modified: []
  db_changes:
    - table: datasources
      change: add (registry for read-only data source connections; encrypted credentials)
    - table: ontology_entities
      change: add (nodes for device/material/process/person/customer)
    - table: ontology_relations
      change: add (edges between entities)
    - table: delivery_standards
      change: add (built-in + user-overridden standards)
    - table: scenarios
      change: add (built-in industry scenario templates)
    - table: flows
      change: add (composed AI business processes)
    - table: flow_runs
      change: add (execution history)
    - table: audit_log
      change: add (immutable append-only log)
  file_estimate: ~80
  risk_level: high
crosses_module_boundary: true
performance_boundary_change: false
auth_change: true
data_migration: false
```

**风险升级判定**：
- `risk_level: high` —— 涉及多模块（前端 / 后端 / DB / 部署 / 配置 / 测试 / 文档）+ 鉴权改造
- `crosses_module_boundary: true` —— 明确跨模块
- `auth_change: true` —— 数据源凭证管理 / 平台 RBAC
- 触发：orchestrator 必弹「方案确认」关卡 + 交付报告 `requires_human_eyes: true`

---

## 7. PRD 完整性自评（5 维 0~100）

| 维度 | 分 | 依据 |
|---|---|---|
| 目标明确性 | 88 | 一句话目标已写清「谁 / 什么场景 / 做什么 / 什么结果」；唯一弱项是「自主构建」的具体形态要等方案 Agent 落 |
| 验收可验证性 | 90 | 12 条验收标准全部按 Given/When/Then 风格，可被 E2E / 接口测试覆盖 |
| 范围清晰性 | 92 | 非目标段 9 条，覆盖行业 / 部署形态 / 数据源边界 / 产品形态边界 |
| 数据/接口契约 | 85 | §6 列了 8 个核心接口的 method/path/req/res + 8 张表的 schema 变更；细化到字段级在方案棒补 |
| 风险与依赖 | 80 | 已识别鉴权 / 多模块协作 / 私有化部署复杂度 / OCR/PDF 抽取准确度 4 类风险 |
| **总分** | **87** | 全部维度 ≥ 60，**通过门禁** |

---

## 8. 阻塞项

无。

---

## 9. 与上游 / 历史的关联

- **与仓库脚手架的关联**：本需求是元冰可可 AIOS 仓库的 **第一个业务需求**（REQ-001 / ID `AIOS-001`）。脚手架（AGENTS.md / 11 Skill / 5 门禁）已就绪，本需求直接进入业务实现层。
- **与参考产品的关联**：范式参考了用户口述 + 截图所示的其他公司产品（行业惯例：不改造系统 + 直读数据元 + 内置交付标准），但不复刻品牌 / 字段命名 / 计费策略。
- **与 AGENTS.md 的关联**：完全遵循 §0 启动序列、§7 制品约定、§9 维护责任；后续 8 棒产物全部落到 `coding_group/kb/artifacts/AIOS-001/`。

---

## 10. 交接给方案 Agent（solution-architect）

请基于本 PRD，重点产出：

1. **架构总览**：前端 / 后端 / 本体层 / 数据接入层 / 部署层 五大模块的拓扑与边界
2. **技术栈选型**：前端框架、后端语言、本体图存储、LLM 接入、部署形态
3. **核心算法 / 数据流**：数据元 → 本体图 → 场景模板 → 流程执行的完整数据流
4. **任务拆解**（`03-tasks.md`）：每个任务可勾可验，工时/依赖清晰
5. **风险预案**：OCR 抽取准确度、本体图构建错误兜底、审计合规
6. **首版必交付物清单**：5 个离散制造场景模板的具体内容