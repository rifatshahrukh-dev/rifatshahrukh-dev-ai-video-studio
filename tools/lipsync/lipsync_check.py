"""Lip-sync check: does the mouth move when the voice speaks? Free, CPU only, no models.

    python3 tools/lipsync/lipsync_check.py video.mp4 --face X Y W H [--fps 12]

--face is the face box in video pixels (look at one frame sheet to pick it). The mouth is the lower 40% of that box.
Reports: speech lines (voice on), the share of each line where the mouth moves, the best audio-to-mouth delay in seconds
(about 0 is in sync; |delay| above 0.12 s looks off), and any line where the mouth stays shut while the voice speaks.
Exit code 1 when a problem is found. It measures motion, not words: it cannot prove a lip shape is right.
"""
import argparse
import subprocess
import sys

import numpy as np


def signals(video, box, fps):
    x, y, w, h = box
    my = y + int(h * 0.6)
    mh = max(2, int(h * 0.4))
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vf", f"fps={fps},crop={w}:{mh}:{x}:{my},scale=48:24,format=gray",
                          "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, 24, 48).astype(np.float32)
    mouth = np.r_[0, np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2))]
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768
    n = len(a) // (16000 // fps)
    voice = np.sqrt((a[: n * (16000 // fps)].reshape(n, -1) ** 2).mean(axis=1))
    m = min(len(mouth), len(voice))
    return mouth[:m], voice[:m]


def analyse(mouth, voice, fps):
    on = voice > max(voice.max() * 0.1, 1e-4)
    mv = mouth > max(mouth.max() * 0.25, 1e-3)
    lines, i = [], 0
    while i < len(on):
        if on[i]:
            j = i
            while j < len(on) and (on[j] or (j + 1 < len(on) and on[j + 1])):
                j += 1
            if j - i >= 2:
                lines.append((i / fps, j / fps, float(mv[i:j].mean())))
            i = j
        i += 1
    best, lag = -2, 0
    for k in range(-int(0.4 * fps), int(0.4 * fps) + 1):
        a, b = (voice[: len(voice) - k], mouth[k:]) if k >= 0 else (voice[-k:], mouth[: len(mouth) + k])
        if len(a) > 3 and a.std() > 0 and b.std() > 0:
            c = float(np.corrcoef(a, b)[0, 1])
            if c > best:
                best, lag = c, k / fps
    return lines, best, lag


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--face", nargs=4, type=int, required=True, metavar=("X", "Y", "W", "H"))
    ap.add_argument("--fps", type=int, default=12)
    a = ap.parse_args()
    mouth, voice = signals(a.video, a.face, a.fps)
    lines, corr, lag = analyse(mouth, voice, a.fps)
    bad = [(s, e) for s, e, share in lines if share < 0.3]
    for s, e, share in lines:
        print(f"voice {s:5.2f}-{e:5.2f}s  mouth moves {share:4.0%}" + ("   <- MOUTH SHUT" if share < 0.3 else ""))
    print(f"correlation {corr:.2f}, delay {lag:+.2f}s ({'ok' if abs(lag) <= 0.12 else 'OFF'})")
    sys.exit(1 if bad or abs(lag) > 0.12 or corr < 0.2 else 0)


if __name__ == "__main__":
    main()
