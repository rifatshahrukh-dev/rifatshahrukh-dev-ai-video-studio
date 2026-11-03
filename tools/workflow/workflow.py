"""Showcrew workflow: describe a video once in JSON, check it, build it.

    python3 tools/workflow/workflow.py check workflow.json     # validate + show resolved timings, no files written
    python3 tools/workflow/workflow.py build workflow.json out_dir   # writes out_dir/index.html + report.json

Spec (all times in seconds; anything can anchor to a spoken word instead):
{"name":"promo","size":[1080,1920],"duration":5,"transcript":"transcript.json",   # transcript optional
 "brand":{"bg":"#0E1420","text":"#FFFFFF","accent":"#4D8FF7"},
 "items":[{"id":"title","kind":"text","text":"Meet Showcrew","y":600,"size":110,"at":{"word":"meet","offset":-0.1,"t":0.2},"hold":3},
          {"id":"card","kind":"card","text":"Script. Film. Edit.","sub":"One brief.","y":1100,"at":{"t":1.2},"hold":3,"sfx":"notify-ding"},
          {"id":"clip","kind":"video","src":"clips/a.mp4","at":{"t":0},"hold":5}],
 "audio":[{"id":"voice","src":"audio/voice.wav","at":{"t":0},"volume":1}, {"id":"music","src":"audio/music.wav","at":{"t":0},"volume":0.15}]}
kinds: robot (role: script|edit|sound|qa, "x" = centre), text, card (white UI card, bold title + grey line), image, video. "keep":true leaves an item on screen to the end; "\n" in text = line break. "sfx" on an item plays shared/audio/sfx/<name> at its start.
"at" may carry both a word and a fallback "t" (used while there is no transcript yet). Changing the script only means re-running build: word anchors move every item with it. Pop-ups share one soft motion (rise + fade, 0.45 s).
"""
import html
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "wordsync"))
from wordsync import wordsync  # noqa: E402

KINDS = {"text", "card", "image", "video", "robot"}
# Pantone-style palette per robot role: body, accent. Roles: script, edit, sound, qa.
ROBOTS = {"script": ("#FFBE98", "#BB2649"), "edit": ("#BB2649", "#FFBE98"), "sound": ("#8B74C9", "#F5DF4D"), "qa": ("#F5DF4D", "#0F4C81")}
SFX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "shared", "audio", "sfx")


def resolve(spec, base="."):
    words = []
    if spec.get("transcript"):
        t = json.load(open(os.path.join(base, spec["transcript"])))
        words = t["words"] if isinstance(t, dict) else t
    rows = []
    for it in spec.get("items", []):
        if it.get("kind") not in KINDS:
            raise SystemExit(f"{it.get('id')}: kind must be one of {sorted(KINDS)}")
        at = it.get("at", {"t": 0})
        if "word" in at and words:
            start = wordsync(words, [{"id": it["id"], **at}])[it["id"]]["start"]
        else:
            start = float(at.get("t", 0))
        rows.append({**it, "start": start, "end": round(start + it.get("hold", 1.5), 3)})
    for a in spec.get("audio", []):
        a["start"] = float(a.get("at", {}).get("t", 0))
    dur = spec.get("duration") or max([r["end"] for r in rows] or [1])
    problems = [f"{r['id']} ends at {r['end']}s after the video ({dur}s)" for r in rows if r["end"] > dur + 0.01]
    return rows, dur, problems


def robot_svg(role):
    body, acc = ROBOTS[role]
    extra = {"script": '<rect x="55" y="196" width="90" height="12" rx="4" fill="#fff" opacity=".9"/><rect x="62" y="199" width="76" height="2" fill="%s"/><rect x="62" y="203" width="50" height="2" fill="%s"/>' % (acc, acc),
             "edit": '<rect x="45" y="198" width="110" height="10" rx="5" fill="#fff" opacity=".9"/><rect x="60" y="198" width="30" height="10" rx="5" fill="%s"/>' % acc,
             "sound": '<path d="M52 70 a48 48 0 0 1 96 0" fill="none" stroke="%s" stroke-width="9" stroke-linecap="round"/><rect x="44" y="64" width="14" height="30" rx="7" fill="%s"/><rect x="142" y="64" width="14" height="30" rx="7" fill="%s"/>' % (acc, acc, acc),
             "qa": '<circle cx="152" cy="196" r="17" fill="none" stroke="%s" stroke-width="7"/><path d="M164 208 l16 16" stroke="%s" stroke-width="8" stroke-linecap="round"/>' % (acc, acc)}[role]
    return (f'<svg viewBox="0 0 200 250" width="100%" height="100%"><ellipse cx="100" cy="238" rx="56" ry="8" fill="#000" opacity=".18"/>'
            f'<line x1="100" y1="22" x2="100" y2="42" stroke="#fff" stroke-width="5"/><circle cx="100" cy="16" r="9" fill="{acc}" class="ant"/>'
            f'<rect x="48" y="40" width="104" height="82" rx="30" fill="{body}"/><rect x="62" y="58" width="76" height="46" rx="20" fill="#0B2A55"/>'
            f'<circle cx="84" cy="81" r="8" fill="{acc}"/><circle cx="116" cy="81" r="8" fill="{acc}"/>'
            f'<rect x="62" y="128" width="76" height="62" rx="24" fill="{body}"/><circle cx="100" cy="159" r="9" fill="#fff" opacity=".85"/>'
            f'<rect x="32" y="136" width="24" height="12" rx="6" fill="{body}"/><rect x="144" y="136" width="24" height="12" rx="6" fill="{body}"/>{extra}</svg>')


