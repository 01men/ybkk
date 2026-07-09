# 00-product-brief.md — V1 核心闭环（AIOS-002 init 棒）

> 触发：AIOS-001 V0 已上 GitHub（commit `6d30217`），用户授权「继续」。
> 目标：把 V0 漏掉的核心闭环补完，让客户拿到产品能「端到端跑通一个场景」。
> 时点：2026-07-09 09:40 +08:00。

---

## 1. V0 状态回顾

- ✅ 8 制品齐 + 5/7 用户故事覆盖
- ✅ 5 层防御（凭证加密 / 只读三层 / 审计 append-only）
- ✅ 0 阻塞项
- ⏸️ 缺：前端控制台 5 页面
- ⏸️ 缺：Temporal worker（场景自主执行）
- ⏸️ 缺：端到端 E2E
- ⏸️ 缺：5 道门禁在客户机器实跑

## 2. V1 范围声明

**V1 = 端到端跑通一个内置场景**。具体：

| 项 | V0 状态 | V1 目标 |
|---|---|---|
| 数据源接入 API | ✅ | ✅ 保留 |
| 4 类关系型 DB 连接器 | ✅ | ✅ 保留 |
| KMS 凭证加密 | ✅ | ✅ 保留 |
| 6 张表 schema + append-only | ✅ | ✅ 保留 |
| 5 个内置场景模板 | ✅ | ✅ 保留 |
| **前端控制台 5 页面** | ⏸️ stub | ✅ **完整实现** |
| **Temporal worker + 5 场景编排** | ⏸️ 接口 | ✅ **完整实现** |
| **FlowRun 状态机** | ⏸️ | ✅ **完整实现** |
| **场景触发器** | ⏸️ | ✅ **完整实现** |
| **端到端 E2E** | ⏸️ | ✅ **Playwright 跑通** |
| **5 道门禁实跑** | ⏸️ PENDING | ✅ **PASS** |

## 3. V1 验收标准

1. 客户启动 Docker Compose → 30 分钟后所有容器 up
2. 打开 `http://<server>:3000` 看到登录页 → 登录后看到控制台
3. 走完一个完整业务链路：
   - 接入 MySQL 测试库
   - 选择「库存预警」场景
   - 启动 → 触发（手动 / 定时）
   - 看 FlowRun 状态：pending → running → succeeded
   - 看 audit_log 出现完整操作记录
4. 5 道门禁在 Linux 8C16G 实跑全部 PASS

## 4. V1 不做的事（V2+ 推进）

- Excel / PDF / 会议 worker 留 V2
- 本体推断留 V2
- 多租户留 V3
- 监控告警留 V3
- 安装脚本完善留 V3

## 5. 风险声明

- 客户机器 443 被防火墙挡 → 已用 SSH 22 解决（V0 推送经验）
- 沙箱内无 docker / pnpm / uv → 5 道门禁本机仍 PENDING，需客户机器实跑
- 5 道门禁的实现本身（PowerShell 5.1 兼容版）已在 V0 落库，V1 直接复用

## 6. 制品清单

`coding_group/kb/artifacts/AIOS-002/` 下 9 制品 + 1 changelog。

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
