"""Break down a reference video (file or YouTube link) for planning an ad. Analysis only: never reuse its media.

    python3 tools/ref_breakdown.py <video file | URL> <out dir>

Writes to <out dir>: video.mp4 (if a URL), cuts.json, sheet.png (one frame per shot, via tools/checks/frames.sh),
words.txt (the platform's subtitles when a URL has them), and prints the pacing summary.
"""
import json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*a):
    return subprocess.run(a, capture_output=True, text=True, check=True)


def main(src, out):
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    video = Path(src)
    if re.match(r"https?://", src):
        video = out / "video.mp4"
        run("yt-dlp", "-q", "-f", "mp4/best", "--write-auto-subs", "--write-subs", "--sub-langs", "bn,en.*",
            "--convert-subs", "srt", "-o", str(out / "video.%(ext)s"), src)
        srt = sorted(out.glob("video*.srt"))
        if srt:  # subtitles → plain words, duplicates from rolling auto-captions removed
            lines = [l.strip() for l in srt[0].read_text(errors="ignore").splitlines()
                     if l.strip() and not l.strip().isdigit() and "-->" not in l]
            words = [l for i, l in enumerate(lines) if i == 0 or l != lines[i - 1]]
            (out / "words.txt").write_text("\n".join(words))
    dur = float(run("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)).stdout)
    log = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(video), "-vf", "select='gt(scene,0.3)',showinfo",
                          "-an", "-f", "null", "-"], capture_output=True, text=True).stderr
    cuts = [round(float(t), 2) for t in re.findall(r"pts_time:([\d.]+)", log)]
    starts = [0.0] + cuts
    shots = [round(b - a, 2) for a, b in zip(starts, starts[1:] + [dur])]
    info = {"duration": round(dur, 2), "shots": len(shots), "cuts": cuts, "shot_lengths": shots,
            "avg_shot": round(dur / len(shots), 2), "cuts_per_10s": round(len(cuts) / dur * 10, 1),
            "hook_shots_first_3s": sum(1 for s in starts if s < 3)}
    (out / "cuts.json").write_text(json.dumps(info, indent=1))
    mids = [round(a + s / 2, 2) for a, s in zip(starts, shots)][:32]   # shortcut: max 32 frames, enough for a Short
    subprocess.run([str(ROOT / "tools/checks/frames.sh"), "sheet", str(video), str(out / "sheet.png"), *map(str, mids)],
                   check=True, capture_output=True)
    print(json.dumps({k: info[k] for k in ("duration", "shots", "avg_shot", "cuts_per_10s", "hook_shots_first_3s")}))


if __name__ == "__main__":
    main(*sys.argv[1:3])
