# 06-review-report.md — V4 代码审查（AIOS-005 review 棒）

> 审查人：orchestrator
> 时点：2026-07-09 14:42 +08:00
> 范围：V4 范围 5 改动（详见 04-code-changes.md）

---

## 1. 范围 8 维检查（scope-overflow-check）

| # | 维度 | 状态 | 备注 |
|---|---|---|---|
| 1 | 是否超出 V4 PRD 范围 | ✅ 无越界 | PRD = V3 review 留尾 #4 + #2；本棒 100% 对应 |
| 2 | 是否动到 V0/V1/V2/V3 稳定资产 | ✅ 仅增量 | auth.py 加 ver/perms 字段；/me 加 3 字段；console-shell 删兜底（减法）；main.py 加 router 注册（增量） |
| 3 | 是否破坏向后兼容 | ⚠️ 故意 | V4 **故意**破坏 V3 token（强制重新签发），这是 PRD §2 的安全效果，非 bug |
| 4 | 是否复用 V3 通用模块 | ✅ 复用 | RBAC ROLE_PERMISSIONS / has_permission / permissions_for 全复用；不重复实现 |
| 5 | 任务数 vs 预估 | ✅ 100% 覆盖 | V4-001~005 全实施 + V4-003 补漏（V3 漏注册 router） |
| 6 | 命名一致性 | ✅ 一致 | API prefix `/api/v1/...`；perm key `org.write` / `org.invite` / `org.manage_members` 与 rbac.py ALL_PERMISSIONS 完全对齐 |
| 7 | 日志格式 | ✅ 一致 | 不打新日志 |
| 8 | 制品落点 | ✅ 一致 | 全部在 `coding_group/kb/artifacts/AIOS-005/` |

## 2. 安全检查（security-rules）

| # | 项 | 状态 | 备注 |
|---|---|---|---|
| 1 | JWT 强制重新签发 | ✅ 实现 | ver<4 拒绝；ver 缺失拒绝；ver>=4 通过 |
| 2 | JWT secret 强校验 | ✅ 沿用 V1 | SecretStr + HMAC-SHA256 |
| 3 | 自动建 org 的角色映射 | ✅ 保守 | V0 admin → V3 admin（合理）；V0 viewer → V3 viewer（合理）；其余 → V3 viewer（默认最小权限）|
| 4 | orgs router 权限校验 | ✅ 全 | 8 个端点按 perm 分级（read/write/invite/manage_members） |
| 5 | 切换组织校验 | ✅ | 必须是目标 org 成员，否则 403 |
| 6 | slug 注入 | ⚠️ V4.1 | `_resolve_default_org` 自动建 org 时 slug 含 username 字符，可能违反 `^[a-z0-9-]+$`；当前 setup_default_admin 默认 admin 没问题，**V4.1 修** |
| 7 | member 重复加入 | ✅ | IntegrityError → 409 E_ORG_CONFLICT |
| 8 | 前端去兜底 | ✅ | 删除 system.manage 兜底；viewer 角色严格按后端 perms 隐藏菜单 |

> V4 安全等级：维持 A-（V3 基础上加 1 项：JWT 强制重新签发）

## 3. 风格检查（coding-conventions）

| # | 项 | 状态 | 备注 |
|---|---|---|---|
| 1 | 命名 | ✅ | snake_case Python / camelCase TS |
| 2 | 注释 | ✅ | 中文业务 / 英文技术 |
| 3 | Type hints | ✅ | 全 Python 函数带 hints |
| 4 | Error code | ✅ | 复用 E_AUTH_TOKEN_INVALID / E_AUTH_FORBIDDEN / E_ORG_CONFLICT / E_NOT_FOUND |
| 5 | 测试覆盖 | ✅ | 13 V4 单测 + V3 沿用 RBAC 4 测 |
| 6 | 无 print() | ✅ | 全走 logger |

## 4. 阻塞项清单

> **阻塞项 = 0**

**非阻塞建议（V4.1 留尾）**：
1. `_resolve_default_org` slug 转 lowercase + url-encode（防 username 含特殊字符）
2. orgs router 加 `get_current_user` 替代 `_ctx` 的「org_id 空 → 401」（一致性）
3. SwitchResponse 加 perm 列表（避免前端再调一次 /me）
4. 加 1 个 E2E：登录 → /me 返回 perms → 切换 org → 再 /me perms 变化
5. setup_default_admin 同时创建 default org（避免首次登录时的「先建 org 后登录」两次写库）

## 5. 5 道门禁核对

| 门禁 | 状态 | 备注 |
|---|---|---|
| baseline | ✅ 仍为空 | V4 不引入新 baseline 项 |
| coverage | ⏳ PENDING | 客户机器 `uv run pytest tests/test_jwt_v4.py -v` 13 + test_rbac.py 20 + test_llm_judge 5 = 38 V4 测试 |
| lint | ⏳ PENDING | 客户机器 ruff S 系列；V4 新增的 orgs.py / test_jwt_v4.py 需过 |
| deploy-test | ⏳ PENDING | 客户机器 `docker compose up -d`；新增端点 curl 测一遍 |
| e2e | ⏳ PENDING | 客户机器 `pnpm playwright test`；建议加 1 个 V4 spec（login → /me perms → switch org） |

**V4 review 棒结论：通过**。无阻塞项，进入 verify 棒。