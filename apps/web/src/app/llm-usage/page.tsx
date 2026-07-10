'use client';

import { App, Button, Card, Col, Form, Input, Row, Space, Statistic, Table, Tag, Typography } from 'antd';
import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import ConsoleShell from '@/components/console-shell';
import { api } from '@/lib/api';

type Usage = {
  total_calls: number;
  total_input_tokens: number;
  total_output_tokens: number;
  total_cost_usd: number;
  by_provider: Record<string, { calls: number; input_tokens: number; output_tokens: number; cost_usd: number }>;
};

type TestResp = {
  response: string;
  duration_ms: number;
};

const PROVIDER_COLOR: Record<string, string> = {
  'qwen-local': 'blue',
  dashscope: 'purple',
  openai: 'green',
  anthropic: 'orange',
};

const PROVIDER_LABEL: Record<string, string> = {
  'qwen-local': 'Qwen 鏈湴',
  dashscope: '闃块噷浜?DashScope',
  openai: 'OpenAI',
  anthropic: 'Anthropic',
};

export default function LLMUsagePage() {
  const { message } = App.useApp();
  const [form] = Form.useForm();
  const [testResp, setTestResp] = useState<TestResp | null>(null);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['llm-usage'],
    queryFn: async () => (await api.get<Usage>('/llm/usage')).data,
  });

  const testMut = useMutation({
    mutationFn: async (vals: { prompt: string; provider: string }) =>
      (await api.post<TestResp>('/llm/test', vals)).data,
    onSuccess: (r) => {
      setTestResp(r);
      message.success(`璋冪敤鎴愬姛锛岃€楁椂 ${r.duration_ms} ms`);
    },
    onError: (e: unknown) => {
      const m = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? '璋冪敤澶辫触';
      message.error(m);
    },
  });

  return (
    <ConsoleShell>
      <Typography.Title level={3}>LLM 鐢ㄩ噺涓庤繛閫氭€?/Typography.Title>
      <Typography.Paragraph type="secondary">
        V2 鎺ュ叆 4 涓?LLM provider锛歈wen 鏈湴锛堥粯璁わ級/ 闃块噷浜?DashScope / OpenAI / Anthropic銆傚け璐ヨ嚜鍔?fallback銆?        鎵€鏈夎皟鐢ㄩ兘璁板叆 llm_calls 琛紙鎸?provider 缁熻锛夈€?      </Typography.Paragraph>

      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic title="鎬昏皟鐢ㄦ鏁? value={data?.total_calls ?? 0} />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic title="杈撳叆 token" value={data?.total_input_tokens ?? 0} />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic title="杈撳嚭 token" value={data?.total_output_tokens ?? 0} />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic
              title="鎬绘垚鏈?(USD)"
              value={data?.total_cost_usd ?? 0}
              precision={4}
              prefix="$"
            />
          </Card>
        </Col>
      </Row>

      <Card title="鎸?Provider 鍒嗙粍" style={{ marginBottom: 16 }} loading={isLoading}>
        <Table
          dataSource={Object.entries(data?.by_provider ?? {}).map(([k, v]) => ({ provider: k, ...v }))}
          rowKey="provider"
          size="small"
          pagination={false}
          columns={[
            {
              title: 'Provider',
              dataIndex: 'provider',
              width: 200,
              render: (p: string) => (
                <Tag color={PROVIDER_COLOR[p] ?? 'default'}>{PROVIDER_LABEL[p] ?? p}</Tag>
              ),
            },
            { title: '璋冪敤娆℃暟', dataIndex: 'calls', width: 100, align: 'right' },
            { title: '杈撳叆 token', dataIndex: 'input_tokens', width: 120, align: 'right' },
            { title: '杈撳嚭 token', dataIndex: 'output_tokens', width: 120, align: 'right' },
            {
              title: '鎴愭湰 (USD)',
              dataIndex: 'cost_usd',
              width: 120,
              align: 'right',
              render: (v: number) => `$${v.toFixed(4)}`,
            },
          ]}
        />
      </Card>

      <Card title="LLM 杩為€氭€ф祴璇?>
        <Form
          form={form}
          layout="vertical"
          onFinish={(v) => testMut.mutate(v)}
          initialValues={{ provider: 'qwen-local', prompt: '鐢ㄤ竴鍙ヨ瘽浠嬬粛鍏冨啺鍙彲 AIOS銆? }}
        >
          <Row gutter={16}>
            <Col xs={24} md={8}>
              <Form.Item label="Provider" name="provider">
                <Space.Compact style={{ width: '100%' }}>
                  {(['qwen-local', 'dashscope', 'openai', 'anthropic'] as const).map((p) => (
                    <Button
                      key={p}
                      type={form.getFieldValue('provider') === p ? 'primary' : 'default'}
                      onClick={() => form.setFieldsValue({ provider: p })}
                    >
                      {p}
                    </Button>
                  ))}
                </Space.Compact>
              </Form.Item>
            </Col>
            <Col xs={24} md={16}>
              <Form.Item label="Prompt" name="prompt" rules={[{ required: true }]}>
                <Input.TextArea rows={2} placeholder="杈撳叆娴嬭瘯 prompt..." />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={testMut.isPending}>
                璋冪敤
              </Button>
              <Button onClick={() => refetch()}>鍒锋柊鐢ㄩ噺</Button>
            </Space>
          </Form.Item>
        </Form>
        {testResp && (
          <Card type="inner" title={`鍝嶅簲锛?{testResp.duration_ms} ms锛塦} style={{ marginTop: 16, background: '#fafafa' }}>
            <pre style={{ whiteSpace: 'pre-wrap', margin: 0 }}>{testResp.response}</pre>
          </Card>
        )}
      </Card>
    </ConsoleShell>
  );
}
