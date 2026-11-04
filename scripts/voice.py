"""One voice command for every engine: picks the best one you have set up, applies your pronunciation list, writes the same files.

    python3 scripts/voice.py script.txt out_dir [--engine auto|elevenlabs|gemini|kokoro] [--pron pronunciation.json]

Engine order for auto: ElevenLabs (ELEVENLABS_API_KEY), Gemini (GEMINI_API_KEY), then offline Kokoro (model files in the current folder
or $KOKORO_DIR). Output: out_dir/narration.wav and out_dir/transcript.json ([{word,start,end}]), whatever the engine.
pronunciation.json: {"Showcrew": "Show crew", "GIF": "jiff"}: whole words, case-insensitive, replaced before speaking (the transcript then holds the respelled words).
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def apply_pron(text, pron):
    for word, say in pron.items():
        text = re.sub(rf"\b{re.escape(word)}\b", say, text, flags=re.I)
    return text


def pick_engine(env=os.environ, kokoro_dir="."):
    if env.get("ELEVENLABS_API_KEY"):
        return "elevenlabs"
    if env.get("GEMINI_API_KEY"):
        return "gemini"
    if os.path.exists(os.path.join(kokoro_dir, "kokoro-v1.0.onnx")):
        return "kokoro"
    raise SystemExit("no voice engine ready: set ELEVENLABS_API_KEY or GEMINI_API_KEY, or put kokoro-v1.0.onnx and voices-v1.0.bin in this folder")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script"); ap.add_argument("out")
    ap.add_argument("--engine", default="auto", choices=["auto", "elevenlabs", "gemini", "kokoro"]); ap.add_argument("--pron")
    a = ap.parse_args()
    kdir = os.environ.get("KOKORO_DIR", ".")
    engine = pick_engine(kokoro_dir=kdir) if a.engine == "auto" else a.engine
    text = open(a.script).read()
    if a.pron:
        text = apply_pron(text, json.load(open(a.pron)))
    os.makedirs(a.out, exist_ok=True)
    tmp = tempfile.mkdtemp()
    open(f"{tmp}/script.txt", "w").write(text)
    if engine == "kokoro":
        subprocess.run([sys.executable, f"{HERE}/kokoro-onnx-tts.py", f"{tmp}/script.txt", tmp, "--model", f"{kdir}/kokoro-v1.0.onnx",
                        "--voices", f"{kdir}/voices-v1.0.bin"], check=True)
        wav = f"{tmp}/narration.wav"
    else:
        subprocess.run([sys.executable, f"{HERE}/{engine}-tts.py", tmp], check=True)
        wav = f"{tmp}/audio/narration.wav"
    shutil.copy(wav, f"{a.out}/narration.wav"); shutil.copy(f"{tmp}/transcript.json", f"{a.out}/transcript.json")
    print(f"engine {engine}: wrote {a.out}/narration.wav and transcript.json")


if __name__ == "__main__":
    main()
