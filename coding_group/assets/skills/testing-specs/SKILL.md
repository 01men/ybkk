---
name: testing-specs
description: 测试规范总集。developer 写测试、reviewer 审查测试时用。触发词：「单测」「E2E」「覆盖率」「测试规范」。
---

# Testing Specs

## 测试金字塔

| 层级 | 数量 | 速度 | 覆盖 |
|---|---|---|---|
| 单元测试 | 多 | 极快（< 10ms/case） | 业务逻辑、工具函数 |
| 集成测试 | 中 | 快（< 500ms/case） | 模块交互、数据库、缓存 |
| E2E 测试 | 少 | 慢（秒级） | 关键用户路径 |

---

## 单元测试规范

### 必须覆盖的场景

- **正常路径**（happy path）
- **边界条件**（空数组、极大、极小、刚好）
- **错误路径**（异常输入、依赖挂掉、超时）
- **状态转换**（状态机的每个转移）

### 命名约定

```
<file>.test.ts
<methodName>_should_<expectedBehavior>_when_<condition>
```

例：`calculateDiscount_should_returnZero_when_amountIsNegative`

### Mock 原则

- 外部依赖（HTTP、DB、文件系统）必须 mock
- 内部调用可以 mock，但优先用真实对象（更可靠）
- Mock 必须验证「被调用了 + 用对了入参」
- **不要 mock 你自己写的代码**

---

## E2E 测试规范

### 工具选择（按栈）

| 栈 | 推荐 |
|---|---|
| Web（TS / Vue / React） | Playwright（首选） / Cypress |
| 移动端 | Detox / Maestro |
| API | Playwright + REST client / k6（负载） |

### 关键路径覆盖清单

每个需求 **至少** 跑过：

```
PRD §4 验收标准里的每一条 → 一个 E2E case
```

### Playwright 范例

```typescript
import { test, expect } from '@playwright/test';

test('REQ-XXX: 输入 URL 5 秒内返回截图', async ({ page }) => {
  await page.goto('https://example.com/p/<id>');
  await page.fill('input[name=url]', 'https://example.com');
  await page.click('button[type=submit]');
  await expect(page.locator('img.screenshot')).toBeVisible({ timeout: 5000 });
});
```

---

## 覆盖率门槛

| 模块 | 门槛 |
|---|---|
| core（业务核心） | ≥ 80% |
| service | ≥ 80% |
| utils / lib | ≥ 90% |
| components（前端） | ≥ 70% |
| controllers / handlers | ≥ 60% |
| 总体 | ≥ 60% |

门禁脚本 `scripts/gates/gate-coverage.sh` 会强制执行。

---

## 测试数据原则

- 测试必须有显式数据，**不能用 `Math.random()`**
- 时区无关化：所有时间用 UTC，UI 显示再用本地
- 不要依赖外部网络（用 mock server、fixture）
- 测试间共享的 fixture 放在 `tests/fixtures/`，**单一来源**

---

## 测试运行规则

- 单测：每次提交前必跑
- 集成测试：合并前必跑
- E2E：合并到 main 前必跑
- 性能测试（k6）：重大变更必跑

---

## 测试类找不到的常见坑

- ❌ Mock 写在了生产代码里（编译时被一起打包） → 用 `jest.mock` / `vi.mock` 写在测试文件
- ❌ 测试只覆盖 happy path → 边界 + 错误路径必跑
- ❌ E2E 跑得太慢（> 5 分钟）→ 拆用例，并行跑
- ❌ 同一份测试数据被多 case 改 → 每个 case 用独立数据

---

## 调试失败用例

- 单测：加 `console.log` 输出关键状态
- E2E：用 `await page.screenshot()` 截图归档
- 常用调试技巧详见 `09-runbook.md` §3
