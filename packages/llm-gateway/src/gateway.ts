/**
 * LLM 网关：选择 provider + 重试 + 降级。
 */

import type { ChatRequest, ChatResponse, LLMClient } from '../index.js';
import { LlmError } from '../index.js';
import { QwenLocalClient } from './providers/qwen-local.js';
import { OpenAIClient } from './providers/openai.js';
import { AnthropicClient } from './providers/anthropic.js';

export interface GatewayConfig {
  primary: 'qwen-local' | 'openai' | 'anthropic';
  fallback?: 'qwen-local' | 'openai' | 'anthropic';
  qwen?: { baseUrl: string };
  openai?: { baseUrl: string; apiKey: string; model?: string };
  anthropic?: { baseUrl: string; apiKey: string; model?: string };
  maxRetries?: number;
}

export class LLMGateway {
  private readonly clients: Map<string, LLMClient>;
  private readonly maxRetries: number;

  constructor(private readonly config: GatewayConfig) {
    this.maxRetries = config.maxRetries ?? 3;
    this.clients = new Map();

    if (config.qwen) {
      this.clients.set('qwen-local', new QwenLocalClient(config.qwen.baseUrl));
    }
    if (config.openai) {
      this.clients.set('openai', new OpenAIClient(
        config.openai.baseUrl,
        config.openai.apiKey,
        config.openai.model,
      ));
    }
    if (config.anthropic) {
      this.clients.set('anthropic', new AnthropicClient(
        config.anthropic.baseUrl,
        config.anthropic.apiKey,
        config.anthropic.model,
      ));
    }
  }

  async chat(req: ChatRequest): Promise<ChatResponse> {
    // 1. 主 provider + 重试
    try {
      return await this.callWithRetry(this.config.primary, req);
    } catch (e) {
      if (!(e instanceof LlmError) || !e.retriable) throw e;
      if (!this.config.fallback || this.config.fallback === this.config.primary) throw e;

      // 2. 降级 provider
      return await this.callWithRetry(this.config.fallback, req);
    }
  }

  private async callWithRetry(provider: string, req: ChatRequest): Promise<ChatResponse> {
    const client = this.clients.get(provider);
    if (!client) {
      throw new LlmError(provider, 'E_LLM_NOT_CONFIGURED', `provider ${provider} not configured`, false);
    }

    let lastError: Error | null = null;
    for (let attempt = 1; attempt <= this.maxRetries; attempt++) {
      try {
        return await client.chat(req);
      } catch (e) {
        lastError = e as Error;
        if (e instanceof LlmError && !e.retriable) throw e;
        if (attempt < this.maxRetries) {
          const delay = Math.min(2 ** attempt * 100, 5000);
          await new Promise((r) => setTimeout(r, delay));
        }
      }
    }
    throw lastError ?? new LlmError(provider, 'E_LLM_UNKNOWN', 'unknown error', true);
  }
}