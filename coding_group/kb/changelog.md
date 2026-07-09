# Changelog — 体系演进日志

> 任何对 AGENTS.md / Skill / Scripts / Workflow 的修改都写一行在这里。三个月后你才会感谢这一份。

## 格式

```markdown
## YYYY-MM-DD: <一句话标题>

- 改动: <改了哪个文件 / 哪一段、为什么>
- 触发原因: <那次撞墙 / 那个需求>
- 影响面: <哪些 Skill / 哪些 Agent 受影响>
- 回滚方法: <如果改坏了怎么改回去>
```

---

## 启动记录

- 2026-07-08：补齐脚手架缺失的家法文件。
  - 改动: 新建仓库根 `AGENTS.md`（之前误置于 `coding_group/AGENTS.md`），新增 `coding_group/kb/AGENTS.md`（之前缺失，违反 orchestrator 启动序列）；全部路径引用已更新为带 `coding_group/` 前缀
  - 触发原因: 脚手架规约要求 `AGENTS.md` 在仓库根，`kb/AGENTS.md` 必须存在；之前把所有研发物料误塞到 `coding_group/`
  - 影响面: 仓库根 + `coding_group/`；脚本路径未改（原本就在 `coding_group/assets/scripts/`），仅文档引用规范化
  - 回滚方法: `git revert` 这次 commit；或删除新建的 `AGENTS.md` 并把 `coding_group/AGENTS.md` 还原为根

- 2026-07-08：清理冗余家法文件。
  - 改动: 删除 `coding_group/AGENTS.md`（与根 `AGENTS.md` 内容重复、路径错位，会让 Agent 误读）
  - 触发原因: 用户确认删除，避免与仓库根家法冲突
  - 影响面: 仅 `coding_group/AGENTS.md`；仓库根 `AGENTS.md` 已是唯一权威
  - 回滚方法: 从 git 历史恢复该文件

- 2026-07-08：V0 交付完成（AIOS-001）。
  - 改动: 落地元冰可可 AIOS V0 —— monorepo 骨架、FastAPI 后端、4 类关系型 DB 连接器、KMS 凭证加密、6 张表 schema、append-only 审计触发器、5 个内置离散制造场景模板、5 个内置交付标准、3 个共享包（standards / audit / llm-gateway）、一键私有化部署（install.sh / backup.sh / upgrade.sh）、5 道门禁双栈（Linux bash + Windows PowerShell 5.1）
  - 触发原因: 用户要求复刻「制造业 AIOS」，目标「企业拿到产品直接 AI 转型，不改造现有系统，直接读数据元」
  - 影响面: AIOS-001 全部 8 制品 + 仓库根脚手架
  - 回滚方法: `git revert` AIOS-001 V0 commit
  - 备注: 9 阶段状态机全跑通；review 0 阻塞、verify 通过、ship 棒 MCP 软降级（无 GitHub/Deploy/Notify MCP 配置）；5 道门禁 PENDING（环境受限）需客户机器重跑

- 2026-07-08：V1+ 全量规划 + GitHub 部署检查。
  - 改动: 新增 09-evolve-plan.md（V1/V2/V3 三个阶段共 27 个任务的优先级、估时、依赖图、风险对策、时间线）；新增 10-github-deploy-checklist.md（git 探测 / secret 扫描 / .gitignore 覆盖 / 推送前必做 / 一键命令）
  - 触发原因: V0 交付完成（stage=done），用户要求「完成下一步所有规划」+「看看应用是否可以部署到 GitHub」
  - 影响面: AIOS-001 制品集（10 制品齐）；git 工作区（建议推送）
  - 回滚方法: 删除 09/10 两份 md 即可
  - 备注: secret 扫描全过（仅占位符 CHANGEME / SecretStr 类型 / 测试用 0）；git origin 已是 https://github.com/01men/ybkk.git；唯一阻塞是 git user.name/user.email 是 Clawdbot 默认值，需用户改成 xiaodao

- YYYY-MM-DD（今天）：V1 建立。
  - 改动: 初始搭脚手架（AGENTS.md / 11 个 Skill / 5 道门禁脚本 / 5 个 Agent prompt）
  - 触发原因: 从零开始按个人编程 Agent 团队搭建方案落地
  - 影响面: 全部
  - 回滚方法: `git revert` 这次 commit，或在 git 历史里找回上一个稳定版本

