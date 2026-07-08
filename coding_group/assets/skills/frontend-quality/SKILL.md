---
name: frontend-quality
description: 前端审查清单。涉及前端的改动在 review 时必跑。触发词：「前端审查」「UI 审查」「DOM 审查」「视觉回归」。
---

# Frontend Quality

> 用于 review 任何带前端的改动。在跑 Playwright E2E 时必触发。

---

## 1. 路由级渲染

每个新路由 / 修改路由：

- [ ] 桌面 1920×1080 渲染正常（无横向滚动条）
- [ ] 平板 768×1024 渲染正常
- [ ] 手机 375×667 渲染正常
- [ ] 未登录访问受保护路由 → 跳转 / 提示
- [ ] 已登录访问公开路由 → 不出问题

---

## 2. DOM 断言

每个改动页面的关键元素：

- [ ] 标题（h1）可见且文案正确
- [ ] 主交互按钮可见且可点
- [ ] 表单校验错误可见（验证一次故意填错）
- [ ] 列表项数与预期一致
- [ ] 图片 / icon 全部加载（无 404）

---

## 3. 控制台

- [ ] 无 JS 报错
- [ ] 无 404 / 5xx 请求
- [ ] 无未处理的 Promise rejection
- [ ] 无 React/Vue warning
- [ ] 网络请求数量合理（不能一个操作触发 N 次请求）

---

## 4. 性能

- [ ] 首屏 < 3s（4G 模拟）
- [ ] 交互响应 < 100ms（P95）
- [ ] 内存无明显泄漏（连续操作不增长）
- [ ] 打包体积无暴增（>+ 30% 必查）

---

## 5. 可访问性（最小集）

- [ ] 所有交互元素可键盘操作（tab order 合理）
- [ ] 图片有 alt
- [ ] 表单有 label
- [ ] 色彩对比度 ≥ 4.5:1
- [ ] 焦点状态可见

---

## 6. 视觉回归（用 Playwright screenshot diff）

```typescript
import { test, expect } from '@playwright/test';

test('REQ-XXX: 页面截图与基线一致', async ({ page }) => {
  await page.goto('https://example.com/p/<id>');
  await expect(page).toHaveScreenshot('page.png', {
    maxDiffPixels: 500,  // 差异 ≥ 500 像素阻断
    threshold: 0.2,
  });
});
```

基线截图存在 `tests/e2e/screenshots/baseline/`。
新增截图 → 自动存为新基线（人工 approve 后才生效）。

---

## 7. 无障碍 / 国际化

如果是面向用户的功能：

- [ ] 支持中文（默认）
- [ ] 支持英文（i18n 抽出）
- [ ] 日期 / 数字本地化
- [ ] 文案里没有开发者黑话（「404」「null」「undefined」）

---

## 8. 移动端特有

涉及移动端时：

- [ ] viewport meta 正确
- [ ] touch target ≥ 44px
- [ ] 软键盘弹出时不遮挡输入
- [ ] iOS Safari / Android Chrome 兼容

---

## Reviewer 的关键差异点

> 前端审查不像后端那样可以靠行覆盖判断。**视觉、可用性、性能必须由 Playwright / 真实浏览器跑过才算**。

因此：

- 没有跑过 Playwright 的改动 → 不算审查完成
- 视觉有差异且没在基线审批流程内 → 打回
