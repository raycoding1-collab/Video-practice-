---
name: shot-list
description: Turn a video idea into a Dreamina/Seedance-ready shot list (keyframe image prompts and motion prompts) sized to the free daily credit budget. Use when the user wants to plan, script or storyboard a new AI video.
---

# Shot list

Turn an idea into `projects/<slug>/shots.md`, ready to paste into Dreamina
(dreamina.capcut.com) one prompt at a time.

## 1. Pin down the brief

From the user's message, work out the idea, total length, aspect ratio and style.
Defaults: 15 s, 16:9, cinematic photoreal. Ask only if the idea itself is missing.

Read the Results tables in earlier `projects/*/shots.md` files and apply what they learned.

## 2. Size it to the budget

- Free daily credits cover about 2–3 video clips. Plan at most 3 video shots per day and put
  the rest under a "Day 2", "Day 3"... heading.
- Each shot is 5 s, so length = shots × 5 s.
- Don't state exact credit costs; tell the user to check their balance in Dreamina.

## 3. Write the blocks once

Write a Character block (if there is a person), a Location block and a Style block. Use
concrete, visual, fixed details: hair, clothing colours, materials, light, lens look.
These blocks are pasted word for word into every prompt. Never paraphrase them between
shots; paraphrasing is what makes characters and places drift.

If there is a recurring character, add a "Step 0" image prompt for a plain reference
portrait so the user can feed it to Dreamina as a reference image.

## 4. Write each shot

- **Purpose** – one line: what the shot does in the story.
- **Keyframe image prompt** – framing + subject + the action frozen mid-moment, then the
  Character, Location and Style blocks written out in full, so it pastes without edits.
- **Motion prompt** – for image-to-video. Only what moves: one main action and one camera
  move. Don't re-describe what is already in the image.
- **Camera** – one of: static, slow push-in, slow pull-out, pan left/right, tilt up/down,
  orbit left/right, handheld.
- **Continuity** – what must match the previous shot. If a shot continues the previous one,
  say "use the last frame of shot N as the start frame".

Rules that save credits:

- Keep the change within a shot small. Fast action, crowds, readable text and complex hand
  gestures fail most often; avoid them or keep them out of focus.
- Tell the user to make 2–4 keyframe images per shot, pick the best, and only then animate.

## 5. Save and hand off

Copy the structure of `templates/shots.md`. The slug is the idea in kebab-case. Then tell
the user, briefly: the order to generate in, to save clips as
`projects/<slug>/clips/01.mp4`, `02.mp4`, ..., and to run `scripts/assemble.sh projects/<slug>`.
