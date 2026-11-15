import Image from 'next/image';
import type { BaseLayoutProps } from 'fumadocs-ui/layouts/shared';
import logo from '@/assets/logo.svg';
import { appName, repoUrl } from './shared';

export function baseOptions(): BaseLayoutProps {
  return {
    nav: {
      title: (
        <>
          {/* The logo is drawn in light ink, so it sits on a navy tile in both themes. */}
          <span className="inline-flex size-7 items-center justify-center rounded-md bg-[#0b1220]">
            <Image src={logo} alt="" width={22} height={22} priority />
          </span>
          <span className="font-semibold">{appName}</span>
        </>
      ),
    },
    githubUrl: repoUrl,
  };
}
