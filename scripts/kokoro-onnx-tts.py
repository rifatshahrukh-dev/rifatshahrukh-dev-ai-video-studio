"""Free offline voice-over, no API key and no PyTorch: Kokoro on ONNX Runtime.

    pip install kokoro-onnx soundfile
    # one-time model files (about 350 MB): kokoro-v1.0.onnx and voices-v1.0.bin from
    #   https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0
    python3 scripts/kokoro-onnx-tts.py script.txt out_dir [--model kokoro-v1.0.onnx] [--voices voices-v1.0.bin] [--voice af_heart]

Writes out_dir/narration.wav and out_dir/transcript.json ([{word,start,end}]). Word times are spread over each sentence by
word length, so they are good to about 0.1-0.2 s: fine for pop-ups and captions, not for lip sync.
"""
import argparse
import json
import re

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

ap = argparse.ArgumentParser()
ap.add_argument("script"); ap.add_argument("out")
ap.add_argument("--model", default="kokoro-v1.0.onnx"); ap.add_argument("--voices", default="voices-v1.0.bin")
ap.add_argument("--voice", default="af_heart"); ap.add_argument("--speed", type=float, default=1.05); ap.add_argument("--lang", default="en-us")
a = ap.parse_args()
k = Kokoro(a.model, a.voices)
sents = [s for s in re.split(r"(?<=[.!?:])\s+", open(a.script).read().strip()) if s]
audio, words, t, pause = [], [], 0.0, 0.25
for s in sents:
    wav, sr = k.create(s, voice=a.voice, speed=a.speed, lang=a.lang)
    ws, total, x = s.split(), sum(len(w) for w in s.split()), t
    for w in ws:
        d = len(wav) / sr * len(w) / total
        words.append({"word": w, "start": round(x, 3), "end": round(x + d, 3)}); x += d
    audio += [wav, np.zeros(int(pause * sr), np.float32)]
    t += len(wav) / sr + pause
sf.write(f"{a.out}/narration.wav", np.concatenate(audio), sr)
json.dump(words, open(f"{a.out}/transcript.json", "w"))
print(f"{t:.1f}s, {len(words)} words")
