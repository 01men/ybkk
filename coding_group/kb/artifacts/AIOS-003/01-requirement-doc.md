# 01-requirement-doc.md — V2 需求文档（AIOS-003 analyze 棒）

> 评估维度：5 维（用户价值 / 范围清晰 / 可验收 / 与架构契合 / 风险识别）
> 评估人：requirements-analyst
> 时点：2026-07-09 10:08 +08:00

---

## 1. V2 一句话定位

**让 AIOS 从「读 DB」升级到「读一切：DB / Excel / PDF / 会议 / 流程规范」，并通过本体图让标准引擎「懂业务」，再让 LLM 让标准「会自学习」。**

## 2. 用户故事（V2 新增 / 升级）

### US-V2-1：Excel 物料清单接入

**作为** 工厂 IT 管理员
**我想要** 在控制台上传 1 个 .xlsx 物料表
**以便** 系统自动解析为本体节点（Material/Supplier/Warehouse），不用手动录

**验收**：
- 浏览器打开 `http://<server>:3000/ingest`
- 看到 3 个 tab：Excel / PDF / 会议
- 选 Excel tab → 拖拽 `materials.xlsx` → 上传
- 进度条 → 完成后显示「解析成功：N 个 Material 节点 / M 个 Supplier 节点 / K 个 Warehouse 节点」
- 进入「本体浏览」页能看到新加的节点

### US-V2-2：PDF 工艺规范解析

**作为** 工艺工程师
**我想要** 上传 PDF 工艺文件
**以便** 系统抽取工艺步骤，自动生成场景模板

**验收**：
- 选 PDF tab → 上传 `process.pdf`
- 解析成功 → 显示「抽取 N 个工艺步骤，DAG 边 K 条」
- 自动生成场景「自定义工艺 A」（从 PDF 提取的标准候选）

### US-V2-3：会议内容转写 + 抽取

**作为** 业务部门负责人
**我想要** 上传会议录音（mp3/wav）
**以便** 系统转写并抽取业务规则，自动生成 DeliveryStandard 候选

**验收**：
- 选「会议」tab → 上传 `meeting.mp3`
- 进度条（ASR 慢，约 30 秒/分钟音频）
- 完成后显示「识别 N 段对话，抽取 M 条业务规则」
- 候选规则列表 → 点「采纳」→ 入 delivery_standards 表

### US-V2-4：本体浏览

**作为** 审计员
**我想要** 看本体图（Neo4j）
**以便** 理解系统「懂什么」

**验收**：
- 打开 `http://<server>:3000/ontology`
- 列表显示所有节点类型（Material / Supplier / Warehouse / Equipment / Process / Order）
- 点类型 → 列节点
- 高级：图谱可视化（V2 简化版用 neo4j 默认浏览器，V3 集成 d3）

### US-V2-5：LLM 增强场景

**作为** 业务部门负责人
**我想要** 场景执行时 LLM 做语义判断
**以便** 不用写复杂规则也能让系统「懂」

**验收**：
- 激活「库存预警」场景 → 启动
- 场景执行到 `inventory_low_stock` step → 调 LLM：「判断这批物料该不该预警？答：YES/NO + 理由」
- LLM 回答 → 写进 step_results.output
- 审计能看到 LLM 调用记录（带 prompt + response hash）

## 3. 范围（IN / OUT）

### IN（V2 必须做）

**多源接入（apps/ingest）**
- Excel parser（openpyxl + 字段类型推断）
- PDF parser（unstructured[pdf] + 表格识别）
- 会议音频 ASR（whisper.cpp 本地 + 阿里云一句话识别云端切换）
- 流程规范解析（python-docx + markdown-it）
- 上传 API + 进度跟踪 + 审计

**本体推断（apps/ontology）**
- Neo4j schema 定义（10 类节点 + 12 类关系）
- 实体抽取（用 LLM 做 NER）
- 关系抽取（用 LLM 做 RE）
- 字段映射规则（DB 列 → 本体属性）
- 本体查询 API：search / by-id / neighbors
- 图谱数据同步（Postgres + Neo4j 双向同步）

**LLM 接入**
- LLM gateway（已有，扩 4 provider）
- Qwen 本地 / OpenAI / Anthropic / DashScope（阿里云）
- Fallback 链路：主失败自动切备
- Token 用量统计 + 成本估算
- Prompt template 库
- LLM 调用审计（按要求）

### OUT（V2 不做）

- 多租户 / RBAC 完整版（V3）
- 监控告警 / Grafana 完善（V3）
- ASR 自训练（用现成 whisper + 阿里云）
- 本体学习（V2 靠 LLM 抽，V3 才考虑在线学习）

## 4. 与架构契合度

| 维度 | 评估 |
|---|---|
| V1 资产延续 | ✅ 100% 复用数据层 + 鉴权 + 审计 + Temporal |
| V1 场景机制 | ✅ V2 场景可在 step 里调 LLM + 查本体 |
| 多源到本体的链路 | ✅ ingest worker → 本体服务 → Neo4j |
| 私有化部署 | ✅ LLM 走本地 Qwen，云端只作 fallback |

## 5. 风险识别

| 风险 | 概率 | 影响 | 对策 |
|---|---|---|---|
| PDF 复杂表格解析失败 | 高 | 中 | V2 接受 80% 准确率；失败时回退到 OCR 文字 + 人工补 |
| ASR 慢（30s/min 音频）| 中 | 中 | 异步处理 + 进度回调 |
| Neo4j 大数据量性能 | 中 | 中 | 加索引（label, key, external_id）|
| LLM 幻觉 | 中 | 高 | 关键决策（> 阈值）必须 schema 验证；加置信度字段 |
| 多源字段映射歧义 | 高 | 中 | 强制要求列名 → 本体属性有显式 mapping，不允许 LLM 猜 |

## 6. 5 维自评

| 维度 | 分 | 评语 |
|---|---|---|
| 用户价值 | 92 | 从「读 DB」→「读一切」= 客户 IT 零成本 |
| 范围清晰 | 86 | 4 类摄取 + 本体 + LLM 范围明确 |
| 可验收 | 82 | 4 个用户故事有具体验收点 |
| 与架构契合 | 90 | 100% 复用 V0/V1 资产 |
| 风险识别 | 80 | 5 个风险都给了对策 |
| **平均** | **86** | ≥ 60 阈值 ✅ |

## 7. 门禁

- ✅ PRD 自评 86 分（≥ 60）→ 进入「方案设计」棒
