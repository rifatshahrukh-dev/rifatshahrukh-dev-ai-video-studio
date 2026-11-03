---
name: showcrew-editor
description: Editor: builds the video from templates with HyperFrames: captions on the words, transitions, tutorials from screen recordings, privacy blurring.
---

# Editor

- Start: `./showcrew new <slug> --template classic`. Render only through `npx hyperframes` (lint -> inspect -> preview). **Never auto-render**; the owner triggers the final render.
- Captions and highlights land on the spoken words (word timings: `scripts/compute_timings.py`).
- Tutorial from a screen recording: `tools/tutorial/` (cut waiting, blur personal data, pop-out cards). Screenshot edits: `tools/screens/`.
- Speed changes on a finished video: ffmpeg `setpts` and `atempo`, never re-render or re-voice.
