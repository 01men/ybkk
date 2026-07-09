import { describe, it, expect, vi, beforeEach } from 'vitest';
import { LLMGateway } from '../src/gateway';
import { LlmError, type ChatRequest, type ChatResponse } from '../src';

function mockResponse(content: string): ChatResponse {
  return {
    content,
    valid_json: true,
    provider: 'mock',
  };
}

describe('LLMGateway', () => {
  let fetchSpy: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchSpy = vi.fn();
    globalThis.fetch = fetchSpy as unknown as typeof fetch;
  });

  const req: ChatRequest = {
    messages: [{ role: 'user', content: 'hello' }],
  };

  describe('happy path', () => {
    it('uses primary provider', async () => {
      fetchSpy.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          choices: [{ message: { content: 'hi' } }],
          usage: { total_tokens: 10 },
        }),
      } as Response);

      const gw = new LLMGateway({
        primary: 'qwen-local',
        qwen: { baseUrl: 'http://qwen:8000' },
      });

      const r = await gw.chat(req);
      expect(r.content).toBe('hi');
      expect(r.provider).toBe('qwen-local');
      expect(fetchSpy).toHaveBeenCalledOnce();
    });
  });

  describe('retry on retriable error', () => {
    it('retries 3 times then succeeds', async () => {
      fetchSpy
        .mockResolvedValueOnce({ ok: false, status: 503, text: async () => 'down' } as Response)
        .mockResolvedValueOnce({ ok: false, status: 503, text: async () => 'down' } as Response)
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => ({ choices: [{ message: { content: 'recovered' } }] }),
        } as Response);

      const gw = new LLMGateway({
        primary: 'qwen-local',
        qwen: { baseUrl: 'http://qwen:8000' },
        maxRetries: 3,
      });

      const r = await gw.chat(req);
      expect(r.content).toBe('recovered');
      expect(fetchSpy).toHaveBeenCalledTimes(3);
    });

    it('does not retry on non-retriable error (400)', async () => {
      fetchSpy.mockResolvedValueOnce({
        ok: false,
        status: 400,
        text: async () => 'bad request',
      } as Response);

      const gw = new LLMGateway({
        primary: 'qwen-local',
        qwen: { baseUrl: 'http://qwen:8000' },
        maxRetries: 3,
      });

      await expect(gw.chat(req)).rejects.toThrow(LlmError);
      expect(fetchSpy).toHaveBeenCalledOnce();
    });
  });

  describe('fallback', () => {
    it('falls back when primary fails retriably', async () => {
      // primary: 全部 503
      fetchSpy
        .mockResolvedValueOnce({ ok: false, status: 503, text: async () => 'down' } as Response)
        .mockResolvedValueOnce({ ok: false, status: 503, text: async () => 'down' } as Response)
        .mockResolvedValueOnce({ ok: false, status: 503, text: async () => 'down' } as Response)
        // fallback: 成功
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => ({ choices: [{ message: { content: 'from fallback' } }] }),
        } as Response);

      const gw = new LLMGateway({
        primary: 'qwen-local',
        fallback: 'openai',
        qwen: { baseUrl: 'http://qwen:8000' },
        openai: { baseUrl: 'https://api.openai.com', apiKey: 'test' },
        maxRetries: 3,
      });

      const r = await gw.chat(req);
      expect(r.provider).toBe('openai');
      expect(r.content).toBe('from fallback');
    });
  });

  describe('configuration errors', () => {
    it('throws when provider not configured', async () => {
      const gw = new LLMGateway({
        primary: 'openai',
        // 没配 openai
      });

      await expect(gw.chat(req)).rejects.toThrow(/not configured/);
    });
  });
});