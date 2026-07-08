---
name: coding-conventions
description: 仓库的代码规约总集。所有写代码的 Agent 在写代码前必读。触发词：「代码规范」「命名」「错误处理」「写法约束」。
---

# Coding Conventions

仓库级代码规约。**所有 Agent 在写代码前必读**。Reviewer 对照检查。

---

## 1. 命名约定

| 元素 | 风格 | 示例 |
|---|---|---|
| 变量 / 函数 | camelCase 或 snake_case **按栈选一种** | `userId`（TS） / `user_id`（Python） |
| 类 / 接口 | PascalCase | `UserService` |
| 常量 | UPPER_SNAKE | `MAX_RETRY` |
| 文件名 | 小写连字符（前端）/下划线（后端） | `user-service.ts` / `user_service.py` |
| 数据库表 | snake_case 复数 | `users` |
| URL 路径 | kebab-case 复数 | `/api/user-profiles` |

**混用 = 阻断**。在 PR 审查时发现两种风格混用立即打回。

---

## 2. 目录结构（前端 + 后端典型布局）

```
src/
├── api/                # 接口定义
├── components/         # 组件
├── pages/              # 路由
├── services/           # 业务逻辑
├── models/             # 数据模型 / DTO
├── utils/              # 工具
├── hooks/              # 自定义 hooks
└── types/              # 类型声明
```

后端：

```
src/
├── controllers/        # HTTP 处理层
├── services/           # 业务层
├── repositories/       # 数据访问层
├── models/             # 实体
├── middleware/         # 中间件
├── config/             # 配置
└── utils/
```

**跨层调用是禁止的**：controller 不能直接调 repository，必须经过 service。

---

## 3. 错误处理

- **必须**用项目统一的错误类型（每栈一种），不要直接抛 `Error` / `Exception`
- 每个 catch 块 **必须** 给出处理（重试 / 转换 / 上报），不能吃
- 错误信息 **必须** 含：错误码、可读消息、上下文（userId、reqId）
- **日志** 错误一律：级别 + 错误码 + 用户级消息 + 上下文 + stack trace

```
[ERROR] [E_USER_NOT_FOUND] "用户 12345 未找到" {reqId: "abc", path: "/api/users/12345"}
```

---

## 4. 类型与契约

- 接口入参、出参 **必须** 有显式类型
- 不要用 `any`（TS） / 不要 `from typing import Any` 然后甩
- 数据库字段必须跑 schema（migration 必填）
- API 契约变更必须改 OpenAPI spec

---

## 5. 提交规范

- commit message 格式：`<type>(<req-id>): <desc>`
- type ∈ {feat, fix, refactor, docs, test, chore, style}
- 一次 commit 只做一件事
- 不允许出现 `wip` / `tmp` / `initial commit`（除非是第一次提交）

---

## 6. 覆盖率与质量

- 核心模块（service / business logic）**单测覆盖率 ≥ 80%**
- 其他模块 ≥ 60%
- 任何新功能 必须 包含单测 + E2E
- 公共库（utils/、lib/）修改必须配单测

---

## 7. 禁止项

> 命中任一条 = Reviewer 直接打回

- ❌ 用 `console.log` 提交业务日志（必须用项目 logger）
- ❌ 把 .env 里的 key 写到代码 / 日志 / 注释
- ❌ 直接拼 SQL（必须 ORM）
- ❌ catch 后只 `console.error` 然后继续走
- ❌ 写 `any` 偷懒
- ❌ TODO 大段注释未实现代码
- ❌ 在 PR 里塞 build artifact / node_modules / 凭据

---

## 8. 栈特定细则（按情况追加）

### Next.js
- App Router > Pages Router（新项目必须）
- Server Components 默认，Client Components 标 `'use client'`
- 数据获取用 React Query 或 Server Action，**不要**两套混

### Vue
- Composition API（`<script setup>`）
- Pinia 管状态
- `<style scoped>` 必须

### Python（FastAPI）
- 类型注解必须
- Pydantic 模型做 IO
- 不准 `from typing import Any`

### Go
- 错误用 `fmt.Errorf("...: %w", err)` 包装
- Context 必须传
- 不准 panic 走业务路径

---

## 9. Reviewer 必查项（编号对应 Reviewer 维度）

| 编号 | 维度 | 检查项 |
|---|---|---|
| 1 | 方案一致性 | 改动是不是真在 02-design-doc.md 里 |
| 3 | 质量基线 | 是否符合本 Skill §3/§4/§6 |
