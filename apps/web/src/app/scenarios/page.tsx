'use client';

import { App, Card, Col, Row, Tag, Typography } from 'antd';
import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import ConsoleShell from '@/components/console-shell';
import { api } from '@/lib/api';

type Scenario = {
  id: string;
  key: string;
  name: string;
  industry: string;
  description: string | null;
  default_standard_keys: string[];
  flow_template: unknown;
  built_in: boolean;
};

const COLORS: Record<string, string> = {
  inventory: 'blue',
  equipment: 'green',
  quality: 'purple',
  production: 'orange',
  inbound: 'red',
};

function colorFor(key: string): string {
  for (const k of Object.keys(COLORS)) {
    if (key.toLowerCase().includes(k)) return COLORS[k]!;
  }
  return 'default';
}

export default function ScenariosPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['scenarios'],
    queryFn: async () => (await api.get<Scenario[]>('/scenarios')).data,
  });

  return (
    <ConsoleShell>
      <Typography.Title level={3}>鍦烘櫙妯℃澘</Typography.Title>
      <Row gutter={[16, 16]}>
        {(data ?? []).map((s) => (
          <Col key={s.key} xs={24} sm={12} md={8} lg={6}>
            <Card
              loading={isLoading}
              title={
                <span>
                  <Tag color={colorFor(s.key)}>{s.industry}</Tag>
                  {s.name}
                </span>
              }
              extra={<Link href={`/scenarios/${s.key}`}>璇︽儏</Link>}
            >
              <Typography.Paragraph type="secondary" ellipsis={{ rows: 3 }}>
                {s.description ?? '鈥?}
              </Typography.Paragraph>
              <div style={{ fontSize: 12, color: '#999' }}>
                鍖呭惈 {s.default_standard_keys.length} 涓爣鍑?路 {s.built_in ? '鍐呯疆' : '鑷畾涔?}
              </div>
            </Card>
          </Col>
        ))}
      </Row>
    </ConsoleShell>
  );
}
