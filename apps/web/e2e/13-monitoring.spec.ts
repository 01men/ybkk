import { test, expect } from '@playwright/test';

test.describe('13 - 监控页', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.getByPlaceholder('admin').fill('admin');
    await page.getByPlaceholder('请输入密码').fill(process.env.TEST_PASSWORD || 'admin123');
    await page.getByRole('button', { name: '登录' }).click();
  });

  test('监控页可见「监控仪表盘」标题', async ({ page }) => {
    await page.goto('/monitoring');
    await expect(page.getByText('监控仪表盘')).toBeVisible();
  });

  test('5 个 dashboard 卡片可见', async ({ page }) => {
    await page.goto('/monitoring');
    await expect(page.getByText('API 监控')).toBeVisible();
    await expect(page.getByText('Flow 监控')).toBeVisible();
    await expect(page.getByText('LLM 监控')).toBeVisible();
    await expect(page.getByText('Ingest 监控')).toBeVisible();
    await expect(page.getByText('Ontology & System 监控')).toBeVisible();
  });

  test('每个 dashboard 卡片有「打开 ↗」链接', async ({ page }) => {
    await page.goto('/monitoring');
    const openLinks = page.getByText('打开 ↗');
    await expect(openLinks.first()).toBeVisible();
    expect(await openLinks.count()).toBeGreaterThanOrEqual(5);
  });

  test('Prometheus 状态卡片可见', async ({ page }) => {
    await page.goto('/monitoring');
    await expect(page.getByText('Prometheus 状态')).toBeVisible();
  });
});