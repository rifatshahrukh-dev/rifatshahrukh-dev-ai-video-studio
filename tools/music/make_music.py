"""Royalty-free background music generated in code (no licensing worries).

    python3 tools/music/make_music.py --style calm  --duration 60 --out videos/<slug>/audio/music.wav
    python3 tools/music/make_music.py --style funky --duration 16 --loud 4.4 10.0 --out videos/<slug>/audio/music.wav

calm  = soft corporate synth bed (pads, plucks, light kick) for explainers / pitch videos / tutorials
funky = groovy bass + drums + clav stabs for ads and live-selling scenes
--loud A B : full level between A and B seconds, ducked (x0.32) elsewhere, e.g. under the voice lines.
Then compress:  ffmpeg -i music.wav -b:a 192k music.mp3
"""
import argparse, wave
import numpy as np
ap = argparse.ArgumentParser()
ap.add_argument("--style", choices=["calm", "funky"], default="calm")
ap.add_argument("--duration", type=float, required=True)
ap.add_argument("--loud", type=float, nargs=2, metavar=("FROM", "TO"))
ap.add_argument("--out", required=True)
args = ap.parse_args()
SR = 44100; DUR = args.duration + 0.3
N = int(SR * DUR); out = np.zeros((N, 2))
def midi(m): return 440 * 2 ** ((m - 69) / 12)

if args.style == "calm":
    BPM = 96; BEAT = 60 / BPM
    CHORDS = [[48, 55, 60, 64, 67], [45, 52, 57, 60, 64], [41, 48, 57, 60, 65], [43, 50, 55, 59, 62]]
    bar = 4 * BEAT
    def add(sig, start, ch_gain=(1, 1)):
        i = int(start * SR); j = min(N, i + len(sig))
        if j <= i: return
        out[i:j, 0] += sig[:j - i] * ch_gain[0]; out[i:j, 1] += sig[:j - i] * ch_gain[1]
    rng = np.random.default_rng(3)
    nbars = int(DUR / bar) + 1
    for b in range(nbars):
        ch = CHORDS[b % 4]; t0 = b * bar
        # pad: detuned soft triangles, slow attack/release
        L = int(SR * (bar + 0.6)); t = np.arange(L) / SR
        env = np.minimum(1, t / 0.6) * np.minimum(1, (bar + 0.6 - t) / 0.8)
        pad = sum(np.sin(2 * np.pi * midi(m) * t * d) * 0.5 + np.sin(2 * np.pi * midi(m) * 2 * t * d) * 0.08
                  for m in ch[1:] for d in (0.998, 1.002))
        add(pad * env * 0.035, t0)
        # bass on beats 1 and 3
        for k in (0, 2):
            L = int(SR * BEAT * 1.8); t = np.arange(L) / SR
            bass = np.sin(2 * np.pi * midi(ch[0] - 12 + 12) * t) * np.exp(-t * 1.6) * np.minimum(1, t / 0.01)
            add(bass * 0.16, t0 + k * BEAT)
        # pluck arpeggio, 8th notes (starts in bar 1 so the intro is calmer)
        if b >= 1:
            pat = [ch[2], ch[3], ch[4], ch[3], ch[2] + 12, ch[4], ch[3], ch[4]]
            for k, m in enumerate(pat):
                L = int(SR * 0.9); t = np.arange(L) / SR
                f = midi(m)
                pl = (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t) + 0.1 * np.sin(2 * np.pi * 3 * f * t))
                pl *= np.exp(-t * 6) * np.minimum(1, t / 0.004)
                pan = 0.5 + 0.35 * np.sin(k)
                add(pl * 0.05, t0 + k * BEAT / 2, (1 - pan + 0.5, pan + 0.5))
        # soft kick + shaker from bar 2
        if b >= 2:
            for k in range(4):
                L = int(SR * 0.35); t = np.arange(L) / SR
                if k in (0, 2):
                    kick = np.sin(2 * np.pi * (45 + 80 * np.exp(-t * 30)) * t) * np.exp(-t * 9)
                    add(kick * 0.22, t0 + k * BEAT)
                for h in (0, 1):
                    L2 = int(SR * 0.08); n = rng.standard_normal(L2) * np.exp(-np.arange(L2) / SR * 60)
                    n = np.diff(n, prepend=0)  # brighter
                    add(n * (0.018 if h else 0.03), t0 + k * BEAT + h * BEAT / 2)
    d = int(SR * BEAT * 0.75)
    out[d:] += out[:-d] * 0.22
