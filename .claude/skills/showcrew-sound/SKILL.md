---
name: showcrew-sound
description: Sound designer: sound effects for every pop-up, generated music, correct levels.
---

# Sound designer

- A short notification-style sound for every pop-up: `shared/audio/sfx/` (make more with `scripts/make_notify_sfx.py`). Sync with `scripts/sync-video-sfx.sh`.
- Levels: SFX `data-volume` <= 0.25, under the voice. Fire within 0.15 s of the visual. Never two within 0.3 s.
- Music is generated in code (`tools/music/make_music.py`), so no licence is needed.
