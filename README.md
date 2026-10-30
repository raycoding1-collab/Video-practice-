# Video practice

Make AI videos for free: **Claude plans, Dreamina generates, a script assembles.**

| Step | Who | Where |
|------|-----|-------|
| 1. Plan the shots and write the prompts | Claude | `/shot-list <your idea>` in Claude Code |
| 2. Generate keyframe images, then animate the best | You | [dreamina.capcut.com](https://dreamina.capcut.com) (free daily credits) |
| 3. Join the clips into one video | Script | `scripts/assemble.sh projects/<name>` |

Dreamina has no free API or official Claude connector, so step 2 is copy and paste.

## Try it now

A ready-made 15-second test is in [`projects/first-test/shots.md`](projects/first-test/shots.md).

1. Sign in at dreamina.capcut.com (the global site) and check your free credit balance.
2. **Step 0:** paste the character reference prompt into image generation. Keep the best one.
3. For each shot: paste the **keyframe image prompt**, make 2–4 images, pick the best,
   then use image-to-video with the **motion prompt**, 5 seconds.
4. Download each clip into `projects/first-test/clips/` as `01.mp4`, `02.mp4`, `03.mp4`.
5. Run:

   ```bash
   scripts/assemble.sh projects/first-test
   ```

   This writes `projects/first-test/final.mp4`. Clips can be different sizes or have no
   audio; the script evens them out. Requires [ffmpeg](https://ffmpeg.org/).
6. Fill in the Results table in `shots.md`. Claude reads it before planning the next video.

## Your own video

In Claude Code, inside this folder:

```
/shot-list a 20-second ad for a handmade candle brand, vertical for Reels
```

Claude writes `projects/<name>/shots.md`, planned to fit about 2–3 free clips a day.

## Notes

- Video files are gitignored to keep the repo small; only the plans are committed.
- Free Dreamina clips may carry a watermark or commercial-use limits. Check the terms
  before using them for clients.
