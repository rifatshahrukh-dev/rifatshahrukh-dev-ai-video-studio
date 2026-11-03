"""LTX-2.5 job server for a Runpod pod with a persistent volume at /workspace.
First boot: install LTX-2 + download models onto /workspace (kept when the pod is stopped). Later boots: ready in ~1 min.
Token-protected HTTP on :8000:
  POST /upload?t=&name=x.jpg   (body = file)          -> /workspace/in/x.jpg
  POST /jobs?t=                (body = JSON list)     -> queued; each {"name","prompt","frames","seed",
                                                         "images":[["x.jpg", frame_idx, strength], ...]}
  GET  /log?t=   status + log;   GET /file?t=&name=y.mp4  download /workspace/out/y.mp4
"""
import http.server, json, os, queue, subprocess, threading, time, traceback, urllib.parse

TOKEN = os.environ["TOKEN"]
WS = "/workspace"; IN = f"{WS}/in"; OUT = f"{WS}/out"; M = f"{WS}/m"; REPO = f"{WS}/LTX-2"
for d in (IN, OUT, M):
    os.makedirs(d, exist_ok=True)
LOG, STATE, T0, Q = [], {"stage": "starting", "done": []}, time.time(), queue.Queue()
FILES = ["diffusion_models/ltx-2.5-22b-distilled-transformer-bf16.safetensors",
         "text_encoders/gemma4-12b-with-proj-ltx-2.5-bf16.safetensors",
         "vae/ltx-2.5-video-vae-bf16.safetensors", "vae/ltx-2.5-audio-vae-bf16.safetensors",
         "model_patches/ltx-2.5-duration-head-bf16.safetensors",
         "latent_upscale_models/ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors"]


def log(m):
    LOG.append(f"[{time.time() - T0:7.1f}s] {m}"); print(LOG[-1], flush=True)


def sh(cmd, cwd=None):
    log("$ " + cmd[:240])
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    if p.returncode:
        log("FAILED:\n" + (p.stdout + p.stderr)[-2500:]); raise RuntimeError(cmd[:80])
    return (p.stdout + p.stderr)[-1500:]


def setup():
    STATE["stage"] = "setup"
    log(sh("nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader"))
    sh("pip install -q -U uv huggingface_hub hf_transfer")
    if not os.path.exists(f"{REPO}/.venv"):
        if not os.path.exists(REPO):
            sh(f"git clone --depth 1 https://github.com/Lightricks/LTX-2 {REPO}")
        sh("uv sync", cwd=REPO)
    log(sh('uv run python -c "import torch; assert torch.cuda.is_available(), \'NO GPU\'; '
           'print(torch.__version__, torch.cuda.get_device_name(0))"', cwd=REPO))
    if not all(os.path.exists(f"{M}/{f}") for f in FILES):
        STATE["stage"] = "download"
        inc = " ".join(f'--include "{f}"' for f in FILES)
        sh(f"HF_HUB_ENABLE_HF_TRANSFER=1 hf download Lightricks/LTX-2.5 {inc} --local-dir {M}")
    log(sh(f"du -sh {M}"))


def run(job):
    m = M
    args = (f"uv run python -m ltx_pipelines.distilled --transformer-path {m}/{FILES[0]} --text-encoder-path {m}/{FILES[1]} "
            f"--video-vae-path {m}/{FILES[2]} --audio-vae-path {m}/{FILES[3]} --duration-head-path {m}/{FILES[4]} "
            f"--spatial-upsampler-path {m}/{FILES[5]} --height {job.get('height', 1344)} --width {job.get('width', 768)} "
            f"--num-frames {job['frames']} --seed {job.get('seed', 42)} ")
    for img, idx, st in job.get("images", []):
        args += f"--image {IN}/{img} {idx} {st} "
    prompt = job["prompt"].replace('"', "'")
    args += f'--prompt "{prompt}" --output-path {OUT}/{job["name"]}.mp4'
    t = time.time()
    try:
        sh("PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True " + args, cwd=REPO)
    except RuntimeError:
        log("retrying with --offload cpu")
        sh("PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True " + args + " --offload cpu", cwd=REPO)
    log(f"{job['name']} done in {time.time() - t:.0f}s")
    STATE["done"].append(job["name"])


def worker():
    try:
        setup()
    except Exception:
        STATE["stage"] = "error"; log("SETUP ERROR\n" + traceback.format_exc()[-2000:]); return
    STATE["stage"] = "ready"
    while True:
        job = Q.get()
        STATE["stage"] = f"running {job['name']} ({Q.qsize()} queued)"
        try:
            run(job)
        except Exception:
            log(f"JOB ERROR {job['name']}\n" + traceback.format_exc()[-1500:])
        STATE["stage"] = "ready" if Q.empty() else STATE["stage"]


class H(http.server.BaseHTTPRequestHandler):
    def q(self):
        return dict(urllib.parse.parse_qsl(urllib.parse.urlparse(self.path).query))

    def ok(self):
        return self.q().get("t") == TOKEN

    def send(self, code, body=b"", ctype="text/plain"):
        self.send_response(code); self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

    def do_GET(self):
        if not self.ok():
            return self.send(403)
        p = urllib.parse.urlparse(self.path).path
        if p == "/file":
            f = os.path.join(OUT, os.path.basename(self.q().get("name", "")))
            return self.send(200, open(f, "rb").read(), "video/mp4") if os.path.isfile(f) else self.send(404)
        body = f"stage: {STATE['stage']}\ndone: {','.join(STATE['done'])}\nqueued: {Q.qsize()}\n" + "\n".join(LOG[-40:])
        self.send(200, body.encode())

    def do_POST(self):
        if not self.ok():
            return self.send(403)
        p = urllib.parse.urlparse(self.path).path
        data = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        if p == "/upload":
            open(os.path.join(IN, os.path.basename(self.q()["name"])), "wb").write(data)
        elif p == "/jobs":
            for j in json.loads(data):
                Q.put(j)
            log(f"queued {len(json.loads(data))} jobs")
        self.send(200, b"ok")

    def log_message(self, *a):
        pass


threading.Thread(target=worker, daemon=True).start()
http.server.ThreadingHTTPServer(("0.0.0.0", 8000), H).serve_forever()