else:
    BPM = 112; B = 60 / BPM; rng = np.random.default_rng(5)
    def add(sig, t, pan=0.5, g=1.0):
        i = int(t * SR); j = min(N, i + len(sig))
        if j > i:
            out[i:j, 0] += sig[:j - i] * g * (1.2 - pan); out[i:j, 1] += sig[:j - i] * g * (0.2 + pan)
    def env(L, a=0.005, d=8.0):
        t = np.arange(L) / SR; return np.minimum(1, t / a) * np.exp(-t * d)
    CH = [[52, 55, 59, 62], [57, 61, 64, 67]]
    BASS = [(0, 40, .4), (.75, 40, .2), (1.5, 52, .2), (2, 43, .35), (2.75, 45, .2), (3.5, 47, .3),
            (4, 40, .4), (4.75, 52, .2), (5.25, 50, .2), (5.5, 47, .2), (6, 45, .4), (7, 43, .2), (7.5, 45, .3)]
    bar = 4 * B; nb = int(DUR / bar) + 1
    for b in range(nb):
        t0 = b * bar; ch = CH[(b // 2) % 2]
        # drums: kick 1 & "and of 2" & 3, snare 2 & 4 (tight), 16th hats with accents
        for k in (0, 1.5, 2, 3.75):
            L = int(SR * .3); t = np.arange(L) / SR
            add(np.sin(2 * np.pi * (48 + 110 * np.exp(-t * 35)) * t) * np.exp(-t * 11), t0 + k * B, .5, .55)
        for k in (1, 3):
            L = int(SR * .18); n = rng.standard_normal(L) * env(L, .001, 22)
            tone = np.sin(2 * np.pi * 190 * np.arange(L) / SR) * env(L, .001, 30)
            add(n * .35 + tone * .25, t0 + k * B, .5, .9)
        for k in range(16):
            L = int(SR * .05); n = np.diff(rng.standard_normal(L + 1)) * env(L, .0005, 70)
            add(n, t0 + k * B / 4 + (0.012 if k % 2 else 0), .65, .09 if k % 4 == 2 else .05)
        # bass (2-bar figure, slightly overdriven)
        if b % 2 == 0:
            for off, m, ln in BASS:
                if (b // 2) % 2: m += 5
                L = int(SR * ln * B); t = np.arange(L) / SR
                s = np.tanh(2.2 * (np.sin(2 * np.pi * midi(m) * t) + .35 * np.sin(4 * np.pi * midi(m) * t))) * env(L, .004, 4)
                add(s, t0 + off * B, .5, .30)
        # clavinet-style chord stabs on the off-beats
        for k in (.5, 1.75, 2.5, 3.25):
            L = int(SR * .16); t = np.arange(L) / SR
            s = sum(np.sign(np.sin(2 * np.pi * midi(m + 12) * t)) * .25 + np.sin(2 * np.pi * midi(m + 12) * t) for m in ch)
            add(s * env(L, .002, 18), t0 + k * B, .3, .045)
        # wah-ish lead blips every other bar
        if b % 2 == 1:
            for i, m in enumerate([71, 74, 76, 74]):
                L = int(SR * .12); t = np.arange(L) / SR
                add(np.sin(2 * np.pi * midi(m) * t + 2 * np.sin(2 * np.pi * 6 * t)) * env(L, .003, 14), t0 + (2 + i * .5) * B, .75, .06)

g = np.ones(N)
if args.loud:
    g[:] = 0.32
    i, j, r = int(args.loud[0] * SR), int(args.loud[1] * SR), int(.25 * SR)
    g[max(0, i - r):i] = np.linspace(.32, 1, i - max(0, i - r)); g[i:j] = 1; g[j:j + r] = np.linspace(1, .32, len(g[j:j + r]))
fi, fo = int(1.0 * SR), int(min(3.0, DUR / 4) * SR)
g[:fi] *= np.linspace(0, 1, fi); g[-fo:] *= np.linspace(1, 0, fo) ** 1.5
out *= g[:, None]
out /= np.abs(out).max() / 0.89
with wave.open(args.out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype("<i2").tobytes())
print("wrote", args.out, round(DUR, 2), "s")
