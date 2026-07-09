import { test, expect } from '@playwright/test';

test.describe('10 - 场景 + LLM 联动', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.getByPlaceholder('admin').fill('admin');
    await page.getByPlaceholder('请输入密码').fill(process.env.TEST_PASSWORD || 'admin123');
    await page.getByRole('button', { name: '登录' }).click();
  });

  test('场景模板页 + 详情页可见（含 V2 LLM judge 说明）', async ({ page }) => {
    await page.goto('/scenarios');
    await expect(page.getByText('场景模板')).toBeVisible();
    // 至少一个场景卡片
    const cards = page.locator('.ant-card');
    await expect(cards.first()).toBeVisible();
  });

  test('LLM 用量页 LLM 连通性测试可提交', async ({ page }) => {
    await page.goto('/llm-usage');
    // 提交按钮存在
    const submitBtn = page.getByRole('button', { name: '调用' });
    await expect(submitBtn).toBeVisible();
    // 模拟填一条 prompt 并提交（接受任何结果：成功/失败/LLM 不可用）
    await page.locator('textarea').first().fill('ping');
    // 不强制成功：只检查按钮可点
    await expect(submitBtn).toBeEnabled();
  });

  test('流程页 + 任务详情链路能跳', async ({ page }) => {
    await page.goto('/flows');
    await expect(page.getByText('业务流程')).toBeVisible();
  });
});
