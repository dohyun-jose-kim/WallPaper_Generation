import {build} from 'esbuild';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const shelf=path.dirname(fileURLToPath(import.meta.url));
await build({absWorkingDir:shelf,entryPoints:['adapters/production.tsx'],bundle:true,format:'iife',globalName:'WallpaperAdapter',
  platform:'browser',target:'es2020',jsx:'automatic',define:{'process.env.NODE_ENV':'"production"'},
  outfile:path.join(shelf,'../src/wallpaper_engine/resources/production.js'),legalComments:'eof'});
