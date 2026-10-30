# Video practice

AI video projects made on free tools: Claude plans, Dreamina (Seedance) generates, ffmpeg assembles.

There is no free way for Claude to call Dreamina directly, so generation is done by hand
in the browser at dreamina.capcut.com. Claude's job is to make every credit count.

## Workflow

1. **Plan** – `/shot-list <idea>` writes `projects/<slug>/shots.md`.
2. **Generate (user, in Dreamina)** – keyframe images first, then animate only the best ones.
   Save clips as `projects/<slug>/clips/01.mp4`, `02.mp4`, ... in story order.
3. **Assemble** – `scripts/assemble.sh projects/<slug>` writes `projects/<slug>/final.mp4`.
4. **Learn** – fill in the Results table in `shots.md` (what worked, what failed) so the
   next shot list avoids the same mistakes. Read past Results tables before planning.

## Rules

- Budget is Dreamina's free daily credits, roughly 2–3 video clips a day. Never plan more
  video shots for one day than that; schedule extras for later days.
- Images before video: images are cheap, video is not.
- Character, Location and Style blocks are copied word for word into every prompt.
- Don't suggest paid plans, API keys or paid extensions unless the user asks.
- Video files are gitignored. Commit `shots.md` files, not media.

## Layout

```
projects/<slug>/shots.md     plan + prompts + results
projects/<slug>/clips/       downloaded clips (01.mp4, 02.mp4, ...)
projects/<slug>/final.mp4    assembled video
templates/shots.md           shot list template
scripts/assemble.sh          joins clips into final.mp4
```
