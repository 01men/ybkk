'use client';

import { App, Button, Card, Form, Input, Modal, Space, Table, Tag, Typography } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useState } from 'react';
import Link from 'next/link';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import ConsoleShell from '@/components/console-shell';
import { api } from '@/lib/api';

type Org = {
  id: string;
  name: string;
  slug: string;
  role_key: string;
  member_count?: number;
  created_at: string;
};

export default function OrgsPage() {
  const { message } = App.useApp();
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm();

  const { data, isLoading } = useQuery({
    queryKey: ['my-orgs'],
    queryFn: async () => (await api.get<Org[]>('/orgs')).data,
  });

  const createMut = useMutation({
    mutationFn: async (v: { name: string; slug: string }) =>
      (await api.post<Org>('/orgs', v)).data,
    onSuccess: () => {
      message.success('宸插垱寤?);
      setOpen(false);
      form.resetFields();
      qc.invalidateQueries({ queryKey: ['my-orgs'] });
    },
    onError: (e: unknown) => {
      const m = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? '鍒涘缓澶辫触';
      message.error(m);
    },
  });

  const switchOrg = async (orgId: string, name: string) => {
    try {
      const resp = await api.post<{ token: string }>(`/orgs/${orgId}/switch`);
      localStorage.setItem('aios_token', resp.data.token);
      message.success(`宸插垏鎹㈠埌 ${name}`);
      qc.invalidateQueries();
    } catch (e: unknown) {
      const m = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? '鍒囨崲澶辫触';
      message.error(m);
    }
  };

  return (
    <ConsoleShell>
      <Space style={{ marginBottom: 16, width: '100%', justifyContent: 'space-between' }}>
        <Typography.Title level={3} style={{ margin: 0 }}>鎴戠殑缁勭粐</Typography.Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setOpen(true)}>
          鏂板缓缁勭粐
        </Button>
      </Space>

      <Card>
        <Table<Org>
          loading={isLoading}
          dataSource={data ?? []}
          rowKey="id"
          columns={[
            { title: '鍚嶇О', dataIndex: 'name' },
            { title: 'Slug', dataIndex: 'slug' },
            {
              title: '鎴戠殑瑙掕壊',
              dataIndex: 'role_key',
              width: 120,
              render: (r: string) => (
                <Tag color={r === 'admin' ? 'red' : r === 'engineer' ? 'blue' : 'default'}>{r}</Tag>
              ),
            },
            { title: '鍒涘缓鏃堕棿', dataIndex: 'created_at', valueType: 'dateTime', width: 180 },
            {
              title: '鎿嶄綔',
              valueType: 'option',
              width: 220,
              render: (_, r) => [
                <Link key="view" href={`/orgs/${r.id}`}>鎴愬憳绠＄悊</Link>,
                <Button key="switch" type="link" onClick={() => switchOrg(r.id, r.name)}>
                  鍒囨崲
                </Button>,
              ],
            },
          ]}
        />
      </Card>

      <Modal
        title="鏂板缓缁勭粐"
        open={open}
        onCancel={() => setOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={createMut.isPending}
      >
        <Form form={form} layout="vertical" onFinish={(v) => createMut.mutate(v)}>
          <Form.Item label="缁勭粐鍚? name="name" rules={[{ required: true }]}>
            <Input placeholder="渚嬶細娣卞湷涓€鍘? />
          </Form.Item>
          <Form.Item
            label="Slug"
            name="slug"
            rules={[{ required: true, pattern: /^[a-z0-9-]+$/, message: '灏忓啓瀛楁瘝/鏁板瓧/鐭í绾? }]}
          >
            <Input placeholder="渚嬶細sz-factory-1" />
          </Form.Item>
        </Form>
      </Modal>
    </ConsoleShell>
  );
}
