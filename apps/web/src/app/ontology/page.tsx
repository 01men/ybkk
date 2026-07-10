'use client';

import { App, Card, Col, Collapse, Input, Row, Select, Space, Statistic, Table, Tag, Typography } from 'antd';
import { useState } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import ConsoleShell from '@/components/console-shell';
import { api } from '@/lib/api';

type Node = {
  external_id: string;
  kind: string;
  props: Record<string, unknown>;
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

const KIND_DESC: Record<string, string> = {
  Material: '鐗╂枡',
  Supplier: '渚涘簲鍟?,
  Warehouse: '浠撳簱',
  Equipment: '璁惧',
  Order: '璁㈠崟',
  Process: '宸ヨ壓娴佺▼',
  ProcessStep: '宸ュ簭',
  DeliveryStandard: '浜や粯鏍囧噯',
  BusinessRule: '涓氬姟瑙勫垯',
  Role: '瑙掕壊',
};

export default function OntologyPage() {
  const { message } = App.useApp();
  const [kind, setKind] = useState<string | undefined>(undefined);
  const [search, setSearch] = useState('');

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['ontology-nodes', kind],
    queryFn: async () => (await api.get<Node[]>('/ontology/nodes', { params: { kind, limit: 200 } })).data,
  });

  const filtered = (data ?? []).filter((n) => {
    if (!search) return true;
    const s = search.toLowerCase();
    return (
      n.external_id.toLowerCase().includes(s) ||
      n.kind.toLowerCase().includes(s) ||
      JSON.stringify(n.props).toLowerCase().includes(s)
    );
  });

  // 鎸?kind 缁熻
  const counts: Record<string, number> = {};
  for (const n of data ?? []) {
    counts[n.kind] = (counts[n.kind] ?? 0) + 1;
  }

  return (
    <ConsoleShell>
      <Typography.Title level={3}>鏈綋娴忚</Typography.Title>
      <Typography.Paragraph type="secondary">
        V2 鏈綋鍥惧叡 10 绫昏妭鐐广€傛墍鏈夎妭鐐圭敱鎽勫彇 / LLM 鎶藉彇 / 瀛楁鏄犲皠涓夌鏂瑰紡鍐欏叆銆傜偣鍑昏妭鐐规煡鐪嬭鎯呬笌閭诲眳鍏崇郴銆?      </Typography.Paragraph>

      {/* V2-010: 宓屽叆 Neo4j 娴忚鍣紙鎶樺彔锛?*/}
      <Collapse
        ghost
        style={{ marginBottom: 16 }}
        items={[
          {
            key: 'neo4j',
            label: <span><Link href="http://localhost:7474" target="_blank">Neo4j Browser (鏂扮獥鍙ｆ墦寮€ 鈫?</Link></span>,
            children: (
              <iframe
                src="http://localhost:7474"
                title="Neo4j Browser"
                style={{ width: '100%', height: 600, border: '1px solid #d9d9d9', borderRadius: 4 }}
                sandbox="allow-scripts allow-same-origin allow-forms"
              />
            ),
          },
        ]}
      />

      {/* 鑺傜偣绫诲瀷缁熻鍗＄墖 */}
      <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
        {Object.entries(KIND_DESC).map(([k, label]) => (
          <Col key={k} xs={12} sm={8} md={6} lg={4}>
            <Card size="small" hoverable onClick={() => setKind(k === kind ? undefined : k)}>
              <Statistic
                title={
                  <Space>
                    <Tag color={KIND_COLOR[k] ?? 'default'}>{label}</Tag>
                  </Space>
                }
                value={counts[k] ?? 0}
                valueStyle={{ fontSize: 20 }}
              />
            </Card>
          </Col>
        ))}
      </Row>

      <Card>
        <Space style={{ marginBottom: 16 }}>
          <Select
            allowClear
            placeholder="鎸夌被鍨嬬瓫閫?
            value={kind}
            onChange={(v) => setKind(v)}
            style={{ width: 200 }}
            options={Object.entries(KIND_DESC).map(([k, v]) => ({ value: k, label: v }))}
          />
          <Input.Search
            placeholder="鎼滅储 external_id / props"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ width: 280 }}
            allowClear
          />
          <a onClick={() => { refetch(); message.success('宸插埛鏂?); }}>鍒锋柊</a>
          <Link href="http://localhost:7474" target="_blank" style={{ color: '#1677ff' }}>
            鎵撳紑 Neo4j 娴忚鍣?鈫?          </Link>
        </Space>
        <Table<Node>
          loading={isLoading}
          dataSource={filtered}
          rowKey="external_id"
          size="small"
          pagination={{ pageSize: 20 }}
          columns={[
            {
              title: '绫诲瀷',
              dataIndex: 'kind',
              width: 130,
              render: (k: string) => <Tag color={KIND_COLOR[k] ?? 'default'}>{KIND_DESC[k] ?? k}</Tag>,
            },
            {
              title: 'External ID',
              dataIndex: 'external_id',
              width: 220,
              ellipsis: true,
              render: (id: string) => <Link href={`/ontology/${encodeURIComponent(id)}`}>{id}</Link>,
            },
            {
              title: '灞炴€?,
              dataIndex: 'props',
              render: (props: Record<string, unknown>) => (
                <code style={{ fontSize: 12, color: '#666' }}>
                  {JSON.stringify(props).slice(0, 200)}
                </code>
              ),
            },
          ]}
        />
      </Card>
    </ConsoleShell>
  );
}
