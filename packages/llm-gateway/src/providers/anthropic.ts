/**
 * Anthropic provider（私有化网关代理）。
 */

import type { ChatRequest, ChatResponse, LLMClient } from '../index.js';
import { LlmError } from '../index.js';

export class AnthropicClient implements LLMClient {
  readonly provider = 'anthropic';

  constructor(
    private readonly baseUrl: string,
    private readonly apiKey: string,
    private readonly model = 'claude-3-5-sonnet-20241022',
    private readonly timeoutMs = 30000
  ) {}

  async chat(req: ChatRequest): Promise<ChatResponse> {
    const url = `${this.baseUrl}/v1/messages`;
    // Anthropic API: system prompt 单独字段
    const systemMessages = req.messages.filter((m) => m.role === 'system').map((m) => m.content).join('\n');
    const userMessages = req.messages.filter((m) => m.role !== 'system');

    const body = {
      model: this.model,
      system: systemMessages,
      messages: userMessages,
      max_tokens: req.max_tokens ?? 2048,
      temperature: req.temperature ?? 0.2,
    };

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeoutMs);

    try {
      const resp = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': this.apiKey,
          'anthropic-version': '2023-06-01',
        },
        body: JSON.stringify(body),
        signal: controller.signal,
      });

      if (!resp.ok) {
        const text = await resp.text().catch(() => '');
        const retriable = resp.status >= 500 || resp.status === 429;
        throw new LlmError(this.provider, `E_LLM_HTTP_${resp.status}`, text, retriable);
      }

      const data = (await resp.json()) as {
        content: { type: string; text: string }[];
        usage?: { input_tokens?: number; output_tokens?: number };
      };

      const textBlock = data.content.find((c) => c.type === 'text');
      const content = textBlock?.text ?? '';

      return {
        content,
        valid_json: !!req.response_schema && this._tryParseJson(content),
        provider: this.provider,
        usage: data.usage
          ? {
              prompt_tokens: data.usage.input_tokens,
              completion_tokens: data.usage.output_tokens,
              total_tokens: (data.usage.input_tokens ?? 0) + (data.usage.output_tokens ?? 0),
            }
          : undefined,
      };
    } catch (e) {
      if (e instanceof LlmError) throw e;
      if ((e as Error).name === 'AbortError') {
        throw new LlmError(this.provider, 'E_LLM_TIMEOUT', `timeout after ${this.timeoutMs}ms`, true);
      }
      throw new LlmError(this.provider, 'E_LLM_NETWORK', (e as Error).message, true);
    } finally {
      clearTimeout(timer);
    }
  }

  private _tryParseJson(s: string): boolean {
    try {
      JSON.parse(s);
      return true;
    } catch {
      return false;
    }
  }
}