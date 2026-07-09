'use client';

import { useEffect } from 'react';
import { App, Layout, Menu, Select, Space, Tag } from 'antd';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import {
  DatabaseOutlined,
  AppstoreOutlined,
  BranchesOutlined,
  AuditOutlined,
  LogoutOutlined,
  CloudUploadOutlined,
  NodeIndexOutlined,
  RobotOutlined,
  TeamOutlined,
  MonitorOutlined,
  ApartmentOutlined,
} from '@ant-design/icons';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

const { Header, Content, Sider } = Layout;

type MyOrg = { id: string; name: string; slug: string; role_key: string };

// V3 RBAC: 哪些 perm 可见对应菜单
const NAV_PERMS: { path: string; perm: string; icon: React.ReactNode; label: string }[] = [
  { path: '/datasources', perm: 'datasource.read', icon: <DatabaseOutlined />, label: '数据源' },
  { path: '/ingest', perm: 'ingest.read', icon: <CloudUploadOutlined />, label: '数据接入' },
  { path: '/scenarios', perm: 'scenario.read', icon: <AppstoreOutlined />, label: '场景模板' },
  { path: '/flows', perm: 'flow.read', icon: <BranchesOutlined />, label: '业务流程' },
  { path: '/ontology', perm: 'ontology.read', icon: <NodeIndexOutlined />, label: '本体浏览' },
  { path: '/llm-usage', perm: 'llm.read', icon: <RobotOutlined />, label: 'LLM 用量' },
  { path: '/audits', perm: 'audit.read', icon: <AuditOutlined />, label: '审计日志' },
  { path: '/orgs', perm: 'org.read', icon: <TeamOutlined />, label: '组织' },
  { path: '/monitoring', perm: 'monitoring.read', icon: <MonitorOutlined />, label: '监控' },
];

const ALL_PERMS = new Set([
  'datasource.read', 'ingest.read', 'scenario.read', 'flow.read', 'ontology.read',
  'llm.read', 'audit.read', 'org.read', 'monitoring.read', 'system.manage',
]);

export default function ConsoleShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const qc = useQueryClient();
  const { message } = App.useApp();

  useEffect(() => {
    api.get('/auth/me').catch(() => router.push('/login'));
  }, [router]);

  // V3: 当前用户的 perms
  const { data: me } = useQuery({
    queryKey: ['me'],
    queryFn: async () => (await api.get<{ role_key: string; perms: string[] }>('/auth/me')).data,
    retry: false,
  });
  const myPerms = new Set(me?.perms ?? []);
  // V3: 兜底：若 /auth/me 没返回 perms，按 V0 的 role 给个全集（admin/operator/viewer）
  if (myPerms.size === 0 && me?.role_key) {
    myPerms.add('system.manage');  // V0 admin 默认全开
  }

  // V3: 我的组织列表（顶部切换器）
  const { data: orgs } = useQuery({
    queryKey: ['my-orgs-quick'],
    queryFn: async () => (await api.get<MyOrg[]>('/orgs')).data,
    retry: false,
  });
  const switchOrg = async (orgId: string) => {
    try {
      const r = await api.post<{ token: string }>(`/orgs/${orgId}/switch`);
      localStorage.setItem('aios_token', r.data.token);
      message.success('已切换组织');
      qc.invalidateQueries();
    } catch (e: unknown) {
      const m = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? '切换失败';
      message.error(m);
    }
  };

  const onLogout = async () => {
    await api.post('/auth/logout');
    router.push('/login');
  };

  // 渲染 nav：按 perm 过滤
  const items = NAV_PERMS.filter((n) => myPerms.has(n.perm)).map((n) => ({
    key: n.path,
    icon: n.icon,
    label: <Link href={n.path}>{n.label}</Link>,
  }));

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: '#001529',
          padding: '0 24px',
        }}
      >
        <div style={{ color: '#fff', fontWeight: 600, fontSize: 18 }}>
          <ApartmentOutlined style={{ marginRight: 8 }} />
          元冰可可 AIOS · 控制台
        </div>
        <Space size="middle">
          {/* V3: 组织切换器 */}
          {orgs && orgs.length > 0 ? (
            <Select
              placeholder="切换组织"
              value={me?.role_key ? undefined : undefined}
              onChange={(v) => switchOrg(v)}
              style={{ width: 200 }}
              options={orgs.map((o) => ({
                value: o.id,
                label: `${o.name} (${o.role_key})`,
              }))}
              variant="filled"
            />
          ) : null}
          {/* V3: 当前角色 tag */}
          {me?.role_key ? (
            <Tag color="blue" style={{ marginLeft: 0 }}>{me.role_key}</Tag>
          ) : null}
          <div style={{ color: '#fff', cursor: 'pointer' }} onClick={onLogout}>
            <LogoutOutlined /> 登出
          </div>
        </Space>
      </Header>
      <Layout>
        <Sider width={210} theme="light">
          <Menu mode="inline" selectedKeys={[pathname ?? '']} items={items} />
        </Sider>
        <Content style={{ padding: 24, background: '#f0f2f5' }}>{children}</Content>
      </Layout>
    </Layout>
  );
}
