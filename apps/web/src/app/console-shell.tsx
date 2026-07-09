'use client';

import { useEffect } from 'react';
import { Layout, Menu } from 'antd';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import {
  DatabaseOutlined,
  AppstoreOutlined,
  BranchesOutlined,
  AuditOutlined,
  LogoutOutlined,
} from '@ant-design/icons';
import { api } from '@/lib/api';

const { Header, Content, Sider } = Layout;

const items = [
  { key: '/datasources', icon: <DatabaseOutlined />, label: <Link href="/datasources">数据源</Link> },
  { key: '/scenarios', icon: <AppstoreOutlined />, label: <Link href="/scenarios">场景模板</Link> },
  { key: '/flows', icon: <BranchesOutlined />, label: <Link href="/flows">业务流程</Link> },
  { key: '/audits', icon: <AuditOutlined />, label: <Link href="/audits">审计日志</Link> },
];

export default function ConsoleShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    api.get('/auth/me').catch(() => router.push('/login'));
  }, [router]);

  const onLogout = async () => {
    await api.post('/auth/logout');
    router.push('/login');
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#001529' }}>
        <div style={{ color: '#fff', fontWeight: 600, fontSize: 18 }}>元冰可可 AIOS · 控制台</div>
        <div style={{ color: '#fff', cursor: 'pointer' }} onClick={onLogout}>
          <LogoutOutlined /> 登出
        </div>
      </Header>
      <Layout>
        <Sider width={200} theme="light">
          <Menu mode="inline" selectedKeys={[pathname ?? '']} items={items} />
        </Sider>
        <Content style={{ padding: 24, background: '#f0f2f5' }}>{children}</Content>
      </Layout>
    </Layout>
  );
}
