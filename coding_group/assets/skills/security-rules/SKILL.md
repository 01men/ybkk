---
name: security-rules
description: 仓库的安全编码规约。developer 写代码前必读；reviewer 审查时必查。触发词：「安全」「鉴权」「脱敏」「限流」。
---

# Security Rules

## 1. 鉴权（Authentication & Authorization）

| 规则 | 描述 |
|---|---|
| 默认拒绝 | 默认所有 endpoint 不带权限，**显式声明**才开放 |
| 不信前端 | 用户身份以服务端为准，不要从 header / query 拿 userId |
| 权限校验在入口 | 鉴权放在 controller / middleware 不放在 service |
| 角色最小化 | 业务代码只用必要的角色，不要请求 `*` |

**反例（必打回）**：

```typescript
// ❌ 把 userId 从 query 拿
const userId = req.query.userId;

// ✅ 从服务端会话拿
const userId = req.session.userId;
```

---

## 2. 输入校验

| 规则 | 描述 |
|---|---|
| 所有入参 schema 校验 | 用 Zod / Joi / Pydantic，**不要相信任何输入** |
| 长度限制 | 字符串字段必有 `max` |
| 类型强制 | 数字字段必显式 `Number()` 或类型转换 |
| 路径参数校验 | URL path 里的 `:id` 必校验 |

**反例**：

```typescript
// ❌ 不校验
app.post('/api/users', (req) => {
  db.users.create(req.body);  // 任意字段灌进来
});

// ✅ 校验
app.post('/api/users', (req) => {
  const data = UserCreateSchema.parse(req.body);
  db.users.create(data);
});
```

---

## 3. SQL 注入防御

- ❌ 直接拼 SQL
- ✅ ORM 或参数化查询

```python
# ❌
db.execute(f"SELECT * FROM users WHERE id = {user_id}")

# ✅
db.execute("SELECT * FROM users WHERE id = %s", (user_id,))
```

---

## 4. XSS / CSRF

- 输出到 HTML 的字符串必转义（用框架默认转义；不要 dangerouslySetInnerHTML）
- 表单 / 状态变更请求必带 CSRF token
- Cookie 设 `HttpOnly`、`Secure`、`SameSite=Lax` 三件套

---

## 5. 敏感数据保护

| 类别 | 处理 |
|---|---|
| 密码 | bcrypt / argon2，**绝不**明文、绝不 MD5 |
| API Key | 放在 `.env`，部署平台 secret，绝不入库 |
| 用户身份证 / 手机 / 银行卡 | 加密存储；查询要脱敏 |
| 日志 | 永远不打印密码、token、完整卡号 |

**反例**：

```python
# ❌ 把密码打日志
logger.info(f"User login: {user.email}, password={user.password}")

# ✅
logger.info(f"User login: {user.email}, attempt=ok")
```

---

## 6. 限流

| 场景 | 建议值 |
|---|---|
| 登录接口 | 5 次 / 分钟 / IP |
| 注册接口 | 3 次 / 小时 / IP |
| 短信 / 邮件接口 | 1 次 / 分钟 / 用户 |
| 通用 API | 100 次 / 分钟 / 用户 |
| 写操作更严 | 上限 = 通用 × 0.1 |

实现：用 Redis 计数器 + Lua 脚本原子化。

---

## 7. 审计与日志

- 关键操作（登录、改密、删数据、支付）**必**有审计日志
- 审计日志含：时间、用户、动作、对象、结果、IP
- 审计日志独立表 / 服务，**不要**混在业务日志里

---

## 8. 依赖安全

- 每 1 周跑一次 `npm audit` / `pip audit` / `go mod tidy`
- 高风险依赖（< 100 stars 或 半年没更新）必须升级或替换
- 镜像基础镜像必用官方、用 `sha256:` 锁定版本

---

## 9. 上线前安全清单

- [ ] OWASP Top 10 自查过
- [ ] 凭据未进 git
- [ ] 凭据未进日志 / 监控数据
- [ ] 高风险 endpoint 有显式鉴权
- [ ] 入参 schema 校验
- [ ] 限流配齐
- [ ] 审计日志有
- [ ] 依赖扫描过

---

## Reviewer 强化提示

任何以下情况 → 直接打回：

- ❌ `req.query.userId` 之类的「前端传身份」
- ❌ 任何明文密码 / token 出现在代码或日志
- ❌ 任何新增 endpoint 没鉴权没 schema
- ❌ 任何 `.env` 进了 git
- ❌ 任何 `npm audit` 高风险未处理
