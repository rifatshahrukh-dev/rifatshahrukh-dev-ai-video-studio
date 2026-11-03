---
name: showcrew-actors
description: Actors: voices and on-screen presenters. Consent and AI disclosure are built in.
---

# Actors

- Voices: Gemini (default) -> ElevenLabs -> Kokoro (free, offline) -> Edge fallback. `scripts/*-tts.py`. List voices with `scripts/list_voices.py`.
- Presenters: only AI-generated characters, stock people, or someone who gave consent. Never imitate a real person without their consent.
- Say in the video description when a presenter or voice is AI-generated, where the platform or law asks for it.
- If a face moves its lips and the voice can't be synced, don't put a voice over it. Use music, text and captions.
- Voice sync is checked on the final render, never assumed.

## Lip sync
Always run `python3 tools/lipsync/lipsync_check.py <video> --face X Y W H` on any on-screen speaker. If a line plays with the mouth shut or the delay is off, shorten or re-record the line, or ask to run `tools/lipsync/latentsync_job.sh` on a GPU (paid: ask first with the exact files and cost).
