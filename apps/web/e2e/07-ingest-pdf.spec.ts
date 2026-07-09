import { test, expect } from '@playwright/test';

test.describe('07 - 摄取 PDF', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.getByPlaceholder('admin').fill('admin');
    await page.getByPlaceholder('请输入密码').fill(process.env.TEST_PASSWORD || 'admin123');
    await page.getByRole('button', { name: '登录' }).click();
  });

  test('切到 PDF tab 后显示 PDF 描述', async ({ page }) => {
    await page.goto('/ingest');
    await page.getByRole('tab', { name: /PDF/ }).click();
    await expect(page.getByText('PDF 工艺文件')).toBeVisible();
    await expect(page.getByText(/工艺规范|操作手册|SOP/)).toBeVisible();
    await expect(page.getByText('选择 PDF 工艺文件 文件')).toBeVisible();
  });

  test('切到会议 tab 显示 ASR 提示', async ({ page }) => {
    await page.goto('/ingest');
    await page.getByRole('tab', { name: /会议/ }).click();
    await expect(page.getByText(/转写.*whisper|whisper.*阿里云/)).toBeVisible();
  });

  test('切到 Markdown tab 显示规范说明', async ({ page }) => {
    await page.goto('/ingest');
    await page.getByRole('tab', { name: /Markdown/ }).click();
    await expect(page.getByText(/制度|流程|规范/)).toBeVisible();
  });
});
