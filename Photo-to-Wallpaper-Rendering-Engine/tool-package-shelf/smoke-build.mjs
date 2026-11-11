// Installation smoke check only: compile unchanged source, no wallpaper adapters.
import { build } from 'esbuild';
import { mkdir, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const shelf = path.dirname(fileURLToPath(import.meta.url));
const out = path.join(shelf, 'dist', 'smoke');
await mkdir(out, { recursive: true });
const result = {};
for (const [id, entry] of [
  ['D1', 'src/renderer.ts'],
  ['D2', 'src/GlassRenderer.ts'],
  ['D3', 'src/index.tsx'],
]) {
  const built = await build({
    absWorkingDir: shelf,
    entryPoints: [path.join('upstream', id, entry)],
    bundle: true,
    format: 'iife',
    globalName: `Preparation${id}`,
    platform: 'browser',
    target: 'es2020',
    jsx: 'automatic',
    define: { 'process.env.NODE_ENV': '"production"' },
    outfile: path.join(out, `${id}.js`),
    metafile: true,
    legalComments: 'eof',
    logLevel: 'warning',
  });
  result[id] = { status: 'compiled', inputs: Object.keys(built.metafile.inputs) };
}
// React DOM is also required by the future D3 scene adapter.
await build({
  stdin: { contents: 'export { createRoot } from "react-dom/client";', resolveDir: shelf },
  bundle: true, format: 'iife', globalName: 'PreparationReactDOM',
  define: { 'process.env.NODE_ENV': '"production"' },
  outfile: path.join(out, 'react-dom.js'), logLevel: 'warning',
});
await writeFile(path.join(out, 'build-results.json'), JSON.stringify(result, null, 2) + '\n');
console.log('PASS: esbuild native binary, D1/D2/D3 source bundles, React DOM bundle.');
