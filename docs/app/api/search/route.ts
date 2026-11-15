import { source } from '@/lib/source';
import { createFromSource } from 'fumadocs-core/search/server';

// Exported once at build time as a static file; the browser runs the search.
export const revalidate = false;

export const { staticGET: GET } = createFromSource(source, {
  language: 'english',
});
