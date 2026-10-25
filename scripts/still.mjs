/**
 * Tek kare (PNG) çıktısı — görsel kontrol için.
 *   node scripts/still.mjs --comp=Prototype20s --frame=120 [--scale=0.5] [--gl=swangle] [--out=out/kare.png]
 */
import { bundle } from '@remotion/bundler';
import { renderStill, selectComposition } from '@remotion/renderer';
import fs from 'node:fs';
import path from 'node:path';
import { findBrowser, parseArgs, root } from './common.mjs';

const args = parseArgs(process.argv.slice(2));
const compId = args.comp ?? 'Prototype20s';
const frames = String(args.frame ?? '0').split(',').map(Number);
const scale = args.scale ? Number(args.scale) : 1;
const gl = args.gl ?? process.env.REMOTION_GL ?? 'angle';
const props = args.props ? JSON.parse(args.props) : {};
const serveUrl = await bundle({ entryPoint: path.join(root, 'src/index.ts') });
const browserExecutable = findBrowser();
const chromiumOptions = { gl };
const composition = await selectComposition({ serveUrl, id: compId, inputProps: props, browserExecutable, chromiumOptions });
for (const frame of frames) {
  const out = path.resolve(root, args.out && frames.length === 1 ? args.out : `out/stills/${compId}-${String(frame).padStart(4, '0')}.png`);
  fs.mkdirSync(path.dirname(out), { recursive: true });
  const t0 = Date.now();
  await renderStill({ serveUrl, composition, frame, output: out, scale, browserExecutable, chromiumOptions, inputProps: props, timeoutInMilliseconds: 240000 });
  console.log(`✔ ${out} (${((Date.now() - t0) / 1000).toFixed(1)} sn)`);
}
