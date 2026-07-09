import { test, expect } from '@playwright/test';

test.describe('05 - 流程页', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.getByPlaceholder('admin').fill('admin');
    await page.getByPlaceholder('请输入密码').fill(process.env.TEST_PASSWORD || 'admin123');
    await page.getByRole('button', { name: '登录' }).click();
  });

  test('业务流程页可见', async ({ page }) => {
    await page.goto('/flows');
    await expect(page.getByText('业务流程')).toBeVisible();
  });
});
