#!/usr/bin/env node
// Render an HTML motion-graphics page to MP4, frame by frame (no GPU, no credits).
// The page sets window.DURATION (seconds) and may define window.seek(t) for
// JS-driven effects; CSS animations are paused and stepped automatically.
//
// Usage: node scripts/render-motion.js motion/<name>.html [out.mp4] [fps]
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');

(async () => {
  const [src, outArg, fpsArg] = process.argv.slice(2);
  if (!src) {
    console.error('usage: node scripts/render-motion.js <page.html> [out.mp4] [fps]');
    process.exit(1);
  }
  const out = outArg || src.replace(/\.html$/, '.mp4');
  const fps = Number(fpsArg) || 30;

  const browser = await chromium.launch();
  // Pages are laid out at 540x960 and captured at 2x: 1080x1920 vertical video.
  const page = await browser.newPage({ viewport: { width: 540, height: 960 }, deviceScaleFactor: 2 });
  await page.goto('file://' + path.resolve(src));
  await page.evaluate(() => document.fonts.ready);
  const duration = await page.evaluate(() => window.DURATION);
  if (!duration) throw new Error('page must set window.DURATION');

  const ffmpeg = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-c:v', 'mjpeg',
    '-framerate', String(fps), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
    '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });

  const frames = Math.round(duration * fps);
  for (let i = 0; i < frames; i++) {
    const t = i / fps;
    await page.evaluate((t) => {
      // seek first: it may show scenes, which is what creates their CSS animations.
      if (window.seek) window.seek(t);
      for (const a of document.getAnimations()) { a.pause(); a.currentTime = t * 1000; }
    }, t);
    ffmpeg.stdin.write(await page.screenshot({ type: 'jpeg', quality: 92 }));
    if (i % fps === 0) process.stdout.write(`\r  ${t.toFixed(0)}s / ${duration}s`);
  }
  ffmpeg.stdin.end();
  await new Promise((resolve, reject) => ffmpeg.on('close', (c) => (c ? reject(new Error('ffmpeg ' + c)) : resolve())));
  await browser.close();
  console.log(`\rWrote ${out} (${frames} frames, ${duration}s)`);
})().catch((e) => { console.error(e); process.exit(1); });
