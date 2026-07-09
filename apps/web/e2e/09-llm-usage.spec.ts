import { test, expect } from '@playwright/test';

test.describe('09 - LLM 用量', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.getByPlaceholder('admin').fill('admin');
    await page.getByPlaceholder('请输入密码').fill(process.env.TEST_PASSWORD || 'admin123');
    await page.getByRole('button', { name: '登录' }).click();
  });

  test('LLM 用量页可见 4 个统计卡片', async ({ page }) => {
    await page.goto('/llm-usage');
    await expect(page.getByText('LLM 用量与连通性')).toBeVisible();
    await expect(page.getByText('总调用次数')).toBeVisible();
    await expect(page.getByText('输入 token')).toBeVisible();
    await expect(page.getByText('输出 token')).toBeVisible();
    await expect(page.getByText('总成本 (USD)')).toBeVisible();
  });

  test('4 个 provider 按钮可点', async ({ page }) => {
    await page.goto('/llm-usage');
    await expect(page.getByRole('button', { name: 'qwen-local' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'dashscope' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'openai' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'anthropic' })).toBeVisible();
  });

  test('按 Provider 分组表头可见', async ({ page }) => {
    await page.goto('/llm-usage');
    await expect(page.getByText('按 Provider 分组')).toBeVisible();
  });
});
