# 08-ship-log.md — V4 发货记录（AIOS-005 ship 棒）

> 发货人：orchestrator
> 时点：2026-07-09 14:50 +08:00
> GitHub: https://github.com/01men/ybkk

---

## 1. Git

| 项 | 值 |
|---|---|
| Commit | `f83b518` |
| Branch | `main` |
| Push | ✅ |
| 变更范围 | 15 files changed, 1092 insertions(+), 12 deletions(-) |
| SSH | ed25519 key `ybkk_github_global_ed25519` |

## 2. 制品清单

### 修改
- `apps/api/src/auth.py` — JWT_CURRENT_VERSION=4 + perms/ver claims
- `apps/api/src/api/v1/auth.py` — /me 返回 perms + _resolve_default_org 自动建 org
- `apps/api/src/main.py` — 注册 orgs router
- `apps/web/src/app/console-shell.tsx` — 删除 system.manage 兜底

### 新增
- `apps/api/src/api/v1/orgs.py` — 8 端点（V3 漏的路由）
- `apps/api/tests/test_jwt_v4.py` — 13 单测
- `coding_group/kb/artifacts/AIOS-005/{00~07 + state.json}` — 9 制品

## 3. 部署影响

**强制重新签发**：所有 V3 token（ver=3 或无 ver）登录后调任何 API 会 401。
前端会自动跳登录页重新签 ver=4 JWT。
**这是预期的安全效果**，部署到生产需提前通知。

## 4. 版本

- AIOS_VERSION: 不变（V4 是 patch 级别，兼容升级 0.4.0 → 0.4.1 语义）

## 5. V4.1 留尾（非阻塞）

1. `_resolve_default_org` slug 转 lowercase + url-encode（防 username 特殊字符）
2. orgs router 加 `get_current_user` 替代 `_ctx` 的「org_id 空 → 401」（一致性）
3. `SwitchResponse` 加 perm 列表（避免前端再调一次 /me）
4. 加 1 个 E2E：登录 → /me 返回 perms → 切换 org → 再 /me perms 变化
5. setup_default_admin 同时创建 default org（避免首次登录时的「先建 org 后登录」两次写库）

## 6. 结束语

V4 (AIOS-005) 5 任务全部完成，9 阶段状态机跑通。
GitHub 主分支已同步 commit `f83b518`。

V0 → V1 → V2 → V3 → V4 五棒连推，元冰可可 AIOS 演进表：

| 版本 | 主题 | 任务 | commits |
|---|---|---|---|
| V0 (AIOS-001) | 脚手架 | 8 | `6d30217` |
| V1 (AIOS-002) | web + temporal + e2e | 12 | `b6603a2` |
| V2 (AIOS-003) | ingest + ontology + LLM | 11 | `42fdc50` |
| V3 (AIOS-004) | 多租户 + RBAC + 监控 + SEC/OPS | 11 | `9e17bd7` |
| V4 (AIOS-005) | JWT 强制 + perms + orgs 补漏 | 5 | `f83b518` |

> V4 实质是「V3 安全补丁 + bug fix」：强制老 token 失效 / 前端不再用兜底 / V3 漏的 router 补上。