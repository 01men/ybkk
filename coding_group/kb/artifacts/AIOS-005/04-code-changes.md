# 04-code-changes.md — V4 代码变更清单（AIOS-005 dev 棒）

> 来源：V3 review 留尾 #4 + #2（详见 AIOS-004/06-review-report.md §4 + AIOS-004/08-ship-log.md §6）
> 时点：2026-07-09 14:38 +08:00

---

## V4-001: auth.py 加 JWT ver + perms（强制重新签发）

**修改** `apps/api/src/auth.py`：
- 加 `JWT_CURRENT_VERSION = 4`
- `user_to_jwt(user, org_id, role_key)` 新增两个 claims：
  - `perms: list[str]` —— 按 role_key 解析 `ROLE_PERMISSIONS` 写入
  - `ver: 4` —— JWT 版本号
- `decode_jwt` 加 ver 校验：`ver < 4` 一律抛 `E_AUTH_TOKEN_INVALID`（含「please re-login」提示）
- import `ROLE_PERMISSIONS`（rbac.py）

**效果**：
- V3 及更早 token（ver=3 或无 ver）登录后调任何 API 都会 401
- 前端 catch 401 自动跳登录页（沿用 V1 `apps/web/src/lib/api.ts` 401 拦截）
- 老用户重新登录拿到 ver=4 token，业务正常

---

## V4-002: auth.py /me 返回 perms（前端可直接用）

**修改** `apps/api/src/api/v1/auth.py`：
- `UserResponse` 加 3 字段：`org_id` / `role_key` / `perms`
- `/auth/me` 从 JWT payload 取 org_id / role_key / perms 返回
- 加 `_resolve_default_org(session, user)` 辅助：
  - 查 `org_members` 找用户已有 org（按 joined_at asc 取最早）
  - 无 org → 自动建一个 `{username}-default` org + 用户为 admin
  - V0 admin → V3 admin；V0 viewer → V3 viewer；其余默认 viewer
- `login` 调用 `_resolve_default_org` 拿到 (org_id, role_key) 再签 JWT

**效果**：
- 用户首次登录立刻有 org 上下文，无需前端先调 `/orgs`
- token 内置 perms，前端 `/auth/me` 直接拿，无需 RBAC 矩阵前端复刻

---

## V4-003: orgs router 补漏（V3 漏注册）

**新增** `apps/api/src/api/v1/orgs.py`：
- `GET  /api/v1/orgs` —— 列出我的组织（带 role_key + member_count）
- `POST /api/v1/orgs` —— 创建组织（需 `org.write` perm，自动把当前用户加为 admin）
- `POST /api/v1/orgs/{org_id}/switch` —— 切换组织（签新 JWT 返回 `SwitchResponse(token, org_id, role_key)`）
- `GET  /api/v1/orgs/{org_id}/members` —— 成员列表
- `POST /api/v1/orgs/{org_id}/members` —— 邀请成员（需 `org.invite`）
- `PATCH /api/v1/orgs/{org_id}/members/{user_id}` —— 改角色（需 `org.manage_members`）
- `DELETE /api/v1/orgs/{org_id}/members/{user_id}` —— 移除成员（需 `org.manage_members`）

**修改** `apps/api/src/main.py`：
- import 加 `orgs`
- `app.include_router(orgs.router, prefix="/api/v1")`（V3 漏的，现在补上）

**效果**：
- 前端 `/orgs` + `/orgs/[id]` 不再 404
- 切换组织返回新 JWT，前端覆盖 `localStorage.aios_token` 后页面继续可用

---

## V4-004: frontend console-shell 去兜底

**修改** `apps/web/src/app/console-shell.tsx`：
- 删除 `if (myPerms.size === 0 && me?.role_key) { myPerms.add('system.manage'); }`（V3 的兜底）
- 注释更新为「V3+V4: 后端 /auth/me 直接返回 perms 列表，无需前端兜底」

**效果**：
- viewer 角色看不到 ingest/ontology 等菜单（如果后端没给 perms）
- admin 不再因后端 bug 自动获得所有权限

---

## V4-005: 单测

**新增** `apps/api/tests/test_jwt_v4.py`：
- `test_jwt_current_version_is_4` —— 验证常量 = 4
- `test_encode_jwt_includes_ver` —— 验证新 token 含 ver=4
- `test_old_ver_token_rejected` —— ver=3 token 抛 AiosError
- `test_no_ver_token_rejected` —— 完全无 ver 字段 token 抛 AiosError（用 raw jwt 构造）
- `test_user_to_jwt_includes_perms` —— admin token perms = ALL_PERMISSIONS
- `test_user_to_jwt_viewer_has_only_6_perms` —— viewer token perms = ROLE_PERMISSIONS['viewer']（6 个）
- `test_user_to_jwt_unknown_role_empty_perms` —— 不存在 role_key → perms=[]
- `test_hash_password_roundtrip` —— PBKDF2 加解密
- V3 沿用的 4 个 RBAC 测试（admin 全集 / 角色级别单调 / viewer 只读 / engineer 部分写）

**总计**：13 单测

---

## 不变更（向后兼容）

- ✅ `apps/api/src/api/v1/orgs.py` 之前不存在（V3 漏），本棒新建
- ✅ V0-V2 业务 API 不动（auth 强校验后，原本老 token 401，但前端会自动跳登录重签）
- ✅ V3 llm_judge / metrics / 监控不动
- ✅ docker-compose 不变

---

## AIOS_VERSION

V3 是 0.4.0；V4 是 patch 级别（兼容升级），不动 version tag。

> V4 实质是「安全补丁 + bug fix」：强制老 token 失效 / 前端不再用兜底 / V3 漏的 router 补上。