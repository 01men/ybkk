# 09-evolve-plan.md — V1+ 全量任务规划（AIOS-001 后续演进）

> 触发：AIOS-001 V0 交付完成（stage=done），9 阶段全跑通。
> 目标：把 V0 漏掉的 50% 任务 + V1+ 新增任务全部排期，按优先级交付。
> 时点：2026-07-08 18:52 +08:00。

---

## 0. V0 现状回顾

- ✅ 覆盖：5/7 用户故事（数据源接入 / 场景模板 / 标准编辑 / 审计 / 私有化部署）
- ⏸️ 漏掉：US-4 自主执行（Temporal worker）/ US-7 多源摄取（Excel/PDF/会议 worker）
- ⏸️ 漏掉：前端控制台 5 个页面（apps/web 只有 stub）
- ⏸️ 漏掉：本体推断（Neo4j adapter）
- ⚠️ 已知：单一租户 / RBAC middleware 串通 / 安装脚本完善 / 监控告警 / 私有化 E2E

V1~V3 目标：**完整可商用**（7/7 US + 端到端跑通 + 客户机器一键部署）。

---

## 1. 优先级矩阵

| 优先级 | 任务 | 理由 |
|---|---|---|
| **P0** | V0 漏的 30 任务中未完成的 ~15 条 | V0 已承诺不烂尾，欠债要还 |
| **P0** | 前端控制台 5 页面 | 客户看不到 UI = 没交付 |
| **P0** | Temporal worker + 场景编排 | US-4 自主执行的核心 |
| **P1** | 多源摄取 worker | US-7 多源融合 |
| **P1** | 本体推断 + Neo4j 适配 | 本体图是「场景 × 职能」匹配的桥梁 |
| **P1** | RBAC + 租户隔离 | 多客户必备 |
| **P2** | 监控告警（Grafana + 飞书） | 运维 |
| **P2** | 安装脚本完善 + 私有化 E2E | 交付质量 |
| **P3** | 体系自身演进（changelog / evolve） | 长期 |

---

## 2. 阶段排期（V1 / V2 / V3）

### V1（核心闭环，约 4~6 周）

| ID | 任务 | 优先级 | 估时 | 状态 |
|---|---|---|---|---|
| V1-001 | 启动 Next.js 14 (App Router) + Ant Design Pro 工程 | P0 | 0.5d | ⏳ |
| V1-002 | 前端 5 页面：数据源管理 / 场景模板 / 标准编辑 / 流程运行 / 审计日志 | P0 | 8d | ⏳ |
| V1-003 | 前端 API client（基于 OpenAPI 自动生成 TS 类型）| P0 | 1d | ⏳ |
| V1-004 | apps/flow_engine 服务骨架 + Temporal worker 注册 | P0 | 2d | ⏳ |
| V1-005 | 把 V0 5 个内置场景的 `flow_template` 翻译成 Temporal Workflow | P0 | 5d | ⏳ |
| V1-006 | FlowRun 状态机（pending / running / succeeded / failed / cancelled）| P0 | 2d | ⏳ |
| V1-007 | 场景触发器（schedule / ontology_event / manual）| P0 | 3d | ⏳ |
| V1-008 | gate-e2e 用 Playwright 跑端到端「接入数据源→加载场景→触发→审计」| P0 | 3d | ⏳ |
| V1-009 | 5 道门禁在客户 Linux 环境实跑 + 贴报告 | P0 | 1d | ⏳ |

**V1 验收**：客户拿到代码可一键部署，看到完整控制台，能跑通一个内置场景的端到端。

### V2（多源 + 本体，约 3~4 周）

| ID | 任务 | 优先级 | 估时 | 状态 |
|---|---|---|---|---|
| V2-001 | apps/ingest 服务骨架（FastAPI + worker）| P1 | 1d | ⏳ |
| V2-002 | Excel 摄取 worker（openpyxl + pandas）| P1 | 3d | ⏳ |
| V2-003 | PDF / DOCX 抽取 worker（pypdf + python-docx + unstructured）| P1 | 4d | ⏳ |
| V2-004 | 会议纪要抽取 worker（语音转写 + LLM 摘要）| P1 | 5d | ⏳ |
| V2-005 | apps/ontology 服务骨架（FastAPI + Neo4j driver）| P1 | 1d | ⏳ |
| V2-006 | Neo4j schema 初始化 + 索引 | P1 | 1d | ⏳ |
| V2-007 | 本体推断：表名 / 字段名 / 注释 → 实体 / 属性 / 关系（LLM 驱动）| P1 | 5d | ⏳ |
| V2-008 | 本体图 CRUD API + Cypher 封装 | P1 | 3d | ⏳ |
| V2-009 | ontology_event 触发器接入 FlowRun | P1 | 2d | ⏳ |
| V2-010 | 回写检测 worker（TASK-062 落地）| P1 | 3d | ⏳ |

**V2 验收**：客户能上传 Excel / 跑场景 / 触发 8D 报告，审计可追溯到多源数据。

### V3（多租户 + 监控 + 运维，约 2~3 周）

