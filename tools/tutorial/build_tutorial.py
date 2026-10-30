"""Build a vertical (9:16) app tutorial from a screen recording + a step spec.

    python tools/tutorial/build_tutorial.py tools/tutorial/specs/<name>.json [--force-tts]

Branding (logo, name, call to action, store badge, language strings) comes from brand/brand.json.
The project is written to videos/<slug>/.

What it does
  1. Narration: one Gemini TTS call for the whole script (one paragraph per step),
     split back into per-step clips at the pauses between paragraphs. Cached by
     script hash in <project>/audio/ so re-runs don't spend API calls.
  2. Edit plan: for every screen step, the source ranges are cut so each step lasts
     as long as its narration — the lead-in is compressed, the screen FREEZES on the
     moment before a tap while the voice explains (highlight + zoom shown there),
     then the tap plays at real speed. Loading screens are left out of the ranges.
  3. Video: ffmpeg cuts/freezes/blurs the recording into assets/screen.mp4.
  4. Composition: writes <project>/index.html from template.html with all step,
     tap, highlight, note and caption timings, plus narration.wav and music.

Spec format: see specs/connect-facebook.json. Coordinates are in recording pixels
(always 1080x2400: recordings are scaled to that first); times are recording seconds.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent          # tools/tutorial -> repo root
sys.path.insert(0, str(REPO / "scripts"))

SRC_W, SRC_H = 1080, 2400
OUT_W, OUT_H = 1080, 2400         # screen.mp4 at full size so pop-out crops stay sharp
FPS = 30
LEAD, TAIL = 0.15, 0.3             # silence before / after each step's narration
MIN_HOLD = 0.35
BN_DIGITS = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")
DEFAULT_STYLE = ("Read this app tutorial aloud like a friendly, patient teacher showing a new user "
                 "how to use an app. Warm, clear and natural, at a calm, unhurried pace, with a short "
                 "pause between paragraphs")


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode:
        sys.exit(f"command failed: {' '.join(map(str, cmd[:6]))} ...\n{r.stderr[-1500:]}")
    return r.stdout


def duration(path):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)]))


# ── 1. Narration ────────────────────────────────────────────────────────────
def narration(spec, proj, force):
    import numpy as np
    import gemini_tts_lib as g
    try:
        from dotenv import load_dotenv
        load_dotenv(REPO / ".archon" / ".env", override=False)
    except ImportError:
        pass
    steps = spec["steps"]
    script = "\n\n".join(s["vo"].strip() for s in steps)
    voice = spec.get("voice", os.environ.get("GEMINI_TTS_VOICE", "Sulafat"))
    style = spec.get("style", DEFAULT_STYLE)
    key = hashlib.sha1(f"{voice}|{style}|{script}".encode()).hexdigest()[:12]
    adir = proj / "audio"
    adir.mkdir(parents=True, exist_ok=True)
    raw = adir / f"vo-{key}.wav"
    if force or not raw.exists():
        cfg = g.settings_from_env()
        print(f"[tts] Gemini voice={voice} ({len(script)} chars)")
        audio = g.synthesize(script, api_key=cfg["api_key"], voice=voice, style=style, model=cfg["model"])
        g.write_wav(raw, audio)
    else:
        print(f"[tts] reusing {raw.name}")
    pcm = run_bytes(["ffmpeg", "-v", "error", "-i", str(raw), "-f", "s16le", "-ac", "1", "-ar", str(g.SAMPLE_RATE), "-"])
    audio = np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32768.0
    words = g.align_words(script, audio)

    # word index ranges per step
    counts = [len([w for w in s["vo"].split() if re.search(r"\w", w)]) for s in steps]
    if sum(counts) != len(words):
        sys.exit(f"word count mismatch: script {sum(counts)} vs aligned {len(words)}")
    clips, i = [], 0
    for k, n in enumerate(counts):
        ws = words[i:i + n]
        i += n
        clips.append(ws)
    # Cut between steps INSIDE a real pause (the paragraph break), never at an
    # estimated word time — estimated cuts clipped words and made the voice stutter.
    sr = g.SAMPLE_RATE
    total_len = len(audio) / sr
    pauses = g._pauses(audio, min_pause=0.12)
    cuts = [0.0]
    for k in range(1, len(clips)):
        est = (clips[k - 1][-1]["end"] + clips[k][0]["start"]) / 2
        cands = [p for p in pauses if abs((p[0] + p[1]) / 2 - est) < 1.5 and (p[0] + p[1]) / 2 > cuts[-1] + 0.3]
        if cands:   # prefer long pauses close to the estimate
            p = min(cands, key=lambda p: abs((p[0] + p[1]) / 2 - est) - 1.5 * (p[1] - p[0]))
            cuts.append((p[0] + p[1]) / 2)
        else:
            print(f"[tts] warning: no pause found near step {k} boundary, cutting at estimate")
            cuts.append(est)
    cuts.append(total_len)
    out = []
    for k, s in enumerate(steps):
        clip = audio[int(cuts[k] * sr):int(cuts[k + 1] * sr)]
        clip = g.trim_silence(clip, pad=0.12)   # roomy tail so soft word endings are never clipped
        f = int(0.03 * sr)                     # 30 ms fades so every clip starts/ends in silence
        if len(clip) > 4 * f:
            clip = clip.copy(); clip[:f] *= np.linspace(0, 1, f); clip[-f:] *= np.linspace(1, 0, f)
        seg = adir / f"step{k:02d}.wav"
        g.write_wav(seg, clip)
        ws = g.align_words(s["vo"].strip(), clip)        # re-align within this clean clip
        out.append({"wav": seg, "len": len(clip) / sr,
                    "words": [{"w": w["word"], "s": w["start"], "e": w["end"]} for w in ws]})
    return out, voice


def run_bytes(cmd):
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode:
        sys.exit(r.stderr.decode()[-800:])
    return r.stdout


# ── 2. Edit plan ────────────────────────────────────────────────────────────
def plan_step(step, target):
    """Pieces for one screen step: [{'a','b','speed'} | {'freeze_at','dur'}], total length."""
    ranges = [tuple(r) for r in step["ranges"]]
    taps = step.get("taps", [])
    holds = step.get("holds")
    if holds is None:
        holds = [{"t": round(taps[0]["t"] - step.get("hold_lead", 0.45), 3), "w": 1}] if taps else []
    holds = [h if isinstance(h, dict) else {"t": h, "w": 1} for h in holds]
    cap = step.get("pre_speed_cap", 3.0)
    post = step.get("post_speed", 1.0)

    # split ranges at hold points
    cuts = sorted(h["t"] for h in holds)
    segs = []                                   # (a, b, is_pre)
    for a, b in ranges:
        pts = [a] + [c for c in cuts if a < c < b] + [b]
        for x, y in zip(pts, pts[1:]):
            segs.append((x, y, bool(cuts) and y <= cuts[0] + 1e-6))
    pre_len = sum(b - a for a, b, p in segs if p)
    post_len = sum(b - a for a, b, p in segs if not p)
    s1 = min(cap, max(1.0, pre_len / 0.9)) if pre_len else 1.0
    played = pre_len / s1 + post_len / post
    extra = max(MIN_HOLD * len(holds), target - played) if holds else 0.0
    wsum = sum(h["w"] for h in holds) or 1
    pieces = []
    for a, b, is_pre in segs:
        pieces.append({"a": a, "b": b, "speed": s1 if is_pre else post})
        for h in holds:
            if abs(h["t"] - b) < 1e-6:
                pieces.append({"freeze_at": b, "dur": extra * h["w"] / wsum})
    total = sum(p["dur"] if "freeze_at" in p else (p["b"] - p["a"]) / p["speed"] for p in pieces)
    if not holds and total < target:            # nothing to freeze on: hold the last frame
        pieces.append({"freeze_at": ranges[-1][1] - 0.04, "dur": target - total, "end": True})
        total = target
    return pieces, total


def mapper(pieces, start):
    """src time -> output time inside this step (first non-freeze piece containing t)."""
    def f(t):
        o = start
        for p in pieces:
            if "freeze_at" in p:
                if abs(p["freeze_at"] - t) < 1e-6 and not p.get("end"):
                    return o                    # start of the freeze
                o += p["dur"]
                continue
            if p["a"] - 1e-6 <= t <= p["b"] + 1e-6:
                return o + (t - p["a"]) / p["speed"]
            o += (p["b"] - p["a"]) / p["speed"]
        return o
    return f


# ── 3. Video ────────────────────────────────────────────────────────────────
def render_screen(src, all_pieces, blurs, out):
    # Normalise every recording to 1080x2400 first, so spec coordinates are the same for any phone.
    chains = [f"[0:v]scale={SRC_W}:{SRC_H},setsar=1[norm]"]
    cur = "[norm]"
    for i, bl in enumerate(blurs):
        x, y, w, h = (int(v) for v in bl["box"])
        t0, t1 = bl["t"]
        chains.append(f"{cur}split[m{i}][c{i}];[c{i}]crop={w}:{h}:{x}:{y},boxblur=lr=15:lp=3:cr=7:cp=3[bb{i}];"
                      f"[m{i}][bb{i}]overlay={x}:{y}:enable='between(t,{t0},{t1})'[v{i}]")
        cur = f"[v{i}]"
    n = len(all_pieces)
    chains.append(f"{cur}fps={FPS},split={n}" + "".join(f"[s{i}]" for i in range(n)))
    labels = []
    for i, p in enumerate(all_pieces):
        if "freeze_at" in p:
            t = max(0.0, p["freeze_at"] - 0.04)
            chains.append(f"[s{i}]trim=start={t:.3f}:duration=0.05,setpts=PTS-STARTPTS,"
                          f"tpad=stop_mode=clone:stop_duration={p['dur']:.3f},trim=duration={p['dur']:.3f},setpts=PTS-STARTPTS[p{i}]")
        else:
            chains.append(f"[s{i}]trim=start={p['a']:.3f}:end={p['b']:.3f},setpts=(PTS-STARTPTS)/{p['speed']:.4f}[p{i}]")
        labels.append(f"[p{i}]")
    chains.append("".join(labels) + f"concat=n={n}:v=1:a=0,fps={FPS},format=yuv420p[out]")
    run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-filter_complex", ";".join(chains), "-map", "[out]",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-an", str(out)])


def make_sfx(times, total, out):
    """Mix the notification ding (shared/audio/sfx/notify-ding.wav) at each time into one track."""
    import wave
    import numpy as np
    with wave.open(str(REPO / "shared/audio/sfx/notify-ding.wav")) as w:
        sr = w.getframerate()
        ding = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float32) / 32767
    mix = np.zeros(int((total + 1) * sr), np.float32)
    for t in times:
        i = int(t * sr)
        mix[i:i + len(ding)] += ding[:max(0, len(mix) - i)]
    mix = np.clip(mix, -1, 1)[:int(total * sr)]
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((mix * 32767).astype("<i2").tobytes())
    print(f"[sfx] {len(times)} notification dings")


def load_brand():
    p = REPO / "brand" / "brand.json"
    if not p.exists():
        sys.exit("brand/brand.json is missing: copy brand/brand.example.json and fill it in (see SETUP.md)")
    return json.loads(p.read_text(encoding="utf-8"))


def num(n, brand):
    """Step numbers in the brand's language digits (Bangla digits when language starts with 'bn')."""
    return str(n).translate(BN_DIGITS) if brand.get("language", "en").startswith("bn") else str(n)


