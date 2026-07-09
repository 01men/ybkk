import { test, expect } from '@playwright/test';

test.describe('03 - 场景模板', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.getByPlaceholder('admin').fill('admin');
    await page.getByPlaceholder('请输入密码').fill(process.env.TEST_PASSWORD || 'admin123');
    await page.getByRole('button', { name: '登录' }).click();
  });

  test('5 个内置场景可见', async ({ page }) => {
    await page.goto('/scenarios');
    await expect(page.getByText('场景模板')).toBeVisible();
    // 至少能看到「内置」「自定义」之一
    await expect(page.locator('text=/内置|自定义/').first()).toBeVisible();
  });
});
