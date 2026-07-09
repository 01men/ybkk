import { test, expect } from '@playwright/test';

/**
 * 15 - Ollama auto pull (OPS-V3-02)
 * 验证 apps/ollama/entrypoint.sh 启动后，qwen2.5:7b 模型已 pull。
 * E2E 通过后端 health + llm-usage 按钮间接验证；纯端到端需要 docker compose up。
 */

test.describe('15 - Ollama 自动 pull', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.getByPlaceholder('admin').fill('admin');
    await page.getByPlaceholder('请输入密码').fill(process.env.TEST_PASSWORD || 'admin123');
    await page.getByRole('button', { name: '登录' }).click();
  });

  test('API /health 端点 200（验证 ollama 通）', async ({ request }) => {
    const r = await request.get('/api/v1/health');
    expect(r.status()).toBe(200);
  });

  test('监控页 ontology dashboard 提到 Ollama 健康', async ({ page }) => {
    await page.goto('/monitoring');
    const card = page.locator('.ant-card').filter({ hasText: 'Ontology' });
    await expect(card).toContainText(/Ollama/);
  });

  test('LLM 用量页 qwen-local 按钮存在（与 ollama qwen2.5:7b 对应）', async ({ page }) => {
    await page.goto('/llm-usage');
    await expect(page.getByRole('button', { name: 'qwen-local' })).toBeVisible();
  });
});