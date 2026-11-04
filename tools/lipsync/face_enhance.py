"""Sharpen a face in a video (fixes the soft mouth after lip-sync). Free, CPU only, about 1.6 s per 768x1344 frame.

    pip install onnxruntime numpy pillow
    # model (340 MB): gfpgan_1.4.onnx from https://github.com/facefusion/facefusion-assets/releases/tag/models-3.0.0 -> ./gfpgan.onnx
    python3 tools/lipsync/face_enhance.py in.mp4 out.mp4 X Y SIZE [WEIGHT]

X Y SIZE = a square around the face in video pixels (pick it from a frame sheet; the face may move a little inside it).
WEIGHT = 0..1 how strongly the restored face replaces the original (default 0.8). The patch edges are feathered. Audio is copied.
Uses the GFPGAN 1.4 face-restoration model (TencentARC, Apache-2.0). Check the weights' terms before commercial use.
"""
import subprocess, sys, json, numpy as np, onnxruntime as ort
from PIL import Image
src, dst, X, Y, S = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
W = float(sys.argv[6]) if len(sys.argv) > 6 else 0.8
info = json.loads(subprocess.check_output(["ffprobe","-v","error","-select_streams","v","-show_entries","stream=width,height,r_frame_rate","-of","json",src]))["streams"][0]
w, h = info["width"], info["height"]; num, den = map(int, info["r_frame_rate"].split("/")); fps = num / den
sess = ort.InferenceSession("gfpgan.onnx", providers=["CPUExecutionProvider"]); name = sess.get_inputs()[0].name
yy, xx = np.mgrid[0:S, 0:S]; d = np.minimum.reduce([xx, yy, S - 1 - xx, S - 1 - yy]) / (S * 0.18)
mask = (np.clip(d, 0, 1) ** 1.5 * W).astype(np.float32)[..., None]   # feathered edges so the patch has no visible border
raw = subprocess.run(["ffmpeg","-v","error","-i",src,"-f","rawvideo","-pix_fmt","rgb24","-"],capture_output=True,check=True).stdout
frames = np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)
out = []
for i, f in enumerate(frames):
    crop = Image.fromarray(f[Y:Y+S, X:X+S]).resize((512, 512), Image.LANCZOS)
    a = ((np.asarray(crop, np.float32) / 255 - 0.5) / 0.5).transpose(2, 0, 1)[None]
    r = sess.run(None, {name: a})[0][0].transpose(1, 2, 0)
    r = ((np.clip(r, -1, 1) * 0.5 + 0.5) * 255).astype(np.uint8)
    r = np.asarray(Image.fromarray(r).resize((S, S), Image.LANCZOS), np.float32)
    g = f.copy().astype(np.float32); g[Y:Y+S, X:X+S] = g[Y:Y+S, X:X+S] * (1 - mask) + r * mask
    out.append(g.clip(0, 255).astype(np.uint8))
    if i % 10 == 0: print(i, len(frames), flush=True)
p = subprocess.Popen(["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{w}x{h}","-r",str(fps),"-i","-","-i",src,"-map","0:v","-map","1:a","-c:v","libx264","-crf","14","-pix_fmt","yuv420p","-c:a","copy",dst],stdin=subprocess.PIPE)
p.communicate(np.stack(out).tobytes())
print("wrote", dst)
