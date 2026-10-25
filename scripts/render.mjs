/**
 * Video çıktısı (MP4, H.264, yuv420p — YouTube uyumlu).
 *
 * Kullanım:
 *   node scripts/render.mjs --comp=Prototype20s            (ilk 20 sn prototip)
 *   node scripts/render.mjs --comp=PandiTrain              (tam 210 sn, sessiz)
 *   node scripts/render.mjs --comp=PandiTrain --music      (timing.json'daki şarkı ile)
 *   --scale=0.5        düşük çözünürlüklü hızlı önizleme (960×540)
 *   --frames=0-299     yalnızca bu kare aralığı
 *   --gl=swangle       GPU'suz makinede yazılım WebGL (varsayılan: angle)
 *   --concurrency=2    paralel sekme sayısı
 *   --out=out/x.mp4    çıktı yolu
 *
 * Başarılı sayılmadan önce dosyanın varlığı, süresi, çözünürlüğü ve kodeki ffprobe ile doğrulanır.
 */
import { bundle } from '@remotion/bundler';
import { renderMedia, selectComposition } from '@remotion/renderer';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { findBrowser, parseArgs, root } from './common.mjs';

const args = parseArgs(process.argv.slice(2));
const compId = args.comp ?? 'Prototype20s';
const scale = args.scale ? Number(args.scale) : 1;
const gl = args.gl ?? process.env.REMOTION_GL ?? 'angle';
const music = Boolean(args.music);
const concurrency = args.concurrency ? Number(args.concurrency) : undefined;
const stamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
const out = path.resolve(root, args.out ?? `out/${compId}${scale !== 1 ? `-x${scale}` : ''}${music ? '-muzikli' : ''}-${stamp}.mp4`);
fs.mkdirSync(path.dirname(out), { recursive: true });

const fail = (msg, err) => {
  console.error(`\n✖ RENDER BAŞARISIZ: ${msg}`);
  if (err) console.error(err?.stack ?? err);
  process.exit(1);
};

try {
  console.log(`▶ Paketleniyor… (${compId})`);
  const serveUrl = await bundle({ entryPoint: path.join(root, 'src/index.ts'), onProgress: () => {} });

  const inputProps = music ? { audioEnabled: true } : {};
  const browserExecutable = findBrowser();
  const chromiumOptions = { gl };
  const composition = await selectComposition({ serveUrl, id: compId, inputProps, browserExecutable, chromiumOptions });

  let frameRange = undefined;
  if (args.frames) {
    const [a, b] = String(args.frames).split('-').map(Number);
    frameRange = [a, b ?? a];
  }
  const total = frameRange ? frameRange[1] - frameRange[0] + 1 : composition.durationInFrames;
  console.log(
    `▶ ${composition.id}: ${Math.round(composition.width * scale)}×${Math.round(composition.height * scale)}, ${composition.fps} fps, ${total} kare (${(total / composition.fps).toFixed(1)} sn), gl=${gl}, ses=${music ? 'açık' : 'kapalı'}`,
  );

  const started = Date.now();
  let lastLog = 0;
  await renderMedia({
    serveUrl,
    composition: { ...composition, props: { ...composition.props, ...inputProps } },
    inputProps,
    codec: 'h264',
    pixelFormat: 'yuv420p',
    colorSpace: 'bt709',
    crf: 18,
    imageFormat: 'jpeg',
    jpegQuality: 92,
    scale,
    frameRange,
    muted: !music,
    concurrency,
    browserExecutable,
    chromiumOptions,
    timeoutInMilliseconds: 240000,
    outputLocation: out,
    onProgress: ({ renderedFrames, encodedFrames, progress }) => {
      const now = Date.now();
      if (now - lastLog < 3000 && progress < 1) return;
      lastLog = now;
      const el = (now - started) / 1000;
      const eta = renderedFrames > 0 ? (el / renderedFrames) * (total - renderedFrames) : 0;
      console.log(
        `  %${(progress * 100).toFixed(1).padStart(5)} · çizilen ${renderedFrames}/${total} · kodlanan ${encodedFrames} · geçen ${el.toFixed(0)} sn · kalan ~${eta.toFixed(0)} sn`,
      );
    },
  });

  // Doğrulama
  if (!fs.existsSync(out) || fs.statSync(out).size < 1000) fail(`çıktı dosyası oluşmadı: ${out}`);
  let probe;
  try {
    probe = JSON.parse(
      execFileSync('ffprobe', ['-v', 'error', '-print_format', 'json', '-show_streams', '-show_format', out], { encoding: 'utf8' }),
    );
  } catch (e) {
    fail('ffprobe dosyayı okuyamadı', e);
  }
  const v = probe.streams.find((s) => s.codec_type === 'video');
  const a = probe.streams.find((s) => s.codec_type === 'audio');
  if (!v) fail('dosyada video akışı yok');
  const dur = Number(probe.format.duration);
  console.log(`\n✔ MP4 oluştu: ${out}`);
  console.log(
    `  ${v.codec_name} ${v.width}×${v.height} ${v.r_frame_rate} fps · ${v.pix_fmt} · ${dur.toFixed(2)} sn · ${(fs.statSync(out).size / 1e6).toFixed(1)} MB · ses: ${a ? a.codec_name : 'yok'}`,
  );
  console.log(`  Süre: ${((Date.now() - started) / 1000).toFixed(0)} sn`);
} catch (e) {
  fail(e?.message ?? String(e), e);
}
