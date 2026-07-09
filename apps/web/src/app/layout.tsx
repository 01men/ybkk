import type { Metadata } from 'next';
import { Providers } from './providers';

export const metadata: Metadata = {
  title: '元冰可可 AIOS',
  description: '制造业 AIOS 控制台',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body style={{ margin: 0 }}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
