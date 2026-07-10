'use client';

import { ProTable, ProColumns } from '@ant-design/pro-components';
import { App, Button, Card, Space, Tag, Typography } from 'antd';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import ConsoleShell from '@/components/console-shell';
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
      message.success(r.data.valid ? '閾惧畬鏁? : `閾惧湪绗?${r.data.broken_at} 鏉¤鐮村潖`);
    } catch {
      message.error('鏍￠獙澶辫触');
    }
  };

  const columns: ProColumns<Audit>[] = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: '鏃堕棿', dataIndex: 'ts', valueType: 'dateTime', width: 180 },
    { title: '鎿嶄綔浜?, dataIndex: 'actor', width: 100 },
    { title: '鍔ㄤ綔', dataIndex: 'action', width: 200 },
    { title: 'Flow', dataIndex: 'flow_id', width: 220, ellipsis: true },
    {
      title: 'Hash', dataIndex: 'hash_chain', width: 140,
      render: (v) => <Tag>{String(v).slice(0, 12)}鈥?/Tag>,
    },
  ];

  return (
    <ConsoleShell>
      <Typography.Title level={3}>瀹¤鏃ュ織</Typography.Title>
      <Card style={{ marginBottom: 16 }}>
        <Space>
          <Button type="primary" onClick={onVerify}>鏍￠獙鍝堝笇閾惧畬鏁存€?/Button>
          {verify && (
            <Tag color={verify.valid ? 'green' : 'red'}>
              {verify.valid
                ? `閾惧畬鏁达紙鍏?${verify.total} 鏉★級`
                : `閾炬柇瑁傦紙鏂偣 ${verify.broken_at} / ${verify.total}锛塦}
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
        request={async () => ({ data: data ?? [], success: true, total: data?.length ?? 0 })}
        toolBarRender={() => [
          <Button key="reload" onClick={() => refetch()}>刷新</Button>,
        ]}
      />
    </ConsoleShell>
  );
}
