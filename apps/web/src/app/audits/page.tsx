'use client';

import { ProTable, ProColumns } from '@ant-design/pro-components';
import { App, Button, Card, Space, Tag, Typography } from 'antd';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import ConsoleShell from '../console-shell';
import { api } from '@/lib/api';

type Audit = {
  id: number;
  ts: string;
  actor: string;
  action: string;
  datasource_id: string | null;
  standard_ref: string | null;
  flow_id: string | null;
  run_id: string | null;
  payload: Record<string, unknown>;
  hash_chain: string;
};

type VerifyResult = { valid: boolean; broken_at: number | null; total: number };

export default function AuditsPage() {
  const { message } = App.useApp();
  const [verify, setVerify] = useState<VerifyResult | null>(null);
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['audits'],
    queryFn: async () => (await api.get<Audit[]>('/audits')).data,
  });

  const onVerify = async () => {
    try {
      const r = await api.get<VerifyResult>('/audits/verify');
      setVerify(r.data);
      message.success(r.data.valid ? '链完整' : `链在第 ${r.data.broken_at} 条被破坏`);
    } catch {
      message.error('校验失败');
    }
  };

  const columns: ProColumns<Audit>[] = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: '时间', dataIndex: 'ts', valueType: 'dateTime', width: 180 },
    { title: '操作人', dataIndex: 'actor', width: 100 },
    { title: '动作', dataIndex: 'action', width: 200 },
    { title: 'Flow', dataIndex: 'flow_id', width: 220, ellipsis: true },
    {
      title: 'Hash', dataIndex: 'hash_chain', width: 140,
      render: (v) => <Tag>{String(v).slice(0, 12)}…</Tag>,
    },
  ];

  return (
    <ConsoleShell>
      <Typography.Title level={3}>审计日志</Typography.Title>
      <Card style={{ marginBottom: 16 }}>
        <Space>
          <Button type="primary" onClick={onVerify}>校验哈希链完整性</Button>
          {verify && (
            <Tag color={verify.valid ? 'green' : 'red'}>
              {verify.valid
                ? `链完整（共 ${verify.total} 条）`
                : `链断裂（断点 ${verify.broken_at} / ${verify.total}）`}
            </Tag>
          )}
        </Space>
      </Card>
      <ProTable<Audit>
        loading={isLoading}
        dataSource={data ?? []}
        columns={columns}
        rowKey="id"
        search={false}
        onReload={() => refetch()}
      />
    </ConsoleShell>
  );
}
