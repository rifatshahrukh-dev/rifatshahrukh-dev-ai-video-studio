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
