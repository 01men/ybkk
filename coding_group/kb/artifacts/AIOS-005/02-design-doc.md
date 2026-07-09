# 02-design-doc.md — V4 设计文档（AIOS-005）

> 时点：2026-07-09 14:32 +08:00

---

## 1. 架构

不破坏 V0-V3 架构。V4 是「安全补丁 + bug fix」级别改动：

```
auth.py
  ├─ encode_jwt (V1, 不变)
  ├─ decode_jwt (V4 +ver 校验)
  ├─ hash_password / verify_password (V1, 不变)
  └─ user_to_jwt (V4 +perms +ver)

api/v1/auth.py
  ├─ /login (V4 自动解析默认 org + 签 ver=4 JWT)
  ├─ /logout (V1, 不变)
  ├─ /me (V4 返回 org_id/role_key/perms)
  ├─ /change-password (V1, 不变)
  └─ _resolve_default_org (V4 NEW helper)

api/v1/orgs.py (V4 NEW)
  ├─ GET    /orgs
  ├─ POST   /orgs
  ├─ POST   /orgs/{id}/switch
  ├─ GET    /orgs/{id}/members
  ├─ POST   /orgs/{id}/members
  ├─ PATCH  /orgs/{id}/members/{user_id}
  └─ DELETE /orgs/{id}/members/{user_id}

main.py (V4 +orgs router 注册)
console-shell.tsx (V4 删 system.manage 兜底)
```

## 2. 数据模型

不动。沿用 V3 migration 0005 的 5 表（orgs / org_members / roles / permissions / role_permissions）。

## 3. JWT Claims (V4 新)

```json
{
  "sub": "user-uuid",
  "username": "admin",
  "role": "admin",          // V1 UserRole enum（保留）
  "org_id": "org-uuid",     // V3 多租户
  "role_key": "admin",      // V3 RBAC 在 org 的角色
  "perms": [                // V4 NEW
    "datasource.read",
    "datasource.write",
    "...",
    "system.manage"
  ],
  "ver": 4,                 // V4 NEW 强制版本
  "iat": 1234567890,
  "exp": 1234567890 + 7*24*3600
}
```

## 4. RBAC 矩阵（V3 沿用）

不变。`permissions_for(role_key)` 返回 frozenset，`user_to_jwt` 转 list 写入。

## 5. /auth/me 响应 (V4 改造)

```json
{
  "id": "user-uuid",
  "username": "admin",
  "role": "admin",
  "created_at": "2026-07-09T...",
  "org_id": "org-uuid",     // V4 NEW
  "role_key": "admin",      // V4 NEW
  "perms": [                // V4 NEW
    "datasource.read",
    "..."
  ]
}
```

## 6. orgs router (V4 NEW)

| Method | Path | 权限 | 说明 |
|---|---|---|---|
| GET    | /orgs                  | 任意已登录 | 列我的组织 |
| POST   | /orgs                  | org.write  | 建组织（自动加我为 admin）|
| POST   | /orgs/{id}/switch      | 必须是成员  | 返回新 JWT |
| GET    | /orgs/{id}/members     | 任意已登录 | 成员列表 |
| POST   | /orgs/{id}/members     | org.invite | 邀请 |
| PATCH  | /orgs/{id}/members/{uid} | org.manage_members | 改角色 |
| DELETE | /orgs/{id}/members/{uid} | org.manage_members | 移除 |

## 7. _resolve_default_org 逻辑 (V4 NEW)

```
输入：(session, user)
输出：(org_id, role_key)

1. SELECT org_members WHERE user_id=? ORDER BY joined_at ASC LIMIT 1
2. 若有 member → return (member.org_id, member.role_key)
3. 若无 → INSERT Org(slug='{username}-default') + INSERT OrgMember(role_key='admin' if user.role==ADMIN else 'viewer')
4. return (new_org.id, role_key)
```

## 8. decode_jwt ver 校验 (V4 NEW)

```python
ver = int(body.get("ver", 0))
if ver < JWT_CURRENT_VERSION:  # JWT_CURRENT_VERSION = 4
    raise AiosError(E_AUTH_TOKEN_INVALID, ...)
```

## 9. console-shell 改动 (V4)

删除：
```typescript
if (myPerms.size === 0 && me?.role_key) {
  myPerms.add('system.manage');
}
```

## 10. 风险

- 强制重新签发 → 所有 V3 token 失效 → 全员被迫下线一次（V4 部署需提前通知）
- 自动建 org 的 slug 校验 → V4.1 修（见 06-review-report.md §4）

## 11. 不变更

- ✅ V0-V2 业务 API
- ✅ V3 metrics / 监控 / llm_judge 反注入
- ✅ docker-compose
- ✅ AIOS_VERSION tag