'use client';

import { ProTable, ProColumns } from '@ant-design/pro-components';
import { App, Tag, Typography } from 'antd';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import ConsoleShell from '../../console-shell';
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
    { title: '任务 ID', dataIndex: 'id', width: 220, ellipsis: true },
    {
      title: '类型',
      dataIndex: 'kind',
      width: 100,
      render: (_, r) => <Tag color={KIND_COLOR[r.kind] ?? 'default'}>{r.kind}</Tag>,
    },
    { title: '文件名', dataIndex: 'filename', width: 220, ellipsis: true },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      render: (_, r) => <Tag color={STATUS_COLOR[r.status] ?? 'default'}>{r.status}</Tag>,
    },
    { title: '解析行数', dataIndex: 'parsed_count', width: 90, align: 'right' },
    { title: '实体数', dataIndex: 'entities_count', width: 90, align: 'right' },
    { title: '关系数', dataIndex: 'relations_count', width: 90, align: 'right' },
    { title: '创建人', dataIndex: 'created_by', width: 100 },
    { title: '创建时间', dataIndex: 'created_at', valueType: 'dateTime', width: 180 },
    { title: '完成时间', dataIndex: 'finished_at', valueType: 'dateTime', width: 180 },
    {
      title: '操作',
      valueType: 'option',
      width: 100,
      render: (_, r) => [<Link key="view" href={`/ingest/jobs/${r.id}`}>详情</Link>],
    },
  ];

  return (
    <ConsoleShell>
      <Typography.Title level={3}>摄取任务</Typography.Title>
      <ProTable<IngestJob>
        headerTitle="历史任务（5s 自动刷新）"
        loading={isLoading}
        dataSource={data ?? []}
        columns={columns}
        rowKey="id"
        search={false}
        onReload={() => {
          refetch();
          message.success('已刷新');
        }}
        pagination={{ pageSize: 20 }}
      />
    </ConsoleShell>
  );
}
