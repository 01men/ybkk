'use client';

import { ProTable, ProColumns } from '@ant-design/pro-components';
import { App, Button, Tag } from 'antd';
import { useRouter } from 'next/navigation';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import ConsoleShell from '@/components/console-shell';
import { api } from '@/lib/api';

type Flow = {
  id: string;
  scenario_id: string;
  status: string;
  trigger_type: string | null;
  trigger_config: Record<string, unknown> | null;
  created_by: string;
  created_at: string;
};

export default function FlowsPage() {
  const router = useRouter();
  const { message } = App.useApp();
  const qc = useQueryClient();

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['flows'],
    queryFn: async () => (await api.get<Flow[]>('/flows')).data,
  });

  const trigger = async (id: string) => {
    try {
      await api.post(`/flows/${id}/trigger`);
      message.success('宸茶Е鍙?);
      qc.invalidateQueries({ queryKey: ['flows'] });
    } catch (e: unknown) {
      const m = (e as { response?: { data?: { error?: { message?: string } } } })
        ?.response?.data?.error?.message ?? '瑙﹀彂澶辫触';
      message.error(m);
    }
  };

  const columns: ProColumns<Flow>[] = [
    { title: 'ID', dataIndex: 'id', width: 220, ellipsis: true },
    { title: '鍦烘櫙 ID', dataIndex: 'scenario_id', width: 220, ellipsis: true },
    {
      title: '鐘舵€?, dataIndex: 'status', width: 100,
      render: (_, r) => <Tag color={r.status === 'active' ? 'green' : 'default'}>{r.status}</Tag>,
    },
    { title: '瑙﹀彂鍣?, dataIndex: 'trigger_type', width: 100 },
    { title: '鍒涘缓浜?, dataIndex: 'created_by', width: 100 },
    { title: '鍒涘缓鏃堕棿', dataIndex: 'created_at', valueType: 'dateTime', width: 180 },
    {
      title: '鎿嶄綔', valueType: 'option', width: 200,
      render: (_, r) => [
        <a key="runs" onClick={() => router.push(`/flows/${r.id}/runs`)}>鏌ョ湅杩愯</a>,
        r.trigger_type === 'manual' ? (
          <Button key="trigger" type="link" onClick={() => trigger(r.id)}>瑙﹀彂</Button>
        ) : null,
      ],
    },
  ];

  return (
    <ConsoleShell>
      <ProTable<Flow>
        headerTitle="涓氬姟娴佺▼"
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
