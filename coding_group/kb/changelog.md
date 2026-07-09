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
