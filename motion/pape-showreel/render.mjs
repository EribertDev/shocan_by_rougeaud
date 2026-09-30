// Rendu image par image de index.html puis encodage MP4.
//   node render.mjs                 -> pape-showreel.mp4 (60 fps, 1920x1080)
//   node render.mjs --stills 1,3.2  -> captures PNG à ces instants (vérification)
import { createRequire } from 'node:module';
import { spawn, execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const require = createRequire(import.meta.url);
const globalRoot = execSync('npm root -g').toString().trim();
const { chromium } = require(path.join(globalRoot, 'playwright'));

const dir = path.dirname(fileURLToPath(import.meta.url));
const FPS = 60, DURATION = 20;
const FFMPEG = process.env.FFMPEG || 'ffmpeg';
const args = process.argv.slice(2);
const stillsArg = args.includes('--stills') ? args[args.indexOf('--stills') + 1] : null;
const outDir = args.includes('--out') ? args[args.indexOf('--out') + 1] : dir;

const browser = await chromium.launch({ args: ['--allow-file-access-from-files'] });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
await page.goto('file://' + path.join(dir, 'index.html') + '?render');
await page.evaluate(() => window.ready);

const grab = async (t, frame) => {
  await page.evaluate(([t, f]) => window.renderFrame(t, f), [t, frame]);
  return page.screenshot({ type: 'png', clip: { x: 0, y: 0, width: 1920, height: 1080 } });
};

if (stillsArg) {
  const fs = await import('node:fs');
  for (const s of stillsArg.split(',').map(Number)) {
    fs.writeFileSync(path.join(outDir, `still-${s.toFixed(2)}.png`), await grab(s, Math.round(s * FPS)));
  }
} else {
  const total = FPS * DURATION;
  const audio = path.join(dir, 'soundtrack.wav');
  const ff = spawn(FFMPEG, [
    '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-',
    '-i', audio,
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p',
    '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart',
    path.join(dir, 'pape-showreel.mp4'),
  ], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let f = 0; f < total; f++) {
    const buf = await grab(f / FPS, f);
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (f % 120 === 0) console.log(`frame ${f}/${total}`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
}
await browser.close();
