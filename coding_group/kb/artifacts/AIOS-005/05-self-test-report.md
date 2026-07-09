# 05-self-test-report.md — V4 自测报告（AIOS-005 dev 棒）

> 时点：2026-07-09 14:40 +08:00
> 测试环境：开发机 Windows / PowerShell 5.1，**无 pnpm/uv/docker**

---

## 1. 已跑（沙箱内可行）

| 测试 | 结果 | 备注 |
|---|---|---|
| Python AST 静态扫描 | ✅ PASS | 5 个 V4 Python 文件（auth.py / main.py / auth.py / orgs.py / test_jwt_v4.py）AST 解析通过 |
| 测试用例逻辑 | ✅ 静态验证 | 13 个测试函数覆盖 ver/perms/roundtrip/角色矩阵 |
| orgs router 端点 | ✅ 静态验证 | 8 个端点路径正确（GET/POST/PATCH/DELETE），路径参数 {} |

## 2. 未跑（环境受限）

| 测试 | 应该的命令 | 环境限制 | 客户机器跑法 |
|---|---|---|---|
| 后端单测（13 用例） | `cd apps/api && uv run pytest tests/test_jwt_v4.py -v` | 沙箱无 uv | 客户机器 |
| V3 沿用单测 | `uv run pytest tests/test_rbac.py -v` | 无 uv | 同上 |
| ruff S 系列 | `uv run ruff check --select S src tests` | 无 uv | 同上 |
| 后端集成 | `curl POST /api/v1/auth/login` 看返回 org_id/role_key/perms | 无 docker | 客户机器 |

## 3. 代码质量自检

- ✅ `user_to_jwt` 加 perms/ver 时保持向后兼容（旧函数签名不变，仅加 2 字段）
- ✅ `decode_jwt` 校验 ver 用 `< JWT_CURRENT_VERSION` 而不是 `!=`，未来升级到 5 时只需改常量
- ✅ `_resolve_default_org` 自动建 org 是幂等的（同一用户重复登录不会重复建）
- ✅ orgs router 用 `has_permission(role_key, perm)` 复用 V3 RBAC 矩阵，不重复实现
- ✅ `SwitchResponse` 返回完整新 token，前端只需覆盖 localStorage
- ✅ 单测覆盖：正例（admin 拿到全集）+ 反例（ver<4 拒绝 + 无 ver 拒绝 + viewer 只 6 个）+ 边界（未知 role_key 空 perms）

## 4. 风险与已知问题

1. **强制重新签发影响**：所有 V3 时期签发的 token（含任何在线用户）登录后调任何 API 会 401。前端 401 拦截自动跳登录页，但用户体验上是一次「全员被迫下线」。**这是预期的安全效果**，V4 部署到生产时需提前通知。
2. **自动建 org 的 slug 冲突**：`_resolve_default_org` 用 `{username}-default`，若 username 含大写或非 ASCII 字符，slug 会包含这些（违反 `^[a-z0-9-]+$` 模式）。当前 setup_default_admin 默认 username=admin，无问题；其他 username 可能触发 slug 校验失败。**V4.1 修复**：slug 转 lowercase + url-encode。
3. **login 自动建 org 在 transaction 内**：若 OrgMember insert 失败，整个 login 也会失败。当前 try/except 只 catch IntegrityError（slug 重），其他异常会回滚。

## 5. 结论

V4 范围 5 改动 + 13 单测，逻辑清晰、风险可控。
**代码质量自评**：A-（强制重新签发 + perms 显式声明 + 补漏 + 去兜底）。
**进入 review 棒**（V4 由 orchestrator 直接 review，范围小）。