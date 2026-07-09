'use client';

import { App, Card, Col, Collapse, Input, Row, Select, Space, Statistic, Table, Tag, Typography } from 'antd';
import { useState } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import ConsoleShell from '../console-shell';
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
  Material: '物料',
  Supplier: '供应商',
  Warehouse: '仓库',
  Equipment: '设备',
  Order: '订单',
  Process: '工艺流程',
  ProcessStep: '工序',
  DeliveryStandard: '交付标准',
  BusinessRule: '业务规则',
  Role: '角色',
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

  // 按 kind 统计
  const counts: Record<string, number> = {};
  for (const n of data ?? []) {
    counts[n.kind] = (counts[n.kind] ?? 0) + 1;
  }

  return (
    <ConsoleShell>
      <Typography.Title level={3}>本体浏览</Typography.Title>
      <Typography.Paragraph type="secondary">
        V2 本体图共 10 类节点。所有节点由摄取 / LLM 抽取 / 字段映射三种方式写入。点击节点查看详情与邻居关系。
      </Typography.Paragraph>

      {/* V2-010: 嵌入 Neo4j 浏览器（折叠） */}
      <Collapse
        ghost
        style={{ marginBottom: 16 }}
        items={[
          {
            key: 'neo4j',
            label: <span><Link href="http://localhost:7474" target="_blank">Neo4j Browser (新窗口打开 ↗)</Link></span>,
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

      {/* 节点类型统计卡片 */}
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
            placeholder="按类型筛选"
            value={kind}
            onChange={(v) => setKind(v)}
            style={{ width: 200 }}
            options={Object.entries(KIND_DESC).map(([k, v]) => ({ value: k, label: v }))}
          />
          <Input.Search
            placeholder="搜索 external_id / props"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ width: 280 }}
            allowClear
          />
          <a onClick={() => { refetch(); message.success('已刷新'); }}>刷新</a>
          <Link href="http://localhost:7474" target="_blank" style={{ color: '#1677ff' }}>
            打开 Neo4j 浏览器 ↗
          </Link>
        </Space>
        <Table<Node>
          loading={isLoading}
          dataSource={filtered}
          rowKey="external_id"
          size="small"
          pagination={{ pageSize: 20 }}
          columns={[
            {
              title: '类型',
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
              title: '属性',
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
