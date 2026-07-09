'use client';

import { App, Card, Col, Row, Space, Tag, Typography } from 'antd';
import { useQuery } from '@tanstack/react-query';
import ConsoleShell from '../console-shell';
import { api } from '@/lib/api';

const DASHBOARDS = [
  { uid: 'aios-api', title: 'API', desc: '请求速率 / P95 延迟 / 5xx 错误率', color: 'blue' },
  { uid: 'aios-flow', title: 'Flow', desc: 'Flow run 状态 / 失败率 / step 耗时', color: 'purple' },
  { uid: 'aios-llm', title: 'LLM', desc: '调用速率 / P95 延迟 / 注入拦截', color: 'green' },
  { uid: 'aios-ingest', title: 'Ingest', desc: '任务速率 / 状态分布', color: 'orange' },
  { uid: 'aios-ontology', title: 'Ontology & System', desc: '本体节点数 / Ollama 健康 / 容器 CPU', color: 'magenta' },
];

export default function MonitoringPage() {
  const { message } = App.useApp();
  const { data, isLoading } = useQuery({
    queryKey: ['prometheus-up'],
    queryFn: async () => {
      try {
        const r = await api.get<string>('/api/v1/health');
        return r.data;
      } catch {
        return null;
      }
    },
  });

  return (
    <ConsoleShell>
      <Typography.Title level={3}>监控仪表盘</Typography.Title>
      <Typography.Paragraph type="secondary">
        V3 监控由 Prometheus + Grafana + Loki + cadvisor 组成。默认未启动（profile=monitoring）。
        启动后访问 <a href="http://localhost:3001" target="_blank">Grafana</a>（admin/admin）。
      </Typography.Paragraph>

      <Row gutter={[16, 16]}>
        {DASHBOARDS.map((d) => (
          <Col key={d.uid} xs={24} sm={12} md={8}>
            <Card
              hoverable
              title={
                <Space>
                  <Tag color={d.color}>{d.title}</Tag>
                  <span style={{ fontSize: 14 }}>{d.title} 监控</span>
                </Space>
              }
              extra={
                <a
                  href={`http://localhost:3001/d/${d.uid}`}
                  target="_blank"
                  rel="noreferrer"
                >
                  打开 ↗
                </a>
              }
            >
              <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
                {d.desc}
              </Typography.Paragraph>
            </Card>
          </Col>
        ))}
      </Row>

      <Card title="Prometheus 状态" style={{ marginTop: 16 }}>
        {isLoading ? (
          <Typography.Text>检查中…</Typography.Text>
        ) : (
          <Space direction="vertical">
            <Tag color="green">API /health 端点可达</Tag>
            <Typography.Text type="secondary">
              Prometheus 抓取状态：<a href="http://localhost:9090/targets" target="_blank">/targets</a>
            </Typography.Text>
            {data ? null : (
              <Typography.Text type="warning">
                API 不可达 — 监控可能无法抓取指标
              </Typography.Text>
            )}
            <Typography.Paragraph style={{ marginTop: 8 }}>
              <a onClick={() => message.info('已刷新')} style={{ marginRight: 16 }}>刷新</a>
              <a onClick={() => window.open('http://localhost:9090/alerts', '_blank')}>
                查看告警 →
              </a>
            </Typography.Paragraph>
          </Space>
        )}
      </Card>
    </ConsoleShell>
  );
}
