'use client';

import { App, Card, Form, Input, Select, Checkbox, Button, message as msgApi } from 'antd';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import ConsoleShell from '@/components/console-shell';
import { api } from '@/lib/api';

export default function NewDatasourcePage() {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const { message } = App.useApp();

  const onFinish = async (values: Record<string, unknown>) => {
    if (!values.read_only_account_ack) {
      message.error('蹇呴』纭浣跨敤鍙璐﹀彿');
      return;
    }
    setLoading(true);
    try {
      const connection = {
        host: values.host,
        port: Number(values.port),
        user: values.user,
        password: values.password,
        database: values.database,
      };
      await api.post('/datasources', {
        type: values.type,
        connection,
        read_only_account_ack: true,
      });
      message.success('鏁版嵁婧愬垱寤烘垚鍔?);
      router.push('/datasources');
    } catch (e: unknown) {
      const m = (e as { response?: { data?: { error?: { message?: string } } } })
        ?.response?.data?.error?.message ?? '鍒涘缓澶辫触';
      message.error(m);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ConsoleShell>
      <Card title="鏂板缓鏁版嵁婧? style={{ maxWidth: 720 }}>
        <Form form={form} layout="vertical" onFinish={onFinish} initialValues={{ type: 'mysql', port: 3306 }}>
          <Form.Item name="type" label="绫诲瀷" rules={[{ required: true }]}>
            <Select options={[
              { value: 'mysql', label: 'MySQL' },
              { value: 'postgres', label: 'PostgreSQL' },
              { value: 'sqlserver', label: 'SQL Server' },
              { value: 'oracle', label: 'Oracle' },
            ]} />
          </Form.Item>
          <Form.Item name="host" label="涓绘満" rules={[{ required: true }]}>
            <Input placeholder="db.example.com" />
          </Form.Item>
          <Form.Item name="port" label="绔彛" rules={[{ required: true }]}>
            <Input type="number" />
          </Form.Item>
          <Form.Item name="user" label="鐢ㄦ埛鍚? rules={[{ required: true }]}>
            <Input placeholder="readonly_user" />
          </Form.Item>
          <Form.Item name="password" label="瀵嗙爜" rules={[{ required: true }]}>
            <Input.Password />
          </Form.Item>
          <Form.Item name="database" label="鏁版嵁搴? rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="read_only_account_ack" valuePropName="checked" rules={[{ required: true }]}>
            <Checkbox>鎴戠‘璁ゆ璐﹀彿浠呮湁鍙鏉冮檺锛圫ELECT / SHOW锛夛紝鏃?DDL/DML 鏉冮檺</Checkbox>
          </Form.Item>
          <Button type="primary" htmlType="submit" loading={loading}>鎻愪氦</Button>
        </Form>
      </Card>
    </ConsoleShell>
  );
}