| ID | 任务 | 优先级 | 估时 | 状态 |
|---|---|---|---|---|
| V3-001 | RBAC 中间件完整实现（JWT 解码 + 角色 + 资源级权限）| P1 | 3d | ⏳ |
| V3-002 | 多租户隔离（tenant_id 中间件 + DB row-level security）| P1 | 4d | ⏳ |
| V3-003 | Grafana 仪表盘（API 响应 / 流程运行 / 错误率 / LLM token）| P2 | 2d | ⏳ |
| V3-004 | 告警规则（飞书 webhook 推送：流程失败 / 凭据解密失败 / disk 90%）| P2 | 2d | ⏳ |
| V3-005 | install.sh 完善：硬件自适应 + 离线安装 + 升级回滚 + 健康检查 | P2 | 3d | ⏳ |
| V3-006 | 私有化部署 E2E（裸机 → install.sh → 控制台可登录 → 跑通一个场景）| P2 | 2d | ⏳ |
| V3-007 | 体系演进：changelog / evolve / 9 阶段状态机 runbook 沉淀 | P3 | 1d | ⏳ |

**V3 验收**：商用就绪（多租户 + 监控 + 告警 + 完整 E2E）。

---

## 3. 跨阶段依赖图

```
V1-001 (Next.js 启动)  ─┐
                         ├─→ V1-002 (5 页面) ─→ V1-003 (API client)
V1-004 (Flow engine) ───┤
                         ├─→ V1-005 (5 场景 → Temporal) ─→ V1-006 (状态机)
V1-007 (触发器) ─────────┘                                  ↓
                                                          V1-008 (E2E) → V1-009 (5 门禁)

V2-002/003/004 (摄取 worker)  ──→ V2-005/006 (ontology 骨架)
                                       ↓
V2-007 (本体推断 LLM) ──→ V2-008 (CRUD) ──→ V2-009 (触发 ontology_event) ──→ V2-010 (回写检测)

V3-001/002 (RBAC + 多租户) ──→ V3-003/004 (监控告警) ──→ V3-005 (install) ──→ V3-006 (私有化 E2E)
```

---

## 4. 风险与对策

| 风险 | 触发条件 | 对策 |
|---|---|---|
| 本体推断准确率低 | LLM 把字段当实体 / 关系识别错 | 给 LLM few-shot 例子 + 人工 review 入口（场景编辑页）|
| 端到端 E2E 跑挂 | Temporal worker 时序问题 | 把 E2E 拆成「5 个单场景 E2E」逐个跑通 |
| 多源摄取性能差 | Excel 100MB 内存爆 | 用 polars 替代 pandas + 流式 |
| 多租户漏数据 | middleware 漏一处 | E2E 加「租户越权」用例 |
| 私有化部署硬件差异 | 客户机器驱动不齐 | install.sh 预检 + 给常见 GPU/网卡打 patch |

---

## 5. 阶段产物模板

每个 V 跑完都用 AIOS-001 的 9 阶段状态机（init → analyze → design → dev → review → verify → ship → END），但 req-id 改为 `AIOS-002-V1` / `AIOS-003-V2` / `AIOS-004-V3`。

每个 V 必写：
- `00-product-brief.md`（V 范围声明）
- `01-requirement-doc.md`（V 需求拆解）
- `02-design-doc.md`（V 技术方案）
- `03-tasks.md`（V 任务清单）
- `04-code-changes.md`（V 改动清单）
- `05-self-test-report.md`（V 自测）
- `06-review-report.md`（V 审查）
- `07-delivery-report.md`（V 验收）
- `08-ship-log.md`（V 交付）

---

## 6. 演进规则

1. **每个 V 必跑 9 阶段状态机**——V0 的 9 棒 SOP 是模板
2. **每个 V 必跑 5 道门禁**——硬门禁不绕过
3. **每个 V 必触发人工关卡**——「需求确认 / 方案确认 / 验收」3 次人工审批
4. **每个 V 必写 changelog**——V0 changelog 模板已就绪
5. **每个 V 必留 MCP 留痕**——失败软降级

---

## 7. 实施时间线（建议）

| 周次 | 阶段 | 关键里程碑 |
|---|---|---|
| W1 | V1-001~004 | Next.js + Flow engine 启动 |
| W2~W3 | V1-002/003 | 5 个前端页面 |
| W4~W5 | V1-005/006/007 | Temporal 场景编排 + 触发器 |
| W6 | V1-008/009 | E2E + 5 道门禁 |
| W7~W10 | V2-001~010 | 多源摄取 + 本体推断 |
| W11~W13 | V3-001~007 | 多租户 + 监控 + 私有化 E2E |

---

## 8. 关键决策（待用户确认）

1. **V1 是否同时启动前后端？** 建议同时，否则前端没 API 调
2. **V2 的 LLM 提供方**：本地 Qwen2.5-72B（私有化）vs 调云端（部署简单但有外网依赖）
3. **V3 的多租户粒度**：行级隔离（强）/ 库级隔离（简单）/ schema 隔离（折中）
4. **V3 的告警通道**：飞书 / 企微 / 邮件 / 多通道

> 用户确认后开 V1-001。
