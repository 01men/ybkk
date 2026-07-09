import { test, expect } from '@playwright/test';

test.describe('08 - 本体浏览', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.getByPlaceholder('admin').fill('admin');
    await page.getByPlaceholder('请输入密码').fill(process.env.TEST_PASSWORD || 'admin123');
    await page.getByRole('button', { name: '登录' }).click();
  });

  test('本体浏览页可见 10 类节点统计卡片', async ({ page }) => {
    await page.goto('/ontology');
    await expect(page.getByText('本体浏览')).toBeVisible();
    for (const label of [
      '物料',
      '供应商',
      '仓库',
      '设备',
      '订单',
      '工艺流程',
      '工序',
      '交付标准',
      '业务规则',
      '角色',
    ]) {
      await expect(page.getByText(label).first()).toBeVisible();
    }
  });

  test('Neo4j Browser 折叠项', async ({ page }) => {
    await page.goto('/ontology');
    await expect(page.getByText(/Neo4j Browser/)).toBeVisible();
  });

  test('点类型卡片可筛选（点物料）', async ({ page }) => {
    await page.goto('/ontology');
    // 直接选物料标签更稳定
    await page.locator('.ant-card').filter({ hasText: '物料' }).first().click();
    // 至少表格不报错
    await expect(page.locator('table').first()).toBeVisible({ timeout: 10_000 });
  });
});
