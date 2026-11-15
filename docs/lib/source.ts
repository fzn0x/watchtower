import { loader } from 'fumadocs-core/source';
import { defineDocs } from 'fumadocs-mdx/macro';
import { metaSchema, pageSchema } from 'fumadocs-core/source/schema';
import { docsRoute } from './shared';

const docs = defineDocs({
  dir: 'content',
  docs: {
    // `navTitle` (optional) sets a shorter sidebar label than the page title,
    // like "Home" for the page titled "Watchtower".
    schema: pageSchema.extend({ navTitle: pageSchema.shape.description }),
  },
  meta: {
    schema: metaSchema,
  },
});

// See https://fumadocs.dev/docs/headless/source-api for more info
export const source = loader({
  baseUrl: docsRoute,
  source: docs.toFumadocsSource(),
  plugins: ({ typedPlugin }) => [
    typedPlugin({
      transformPageTree: {
        file(node, filePath) {
          const file = filePath ? this.storage.read(filePath) : undefined;
          if (file?.format === 'page' && file.data.navTitle) node.name = file.data.navTitle;
          return node;
        },
      },
    }),
  ],
});
