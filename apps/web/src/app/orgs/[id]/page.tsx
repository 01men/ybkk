'use client';

import { App, Button, Card, Form, Input, Result, Select, Space, Spin, Table, Tag, Typography } from 'antd';
import { useState } from 'react';
import Link from 'next/link';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useParams } from 'next/navigation';
import ConsoleShell from '../../console-shell';
import { api } from '@/lib/api';

type Member = {
  user_id: string;
  username: string;
  role_key: string;
  joined_at: string;
};

type Org = {
  id: string;
  name: string;
  slug: string;
};

const ROLE_OPTIONS = [
  { value: 'admin', label: 'admin (管理员)' },
  { value: 'engineer', label: 'engineer (工程师)' },
  { value: 'operator', label: 'operator (操作员)' },
  { value: 'viewer', label: 'viewer (只读)' },
];

export default function OrgMembersPage() {
  const { id } = useParams<{ id: string }>();
  const { message } = App.useApp();
  const qc = useQueryClient();
  const [inviteOpen, setInviteOpen] = useState(false);

  const { data: members, isLoading } = useQuery({
    queryKey: ['org-members', id],
    queryFn: async () => (await api.get<Member[]>(`/orgs/${id}/members`)).data,
  });

  const inviteMut = useMutation({
    mutationFn: async (v: { username: string; role_key: string }) =>
      (await api.post(`/orgs/${id}/members`, v)).data,
    onSuccess: () => {
      message.success('已邀请');
      setInviteOpen(false);
      qc.invalidateQueries({ queryKey: ['org-members', id] });
    },
    onError: (e: unknown) => {
      const m = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? '邀请失败';
      message.error(m);
    },
  });

  const updateRole = async (userId: string, role: string) => {
    try {
      await api.patch(`/orgs/${id}/members/${userId}`, { role_key: role });
      message.success('已更新');
      qc.invalidateQueries({ queryKey: ['org-members', id] });
    } catch (e: unknown) {
      const m = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? '更新失败';
      message.error(m);
    }
  };

  const remove = async (userId: string) => {
    try {
      await api.delete(`/orgs/${id}/members/${userId}`);
      message.success('已移除');
      qc.invalidateQueries({ queryKey: ['org-members', id] });
    } catch (e: unknown) {
      const m = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? '移除失败';
      message.error(m);
    }
  };

  if (isLoading) {
    return (
      <ConsoleShell>
        <Spin tip="加载中…" />
      </ConsoleShell>
    );
  }

  return (
    <ConsoleShell>
      <Space style={{ marginBottom: 16 }}>
        <Link href="/orgs">← 返回组织列表</Link>
      </Space>
      <Typography.Title level={3}>组织成员</Typography.Title>

      <Card
        extra={<Button type="primary" onClick={() => setInviteOpen(true)}>邀请用户</Button>}
      >
        <Table<Member>
          dataSource={members ?? []}
          rowKey="user_id"
          columns={[
            { title: '用户名', dataIndex: 'username' },
            {
              title: '角色',
              dataIndex: 'role_key',
              width: 220,
              render: (r: string, row) => (
                <Select
                  value={r}
                  options={ROLE_OPTIONS}
                  onChange={(v) => updateRole(row.user_id, v)}
                  style={{ width: 200 }}
                />
              ),
            },
            { title: '加入时间', dataIndex: 'joined_at', valueType: 'dateTime', width: 180 },
            {
              title: '操作',
              width: 100,
              render: (_, r) => (
                <Button type="link" danger onClick={() => remove(r.user_id)}>
                  移除
                </Button>
              ),
            },
          ]}
        />
      </Card>

      {inviteOpen && (
        <Card style={{ marginTop: 16 }}>
          <Form
            layout="inline"
            onFinish={(v) => inviteMut.mutate(v)}
            initialValues={{ role_key: 'viewer' }}
          >
            <Form.Item label="用户名" name="username" rules={[{ required: true }]}>
              <Input placeholder="对方登录名" />
            </Form.Item>
            <Form.Item label="角色" name="role_key">
              <Select options={ROLE_OPTIONS} style={{ width: 180 }} />
            </Form.Item>
            <Form.Item>
              <Button type="primary" htmlType="submit" loading={inviteMut.isPending}>
                邀请
              </Button>
              <Button onClick={() => setInviteOpen(false)} style={{ marginLeft: 8 }}>
                取消
              </Button>
            </Form.Item>
          </Form>
        </Card>
      )}
    </ConsoleShell>
  );
}
