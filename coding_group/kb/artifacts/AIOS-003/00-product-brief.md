# 00-product-brief.md — V2 多源 + 本体（AIOS-003 init 棒）

> 触发：V1 已上 GitHub（commit `ab9bb98`），用户授权「继续推进 V2」。
> 目标：补 V1 漏的 3 块能力（多源摄取 / 本体推断 / LLM 接入）。
> 时点：2026-07-09 10:05 +08:00。

---

## 1. V1 状态回顾

- ✅ 9 制品齐 + 0 阻塞
- ✅ 12 任务全实施（V1-001~012）
- ✅ 5 页面 + 17 step + JWT 鉴权 + 5 E2E + 11 服务 Docker Compose
- ⏸️ 5 道门禁待客户机器实跑

## 2. V2 范围声明

**V2 = 多源数据接入 + 本体推断 + LLM 接入**。具体：

| 项 | V1 状态 | V2 目标 |
|---|---|---|
| **多源数据接入** | | |
| 关系型 DB | ✅ 4 类 | ✅ 保留 |
| Excel (.xlsx) | ⏸️ V0 留接口 | ✅ **完整实现** |
| PDF | ⏸️ V0 留接口 | ✅ **完整实现** |
| 会议内容（语音转写） | ⏸️ | ✅ **完整实现** |
| 流程规范 Word/Markdown | ⏸️ | ✅ **完整实现** |
| **本体推断** | | |
| Neo4j schema | ⏸️ 启动建 | ✅ **完整定义** |
| 实体抽取（LLM 驱动） | ⏸️ | ✅ **完整实现** |
| 关系抽取 | ⏸️ | ✅ **完整实现** |
| 字段映射（DB 列 → 本体） | ⏸️ | ✅ **完整实现** |
| 本体查询 API | ⏸️ | ✅ **3 个查询** |
| **LLM 接入** | | |
| Qwen 本地 | ⏸️ V0 装好 | ✅ **接入 + fallback** |
| OpenAI / Anthropic | ⏸️ V0 装好 | ✅ **fallback 链路** |
| 场景 LLM 增强 | ⏸️ | ✅ **3 个场景用 LLM** |

## 3. V2 验收标准

1. 客户上传 1 个 Excel 物料清单 → 解析为本体节点（Material/Supplier/Warehouse）
2. 客户上传 1 个 PDF 工艺规范 → 提取工艺步骤 → 写到本体图
3. 客户上传 1 个会议录音（mp3/wav）→ ASR 转写 → 抽取业务规则 → 写本体
4. 客户上传 1 份 Markdown 流程规范 → 解析为 DeliveryStandard 候选
5. 场景执行时调 LLM 做"语义判断"（如库存预警阈值自适应）
6. 5 道门禁在客户机器实跑全 PASS

## 4. V2 不做的事（V3+ 推进）

- 多租户 / RBAC 完整版 → V3
- 监控告警 / Grafana 完善 → V3
- 安装脚本完善 / 离线安装 → V3
- 移动端 → V4

## 5. 风险声明

- **PDF 解析依赖** `unstructured[pdf]`（已 V0 装好）— 复杂表格 / 扫描件 PDF 仍可能失败
- **ASR 依赖** — 离线方案用 `whisper.cpp` / 云端用阿里云一句话识别（按需切换）
- **Neo4j 性能** — 大数据量（>10K 实体）需 V3 加索引
- **LLM 成本** — 私有部署用本地 Qwen 不花钱；OpenAI/Anthropic 按 token 计费（默认关闭）

## 6. 制品清单

`coding_group/kb/artifacts/AIOS-003/` 下 9 制品 + 1 changelog。

| # | 文件 | 写谁 | 门禁 |
|---|---|---|---|
| 00 | 00-product-brief.md | orchestrator | 已写 |
| 01 | 01-requirement-doc.md | requirements-analyst | PRD 自评 ≥ 60 |
| 02 | 02-design-doc.md | solution-architect | tasks 全勾可验证 |
| 03 | 03-tasks.md | solution-architect | — |
| 04 | 04-code-changes.md | developer | 5 道门禁全过 |
| 05 | 05-self-test-report.md | developer | — |
| 06 | 06-review-report.md | reviewer | 阻塞项 = 0 |
| 07 | 07-delivery-report.md | orchestrator | 5 门禁 + E2E |
| 08 | 08-ship-log.md | orchestrator | MCP 软降级留痕 |