def build_html(spec, rows, dur):
    w, h = spec.get("size", [1080, 1920])
    b = {"bg": "#0E1420", "text": "#FFFFFF", "accent": "#4D8FF7", **spec.get("brand", {})}
    el, tl, au = [], [], []
    grid = "#root::before{content:\"\";position:absolute;inset:0;background:repeating-linear-gradient(0deg,rgba(255,255,255,.06) 0 2px,transparent 2px 80px),repeating-linear-gradient(90deg,rgba(255,255,255,.06) 0 2px,transparent 2px 80px)}" if b.get("grid") else ""
    for r in rows:
        i, e = r["id"], html.escape
        y = r.get("y", 700)
        if r["kind"] == "text":
            el.append(f'<div class="i t" id="{i}" style="top:{y}px;font-size:{r.get("size", 90)}px">{e(r.get("text", "")).replace(chr(10), "<br>")}</div>')
        elif r["kind"] == "card":
            el.append(f'<div class="i c" id="{i}" style="top:{y}px"><b>{e(r.get("text", ""))}</b><i>{e(r.get("sub", ""))}</i></div>')
        elif r["kind"] == "robot":
            sz = r.get("size", 300)
            el.append(f'<div class="i" id="{i}" style="top:{y}px;left:{r.get("x", w // 2) - sz // 2}px;width:{sz}px;height:{sz * 5 // 4}px">'
                      f'<div id="{i}-b" style="width:100%;height:100%">{robot_svg(r["role"])}</div></div>')
            n = max(int((r["end"] - r["start"] - .6) / 1.4), 1)
            tl.append(f'tl.to("#{i}-b",{{y:-14,duration:.7,yoyo:true,repeat:{n * 2 - 1},ease:"sine.inOut"}},{r["start"] + .5});'
                      f'tl.to("#{i} .ant",{{opacity:.35,duration:.5,yoyo:true,repeat:{n * 2 + 1},ease:"sine.inOut"}},{r["start"] + .5});')
        elif r["kind"] == "image":
            el.append(f'<img class="i m" id="{i}" src="{e(r["src"])}" style="top:{y}px">')
        else:
            el.append(f'<video class="clip i m" id="{i}" src="{e(r["src"])}" muted playsinline data-start="{r["start"]}" '
                      f'data-duration="{r["end"] - r["start"]:.3f}" data-track-index="0" style="top:{y}px"></video>')
        fade = "" if r.get("keep") else f'.to("#{i}",{{opacity:0,duration:.3}},{max(r["end"] - .3, r["start"])})'
        tl.append(f'tl.from("#{i}",{{y:30,opacity:0,duration:.45}},{r["start"]}){fade};')
        if r.get("sfx"):
            f = next((x for x in sorted(os.listdir(SFX_DIR)) if x.startswith(r["sfx"])), None)
            if not f:
                raise SystemExit(f"{i}: no sfx '{r['sfx']}' in shared/audio/sfx")
            au.append({"id": f"sfx-{i}", "src": f"audio/{f}", "start": r["start"], "dur": 1, "vol": 0.2, "copy": os.path.join(SFX_DIR, f)})
    for a in spec.get("audio", []):
        au.append({"id": a["id"], "src": a["src"], "start": a["start"], "dur": a.get("hold", dur), "vol": a.get("volume", 1)})
    tags = "\n".join(f'<audio id="{a["id"]}" src="{a["src"]}" data-start="{a["start"]}" data-duration="{a["dur"]}" '
                     f'data-track-index="{k + 1}" data-volume="{a["vol"]}"></audio>' for k, a in enumerate(au))
    return f"""<!doctype html><html><head><meta charset="UTF-8"><title>{html.escape(spec.get("name", "video"))}</title>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>*{{margin:0;padding:0;box-sizing:border-box}}html,body{{width:{w}px;height:{h}px;overflow:hidden;background:#0E1420;font-family:system-ui,sans-serif;color:{b["text"]}}}
#root{{position:relative;width:{w}px;height:{h}px;background:{b["bg"]}}}{grid}.i{{position:absolute}}.t{{left:60px;right:60px;text-align:center;font-weight:800;line-height:1.1}}
.c{{left:140px;right:140px;background:#fff;color:#111;border-radius:36px;padding:44px;box-shadow:0 30px 80px rgba(0,0,0,.4)}}.c b{{display:block;font-size:54px}}.c i{{font-style:normal;font-size:36px;color:#667}}
.m{{left:90px;width:{w - 180}px}}</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{dur}" data-width="{w}" data-height="{h}">
{chr(10).join(el)}
{tags}
</div>
<script>window.__timelines=window.__timelines||{{}};const tl=gsap.timeline({{paused:true}});
{chr(10).join(tl)}
window.__timelines["main"]=tl;</script></body></html>
""", au


def main():
    cmd, path = sys.argv[1], sys.argv[2]
    spec = json.load(open(path))
    rows, dur, problems = resolve(spec, os.path.dirname(os.path.abspath(path)))
    for r in rows:
        print(f"{r['id']:16} {r['kind']:6} {r['start']:6.2f} -> {r['end']:6.2f}")
    print(f"duration {dur}s; " + ("PROBLEMS: " + "; ".join(problems) if problems else "ok"))
    if cmd == "check":
        sys.exit(1 if problems else 0)
    out = sys.argv[3]
    page, au = build_html(spec, rows, dur)
    os.makedirs(os.path.join(out, "audio"), exist_ok=True)
    open(os.path.join(out, "index.html"), "w").write(page)
    for a in au:
        if a.get("copy"):
            shutil.copy(a["copy"], os.path.join(out, a["src"]))
    json.dump({"name": spec.get("name"), "duration": dur, "items": [{k: r[k] for k in ("id", "kind", "start", "end")} for r in rows],
               "problems": problems}, open(os.path.join(out, "report.json"), "w"), indent=1)
    print("wrote", out)


if __name__ == "__main__":
    main()
