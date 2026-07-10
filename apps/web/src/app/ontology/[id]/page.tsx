'use client';

import { App, Card, Col, Descriptions, Result, Row, Space, Spin, Tag, Typography } from 'antd';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { useParams } from 'next/navigation';
import ConsoleShell from '@/components/console-shell';
import { api } from '@/lib/api';

type Node = {
  external_id: string;
  kind: string;
  props: Record<string, unknown>;
};

type Neighbor = {
  nodes: Array<{ external_id: string; kind: string; props: Record<string, unknown> }>;
  edges: Array<{ source: string; target: string; type: string }>;
};

const KIND_COLOR: Record<string, string> = {
  Material: 'blue',
  Supplier: 'green',
  Warehouse: 'cyan',
  Equipment: 'orange',
  Order: 'purple',
  Process: 'magenta',
  ProcessStep: 'volcano',
  DeliveryStandard: 'gold',
  BusinessRule: 'red',
  Role: 'geekblue',
};

const REL_COLOR: Record<string, string> = {
  SUPPLIED_BY: 'green',
  STORED_IN: 'cyan',
  MAINTAINED_BY: 'geekblue',
  HAS_STEP: 'magenta',
  NEXT: 'volcano',
  USES_MATERIAL: 'blue',
  PRODUCED_BY: 'orange',
  APPLIES_TO: 'gold',
  OWNED_BY: 'geekblue',
  DERIVED_FROM: 'red',
  DEFINES: 'gold',
  CRITICAL_TO: 'magenta',
};

export default function OntologyNodeDetailPage() {
  const { id } = useParams<{ id: string }>();
  const decodedId = decodeURIComponent(id ?? '');
  const { message } = App.useApp();

  const nodeQ = useQuery({
    queryKey: ['ontology-node', decodedId],
    queryFn: async () => (await api.get<Node>(`/ontology/nodes/${encodeURIComponent(decodedId)}`)).data,
  });

  const neighborsQ = useQuery({
    queryKey: ['ontology-neighbors', decodedId],
    queryFn: async () =>
      (await api.get<Neighbor>(`/ontology/nodes/${encodeURIComponent(decodedId)}/neighbors`, { params: { depth: 1 } })).data,
  });

  if (nodeQ.isLoading) {
    return (
      <ConsoleShell>
        <Spin tip="加载中…" />
      </ConsoleShell>
    );
  }

  if (nodeQ.error || !nodeQ.data) {
    return (
      <ConsoleShell>
        <Result
          status="404"
          title="节点不存在"
          subTitle={(nodeQ.error as { message?: string })?.message ?? `external_id: ${decodedId}`}
          extra={[<Link key="back" href="/ontology">返回本体浏览</Link>]}
        />
      </ConsoleShell>
    );
  }

  const n = nodeQ.data;
  const nb = neighborsQ.data;

  return (
    <ConsoleShell>
      <Space style={{ marginBottom: 16 }}>
        <Link href="/ontology">← 返回本体浏览</Link>
      </Space>
      <Typography.Title level={3}>
        {n.external_id}{' '}
        <Tag color={KIND_COLOR[n.kind] ?? 'default'}>{n.kind}</Tag>
      </Typography.Title>

      <Row gutter={16}>
        <Col xs={24} md={12}>
          <Card title="属性" style={{ marginBottom: 16 }}>
            <Descriptions column={1} bordered size="small">
              {Object.entries(n.props).map(([k, v]) => (
                <Descriptions.Item label={k} key={k}>
                  {typeof v === 'object' ? <code>{JSON.stringify(v)}</code> : String(v)}
                </Descriptions.Item>
              ))}
            </Descriptions>
          </Card>
        </Col>

        <Col xs={24} md={12}>
          <Card title="邻居节点（1 跳）" style={{ marginBottom: 16 }} loading={neighborsQ.isLoading}>
            {nb && (
              <>
                <Typography.Paragraph type="secondary">
                  共 {nb.edges.length} 条关系，{nb.nodes.length} 个邻居节点
                </Typography.Paragraph>
                <Space direction="vertical" style={{ width: '100%' }}>
                  {nb.edges.map((e, i) => {
                    const from = e.source === n.external_id ? 'this' : e.source;
                    const to = e.target === n.external_id ? 'this' : e.target;
                    return (
                      <div key={i} style={{ fontSize: 13 }}>
                        <Link href={`/ontology/${encodeURIComponent(e.source)}`}>{from}</Link>
                        {' → '}
                        <Tag color={REL_COLOR[e.type] ?? 'default'}>{e.type}</Tag>
                        {' → '}
                        <Link href={`/ontology/${encodeURIComponent(e.target)}`}>{to}</Link>
                      </div>
                    );
                  })}
                </Space>
              </>
            )}
            {neighborsQ.error && (
              <Typography.Text type="danger">查询失败：{(neighborsQ.error as Error).message}</Typography.Text>
            )}
          </Card>
        </Col>
      </Row>
    </ConsoleShell>
  );
}
