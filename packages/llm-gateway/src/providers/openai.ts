/**
 * OpenAI provider（私有化网关代理）。
 */

import type { ChatRequest, ChatResponse, LLMClient } from '../index.js';
import { LlmError } from '../index.js';

export class OpenAIClient implements LLMClient {
  readonly provider = 'openai';

  constructor(
    private readonly baseUrl: string,
    private readonly apiKey: string,
    private readonly model = 'gpt-4o-mini',
    private readonly timeoutMs = 30000
  ) {}

  async chat(req: ChatRequest): Promise<ChatResponse> {
    const url = `${this.baseUrl}/chat/completions`;
    const body = {
      model: this.model,
      messages: req.messages,
      temperature: req.temperature ?? 0.2,
      max_tokens: req.max_tokens ?? 2048,
      response_format: req.response_schema ? { type: 'json_object' } : undefined,
    };

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeoutMs);

    try {
      const resp = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${this.apiKey}`,
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
        choices: { message: { content: string } }[];
        usage?: { prompt_tokens?: number; completion_tokens?: number; total_tokens?: number };
      };

      const content = data.choices[0]?.message.content ?? '';

      return {
        content,
        valid_json: !!req.response_schema && this._tryParseJson(content),
        provider: this.provider,
        usage: data.usage,
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