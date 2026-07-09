'use client';

import { App, Button, Card, Col, Form, Row, Select, Space, Tabs, Tag, Typography, Upload } from 'antd';
import { UploadOutlined, FileExcelOutlined, FilePdfOutlined, AudioOutlined, FileTextOutlined } from '@ant-design/icons';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import ConsoleShell from '../console-shell';
import { api } from '@/lib/api';

const KIND_META: Record<string, { label: string; color: string; icon: React.ReactNode; accept: string; desc: string }> = {
  excel: {
    label: 'Excel 表格',
    color: 'green',
    icon: <FileExcelOutlined />,
    accept: '.xlsx,.xls',
    desc: '物料主数据、库存数据、供应商清单。系统自动识别表头 + 推断列类型，提取 Material/Supplier 节点。',
  },
  pdf: {
    label: 'PDF 工艺文件',
    color: 'red',
    icon: <FilePdfOutlined />,
    accept: '.pdf',
    desc: '工艺规范、操作手册、SOP。提取 Process/ProcessStep 节点。',
  },
  meeting: {
    label: '会议录音',
    color: 'purple',
    icon: <AudioOutlined />,
    accept: '.mp3,.wav,.m4a',
    desc: '晨会、复盘会、决策会录音。先转写（whisper / 阿里云 ASR），再提取 BusinessRule 节点。',
  },
  doc: {
    label: 'Markdown 规范',
    color: 'blue',
    icon: <FileTextOutlined />,
    accept: '.md,.markdown',
    desc: '制度、流程、规范、考核标准文档。提取 DeliveryStandard 候选。',
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
      message.success(`上传成功：${r.data.filename}（${r.data.status}）`);
      router.push(`/ingest/jobs/${r.data.id}`);
    } catch (e: unknown) {
      const m = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? '上传失败';
      message.error(m);
    } finally {
      setUploading(false);
    }
    return false; // 阻止 antd 默认上传
  };

  const meta = KIND_META[kind]!;

  return (
    <ConsoleShell>
      <Typography.Title level={3}>数据接入</Typography.Title>
      <Typography.Paragraph type="secondary">
        V2 支持 4 类源数据上传：Excel / PDF / 会议录音 / Markdown。文件经解析后自动写入本体图（Neo4j），并生成业务规则候选。
      </Typography.Paragraph>

      <Card style={{ marginBottom: 16 }}>
        <Form form={form} layout="vertical">
          <Form.Item label="选择数据源类型" required>
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
                        {uploading ? '处理中…' : `选择 ${m.label} 文件`}
                      </Button>
                    </Upload>
                  </Col>
                  <Col>
                    <Typography.Text type="secondary">
                      支持格式：<Tag>{m.accept}</Tag>
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
