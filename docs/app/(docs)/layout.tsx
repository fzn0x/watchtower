import { DocsLayout } from 'fumadocs-ui/layouts/notebook';
import { baseOptions } from '@/lib/layout.shared';
import { source } from '@/lib/source';

export default function Layout({ children }: LayoutProps<'/'>) {
  const { nav, ...base } = baseOptions();

  return (
    <DocsLayout {...base} nav={{ ...nav, mode: 'top' }} tree={source.getPageTree()}>
      {children}
    </DocsLayout>
  );
}
