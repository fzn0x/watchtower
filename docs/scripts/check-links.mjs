// Checks every internal link, asset, and anchor in the static export (out/).
// The site is plain HTML after `npm run build`, so this reads the files
// directly and needs no dependencies. Exits 1 if anything is broken.
import { readFileSync, readdirSync, statSync, existsSync } from 'node:fs';
import { join, relative, sep } from 'node:path';

const OUT = 'out';
const BASE = '/watchtower';

function htmlFiles(dir) {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) return htmlFiles(path);
    return path.endsWith('.html') ? [path] : [];
  });
}

// out/tools/index.html is served at /watchtower/tools/.
function urlOf(file) {
  const rel = relative(OUT, file).split(sep).join('/');
  return `${BASE}/${rel.replace(/(^|\/)index\.html$/, '$1')}`;
}

// The file a site path is served from, or null.
function fileFor(path) {
  const local = join(OUT, decodeURIComponent(path.slice(BASE.length)));
  for (const candidate of [local, join(local, 'index.html'), `${local}.html`]) {
    if (existsSync(candidate) && statSync(candidate).isFile()) return candidate;
  }
  return null;
}

const decode = (s) => s.replace(/&amp;/g, '&').replace(/&quot;/g, '"').replace(/&#x27;/g, "'");

if (!existsSync(OUT)) {
  console.error(`No ${OUT}/ directory. Run npm run build first.`);
  process.exit(1);
}

const pages = new Map(); // file -> { url, html, ids }
for (const file of htmlFiles(OUT)) {
  const html = readFileSync(file, 'utf8');
  const ids = new Set([...html.matchAll(/\sid="([^"]+)"/g)].map((m) => decode(m[1])));
  pages.set(file, { url: urlOf(file), html, ids });
}

const broken = [];
let checked = 0;
for (const [file, { url, html }] of pages) {
  for (const m of html.matchAll(/\s(?:href|src)="([^"]+)"/g)) {
    const ref = decode(m[1]);
    if (/^(?:[a-z][a-z0-9+.-]*:|\/\/)/i.test(ref)) continue; // external, mailto:, data:
    checked += 1;
    const [pathPart, anchor] = ref.split('#');
    const path = pathPart === '' ? url : pathPart;
    if (!path.startsWith(`${BASE}/`) && path !== BASE) {
      broken.push(`${url}: ${ref} (not under ${BASE})`);
      continue;
    }
    const target = pathPart === '' ? file : fileFor(path);
    if (!target) {
      broken.push(`${url}: ${ref} (no such page or file)`);
      continue;
    }
    if (anchor && target.endsWith('.html') && !pages.get(target)?.ids.has(decodeURIComponent(anchor))) {
      broken.push(`${url}: ${ref} (no element with id "${anchor}")`);
    }
  }
}

if (broken.length) {
  console.error(`${broken.length} broken link(s):`);
  for (const line of [...new Set(broken)]) console.error(`  ${line}`);
  process.exit(1);
}
console.log(`Checked ${checked} internal links in ${pages.size} pages: all resolve.`);
