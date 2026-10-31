---
paths:
  - "videos/**"
---

# Video essentials (short version of the Shorts rules, for every video)

- **Text sizes on 1080×1920:** headline ≥ 56px, labels ≥ 48px, body/captions ≥ 32px, end-card slogan ≥ 120px.
  Shorten text before shrinking it.
- **Pacing:** something new on screen at least every 5 s (a card, a caption, a cut). Pulses and glows don't count.
- **End card:** hold the last frame still for ≥ 1.5 s with logo, slogan and CTA (it becomes the thumbnail and loop frame).
- **Lists:** reveal items one by one, in time with the voice.
- **GSAP:** hide with `tl.set(el, {opacity:0}, 0)` and reveal with `tl.to(...)`; avoid `tl.from()` on long timelines.
  Filters tweened between two values must use the same function list (else they jump).
- **Sound:** SFX `data-volume` ≤ 0.25, fired within 0.15 s of their visual; never two within 0.3 s; one audio clip per
  track at a time. Music is fine for ads when the owner wants it.
- **Speed changes** of a finished video: ffmpeg `setpts` + `atempo` on the rendered MP4, never re-TTS or re-render.
- **Checks:** use `tools/checks/frames.sh` for contact sheets, crops and mouth strips (small images, one sheet per check).
