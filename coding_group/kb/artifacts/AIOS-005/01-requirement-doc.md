# 01-requirement-doc.md — V4 需求文档（AIOS-005）

> 时点：2026-07-09 14:31 +08:00

---

## 5 维 PRD 自评（满分 100）

| # | 维度 | 评分 | 备注 |
|---|---|---|---|
| 1 | 用户价值 | 88 | 安全补丁 + bug fix，强制重新签发提升安全性 |
| 2 | 范围 | 92 | 5 改动范围可控，全在 V3 review 留尾内 |
| 3 | 可验收 | 90 | 13 单测 + curl 验证 + E2E（建议加 1 spec） |
| 4 | 架构契合 | 95 | 复用 V3 RBAC 矩阵，不重复实现 |
| 5 | 风险 | 78 | slug 校验 V4.1 修；强制重新签发 = 用户被迫下线一次 |

**5 维平均**：88.6 ≥ 60，PRD 自评通过

## 用户故事

1. **作为用户**，我希望登录后 JWT 立刻带 org_id / role_key / perms，避免调 /orgs 才看到我的组织
2. **作为开发者**，我希望 JWT 有版本号强制重新签发，所有老 token 失效，防止泄露 token 长期滥用
3. **作为前端**，我希望 /auth/me 直接返回 perms 列表，不依赖 system.manage 兜底
4. **作为运维**，我希望能切换组织并立刻拿到新 JWT（无需重新登录）

## 验收标准

- [ ] `user_to_jwt` 签出的 token 含 `perms: [...]` 和 `ver: 4`
- [ ] `decode_jwt` 拒绝 `ver < 4` 的 token（含 ver=3 和无 ver 两种）
- [ ] `/auth/login` 返回 UserResponse 含 `org_id / role_key`
- [ ] `/auth/me` 返回 UserResponse 含 `org_id / role_key / perms`
- [ ] `/api/v1/orgs` 路由可达（V3 漏注册，现补上）
- [ ] `/api/v1/orgs/{id}/switch` 返回新 JWT
- [ ] console-shell 不再有 `system.manage` 兜底逻辑
- [ ] test_jwt_v4.py 13 测试全过