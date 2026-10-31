# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

**AI Video Studio**: an AI-agent video production kit built on HyperFrames (HTML/GSAP videos). New users start
with `SETUP.md` (step-by-step, asks questions, marks mandatory vs optional). Tools:
`tools/tutorial/` (screen recording → tutorial), `tools/screens/` (edit/blur screenshots), `tools/music/`
(generated music), `tools/kaggle/` (free-GPU AI video), `scripts/` (TTS engines, SFX). Brand settings live in
`brand/`. Each video is a self-contained HyperFrames project in `videos/<slug>/`.

It also keeps the **original topic-to-Short workflow** (credit: Cole Medin, coleam00/hyperframes-ai-video-generation),
described in `docs/shorts-workflow.md`: an Archon workflow that spawns `videos/<slug>/` from a template,
runs research + script + TTS + composition + lint, and opens a browser preview. Render is always manual.

Video essentials (sizes, pacing, sound levels, GSAP gotchas) are in `.claude/rules/video-essentials.md`; check frames
with `tools/checks/frames.sh`. The Shorts workflow's commands, architecture and gotchas are in
`docs/shorts-workflow.md`, and its rule files in `.claude/rules/` only load when working on its templates.

## Standing rules for this kit (follow on every video)

The craft (how to plan, direct, review and write posts for each kind of video) is in `PLAYBOOK.md`: read it
before making a video. The rules below are non-negotiable.

### Brand
Read `brand/brand.json` and `brand/BRAND.md` before making any video. If they don't exist yet, run the setup
questions in `SETUP.md` first. Say the brand name in the first narration line.

### Paid tools and credits
- **Never use a paid service, subscription or credits** (Kling, ElevenLabs, paid API tiers…) unless the owner
  asks for it in that conversation. **Always look for a free option first** and say what you found.
- Even when the owner asks for a paid tool, **confirm before every paid job** with the exact model, settings and
  expected cost. An earlier approval never covers a new job.

### Show inputs before sending them anywhere
Before sending any photo or video **anywhere outside this session — paid or free** (Kling, Kaggle notebooks,
Hugging Face Spaces, any AI or upload service), show the owner every file and the full prompt and wait for approval.

### Voiceover sync check (every video)
- On-screen speakers: find when the mouth actually moves (6 fps face-crop strip) and place each line inside that
  window; shorten or re-record a line rather than play it over a closed mouth. If the lips move in another language
  or can't be synced, don't put a voice line over them.
- Narration: captions and on-screen beats land on the spoken words (word timings); every voice clip starts and ends
  ≤ −40 dB (no cut-off words). Spot-check the final render and tell the owner what was checked.

### Pop-up sounds (every video)
Every on-screen pop-up gets a short sound: `shared/audio/sfx/notify-ding.wav` (comments, cards),
`order-chime.wav` (orders / success), `pop.mp3` (quick UI pops). Generate more in code with
`scripts/make_notify_sfx.py`. Keep SFX under the voice (≤ 0.25 volume) and never stack two within 0.3 s.

### Transitions with AI footage
Never cross-fade between two AI clips of the same person (the product ghosts through). Hide the change behind an
on-screen element instead (e.g. the next product card sweeping across the frame), or cut on a natural action.

### Privacy
Blur names, phone numbers, addresses, passwords, account/page/shop names and business figures in every recording or
screenshot. Never commit raw recordings (`source/` is gitignored) or API keys.

### AI footage
Recommend in this order (see `PLAYBOOK.md` §6): **LTX-2.5 on a rented GPU** (best quality and speed, cents per clip),
MiniMax H3 (slow, region-limited open model; paid service for worldwide use), Kling (weakest in tests), and Wan 2.2
on Kaggle when it must cost nothing. Anything paid needs the owner's request and a cost estimate. Keep faces
consistent: start from an approved frame, never cover the lens, swap products below the frame, and never show a side
of a product the model hasn't seen.

### Feedback template (every video sent for review)
End the message with a template so the owner can answer everything at once (one batch of changes = one render):
```
Overall: good to go / needs changes / start over
Scenes (time → what you see): write "ok" or what to change
  0:00–0:04 …
Voice / captions (wording, speed, sync):
Music / sounds (louder, softer, remove):
Text and pop-ups (wording, size, timing):
Ending / call to action:
Anything else:
```

### Saving tokens
Check frames with `tools/checks/frames.sh` (small thumbnails, one sheet per check, only at cuts and key moments);
read only the part of a file you need and keep command output short; suggest a new chat when a video is finished and
a cheaper model (`/model`) for routine steps such as re-renders and small text fixes.

### Scope discipline
Only modify files directly related to the task.
