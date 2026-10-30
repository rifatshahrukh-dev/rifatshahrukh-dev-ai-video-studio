"""Generate notification-style SFX in code (no licensing): shared/audio/sfx/notify-ding.wav and order-chime.wav.
    python3 scripts/make_notify_sfx.py
"""
import wave
from pathlib import Path
import numpy as np
SR = 44100
OUT = Path(__file__).resolve().parent.parent / "shared" / "audio" / "sfx"

def tone(f, dur, decay, amp=1.0, harm=(1, .35, .12)):
    t = np.arange(int(SR * dur)) / SR
    s = sum(a * np.sin(2 * np.pi * f * (k + 1) * t) for k, a in enumerate(harm))
    return amp * s * np.minimum(1, t / .004) * np.exp(-t * decay)

def place(parts, total):
    out = np.zeros(int(SR * total))
    for start, sig in parts:
        i = int(start * SR); out[i:i + len(sig)] += sig[:len(out) - i]
    return out

def save(name, x):
    x = x / np.abs(x).max() * 0.9
    f = int(.01 * SR); x[-f:] *= np.linspace(1, 0, f)
    with wave.open(str(OUT / name), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).astype("<i2").tobytes())
    print("wrote", OUT / name)

# soft two-tone notification "ding-dong up" (comments, pop-out cards)
save("notify-ding.wav", place([(0, tone(1318.5, .35, 14, .8)), (.075, tone(1760, .45, 11, 1))], .55))
# bright order chime: quick rising triad + sparkle (new order)
save("order-chime.wav", place([(0, tone(1046.5, .4, 9, .7)), (.06, tone(1318.5, .4, 9, .8)), (.12, tone(1568, .55, 7, 1)),
                               (.12, tone(3136, .3, 18, .25, harm=(1,)))], .75))
