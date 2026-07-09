# 00-product-brief.md — V4 产品简报（AIOS-005）

> 时点：2026-07-09 14:30 +08:00

---

## 主题

V4 = V3 review 留尾 #4 + #2

## 范围

| # | 任务 | 来源 |
|---|---|---|
| V4-001 | auth.py 加 JWT ver + perms（强制重新签发） | V3 review 留尾 #2 |
| V4-002 | /me 返回 perms / org_id / role_key | V3 review 留尾 #4 |
| V4-003 | orgs router 补漏（V3 漏注册） | dev 棒发现 + fix |
| V4-004 | console-shell 去掉 system.manage 兜底 | V3 review 留尾 #4 联动 |
| V4-005 | JWT ver + perms 单测 | 自带 |

## 触发原因

V3 完成后用户说"继续"，选 C（修 V4 留尾），选 #4+#2 一起做。

## 影响面

- apps/api: auth.py / api/v1/auth.py / api/v1/orgs.py (NEW) / main.py / tests/test_jwt_v4.py (NEW)
- apps/web: console-shell.tsx

## 安全价值

1. JWT ver=4 强制重新签发：所有 V3 及更早 token 失效（防老 token 滥用）
2. perms claim 内置：前端不需复刻 RBAC 矩阵
3. orgs router 补漏：前端 /orgs 不再 404
4. console-shell 去兜底：viewer 严格按后端 perms 隐藏菜单

## AIOS_VERSION

不动（patch 级别，兼容升级）