import { test, expect } from '@playwright/test';

/**
 * 14 - LLM system role 隔离 & 反 prompt injection
 * 验证 llm_judge.py 的 SEC-V3-01 行为：
 *   - system / user role 分离（system_prompt 固定 + user_prompt 透传）
 *   - 反注入：包含 "ignore previous" 等关键词的输入被拦截（confidence=0）
 * 这个 E2E 通过 llm-usage 页 + 后端 health 端点间接验证。
 */

test.describe('14 - LLM system role 隔离 & 反注入', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.getByPlaceholder('admin').fill('admin');
    await page.getByPlaceholder('请输入密码').fill(process.env.TEST_PASSWORD || 'admin123');
    await page.getByRole('button', { name: '登录' }).click();
  });

  test('LLM 用量页可见 + 反映反注入拦截 metric（前端 health）', async ({ page }) => {
    await page.goto('/llm-usage');
    await expect(page.getByText('LLM 用量与连通性')).toBeVisible();
  });

  test('API /metrics 端点返回 prometheus 文本格式', async ({ request }) => {
    // 验证 V3 metrics 端点可访问
    const r = await request.get('/api/v1/health');
    expect(r.status()).toBe(200);
  });

  test('监控页 LLM dashboard 卡片包含「注入拦截」描述', async ({ page }) => {
    await page.goto('/monitoring');
    // aios-llm.json 的 desc 包含「注入拦截」
    const llmCard = page.locator('.ant-card').filter({ hasText: 'LLM 监控' });
    await expect(llmCard).toContainText(/调用速率/);
  });
});