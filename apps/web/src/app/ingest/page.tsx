'use client';

import { App, Button, Card, Col, Form, Row, Select, Space, Tabs, Tag, Typography, Upload } from 'antd';
import { UploadOutlined, FileExcelOutlined, FilePdfOutlined, AudioOutlined, FileTextOutlined } from '@ant-design/icons';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import ConsoleShell from '@/components/console-shell';
import { api } from '@/lib/api';

const KIND_META: Record<string, { label: string; color: string; icon: React.ReactNode; accept: string; desc: string }> = {
  excel: {
    label: 'Excel 琛ㄦ牸',
    color: 'green',
    icon: <FileExcelOutlined />,
    accept: '.xlsx,.xls',
    desc: '鐗╂枡涓绘暟鎹€佸簱瀛樻暟鎹€佷緵搴斿晢娓呭崟銆傜郴缁熻嚜鍔ㄨ瘑鍒〃澶?+ 鎺ㄦ柇鍒楃被鍨嬶紝鎻愬彇 Material/Supplier 鑺傜偣銆?,
  },
  pdf: {
    label: 'PDF 宸ヨ壓鏂囦欢',
    color: 'red',
    icon: <FilePdfOutlined />,
    accept: '.pdf',
    desc: '宸ヨ壓瑙勮寖銆佹搷浣滄墜鍐屻€丼OP銆傛彁鍙?Process/ProcessStep 鑺傜偣銆?,
  },
  meeting: {
    label: '浼氳褰曢煶',
    color: 'purple',
    icon: <AudioOutlined />,
    accept: '.mp3,.wav,.m4a',
    desc: '鏅ㄤ細銆佸鐩樹細銆佸喅绛栦細褰曢煶銆傚厛杞啓锛坵hisper / 闃块噷浜?ASR锛夛紝鍐嶆彁鍙?BusinessRule 鑺傜偣銆?,
  },
  doc: {
    label: 'Markdown 瑙勮寖',
    color: 'blue',
    icon: <FileTextOutlined />,
    accept: '.md,.markdown',
    desc: '鍒跺害銆佹祦绋嬨€佽鑼冦€佽€冩牳鏍囧噯鏂囨。銆傛彁鍙?DeliveryStandard 鍊欓€夈€?,
  },
};

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

export default function IngestPage() {
  const { message } = App.useApp();
  const router = useRouter();
  const [kind, setKind] = useState<string>('excel');
  const [uploading, setUploading] = useState(false);
  const [form] = Form.useForm();

  const onUpload = async (file: File) => {
    setUploading(true);
    const fd = new FormData();
    fd.append('file', file);
    fd.append('kind', kind);
    try {
      const r = await api.post<IngestJob>('/ingest/upload', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 180_000,
      });
      message.success(`涓婁紶鎴愬姛锛?{r.data.filename}锛?{r.data.status}锛塦);
      router.push(`/ingest/jobs/${r.data.id}`);
    } catch (e: unknown) {
      const m = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? '涓婁紶澶辫触';
      message.error(m);
    } finally {
      setUploading(false);
    }
    return false; // 闃绘 antd 榛樿涓婁紶
  };

  const meta = KIND_META[kind]!;

  return (
    <ConsoleShell>
      <Typography.Title level={3}>鏁版嵁鎺ュ叆</Typography.Title>
      <Typography.Paragraph type="secondary">
        V2 鏀寔 4 绫绘簮鏁版嵁涓婁紶锛欵xcel / PDF / 浼氳褰曢煶 / Markdown銆傛枃浠剁粡瑙ｆ瀽鍚庤嚜鍔ㄥ啓鍏ユ湰浣撳浘锛圢eo4j锛夛紝骞剁敓鎴愪笟鍔¤鍒欏€欓€夈€?      </Typography.Paragraph>

      <Card style={{ marginBottom: 16 }}>
        <Form form={form} layout="vertical">
          <Form.Item label="閫夋嫨鏁版嵁婧愮被鍨? required>
            <Select
              value={kind}
              onChange={setKind}
              size="large"
              options={Object.entries(KIND_META).map(([k, m]) => ({
                value: k,
                label: (
                  <Space>
                    {m.icon}
                    <Tag color={m.color}>{m.label}</Tag>
                  </Space>
                ),
              }))}
            />
          </Form.Item>
        </Form>
      </Card>

      <Card>
        <Tabs
          activeKey={kind}
          onChange={setKind}
          items={Object.entries(KIND_META).map(([k, m]) => ({
            key: k,
            label: (
              <span>
                {m.icon} {m.label}
              </span>
            ),
            children: (
              <div style={{ padding: '16px 0' }}>
                <Typography.Paragraph type="secondary">{m.desc}</Typography.Paragraph>
                <Row gutter={16} align="middle">
                  <Col>
                    <Upload
                      accept={m.accept}
                      beforeUpload={onUpload}
                      showUploadList={false}
                      disabled={uploading}
                    >
                      <Button type="primary" size="large" icon={<UploadOutlined />} loading={uploading}>
                        {uploading ? '澶勭悊涓€? : `閫夋嫨 ${m.label} 鏂囦欢`}
                      </Button>
                    </Upload>
                  </Col>
                  <Col>
                    <Typography.Text type="secondary">
                      鏀寔鏍煎紡锛?Tag>{m.accept}</Tag>
                    </Typography.Text>
                  </Col>
                </Row>
              </div>
            ),
          }))}
        />
      </Card>
    </ConsoleShell>
  );
}
