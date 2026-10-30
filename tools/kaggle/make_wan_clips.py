"""Build a Kaggle notebook that makes image-to-video clips with Wan 2.2 TI2V-5B on Kaggle's FREE T4 x2 GPUs.

    python3 tools/kaggle/make_wan_clips.py tools/kaggle/clips.example.json   -> <config name>.ipynb

Config (JSON): "prompts" {name: prompt}, "chains" [{seed, steps: [[prompt name, start image | "prev"]]}],
"images" [paths of start images]. Two chains run in parallel (one per GPU). "prev" starts a clip from the
previous clip's last frame. Push the notebook with the Kaggle API (see SETUP.md) or upload it on kaggle.com,
set Accelerator = GPU T4 x2 and Internet = On, then "Save & Run All". About 30 min per 5 s clip.

Lessons that keep a person's face consistent:
  - start every chain from a real, approved frame of the person; restart chains from known-good frames
  - never let an object come close to or cover the lens (the model loses the identity after a cover)
  - product swaps: lower the item out of the bottom of the frame, lift the next one up from below
  - ask for "deep focus, face always in sharp focus", locked-off tripod, no zoom
"""
import base64
import json
import sys
from pathlib import Path

cfg_path = Path(sys.argv[1])
C = json.loads(cfg_path.read_text())
PROMPTS, CHAINS = C["prompts"], C["chains"]
WIDTH, HEIGHT, FRAMES, FPS = C.get("width", 480), C.get("height", 832), C.get("frames", 121), C.get("fps", 24)
images = {Path(p).name: base64.b64encode((cfg_path.parent / p).read_bytes()).decode() for p in C["images"]}

ENCODE = r'''
import json, torch
from transformers import AutoTokenizer, UMT5EncoderModel
cfg = json.load(open("/kaggle/working/jobs2.json"))
mid = "Wan-AI/Wan2.2-TI2V-5B-Diffusers"
tok = AutoTokenizer.from_pretrained(mid, subfolder="tokenizer")
te = UMT5EncoderModel.from_pretrained(mid, subfolder="text_encoder", torch_dtype=torch.float16).to("cuda:0").eval()
NEG = ("blurry, low quality, distorted face, different person, changing face, deformed hands, extra fingers, bad anatomy, "
       "watermark, text, subtitles, static image, jittery, flicker, color shift, camera shake, zoom, out of focus face, "
       "object covering the camera, cartoon, 3d render")
def enc(text):
    t = tok([text], padding="max_length", max_length=512, truncation=True, add_special_tokens=True,
            return_attention_mask=True, return_tensors="pt")
    ids, mask = t.input_ids.to("cuda:0"), t.attention_mask.to("cuda:0")
    with torch.no_grad():
        h = te(ids, mask).last_hidden_state
    n = int(mask.sum())
    h = h[:, :n]
    return torch.cat([h, h.new_zeros(1, 512 - n, h.size(2))], dim=1).cpu()   # same padding as the diffusers pipeline
out = {name: enc(p) for name, p in cfg["prompts"].items()}
out["__neg__"] = enc(NEG)
torch.save(out, "/kaggle/working/embeds.pt")
print("encoded", list(out))
'''

