import { Inter } from 'next/font/google';
import type { Metadata } from 'next';
import { Provider } from '@/components/provider';
import favicon from '@/assets/favicon.svg';
import { appDescription, appName } from '@/lib/shared';
import './global.css';

// Vega, the default shadcn style, sets Inter as the body font.
const inter = Inter({
  subsets: ['latin'],
});

export const metadata: Metadata = {
  metadataBase: new URL('https://fzn0x.github.io/watchtower/'),
  title: {
    template: `%s | ${appName}`,
    default: appName,
  },
  description: appDescription,
  // A static import carries the base path, so the icon resolves under /watchtower.
  icons: { icon: { url: favicon.src, type: 'image/svg+xml' } },
};

export default function Layout({ children }: LayoutProps<'/'>) {
  return (
    <html lang="en" className={inter.className} suppressHydrationWarning>
      <body className="flex flex-col min-h-screen">
        <Provider>{children}</Provider>
      </body>
    </html>
  );
}
