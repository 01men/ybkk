'use client';

import { App, Card, Descriptions, Tag, Typography } from 'antd';
import { useQuery } from '@tanstack/react-query';
import { useParams } from 'next/navigation';
import ConsoleShell from '@/components/console-shell';
import { api } from '@/lib/api';

type Scenario = {
  id: string;
  key: string;
  name: string;
  industry: string;
  description: string | null;
  default_standard_keys: string[];
  flow_template: { id: string; standard_key: string }[];
  built_in: boolean;
};

export default function ScenarioDetailPage() {
  const params = useParams<{ key: string }>();
  const { data, isLoading } = useQuery({
    queryKey: ['scenarios', params.key],
    queryFn: async () => (await api.get<Scenario>(`/scenarios/${params.key}`)).data,
  });

  return (
    <ConsoleShell>
      {data ? (
        <>
          <Typography.Title level={3}>
            {data.name} <Tag>{data.industry}</Tag>
          </Typography.Title>
          <Card loading={isLoading} style={{ marginBottom: 16 }}>
            <Typography.Paragraph>{data.description}</Typography.Paragraph>
            <Descriptions column={1} size="small">
              <Descriptions.Item label="Key">{data.key}</Descriptions.Item>
              <Descriptions.Item label="内置">{data.built_in ? '是' : '否'}</Descriptions.Item>
              <Descriptions.Item label="默认标准">
                {data.default_standard_keys.map((k) => <Tag key={k}>{k}</Tag>)}
              </Descriptions.Item>
            </Descriptions>
          </Card>
          <Card title="流模板（按顺序执行）">
            {data.flow_template.map((step, i) => (
              <div key={step.id} style={{ padding: 8, borderBottom: '1px solid #f0f0f0' }}>
                <strong>Step {i + 1}</strong> · <Tag color="blue">{step.standard_key}</Tag>
              </div>
            ))}
          </Card>
        </>
      ) : (
        <Card loading>加载中</Card>
      )}
    </ConsoleShell>
  );
}
