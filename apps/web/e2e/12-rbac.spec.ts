import { test, expect } from '@playwright/test';

test.describe('12 - RBAC 权限', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.getByPlaceholder('admin').fill('admin');
    await page.getByPlaceholder('请输入密码').fill(process.env.TEST_PASSWORD || 'admin123');
    await page.getByRole('button', { name: '登录' }).click();
  });

  test('菜单「监控」对 admin 可见', async ({ page }) => {
    await expect(page.getByRole('link', { name: '监控' })).toBeVisible();
  });

  test('菜单「组织」对 admin 可见', async ({ page }) => {
    await expect(page.getByRole('link', { name: '组织' })).toBeVisible();
  });

  test('顶部显示当前角色 tag', async ({ page }) => {
    // 等 /auth/me 加载完，顶部应出现 role tag
    await page.waitForTimeout(800);
    const headerTag = page.locator('header').getByText(/admin|engineer|operator|viewer/).first();
    await expect(headerTag).toBeVisible();
  });

  test('菜单「审计日志」可见（admin 拥有 audit.read）', async ({ page }) => {
    await expect(page.getByRole('link', { name: '审计日志' })).toBeVisible();
  });
});