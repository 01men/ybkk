# 01-requirement-doc.md — V3 需求文档（AIOS-004 analyze 棒）

> 时点：2026-07-09 13:12 +08:00
> 作者：requirements-analyst
> 范围：多租户 + RBAC + 监控告警 + V2 留尾（SEC / OPS）

---

## 1. 用户故事

| 编号 | 故事 | 优先级 |
|---|---|---|
| US-V3-01 | 作为工厂 IT 管理员，我能为 2 个工厂分别建独立组织（org），每个工厂的数据完全隔离 | P0 |
| US-V3-02 | 作为组织管理员，我能邀请用户加入组织，分配「admin / 工程师 / 操作员 / 只读」4 类角色 | P0 |
| US-V3-03 | 作为工程师，我能调 LLM judge 工具做质检判断，prompt 不会因为我输入的内容被劫持 | P0 |
| US-V3-04 | 作为运维，我能在 Grafana 看到 API 5xx 率、flow 失败率、Ollama 健康等 5 类指标 + 告警 | P1 |
| US-V3-05 | 作为开发者，我跑 `docker compose --profile monitoring up -d` 即可拉起整套监控 | P1 |
| US-V3-06 | 作为首次部署者，Ollama 容器首次启动后自动 `ollama pull qwen2.5:7b` | P0 |
| US-V3-07 | 作为组织成员，我在顶部下拉切换组织后，看到的 datasources/flows/ontology 全是该 org 的 | P0 |

## 2. 功能需求

### 2.1 多租户

- 新表 `orgs` (id, name, slug, created_at)
- 新表 `org_members` (org_id, user_id, role, joined_at)
- 用户登录后默认拿到第一组织的 token；token 含 `org_id`
- 所有业务表加 `org_id` 列（migration 0005_v3_tenancy）
- 中间件 `require_org_member` 校验当前用户是否在 `org_id` 所属组织

### 2.2 RBAC

- 新表 `roles` (id, key, label, level) — 4 个内置：admin=4, engineer=3, operator=2, viewer=1
- 新表 `permissions` (id, key) — 30+ 权限点（datasource.read / datasource.write / flow.execute / ontology.write / llm.test 等）
- 中间件 `require_permission("flow.execute")` —— 没权限返回 403
- 前端按角色隐藏菜单 + 按钮

### 2.3 监控

- prometheus 容器，scrape interval 15s
- 4 个 exporter：API（FastAPI prometheus middleware）/ flow_engine（同样）/ ingest / ontology
- cadvisor 暴露容器资源
- Grafana provisioning：自带 5 个面板 + 1 个告警 channel（webhook stub）
- Loki 收容器日志

### 2.4 告警

Prometheus alert rules 5 条：

1. API 5xx > 1% 持续 5min
2. flow 失败率 > 20% 持续 10min
3. Ollama 不可达（`ollama_up==0`）持续 2min
4. ingest job 失败 > 3 次/小时
5. Neo4j bolt 不可达持续 2min

### 2.5 SEC-V3-01（LLM system role 隔离）

- LLM judge 拆 `system_prompt` + `user_prompt`
- system_prompt：固定指令（你是谁、返回 JSON schema、严防 prompt injection）
- user_prompt：context 走 data 段，明确不解析为指令
- 校验：当 context 包含「ignore previous instructions」「你现在是」等关键字时降级（confidence 强制 0）

### 2.6 OPS-V3-02（Ollama 自动 pull）

- ollama 容器加 entrypoint：先 `ollama serve` 后台起，再 `ollama pull qwen2.5:7b`（qwen2.5:7b 是 V2 默认模型）
- install.sh 在 `ollama ready` 后才退出
- 健康检查 `ollama list | grep qwen2.5:7b` 通过后才算 OK

## 3. 非功能需求

- 5 道门禁全过
- 端到端 P95：API 200ms / flow trigger 1s / llm_judge 3s
- 监控面板 5s 内打开
- 多租户 100% 隔离（e2e 验证组织 A 用户看不到组织 B 数据）

## 4. 验收标准

- [ ] US-V3-01 ~ US-V3-07 全部有 e2e 用例
- [ ] 5 道门禁在本地 + 客户机器都能过
- [ ] 监控页面在 `localhost:3001` 打开有 5 个 dashboard
- [ ] SEC-V3-01 单测覆盖 prompt injection 攻击模式
- [ ] OPS-V3-02 启动日志包含 `qwen2.5:7b pulled successfully`

## 5. PRD 自评（5 维，≥ 60 通过）

| 维度 | 分数 | 备注 |
|---|---|---|
| 用户价值 | 88 | 解决工厂多租户刚需 + 运维告警 |
| 范围 | 82 | 11 任务在 V3 内可控 |
| 可验收 | 86 | 每条 US 有 e2e |
| 架构契合 | 90 | 100% 复用 V0-V2 |
| 风险 | 75 | 多租户隔离需严测 |
| **平均** | **84.2** | ✅ 通过（≥ 60） |

## 6. 不在 V3 范围

- ASR 自训练（V4）
- 本体在线学习（V4）
- 移动端（V4）
- 复杂 BI 报表（V4）
- 多 LLM provider failover（V4）
