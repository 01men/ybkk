'use client';

import { ProTable, ProColumns } from '@ant-design/pro-components';
import { App, Tag } from 'antd';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import ConsoleShell from '../console-shell';
import { api } from '@/lib/api';

type Datasource = {
  id: string;
  type: string;
  status: string;
  last_check_at: string | null;
  created_at: string;
};

export default function DatasourcesPage() {
  const { message } = App.useApp();
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['datasources'],
    queryFn: async () => (await api.get<Datasource[]>('/datasources')).data,
  });

  const columns: ProColumns<Datasource>[] = [
    { title: 'ID', dataIndex: 'id', width: 220, ellipsis: true },
    { title: '类型', dataIndex: 'type', width: 100 },
    {
      title: '状态',
      dataIndex: 'status',
      width: 110,
      render: (_, r) => {
        const color = r.status === 'connected' ? 'green' : r.status === 'failed' ? 'red' : 'default';
        return <Tag color={color}>{r.status}</Tag>;
      },
    },
    { title: '最后检查', dataIndex: 'last_check_at', valueType: 'dateTime', width: 180 },
    { title: '创建时间', dataIndex: 'created_at', valueType: 'dateTime', width: 180 },
  ];

  return (
    <ConsoleShell>
      <ProTable<Datasource>
        headerTitle="数据源"
        loading={isLoading}
        dataSource={data ?? []}
        columns={columns}
        rowKey="id"
        search={false}
        toolBarRender={() => [
          <Link key="new" href="/datasources/new">
            <a style={{ color: '#1677ff' }}>新建数据源</a>
          </Link>,
        ]}
        request={async () => ({ data: data ?? [], success: true, total: data?.length ?? 0 })}
        onError={() => message.error('加载失败')}
        onReload={() => refetch()}
      />
    </ConsoleShell>
  );
}
