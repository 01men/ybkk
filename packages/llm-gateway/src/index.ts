/**
 * LLM 抽象网关：本地 Qwen / OpenAI / Anthropic 统一接口。
 *
 * 设计原则：
 *  - 私有化优先：默认走本地 Qwen2.5-72B
 *  - 接口统一：所有 provider 实现 LLMClient 接口
 *  - 重试 + 降级：网络错误重试 3 次；最终失败抛 LlmError
 *  - 限流：每分钟 60 次（Redis 计数器，业务层实现）
 */

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface ChatRequest {
  messages: ChatMessage[];
  temperature?: number;
  max_tokens?: number;
  /** 响应 JSON schema（约束结构化输出）*/
  response_schema?: Record<string, unknown>;
}

export interface ChatResponse {
  content: string;
  /** 是否通过 JSON schema 校验（仅当传了 schema）*/
  valid_json: boolean;
  /** 实际 provider */
  provider: string;
  /** 用量 */
  usage?: {
    prompt_tokens?: number;
    completion_tokens?: number;
    total_tokens?: number;
  };
}

export interface LLMClient {
  readonly provider: string;
  chat(req: ChatRequest): Promise<ChatResponse>;
}

export class LlmError extends Error {
  constructor(
    public readonly provider: string,
    public readonly code: string,
    message: string,
    public readonly retriable: boolean
  ) {
    super(message);
    this.name = 'LlmError';
  }
}

export * from './providers/qwen-local.js';
export * from './providers/openai.js';
export * from './providers/anthropic.js';
export * from './gateway.js';