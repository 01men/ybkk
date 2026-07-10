'use client';

import { ProTable, ProColumns } from '@ant-design/pro-components';
import { App, Tag, Typography } from 'antd';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import ConsoleShell from '@/components/console-shell';
import { api } from '@/lib/api';

type IngestJob = {
  id: string;
  kind: string;
  filename: string;
  status: string;
  parsed_count: number;
  entities_count: number;
  relations_count: number;
  error: string | null;
  created_by: string;
  created_at: string;
  finished_at: string | null;
};

const KIND_COLOR: Record<string, string> = {
  excel: 'green',
  pdf: 'red',
  meeting: 'purple',
  doc: 'blue',
};

const STATUS_COLOR: Record<string, string> = {
  pending: 'default',
  processing: 'gold',
  succeeded: 'green',
  failed: 'red',
};

export default function IngestJobsPage() {
  const { message } = App.useApp();
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['ingest-jobs'],
    queryFn: async () => (await api.get<IngestJob[]>('/ingest/jobs')).data,
    refetchInterval: 5_000,
  });

  const columns: ProColumns<IngestJob>[] = [
    { title: '浠诲姟 ID', dataIndex: 'id', width: 220, ellipsis: true },
    {
      title: '绫诲瀷',
      dataIndex: 'kind',
      width: 100,
      render: (_, r) => <Tag color={KIND_COLOR[r.kind] ?? 'default'}>{r.kind}</Tag>,
    },
    { title: '鏂囦欢鍚?, dataIndex: 'filename', width: 220, ellipsis: true },
    {
      title: '鐘舵€?,
      dataIndex: 'status',
      width: 100,
      render: (_, r) => <Tag color={STATUS_COLOR[r.status] ?? 'default'}>{r.status}</Tag>,
    },
    { title: '瑙ｆ瀽琛屾暟', dataIndex: 'parsed_count', width: 90, align: 'right' },
    { title: '瀹炰綋鏁?, dataIndex: 'entities_count', width: 90, align: 'right' },
    { title: '鍏崇郴鏁?, dataIndex: 'relations_count', width: 90, align: 'right' },
    { title: '鍒涘缓浜?, dataIndex: 'created_by', width: 100 },
    { title: '鍒涘缓鏃堕棿', dataIndex: 'created_at', valueType: 'dateTime', width: 180 },
    { title: '瀹屾垚鏃堕棿', dataIndex: 'finished_at', valueType: 'dateTime', width: 180 },
    {
      title: '鎿嶄綔',
      valueType: 'option',
      width: 100,
      render: (_, r) => [<Link key="view" href={`/ingest/jobs/${r.id}`}>璇︽儏</Link>],
    },
  ];

  return (
    <ConsoleShell>
      <Typography.Title level={3}>鎽勫彇浠诲姟</Typography.Title>
      <ProTable<IngestJob>
        headerTitle="鍘嗗彶浠诲姟锛?s 鑷姩鍒锋柊锛?
        loading={isLoading}
        dataSource={data ?? []}
        columns={columns}
        rowKey="id"
        search={false}
        request={async () => ({ data: data ?? [], success: true, total: data?.length ?? 0 })}
        pagination={{ pageSize: 20 }}
      />
    </ConsoleShell>
  );
}
