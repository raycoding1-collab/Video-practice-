#!/usr/bin/env node
// Render an HTML motion-graphics page to MP4, frame by frame (no GPU, no credits).
//
// The page sets window.DURATION (seconds), may define window.seek(t) for JS-driven
// effects, and may set window.SOUND ({bpm, music: [start, end], cues: [...]}) to get
// a synthesised soundtrack (see scripts/sound.py). CSS animations are stepped
// automatically. Each frame blends BLUR sub-frames for real motion blur.
//
// Usage: node scripts/render-motion.js motion/<name>.html [out.mp4]
// Env:   FPS (default 30), BLUR sub-frames per frame (default 4, 1 = off)
const { chromium } = require('playwright');
const { spawn, execFileSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

(async () => {
  const [src, outArg] = process.argv.slice(2);
  if (!src) {
    console.error('usage: node scripts/render-motion.js <page.html> [out.mp4]');
    process.exit(1);
  }
  const out = outArg || src.replace(/\.html$/, '.mp4');
  const fps = Number(process.env.FPS) || 30;
  const blur = Math.max(1, Number(process.env.BLUR) || 4);
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'motion-'));

  const browser = await chromium.launch();
  // Pages are laid out at 540x960 and captured at 2x: 1080x1920 vertical video.
  const page = await browser.newPage({ viewport: { width: 540, height: 960 }, deviceScaleFactor: 2 });
  await page.goto('file://' + path.resolve(src));
  await page.evaluate(() => document.fonts.ready);
  const { duration, sound } = await page.evaluate(() => ({ duration: window.DURATION, sound: window.SOUND }));
  if (!duration) throw new Error('page must set window.DURATION');

  // Sub-frames come in at fps*blur; tmix averages each group, select keeps one per group.
  const video = path.join(tmp, 'video.mp4');
  const vf = blur > 1 ? ['-vf', `tmix=frames=${blur},select='eq(mod(n\\,${blur})\\,${blur - 1})'`] : [];
  const ffmpeg = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-c:v', 'mjpeg',
    '-framerate', String(fps * blur), '-i', '-', ...vf, '-r', String(fps),
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', video],
    { stdio: ['pipe', 'inherit', 'inherit'] });

  const frames = Math.round(duration * fps);
  for (let i = 0; i < frames; i++) {
    for (let k = 0; k < blur; k++) {
      const t = (i + (k / blur) * 0.5) / fps; // 180-degree shutter
      await page.evaluate((t) => {
        // seek first: it may show scenes, which is what creates their CSS animations.
        if (window.seek) window.seek(t);
        for (const a of document.getAnimations()) { a.pause(); a.currentTime = t * 1000; }
      }, t);
      ffmpeg.stdin.write(await page.screenshot({ type: 'jpeg', quality: 92 }));
    }
    if (i % fps === 0) process.stdout.write(`\r  ${(i / fps).toFixed(0)}s / ${duration}s`);
  }
  ffmpeg.stdin.end();
  await new Promise((resolve, reject) => ffmpeg.on('close', (c) => (c ? reject(new Error('ffmpeg ' + c)) : resolve())));
  await browser.close();

  if (sound) {
    const cues = path.join(tmp, 'cues.json');
    const wav = path.join(tmp, 'sound.wav');
    fs.writeFileSync(cues, JSON.stringify({ duration, ...sound }));
    execFileSync('python3', [path.join(__dirname, 'sound.py'), cues, wav], { stdio: 'inherit' });
    execFileSync('ffmpeg', ['-y', '-v', 'error', '-i', video, '-i', wav, '-map', '0:v', '-map', '1:a',
      '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-movflags', '+faststart', out]);
  } else {
    execFileSync('ffmpeg', ['-y', '-v', 'error', '-i', video, '-c', 'copy', '-movflags', '+faststart', out]);
  }
  fs.rmSync(tmp, { recursive: true, force: true });
  console.log(`\rWrote ${out} (${frames} frames, ${duration}s${sound ? ', with sound' : ''})`);
})().catch((e) => { console.error(e); process.exit(1); });
