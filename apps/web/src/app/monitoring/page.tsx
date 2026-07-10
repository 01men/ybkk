'use client';

import { App, Card, Col, Row, Space, Tag, Typography } from 'antd';
import { useQuery } from '@tanstack/react-query';
import ConsoleShell from '@/components/console-shell';
import { api } from '@/lib/api';

const DASHBOARDS = [
  { uid: 'aios-api', title: 'API', desc: '璇锋眰閫熺巼 / P95 寤惰繜 / 5xx 閿欒鐜?, color: 'blue' },
  { uid: 'aios-flow', title: 'Flow', desc: 'Flow run 鐘舵€?/ 澶辫触鐜?/ step 鑰楁椂', color: 'purple' },
  { uid: 'aios-llm', title: 'LLM', desc: '璋冪敤閫熺巼 / P95 寤惰繜 / 娉ㄥ叆鎷︽埅', color: 'green' },
  { uid: 'aios-ingest', title: 'Ingest', desc: '浠诲姟閫熺巼 / 鐘舵€佸垎甯?, color: 'orange' },
  { uid: 'aios-ontology', title: 'Ontology & System', desc: '鏈綋鑺傜偣鏁?/ Ollama 鍋ュ悍 / 瀹瑰櫒 CPU', color: 'magenta' },
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
      <Typography.Title level={3}>鐩戞帶浠〃鐩?/Typography.Title>
      <Typography.Paragraph type="secondary">
        V3 鐩戞帶鐢?Prometheus + Grafana + Loki + cadvisor 缁勬垚銆傞粯璁ゆ湭鍚姩锛坧rofile=monitoring锛夈€?        鍚姩鍚庤闂?<a href="http://localhost:3001" target="_blank">Grafana</a>锛坅dmin/admin锛夈€?      </Typography.Paragraph>

      <Row gutter={[16, 16]}>
        {DASHBOARDS.map((d) => (
          <Col key={d.uid} xs={24} sm={12} md={8}>
            <Card
              hoverable
              title={
                <Space>
                  <Tag color={d.color}>{d.title}</Tag>
                  <span style={{ fontSize: 14 }}>{d.title} 鐩戞帶</span>
                </Space>
              }
              extra={
                <a
                  href={`http://localhost:3001/d/${d.uid}`}
                  target="_blank"
                  rel="noreferrer"
                >
                  鎵撳紑 鈫?                </a>
              }
            >
              <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
                {d.desc}
              </Typography.Paragraph>
            </Card>
          </Col>
        ))}
      </Row>

      <Card title="Prometheus 鐘舵€? style={{ marginTop: 16 }}>
        {isLoading ? (
          <Typography.Text>妫€鏌ヤ腑鈥?/Typography.Text>
        ) : (
          <Space direction="vertical">
            <Tag color="green">API /health 绔偣鍙揪</Tag>
            <Typography.Text type="secondary">
              Prometheus 鎶撳彇鐘舵€侊細<a href="http://localhost:9090/targets" target="_blank">/targets</a>
            </Typography.Text>
            {data ? null : (
              <Typography.Text type="warning">
                API 涓嶅彲杈?鈥?鐩戞帶鍙兘鏃犳硶鎶撳彇鎸囨爣
              </Typography.Text>
            )}
            <Typography.Paragraph style={{ marginTop: 8 }}>
              <a onClick={() => message.info('宸插埛鏂?)} style={{ marginRight: 16 }}>鍒锋柊</a>
              <a onClick={() => window.open('http://localhost:9090/alerts', '_blank')}>
                鏌ョ湅鍛婅 鈫?              </a>
            </Typography.Paragraph>
          </Space>
        )}
      </Card>
    </ConsoleShell>
  );
}
