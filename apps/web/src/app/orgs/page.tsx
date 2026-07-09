'use client';

import { App, Button, Card, Form, Input, Modal, Space, Table, Tag, Typography } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useState } from 'react';
import Link from 'next/link';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import ConsoleShell from '../console-shell';
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
      message.success('已创建');
      setOpen(false);
      form.resetFields();
      qc.invalidateQueries({ queryKey: ['my-orgs'] });
    },
    onError: (e: unknown) => {
      const m = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? '创建失败';
      message.error(m);
    },
  });

  const switchOrg = async (orgId: string, name: string) => {
    try {
      const resp = await api.post<{ token: string }>(`/orgs/${orgId}/switch`);
      localStorage.setItem('aios_token', resp.data.token);
      message.success(`已切换到 ${name}`);
      qc.invalidateQueries();
    } catch (e: unknown) {
      const m = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? '切换失败';
      message.error(m);
    }
  };

  return (
    <ConsoleShell>
      <Space style={{ marginBottom: 16, width: '100%', justifyContent: 'space-between' }}>
        <Typography.Title level={3} style={{ margin: 0 }}>我的组织</Typography.Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setOpen(true)}>
          新建组织
        </Button>
      </Space>

      <Card>
        <Table<Org>
          loading={isLoading}
          dataSource={data ?? []}
          rowKey="id"
          columns={[
            { title: '名称', dataIndex: 'name' },
            { title: 'Slug', dataIndex: 'slug' },
            {
              title: '我的角色',
              dataIndex: 'role_key',
              width: 120,
              render: (r: string) => (
                <Tag color={r === 'admin' ? 'red' : r === 'engineer' ? 'blue' : 'default'}>{r}</Tag>
              ),
            },
            { title: '创建时间', dataIndex: 'created_at', valueType: 'dateTime', width: 180 },
            {
              title: '操作',
              valueType: 'option',
              width: 220,
              render: (_, r) => [
                <Link key="view" href={`/orgs/${r.id}`}>成员管理</Link>,
                <Button key="switch" type="link" onClick={() => switchOrg(r.id, r.name)}>
                  切换
                </Button>,
              ],
            },
          ]}
        />
      </Card>

      <Modal
        title="新建组织"
        open={open}
        onCancel={() => setOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={createMut.isPending}
      >
        <Form form={form} layout="vertical" onFinish={(v) => createMut.mutate(v)}>
          <Form.Item label="组织名" name="name" rules={[{ required: true }]}>
            <Input placeholder="例：深圳一厂" />
          </Form.Item>
          <Form.Item
            label="Slug"
            name="slug"
            rules={[{ required: true, pattern: /^[a-z0-9-]+$/, message: '小写字母/数字/短横线' }]}
          >
            <Input placeholder="例：sz-factory-1" />
          </Form.Item>
        </Form>
      </Modal>
    </ConsoleShell>
  );
}
