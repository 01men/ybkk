'use client';

import { ProTable, ProColumns } from '@ant-design/pro-components';
import { App, Card, Tag, Typography } from 'antd';
import { useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import ConsoleShell from '@/components/console-shell';
import { api } from '@/lib/api';

type Run = {
  id: string;
  flow_id: string;
  status: string;
  trigger_type: string | null;
  actor: string | null;
  triggered_at: string;
  finished_at: string | null;
};

const COLOR: Record<string, string> = {
  success: 'green',
  running: 'blue',
  pending: 'default',
  failed: 'red',
  cancelled: 'default',
};

export default function FlowRunsPage() {
  const params = useParams<{ id: string }>();
  const { data, isLoading } = useQuery({
    queryKey: ['flow-runs', params.id],
    queryFn: async () => (await api.get<Run[]>(`/flow-runs/by-flow/${params.id}`)).data,
    refetchInterval: 5000,
  });

  const columns: ProColumns<Run>[] = [
    { title: 'Run ID', dataIndex: 'id', width: 220, ellipsis: true },
    {
      title: '状态', dataIndex: 'status', width: 100,
      render: (_, r) => <Tag color={COLOR[r.status] ?? 'default'}>{r.status}</Tag>,
    },
    { title: '触发器', dataIndex: 'trigger_type', width: 100 },
    { title: '触发人', dataIndex: 'actor', width: 120 },
    { title: '触发时间', dataIndex: 'triggered_at', valueType: 'dateTime', width: 180 },
    { title: '完成时间', dataIndex: 'finished_at', valueType: 'dateTime', width: 180 },
  ];

  return (
    <ConsoleShell>
      <Typography.Title level={3}>Flow Runs</Typography.Title>
      <Card>
        <ProTable<Run>
          loading={isLoading}
          dataSource={data ?? []}
          columns={columns}
          rowKey="id"
          search={false}
          options={{ reload: () => {} }}
        />
      </Card>
    </ConsoleShell>
  );
}
