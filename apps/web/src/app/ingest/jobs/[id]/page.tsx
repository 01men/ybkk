'use client';

import { App, Card, Descriptions, Result, Space, Spin, Tag, Typography } from 'antd';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { useParams } from 'next/navigation';
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

const STATUS_COLOR: Record<string, string> = {
  pending: 'default',
  processing: 'gold',
  succeeded: 'green',
  failed: 'red',
};

const KIND_LABEL: Record<string, string> = {
  excel: 'Excel 表格',
  pdf: 'PDF 工艺文件',
  meeting: '会议录音',
  doc: 'Markdown 规范',
};

export default function IngestJobDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { message } = App.useApp();
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['ingest-job', id],
    queryFn: async () => (await api.get<IngestJob>(`/ingest/jobs/${id}`)).data,
    refetchInterval: (q) => {
      const s = (q.state.data as IngestJob | undefined)?.status;
      return s === 'succeeded' || s === 'failed' ? false : 3_000;
    },
  });

  if (isLoading) {
    return (
      <ConsoleShell>
        <Spin tip="加载中…" />
      </ConsoleShell>
    );
  }

  if (error || !data) {
    return (
      <ConsoleShell>
        <Result
          status="404"
          title="任务不存在"
          subTitle={(error as { message?: string })?.message ?? '可能已被删除或 ID 错误'}
          extra={[<Link key="back" href="/ingest/jobs">返回任务列表</Link>]}
        />
      </ConsoleShell>
    );
  }

  return (
    <ConsoleShell>
      <Space style={{ marginBottom: 16 }}>
        <Link href="/ingest/jobs">← 返回任务列表</Link>
      </Space>
      <Typography.Title level={3}>
        摄取任务 <Tag color={STATUS_COLOR[data.status] ?? 'default'}>{data.status}</Tag>
      </Typography.Title>

      <Card title="基本信息" style={{ marginBottom: 16 }}>
        <Descriptions column={2} bordered size="small">
          <Descriptions.Item label="任务 ID">{data.id}</Descriptions.Item>
          <Descriptions.Item label="类型">
            <Tag>{KIND_LABEL[data.kind] ?? data.kind}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="文件名" span={2}>
            {data.filename}
          </Descriptions.Item>
          <Descriptions.Item label="创建人">{data.created_by}</Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {new Date(data.created_at).toLocaleString('zh-CN')}
          </Descriptions.Item>
          <Descriptions.Item label="完成时间">
            {data.finished_at ? new Date(data.finished_at).toLocaleString('zh-CN') : '—'}
          </Descriptions.Item>
          <Descriptions.Item label="耗时">
            {data.finished_at
              ? `${Math.round(
                  (new Date(data.finished_at).getTime() - new Date(data.created_at).getTime()) / 1000
                )} s`
              : '进行中'}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="解析结果" style={{ marginBottom: 16 }}>
        <Descriptions column={3} bordered size="small">
          <Descriptions.Item label="解析行数 / 段数">{data.parsed_count}</Descriptions.Item>
          <Descriptions.Item label="实体数">{data.entities_count}</Descriptions.Item>
          <Descriptions.Item label="关系数">{data.relations_count}</Descriptions.Item>
        </Descriptions>
      </Card>

      {data.status === 'processing' || data.status === 'pending' ? (
        <Card>
          <Space direction="vertical" style={{ width: '100%' }}>
            <Spin tip="处理中…3 秒自动刷新" />
            <a onClick={() => { refetch(); message.success('已刷新'); }}>手动刷新</a>
          </Space>
        </Card>
      ) : null}

      {data.status === 'failed' && data.error ? (
        <Card title="错误详情" style={{ borderColor: '#ff4d4f' }}>
          <Typography.Text type="danger" style={{ whiteSpace: 'pre-wrap' }}>
            {data.error}
          </Typography.Text>
        </Card>
      ) : null}

      {data.status === 'succeeded' && (data.entities_count > 0 || data.relations_count > 0) ? (
        <Card style={{ background: '#f6ffed' }}>
          <Typography.Text>
            ✅ 已写入本体图。前往{' '}
            <Link href="/ontology">本体浏览</Link> 查看抽取的节点。
          </Typography.Text>
        </Card>
      ) : null}
    </ConsoleShell>
  );
}
