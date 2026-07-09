import { test, expect } from '@playwright/test';

test.describe('11 - 组织切换', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.getByPlaceholder('admin').fill('admin');
    await page.getByPlaceholder('请输入密码').fill(process.env.TEST_PASSWORD || 'admin123');
    await page.getByRole('button', { name: '登录' }).click();
  });

  test('组织页可见「我的组织」标题 + 新建按钮', async ({ page }) => {
    await page.goto('/orgs');
    await expect(page.getByText('我的组织')).toBeVisible();
    await expect(page.getByRole('button', { name: '新建组织' })).toBeVisible();
  });

  test('点击「新建组织」弹出 Modal 含 Slug 字段', async ({ page }) => {
    await page.goto('/orgs');
    await page.getByRole('button', { name: '新建组织' }).click();
    await expect(page.getByText('组织名')).toBeVisible();
    await expect(page.getByText('Slug')).toBeVisible();
    await expect(page.getByPlaceholder('例：sz-factory-1')).toBeVisible();
  });

  test('组织页有「成员管理」操作列', async ({ page }) => {
    await page.goto('/orgs');
    // 等待表格加载
    await page.waitForTimeout(500);
    // 操作列标题
    await expect(page.getByText('操作').first()).toBeVisible();
  });
});