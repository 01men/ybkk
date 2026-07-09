import { test, expect } from '@playwright/test';

test.describe('06 - 摄取 Excel', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.getByPlaceholder('admin').fill('admin');
    await page.getByPlaceholder('请输入密码').fill(process.env.TEST_PASSWORD || 'admin123');
    await page.getByRole('button', { name: '登录' }).click();
  });

  test('数据接入 4 tab + 任务详情页', async ({ page }) => {
    await page.goto('/ingest');
    await expect(page.getByText('数据接入')).toBeVisible();
    // 4 tab 标题
    await expect(page.getByText('Excel 表格')).toBeVisible();
    await expect(page.getByText('PDF 工艺文件')).toBeVisible();
    await expect(page.getByText('会议录音')).toBeVisible();
    await expect(page.getByText('Markdown 规范')).toBeVisible();
  });

  test('摄取任务列表页', async ({ page }) => {
    await page.goto('/ingest/jobs');
    await expect(page.getByText('摄取任务')).toBeVisible();
    await expect(page.getByText('历史任务（5s 自动刷新）')).toBeVisible();
  });

  test('任务详情页（不存在的 ID 显示 404）', async ({ page }) => {
    await page.goto('/ingest/jobs/00000000-0000-0000-0000-000000000000');
    await expect(page.getByText('任务不存在')).toBeVisible({ timeout: 10_000 });
  });
});