def store_badge(store):
    t2 = {"google_play": "Google Play", "app_store": "App Store"}.get(store)
    if not t2:
        return ""
    t1 = "GET IT ON" if store == "google_play" else "Download on the"
    return f'<div class="play"><div class="tri"></div><div><div class="t1">{t1}</div><div class="t2">{t2}</div></div></div>'


def text_logo(name, out, stacked=False):
    from PIL import Image, ImageDraw, ImageFont
    size = (600, 600) if stacked else (900, 240)
    im = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    font = None
    for fs in range(170, 20, -6):                 # largest size that fits with a margin
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", fs)
        except OSError:
            font = ImageFont.load_default()
            break
        l, t, r, btm = d.textbbox((0, 0), name, font=font)
        if r - l <= size[0] * 0.9 and btm - t <= size[1] * 0.8:
            break
    l, t, r, btm = d.textbbox((0, 0), name, font=font)
    d.text(((size[0] - (r - l)) / 2 - l, (size[1] - (btm - t)) / 2 - t), name, font=font, fill=(30, 30, 40, 255))
    im.save(out)


# ── 4. Build ────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec", type=Path)
    ap.add_argument("--force-tts", action="store_true")
    args = ap.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    proj = REPO / "videos" / spec["slug"]
    (proj / "assets").mkdir(parents=True, exist_ok=True)
    brand = load_brand()
    for kind in ("horizontal", "stacked"):
        src = REPO / "brand" / brand.get(f"logo_{kind}", f"logos/logo-{kind}.png")
        if src.exists():
            shutil.copy(src, proj / "assets" / f"logo-{kind}.png")
        else:                                     # no logo yet: make a simple text logo from the brand name
            text_logo(brand["name"], proj / "assets" / f"logo-{kind}.png", stacked=(kind == "stacked"))
    if not (proj / "assets/fonts").exists():
        shutil.copytree(REPO / "brand/fonts", proj / "assets/fonts")

    vo, voice = narration(spec, proj, args.force_tts)
    steps = spec["steps"]
    t = 0.0
    data_steps, screen_pieces, screen_t0, screen_t1 = [], [], None, None
    taps, highlights, notes, caps = [], [], [], []
    n_screen = 0
    for k, (s, v) in enumerate(zip(steps, vo)):
        target = LEAD + v["len"] + TAIL
        kind = s.get("kind", "screen")
        st = {"kind": kind, "start": round(t, 3), "title": s.get("title", "")}
        if kind == "screen":
            if not s.get("cont"):          # "cont": true = sub-step of the previous numbered step
                n_screen += 1
                group_title = s.get("title", "")
            st["num"] = num(n_screen, brand)
            st["group"] = n_screen
            st["title"] = group_title
            pieces, dur = plan_step(s, target)
            if screen_t0 is None:
                screen_t0 = t
            f = mapper(pieces, t)
            for tp in s.get("taps", []):
                taps.append({"t": round(f(tp["t"]), 3), "x": tp["x"], "y": tp["y"], "label": tp.get("label", ""),
                             "ring": round(f(tp.get("ring_from", tp["t"] - s.get("hold_lead", 0.45))), 3),
                             "lpos": tp.get("lpos", "above"), "box": tp.get("box")})
            for hl in s.get("highlights", []):
                a = f(hl["t"])
                b = f(hl["until"]) if "until" in hl else t + dur - 0.1
                highlights.append({"a": round(a, 3), "b": round(b, 3), "box": hl["box"], "label": hl.get("label", ""),
                                   "zoom": hl.get("zoom", 1.0), "lpos": hl.get("lpos", "above")})
            screen_pieces += pieces
            screen_t1 = t + dur
        else:
            dur = max(target, s.get("min", 2.2))
        if s.get("note"):
            nt = s["note"]
            a = f(nt["src_t"]) if (kind == "screen" and "src_t" in nt) else t + nt.get("at", 0.5)
            notes.append({"a": round(a, 3), "b": round(t + dur - 0.15, 3), "pos": nt.get("pos", "bottom"),
                          "icon": nt.get("icon", "ℹ️"), "text": nt["text"], "tone": nt.get("tone", "info")})
        caps.append([{"w": w["w"], "s": round(t + LEAD + w["s"], 3), "e": round(t + LEAD + w["e"], 3)} for w in v["words"]])
        st["end"] = round(t + dur, 3)
        st["vo_at"] = round(t + LEAD, 3)
        data_steps.append(st)
        t += dur
    total = round(t, 3)
    print(f"[plan] {len(steps)} steps, total {total:.2f}s, screen {screen_t0:.2f}–{screen_t1:.2f}s")

    print("[video] cutting screen recording…")
    render_screen(Path(spec["source"]), screen_pieces, spec.get("blurs", []), proj / "assets/screen.mp4")
    sdur = duration(proj / "assets/screen.mp4")

    # pop-out cards: crop each tapped button from the (already blurred) screen video
    pdir = proj / "assets/pops"
    shutil.rmtree(pdir, ignore_errors=True)
    pdir.mkdir(parents=True)
    for i, tp in enumerate(taps):
        if not tp["box"]:
            continue
        x, y, w, h = (int(v) for v in tp["box"])
        at = max(0.0, tp["ring"] + 0.12 - screen_t0)
        img = pdir / f"pop{i:02d}.png"
        run(["ffmpeg", "-y", "-v", "error", "-ss", f"{at:.3f}", "-i", str(proj / "assets/screen.mp4"), "-frames:v", "1",
             "-vf", f"crop={w}:{h}:{x}:{y}", str(img)])
        tp["pop"] = f"assets/pops/{img.name}"

    # narration track: each step clip at its vo_at
    inputs, flt = [], []
    for i, (st, v) in enumerate(zip(data_steps, vo)):
        inputs += ["-i", str(v["wav"])]
        ms = int(st["vo_at"] * 1000)
        flt.append(f"[{i}:a]aresample=48000,adelay={ms}|{ms}[a{i}]")
    flt.append("".join(f"[a{i}]" for i in range(len(vo))) + f"amix=inputs={len(vo)}:normalize=0,apad,atrim=0:{total},"
               "loudnorm=I=-15:TP=-1.5:LRA=11[o]")
    run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(flt), "-map", "[o]",
         "-ac", "1", "-ar", "48000", "-c:a", "pcm_s16le", str(proj / "audio/narration.wav")])
    # soft music bed, looped to length
    music = REPO / spec.get("music", "public/music/Archon.mp3")
    run(["ffmpeg", "-y", "-v", "error", "-stream_loop", "-1", "-i", str(music), "-t", f"{total}",
         "-af", f"afade=t=in:d=0.6,afade=t=out:st={max(0, total - 2):.2f}:d=2,loudnorm=I=-14:TP=-1.5",
         "-ar", "44100", "-ac", "2", "-b:a", "160k", str(proj / "audio/music.mp3")])

    # notification "ding" on every pop-up: pop-out cards (tap ring + 0.08 s), highlight boxes and note cards
    cues = sorted([tp["ring"] + 0.08 for tp in taps] + [h["a"] for h in highlights] + [n["a"] for n in notes])
    kept = []
    for c in cues:                                 # one ding per moment, never two on top of each other
        if not kept or c - kept[-1] > 0.3:
            kept.append(c)
    make_sfx(kept, total, proj / "audio/sfx.wav")

    data = {"total": total, "screen": {"start": round(screen_t0, 3), "dur": round(sdur, 3)},
            "steps": data_steps, "taps": taps, "highlights": highlights, "notes": notes, "captions": caps,
            "title": spec["title"], "subtitle": spec.get("subtitle", ""), "nsteps": num(n_screen, brand),
            "stepsChip": brand.get("steps_chip", "{n} easy steps"), "stepWord": brand.get("step_word", "Step")}
    html = (HERE / "template.html").read_text(encoding="utf-8")
    html = html.replace("{{DATA}}", json.dumps(data, ensure_ascii=False)).replace("{{TOTAL}}", f"{total}")
    html = html.replace("{{SCREEN_START}}", f"{screen_t0:.3f}").replace("{{SCREEN_DUR}}", f"{sdur:.3f}")
    html = html.replace("{{PAGE_TITLE}}", spec["title"]).replace("{{BRAND}}", brand["name"])
    html = html.replace("{{GUIDE_PILL}}", brand.get("guide_pill", "Step-by-step guide")).replace("{{CTA}}", brand.get("cta", f"Try {brand['name']} today"))
    html = html.replace("{{STORE_BADGE}}", store_badge(brand.get("store", "")))
    (proj / "index.html").write_text(html, encoding="utf-8")
    (proj / "meta.json").write_text(json.dumps({"id": spec["slug"], "name": spec["title"]}, ensure_ascii=False, indent=2))
    (proj / "hyperframes.json").write_text(json.dumps({
        "$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
        "registry": "https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry",
        "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"}}, indent=2))
    (proj / "transcript.json").write_text(json.dumps({"voice": voice, "steps": caps}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[done] {proj.relative_to(REPO)}  total={total}s")


if __name__ == "__main__":
    main()