- 2026-07-09：V1 交付完成（AIOS-002）。
  - 改动: 落地元冰可可 AIOS V1 —— JWT + PBKDF2 鉴权、9 个 V1 API（auth / scenarios / flows / flow_runs / audits / internal）、migration 0003_v1_core、apps/flow_engine 全新包（Temporal worker + 17 step handlers）、apps/web 全新 Next.js 14 前端（控制台 + 9 页面 + 5 E2E）、docker-compose V1 升级到 11 核心服务、5 道门禁就位
  - 触发原因: V0 完成后用户要求「继续」进入 V1；9 阶段状态机跑通；commit ab9bb98
  - 影响面: 仓库根 + apps/api + apps/flow_engine + apps/web + deploy/compose
  - 回滚方法: `git revert` V1 commits（b6603a2 + ab9bb98）

- 2026-07-09：V2 交付完成（AIOS-003）。
  - 改动: 落地元冰可可 AIOS V2 —— 多源摄取（apps/ingest 全新：4 类 parser：Excel / PDF / 会议 / Markdown）、本体图（apps/ontology 全新：10 节点 + 12 关系 + LLM 实体+关系抽取 + 字段映射）、LLM judge（flow_engine 新 activity + 15 单测 + 3 内置模板）、migration 0004_v2_ingest（ingest_jobs / llm_calls / ontology_field_mappings）、6 新前端页面（数据接入 / 任务列表 / 任务详情 / 本体浏览 / 节点详情 / LLM 用量）、5 新 E2E、docker-compose V2 升级（加 ollama 服务 + 独立 ingest/ontology image）、gate-deploy-test V2 补丁（ingest/ontology/ollama health）、Neo4j iframe 折叠面板
  - 触发原因: V1 完成后用户要求「继续推进 V2」；9 阶段状态机跑通；commit 42fdc50 + 12435d0
  - 影响面: 仓库根 + apps/api（3 路由 + 1 migration + models 加 3 类）+ apps/ingest（V2 全新）+ apps/ontology（V2 全新）+ apps/flow_engine（1 新 activity + 1 workflow 改）+ apps/web（6 页面 + console-shell 加 3 菜单 + 5 E2E）+ deploy/compose（V2 升级）+ coding_group/assets/scripts/gate-deploy-test.sh
  - 单测: 30/30 通过（6 ingest + 9 ontology + 15 flow_engine）
  - Review: 0 阻塞 / 4 V3 建议
  - 回滚方法: `git revert` V2 commits（42fdc50 + 12435d0）
  - V3 留尾: SEC/TS/OPS 共 4 项 + 多租户 RBAC + 监控告警 + ASR 自训练 + 本体在线学习

- 2026-07-09：V3 交付完成（AIOS-004）。
  - 改动: 落地元冰可可 AIOS V3 —— 多租户（migration 0005 + OrgContext + JWT org_id/role_key + 7 业务表加 org_id）、RBAC（4 角色 × 30 权限 + require_permission + 20 关键矩阵单测）、监控（profile=monitoring：Prometheus + Grafana + Loki + Promtail + cadvisor + 5 dashboard + 6 alert rules）、5 服务 metrics 端点（stdlib-only）、SEC-V3-01（LLM system role 隔离 + 10 关键词反注入 + 5 单测）、OPS-V3-02（apps/ollama 独立 image + entrypoint.sh 自动 pull qwen2.5:7b）、前端（/orgs + /orgs/[id] + /monitoring + console-shell perm 过滤 + 顶部 org Select）、5 新 E2E（11~15）、docker-compose V3 升级（AIOS_VERSION 0.4.0 + 5 monitoring service）、5 道门禁 V3 补丁（gate-lint 加 ruff S + gate-deploy-test 加 3 健康检查）
  - 触发原因: V2 完成后用户要求「完成 V3 的开发」；9 阶段状态机跑通；commit 9e17bd7 + 508db46
  - 影响面: 仓库根 + apps/api（migration 0005 + 5 模型 + 2 middleware + metrics + 2 路由 + rbac 单测 + models/auth 改）+ apps/flow_engine（llm_judge 大改 + 反注入测试 + workflow 改 + metrics）+ apps/ingest（metrics）+ apps/ontology（metrics）+ apps/ollama（V3 全新）+ apps/web（3 页面 + console-shell 改 + 5 E2E）+ deploy/compose/docker-compose.yml（V3 升级）+ deploy/compose/monitoring/（V3 全新 14 文件）+ coding_group/assets/scripts/gate-{lint,deploy-test}.sh
  - 单测: 4×5=20 RBAC + 5 反注入 = 25 V3 关键测试
  - Review: 0 阻塞 / 5 V4 留尾建议
  - Verify: AST/YAML/JSON 沙箱解析全过；5 道门禁 PENDING 需客户机器实跑
  - 回滚方法: `git revert` V3 commits（9e17bd7 + 508db46）
  - V4 留尾: 反注入正则升级 + JWT 强制重新签发 + Grafana extra_hosts + /auth/me 返回 perms + admin org.delete 测试 + internal API mTLS
  - AIOS_VERSION: 0.3.0 -> 0.4.0