WORKER = r'''
import gc, io, json, os, sys, time, traceback, base64
import torch
from PIL import Image
from diffusers import AutoencoderKLWan, WanImageToVideoPipeline
from diffusers.utils import export_to_video

wid = int(sys.argv[1]); cfg = json.load(open("/kaggle/working/jobs2.json"))
chain = cfg["chains"][wid]
E = torch.load("/kaggle/working/embeds.pt")
OUT = "/kaggle/working/clips"; os.makedirs(OUT, exist_ok=True)
mid = "Wan-AI/Wan2.2-TI2V-5B-Diffusers"
vae = AutoencoderKLWan.from_pretrained(mid, subfolder="vae", torch_dtype=torch.float32)
pipe = WanImageToVideoPipeline.from_pretrained(mid, vae=vae, text_encoder=None, tokenizer=None, torch_dtype=torch.float16)
try:
    pipe.vae.enable_tiling()
except Exception:
    pass
pipe.enable_sequential_cpu_offload(gpu_id=0)

def fit(im, w, h):
    r = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    l, t = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((l, t, l + w, t + h))

prev = None
for k, (name, start) in enumerate(chain["steps"]):
    t0 = time.time(); out = f"chain{wid}-{k:02d}-{name}"
    try:
        if start == "prev":
            img = prev
        else:
            img = Image.open(io.BytesIO(base64.b64decode(cfg["images"][start]))).convert("RGB")
        g = torch.Generator("cpu").manual_seed(chain["seed"] + k)
        frames = pipe(image=fit(img, cfg["w"], cfg["h"]), prompt_embeds=E[name].to(torch.float16),
                      negative_prompt_embeds=E["__neg__"].to(torch.float16), width=cfg["w"], height=cfg["h"],
                      num_frames=cfg["n"], num_inference_steps=40, guidance_scale=4.0, generator=g).frames[0]
        export_to_video(frames, f"{OUT}/{out}.mp4", fps=cfg["fps"], quality=10)
        last = frames[-1]
        prev = last if isinstance(last, Image.Image) else Image.fromarray((last * 255).clip(0, 255).astype("uint8"))
        prev.save(f"{OUT}/{out}-last.png")
        print(f"OK   worker{wid} {out} {time.time() - t0:.0f}s", flush=True)
    except Exception as e:
        print(f"FAIL worker{wid} {out}: {e}", flush=True); traceback.print_exc()
        prev = None
        if k + 1 < len(chain["steps"]) and chain["steps"][k + 1][1] == "prev":
            break
    gc.collect(); torch.cuda.empty_cache()
'''


def md(t):
    return {"cell_type": "markdown", "metadata": {}, "source": t.splitlines(keepends=True)}


def code(t):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": t.strip("\n").splitlines(keepends=True)}


cfg = {"prompts": PROMPTS, "chains": CHAINS, "images": images, "w": WIDTH, "h": HEIGHT, "n": FRAMES, "fps": FPS}
cells = [
    md("# Wan 2.2 image-to-video clips (Wan 2.2, free Kaggle T4 x2)\nVertical product swaps; face never covered.\n"),
    code('!nvidia-smi --query-gpu=name,memory.total --format=csv\n'
         '!pip install -q -U "diffusers>=0.35.1" "transformers>=4.51" accelerate sentencepiece ftfy imageio imageio-ffmpeg'),
    code("import json\ncfg = json.loads(r'''" + json.dumps(cfg) + "''')\n"
         "json.dump(cfg, open('/kaggle/working/jobs2.json', 'w'))\n"
         "open('/kaggle/working/encode.py', 'w').write(r'''" + ENCODE + "''')\n"
         "open('/kaggle/working/worker.py', 'w').write(r'''" + WORKER + "''')\nprint('ready')"),
    code('''
import subprocess, os
p = subprocess.run(["python", "/kaggle/working/encode.py"], env=dict(os.environ, CUDA_VISIBLE_DEVICES="0"),
                   capture_output=True, text=True)
print(p.stdout[-2000:]); print(p.stderr[-3000:])
assert os.path.exists("/kaggle/working/embeds.pt"), "prompt encoding failed"
'''),
    code(r'''
import subprocess, os, shutil, time
procs = []
for wid in (0, 1):
    env = dict(os.environ, CUDA_VISIBLE_DEVICES=str(wid))
    log = open(f"/kaggle/working/worker{wid}.log", "w")
    procs.append((subprocess.Popen(["python", "/kaggle/working/worker.py", str(wid)], env=env,
                                   stdout=log, stderr=subprocess.STDOUT), log))
    time.sleep(240)   # stagger model loading so both workers don't peak in RAM together
while any(p.poll() is None for p, _ in procs):
    time.sleep(60)
for p, log in procs:
    log.close()
for wid in (0, 1):
    print(f"--- worker{wid}")
    print("".join(l for l in open(f"/kaggle/working/worker{wid}.log") if l.startswith(("OK", "FAIL"))))
!ls -la /kaggle/working/clips
'''),
]
for i, c in enumerate(cells):
    c["id"] = f"cell-{i}"
nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                   "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
out = cfg_path.with_suffix(".ipynb")
out.write_text(json.dumps(nb, indent=1, ensure_ascii=False))
print("wrote", out, f"{out.stat().st_size / 1024:.0f} KB")
