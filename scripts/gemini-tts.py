"""Generate Google Gemini TTS for a HyperFrames video — most human-sounding free option.

Drop-in alternative to `scripts/kokoro-tts.py` / `scripts/elevenlabs-tts.py`.
Writes the same files in the same format:

  <project_dir>/audio/narration.wav   (24 kHz mono PCM)
  <project_dir>/transcript.json        (flat list of {word, start, end} entries)

Usage:
  python scripts/gemini-tts.py <project_dir> [--shorts] [--voice NAME]
                                             [--style "..."] [--model NAME]

Flags:
  --shorts        Ask for a livelier, brisker read (GEMINI_TTS_STYLE_SHORTS).
  --voice NAME    Override GEMINI_TTS_VOICE (default 'Sulafat' — warm).
  --style TEXT    Override GEMINI_TTS_STYLE, the plain-language direction for
                  the read, e.g. "Say warmly, like a friendly Bangladeshi shop owner".
  --model NAME    Override GEMINI_TTS_MODEL (default gemini-2.5-flash-preview-tts).

Setup:
  1. Free API key: https://aistudio.google.com/apikey
  2. Add GEMINI_API_KEY=... to .archon/.env (never commit it)
  3. pip install numpy python-dotenv   (no Google SDK needed)

Language is detected from the script text, so Bengali, Hindi, Spanish, etc.
work without extra settings.

Word timestamps: Gemini returns audio only, so word times are ESTIMATED from
the pauses in the audio (see scripts/gemini_tts_lib.py: align_words). Phrase
boundaries land on real pauses; word highlights inside a phrase are approximate.

Phase boundaries: like kokoro-tts.py, the script is split on blank lines; each
phase is one Gemini request, joined with 0.4s of silence. SSML <break> tags,
HTML comments and [SCENE:] markers are stripped (Gemini reads them aloud
otherwise).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv  # noqa: E402

import gemini_tts_lib as g  # noqa: E402

PHASE_BREAK_SECONDS = 0.4

_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_BREAK_TAG_RE = re.compile(r"<break\s[^>]*/?>", re.IGNORECASE)
_SCENE_TAG_RE = re.compile(r"\[SCENE:[^\]]*\]\s*\n?", re.IGNORECASE)


def strip_markup(text: str) -> str:
    cleaned = _HTML_COMMENT_RE.sub("", text)
    cleaned = _BREAK_TAG_RE.sub("", cleaned)
    cleaned = _SCENE_TAG_RE.sub("", cleaned)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def split_phases(text: str) -> list[str]:
    return [" ".join(block.split()) for block in re.split(r"\n\s*\n", text) if block.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Gemini TTS narration + transcript for a HyperFrames video.")
    parser.add_argument("project_dir", type=Path)
    parser.add_argument("--shorts", action="store_true", help="Livelier, brisker read for Shorts.")
    parser.add_argument("--voice", default=None, help="Gemini prebuilt voice name (e.g. Sulafat, Kore, Aoede).")
    parser.add_argument("--style", default=None, help="Plain-language direction for the read.")
    parser.add_argument("--model", default=None, help="Gemini TTS model name.")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    load_dotenv(repo_root / ".archon" / ".env", override=False)
    load_dotenv(repo_root / ".env", override=True)

    project = args.project_dir if args.project_dir.is_absolute() else (repo_root / args.project_dir).resolve()
    script_path = project / "script.txt"
    narration_wav = project / "audio" / "narration.wav"
    transcript_json = project / "transcript.json"

    if not script_path.exists():
        print(f"ERROR: {script_path} not found", file=sys.stderr)
        return 2
    phases = split_phases(strip_markup(script_path.read_text(encoding="utf-8")))
    if not phases:
        print(f"ERROR: {script_path} has no text after stripping markup", file=sys.stderr)
        return 2

    try:
        cfg = g.settings_from_env(shorts=args.shorts)
    except g.GeminiTTSError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 3
    cfg["voice"] = args.voice or cfg["voice"]
    cfg["style"] = args.style if args.style is not None else cfg["style"]
    cfg["model"] = args.model or cfg["model"]
    print(f"[gemini] model={cfg['model']} voice={cfg['voice']} phases={len(phases)}")
    print(f"[gemini] style: {cfg['style']}")

    import numpy as np

    chunks, words, t = [], [], 0.0
    gap = np.zeros(int(PHASE_BREAK_SECONDS * g.SAMPLE_RATE), dtype=np.float32)
    for i, phase in enumerate(phases):
        print(f"[gemini] phase {i + 1}/{len(phases)} ({len(phase)} chars)")
        try:
            audio = g.synthesize(phase, api_key=cfg["api_key"], voice=cfg["voice"],
                                 style=cfg["style"], model=cfg["model"])
        except g.GeminiTTSError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 4
        for w in g.align_words(phase, audio):
            words.append({"word": w["word"], "start": round(t + w["start"], 3), "end": round(t + w["end"], 3)})
        chunks.append(audio)
        t += len(audio) / g.SAMPLE_RATE
        if i < len(phases) - 1:
            chunks.append(gap)
            t += PHASE_BREAK_SECONDS

    narration_wav.parent.mkdir(parents=True, exist_ok=True)
    full = np.concatenate(chunks)
    g.write_wav(narration_wav, full)
    print(f"[gemini] wrote {narration_wav} ({len(full) / g.SAMPLE_RATE:.2f}s)")
    transcript_json.write_text(json.dumps(words, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[gemini] wrote {transcript_json} ({len(words)} words, timings estimated from pauses)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
