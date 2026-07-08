---
name: deployment-checklist
description: 部署前 / 部署时的强制清单。developer 在 E2E 通过后、reviewer 通过前必跑。触发词：「部署」「staging」「上线」「回滚」。
---

# Deployment Checklist

## 部署前（developer 必跑 8 项）

1. **依赖锁定**：`package-lock.json` / `pnpm-lock.yaml` / `requirements.txt`（含 hash）都 commit
2. **环境变量齐**：`.env.example` 列全，部署平台的 Project Settings 都填了
3. **数据库迁移**：所有 schema 变更有版本化 migration 文件
4. **静态扫描通过**：`./scripts/gates/gate-lint.sh`
5. **单测通过 + 覆盖率达标**：`./scripts/gates/gate-coverage.sh`
6. **E2E 通过**：`./scripts/gates/gate-e2e.sh`（至少跑过一遍 staging）
7. **回滚方案就绪**：上一版本二进制 / 容器镜像仍在 registry
8. **监控仪表盘就绪**：关键指标有看板 + 告警

漏 1 项 → 不准进入「验收」。

---

## 部署中的灰度策略

| 阶段 | 流量占比 | 持续时长 | 通过条件 |
|---|---|---|---|
| 内部用户 | 5% | ≥ 30 分钟 | 无 error 上升 |
| 小流量 | 10% | ≥ 1 小时 | P99 < 阈值 |
| 半量 | 50% | ≥ 2 小时 | 业务指标无下跌 |
| 全量 | 100% | — | — |

**任一阶段不通过 → 自动回滚（触发回滚脚本）**

---

## 回滚触发条件（满足任一即回滚）

- 错误率上升 > 0.5%（5xx 比例）
- P99 延迟上升 > 30%
- 关键业务指标（转化、登录）下跌 > 2%
- 监控告警 >= 3 条

**回滚不犹豫**。回滚后再定位问题，永远比线上抗住便宜。

---

## 回滚动作

```
./scripts/gates/gate-rollback.sh <version>
```

强制要求：

- 一键回滚 ≤ 5 分钟
- 回滚后必须发飞书通知
- 回滚后必须 30 分钟内写事故复盘到 `kb/incidents/`

---

## 监控指标（最小集合）

| 类别 | 指标 |
|---|---|
| HTTP | QPS / 错误率 / P50 P99 延迟 |
| 数据库 | 连接池使用率 / 慢查询数 |
| 缓存 | 命中率 / 内存使用 |
| 业务 | DAU / 转化 / 关键流程完成数 |
| 自定义 | 按业务加 |

每个需求必须声明「本需求会动到哪些监控指标」。

---

## 部署渠道

| 环境 | 谁触发 | 用什么 |
|---|---|---|
| dev | developer | Vercel preview / GitHub Action |
| staging | developer | 手动 / 自动 |
| production | reviewer 通过后由 orchestrator | MCP 触发 |

**production 部署必须有 reviewer 通过为前提。**

---

## 上线 SOP（每一个 production 部署）

```
1. 拉最新 main → 跑 5 道门禁 → 通过
2. 打 tag（vX.Y.Z）
3. 触发 staging 部署 → 等 staging E2E 通过
4. 触发灰度（5%）→ 30 分钟观察
5. 触发灰度（10%、50%）→ 通过 → 100%
6. 发飞书通知（含版本号、变更、监控链接）
7. 30 分钟后盯监控 → 关闭事故 ticket

任一步失败 → 触发回滚 → 写事故复盘
```
