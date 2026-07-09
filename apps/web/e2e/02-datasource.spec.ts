import { test, expect } from '@playwright/test';

test.describe('02 - 数据源', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.getByPlaceholder('admin').fill('admin');
    await page.getByPlaceholder('请输入密码').fill(process.env.TEST_PASSWORD || 'admin123');
    await page.getByRole('button', { name: '登录' }).click();
    await expect(page).toHaveURL(/\/datasources/);
  });

  test('新建数据源表单可填', async ({ page }) => {
    await page.goto('/datasources/new');
    await expect(page.getByText('新建数据源')).toBeVisible();
    await page.getByPlaceholder('db.example.com').fill('localhost');
    await page.getByPlaceholder('readonly_user').fill('readonly');
    await page.getByLabel('数据库').fill('test');
    // 勾选只读确认
    await page.getByLabel(/我确认此账号仅有只读权限/).check();
    await expect(page.getByRole('button', { name: '提交' })).toBeVisible();
  });
});
