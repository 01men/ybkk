# 03-tasks.md — V4 任务清单（AIOS-005 design 棒）

> 来源：02-design-doc.md
> 时点：2026-07-09 14:33 +08:00

---

## V4-001: auth.py 加 JWT ver + perms（强制重新签发）

- [x] `JWT_CURRENT_VERSION = 4` 常量
- [x] `user_to_jwt` 加 `perms: list[str]` + `ver: int` 两个 claims
- [x] `decode_jwt` 加 ver 校验（<4 拒绝）
- [x] `__all__` 加 `JWT_CURRENT_VERSION`

## V4-002: /me 返回 perms + login 自动建默认 org

- [x] `UserResponse` 加 `org_id` / `role_key` / `perms`
- [x] `/auth/me` 从 JWT payload 取 3 字段返回
- [x] `_resolve_default_org(session, user)` helper
- [x] `/auth/login` 调用 helper 后签 JWT

## V4-003: orgs router 补漏

- [x] `apps/api/src/api/v1/orgs.py` (NEW) 8 端点
- [x] `main.py` import `orgs`
- [x] `main.py` `app.include_router(orgs.router, prefix="/api/v1")`

## V4-004: console-shell 去兜底

- [x] 删除 `system.manage` 兜底 if 块
- [x] 注释更新

## V4-005: JWT ver + perms 单测

- [x] `apps/api/tests/test_jwt_v4.py` (NEW)
- [x] 13 测试用例（ver 强制 / perms claim / 密码 roundtrip / V3 沿用 RBAC）

---

**任务勾选统计**：5 个父任务，19 子项，全部完成