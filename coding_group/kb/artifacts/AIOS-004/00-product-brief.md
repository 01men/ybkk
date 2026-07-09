# 00-product-brief.md — V3 产品简报（AIOS-004 init 棒）

> 时点：2026-07-09 13:08 +08:00
> 发起人：orchestrator
> 背景：V0 → V1 → V2 已交付（9 阶段状态机跑通 2 次），V2 留尾清单中明确把多租户/RBAC、监控告警、SEC-V3-01、OPS-V3-02 留到 V3

---

## 1. V3 范围（从 V2 留尾 + V1/V2 设计 §「不包含」段收齐）

| 任务 ID | 标题 | 优先级 | 来源 |
|---|---|---|---|
| V3-001 | 多租户：orgs 表 + org_id 隔离 + 邀请码 | P0 | V1/V2 设计「不包含」段 |
| V3-002 | RBAC：roles / permissions / 角色绑定 + 中间件 | P0 | V1/V2 设计「不包含」段 |
| V3-003 | 监控：Prometheus + Grafana + Loki (docker-compose profile=monitoring) | P1 | V1/V2 设计「不包含」段 |
| V3-004 | 应用 metrics 端点（API / flow_engine / ingest / ontology / web 前端） | P1 | V3-003 配套 |
| V3-005 | 告警规则：5 类（API 5xx / flow 失败 / ollama 不可用 / ingest 失败 / Neo4j 不可达） | P1 | V3-003 配套 |
| V3-006 | SEC-V3-01：LLM judge 加 system role 隔离（user 上下文只放 data 段） | P0 | V2 review SEC-V3-01 |
| V3-007 | OPS-V3-02：Ollama docker entrypoint 自动 `ollama pull qwen2.5:7b` | P0 | V2 review OPS-V3-02 |
| V3-008 | 前端：组织切换器 + 用户管理 + 监控页 | P1 | V3-001/002/003 UI |
| V3-009 | 5 道门禁 V3 补丁（gate-baseline V3 + gate-coverage 多包 + gate-lint 加 ruff 安全规则） | P0 | V3 全 |
| V3-010 | 5 个 V3 E2E（11-org-switch / 12-rbac / 13-monitoring / 14-llm-system-role / 15-ollama-pull） | P1 | V3 全 |
| V3-011 | docker-compose V3 升级：postgres-temporal 已存在 → 加 prometheus/grafana/loki/cadvisor | P0 | V3-003 配套 |

**总计 11 个父任务 / 约 40 子项**

## 2. 不在 V3 范围

- ASR 自训练（V4）
- 本体在线学习（V4）
- 移动端（V4）
- 复杂 BI 报表（V4）

## 3. V3 与 V0-V2 衔接

- V0 数据层 + 错误体系 + 审计 100% 复用
- V1 JWT 鉴权保留；V3 升级为 multi-tenant + RBAC
- V2 4 类 parser / 本体 / LLM judge 100% 复用
- 5 道门禁基础保留，V3 加组织 + 监控 + 安全的门禁点

## 4. 风险

- 多租户容易引入「跨组织数据泄露」—— 严格依赖中间件 + 集成测试
- Prometheus + Grafana 拉起会增大镜像—— 走 profile=monitoring，按需启动
- 4 类 LLM provider（dashscope / openai / anthropic）暂留 V4，V3 只接 Ollama
