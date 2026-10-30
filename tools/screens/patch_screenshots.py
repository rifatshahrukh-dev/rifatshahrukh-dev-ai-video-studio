"""Edit real app screenshots: replace a product photo, name, price or any text, and blur personal data.

Each patch is a box drawn over the original screenshot: filled with the colour sampled from the screenshot (so it
blends in) plus new HTML text, or an image (e.g. your product photo). Rendered at full resolution with Playwright
(Node), so fonts and anti-aliasing match the real UI.

    python3 tools/screens/patch_screenshots.py tools/screens/patches.example.json

Config: {"out_dir": "...", "fonts_css": "...optional @font-face rules...",
         "screens": [{"src": "shot.png", "out": "shot-edited.jpg",
                      "blur": [[x, y, w, h], ...],
                      "patches": [{"box": [x, y, w, h], "sample": [x, y] | null, "html": "...", "css": "..."}]}]}
Paths are relative to the config file. Needs Node + Playwright (`npm i playwright`).
"""
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageFilter

cfg_path = Path(sys.argv[1]).resolve()
C = json.loads(cfg_path.read_text())
base = cfg_path.parent
out_dir = base / C.get("out_dir", "edited")
out_dir.mkdir(parents=True, exist_ok=True)
jobs = []
for i, s in enumerate(C["screens"]):
    src = base / s["src"]
    img = Image.open(src).convert("RGB")
    for x, y, w, h in s.get("blur", []):                       # privacy blur first
        img.paste(img.crop((x, y, x + w, y + h)).filter(ImageFilter.GaussianBlur(16)), (x, y))
    pre = out_dir / f"_pre{i}.png"
    img.save(pre)
    divs = []
    for p in s.get("patches", []):
        x, y, w, h = p["box"]
        bg = ""
        if p.get("sample"):
            r, g, b = img.getpixel(tuple(p["sample"]))
            bg = f"background:rgb({r},{g},{b});"
        divs.append(f"<div style='position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;overflow:hidden;"
                    f"{bg}{p.get('css', '')}'>{p.get('html', '')}</div>")
    html = (f"<html><head><style>{C.get('fonts_css', '')} *{{margin:0;padding:0;box-sizing:border-box}}"
            f"body{{width:{img.width}px;height:{img.height}px;position:relative;background:url({pre.name}) 0 0/100% 100%}}"
            f"</style></head><body>{''.join(divs)}</body></html>")
    page = out_dir / f"_page{i}.html"
    page.write_text(html)
    jobs.append({"html": page.as_uri(), "png": str(out_dir / f"_shot{i}.png"), "w": img.width, "h": img.height,
                 "out": str(out_dir / s["out"]), "tmp": [str(pre), str(page)]})
js = """const { chromium } = require('playwright');
(async () => { const b = await chromium.launch(); const p = await b.newPage();
  for (const j of JSON.parse(process.argv[1])) { await p.setViewportSize({ width: j.w, height: j.h });
    await p.goto(j.html); await p.waitForTimeout(400); await p.screenshot({ path: j.png }); }
  await b.close(); })();"""
subprocess.run(["node", "-e", js, json.dumps(jobs)], check=True)
for j in jobs:
    Image.open(j["png"]).convert("RGB").save(j["out"], quality=92)
    for t in j["tmp"] + [j["png"]]:
        Path(t).unlink()
    print("wrote", j["out"])
