import { test, expect } from '@playwright/test';

test.describe('04 - 审计 + 链校验', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.getByPlaceholder('admin').fill('admin');
    await page.getByPlaceholder('请输入密码').fill(process.env.TEST_PASSWORD || 'admin123');
    await page.getByRole('button', { name: '登录' }).click();
  });

  test('审计页 + 校验链按钮可见', async ({ page }) => {
    await page.goto('/audits');
    await expect(page.getByText('审计日志')).toBeVisible();
    await expect(page.getByRole('button', { name: '校验哈希链完整性' })).toBeVisible();
  });
});
