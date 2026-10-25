import fs from 'node:fs';
import path from 'node:path';

/** Basit --anahtar=değer argüman ayrıştırıcı. */
export const parseArgs = (argv) => {
  const out = {};
  for (const a of argv) {
    const m = a.match(/^--([^=]+)(?:=(.*))?$/);
    if (m) out[m[1]] = m[2] ?? true;
  }
  return out;
};

/**
 * Tarayıcı: REMOTION_BROWSER ortam değişkeni → önceden kurulu headless shell → Remotion'un kendi indirdiği.
 */
export const findBrowser = () => {
  if (process.env.REMOTION_BROWSER) return process.env.REMOTION_BROWSER;
  const base = '/opt/pw-browsers';
  if (fs.existsSync(base)) {
    for (const d of fs.readdirSync(base)) {
      if (!d.startsWith('chromium_headless_shell')) continue;
      for (const sub of ['chrome-headless-shell-linux64/chrome-headless-shell', 'chrome-linux/headless_shell']) {
        const p = path.join(base, d, sub);
        if (fs.existsSync(p)) return p;
      }
    }
  }
  return null;
};

export const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
