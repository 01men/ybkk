'use client';

import { App, Card, Form, Input, Select, Checkbox, Button, message as msgApi } from 'antd';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import ConsoleShell from '../console-shell';
import { api } from '@/lib/api';

export default function NewDatasourcePage() {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const { message } = App.useApp();

  const onFinish = async (values: Record<string, unknown>) => {
    if (!values.read_only_account_ack) {
      message.error('必须确认使用只读账号');
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
      message.success('数据源创建成功');
      router.push('/datasources');
    } catch (e: unknown) {
      const m = (e as { response?: { data?: { error?: { message?: string } } } })
        ?.response?.data?.error?.message ?? '创建失败';
      message.error(m);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ConsoleShell>
      <Card title="新建数据源" style={{ maxWidth: 720 }}>
        <Form form={form} layout="vertical" onFinish={onFinish} initialValues={{ type: 'mysql', port: 3306 }}>
          <Form.Item name="type" label="类型" rules={[{ required: true }]}>
            <Select options={[
              { value: 'mysql', label: 'MySQL' },
              { value: 'postgres', label: 'PostgreSQL' },
              { value: 'sqlserver', label: 'SQL Server' },
              { value: 'oracle', label: 'Oracle' },
            ]} />
          </Form.Item>
          <Form.Item name="host" label="主机" rules={[{ required: true }]}>
            <Input placeholder="db.example.com" />
          </Form.Item>
          <Form.Item name="port" label="端口" rules={[{ required: true }]}>
            <Input type="number" />
          </Form.Item>
          <Form.Item name="user" label="用户名" rules={[{ required: true }]}>
            <Input placeholder="readonly_user" />
          </Form.Item>
          <Form.Item name="password" label="密码" rules={[{ required: true }]}>
            <Input.Password />
          </Form.Item>
          <Form.Item name="database" label="数据库" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="read_only_account_ack" valuePropName="checked" rules={[{ required: true }]}>
            <Checkbox>我确认此账号仅有只读权限（SELECT / SHOW），无 DDL/DML 权限</Checkbox>
          </Form.Item>
          <Button type="primary" htmlType="submit" loading={loading}>提交</Button>
        </Form>
      </Card>
    </ConsoleShell>
  );
}
