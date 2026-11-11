import {build} from 'esbuild';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const shelf=path.dirname(fileURLToPath(import.meta.url));
await build({absWorkingDir:shelf,entryPoints:['adapters/browser.tsx'],bundle:true,format:'iife',globalName:'WallpaperAdapter',
  platform:'browser',target:'es2020',jsx:'automatic',define:{'process.env.NODE_ENV':'"production"'},
  outfile:path.join(shelf,'dist','comparison.js'),legalComments:'eof'});
console.log('Browser adapters built.');
