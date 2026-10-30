"""Google Gemini TTS helpers — shared by scripts/gemini-tts.py and per-video builders.

Gemini's speech models ("gemini-*-tts") sound noticeably more human than
Kokoro or Edge TTS, speak 20+ languages including Bengali, and take a plain-
language style direction ("warm, friendly, smiling"). There is a free tier via a
Google AI Studio API key (https://aistudio.google.com/apikey).

Gemini returns raw audio only — no word timestamps. `align_words()` estimates
them: it finds the pauses in the audio, snaps each phrase boundary (commas,
dandas, full stops…) to the nearest pause, and spreads the words of each phrase
across it by length. Captions therefore switch phrases on time; per-word
highlights inside a phrase are approximate (typically within ~0.15s).

Only the standard library + numpy are needed.
"""
from __future__ import annotations

import base64
import json
import os
import re
import time
import urllib.error
import urllib.request

import numpy as np

SAMPLE_RATE = 24_000          # Gemini TTS returns 24 kHz, 16-bit, mono PCM
API_ROOT = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_MODEL = "gemini-2.5-flash-preview-tts"
DEFAULT_VOICE = "Sulafat"      # "warm" female voice; see .env.example for others
DEFAULT_STYLE = "Read this aloud in a warm, friendly, natural voice, like a real person talking to a friend"

# Phrase-ending punctuation (Latin + Bengali danda/double danda + ellipsis)
_PHRASE_END_RE = re.compile(r"[,;:.!?…।॥]+[\"'”’)]*$|\.\.\.$")
_WORDCHAR_RE = re.compile(r"\w")


class GeminiTTSError(RuntimeError):
    pass


def _post_json(url: str, body: dict, api_key: str, timeout: float = 120.0) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def list_tts_models(api_key: str) -> list[str]:
    """Names of the models on this key that look like speech models."""
    req = urllib.request.Request(f"{API_ROOT}/models?pageSize=200", headers={"x-goog-api-key": api_key})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return sorted(m["name"].split("/", 1)[-1] for m in data.get("models", []) if "tts" in m.get("name", ""))


def synthesize(text: str, *, api_key: str, voice: str = DEFAULT_VOICE, style: str = DEFAULT_STYLE,
               model: str = DEFAULT_MODEL, retries: int = 4) -> np.ndarray:
    """Speak `text` and return float32 mono samples at SAMPLE_RATE."""
    prompt = f"{style.rstrip(': ')}:\n{text}" if style else text
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}},
        },
    }
    url = f"{API_ROOT}/models/{model}:generateContent"
    for attempt in range(retries + 1):
        try:
            data = _post_json(url, body, api_key)
            break
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:500]
            if e.code == 404:
                try:
                    avail = ", ".join(list_tts_models(api_key)) or "none found"
                except Exception:  # noqa: BLE001 — best-effort hint only
                    avail = "could not list models"
                raise GeminiTTSError(f"Model '{model}' not found. TTS models on this key: {avail}. "
                                     "Set GEMINI_TTS_MODEL to one of them.") from e
            if e.code in (429, 500, 502, 503, 504) and attempt < retries:
                wait = 2 ** (attempt + 1)
                print(f"[gemini] HTTP {e.code}, retrying in {wait}s…")
                time.sleep(wait)
                continue
            if e.code in (400, 401, 403):
                raise GeminiTTSError(f"Gemini rejected the request (HTTP {e.code}). Check GEMINI_API_KEY. {detail}") from e
            raise GeminiTTSError(f"Gemini HTTP {e.code}: {detail}") from e
    parts = (data.get("candidates") or [{}])[0].get("content", {}).get("parts", [])
    audio_b64 = next((p["inlineData"]["data"] for p in parts if "inlineData" in p), None)
    if not audio_b64:
        raise GeminiTTSError(f"Gemini returned no audio: {json.dumps(data)[:400]}")
    pcm = np.frombuffer(base64.b64decode(audio_b64), dtype="<i2").astype(np.float32) / 32768.0
    return trim_silence(pcm)


def trim_silence(x: np.ndarray, pad: float = 0.06) -> np.ndarray:
    """Trim leading/trailing silence, keeping a short pad."""
    env = _envelope(x)
    on = np.nonzero(env > _threshold(env))[0]
    if not len(on):
        return x
    hop = int(SAMPLE_RATE * 0.01)
    a = max(0, on[0] * hop - int(pad * SAMPLE_RATE))
    b = min(len(x), (on[-1] + 1) * hop + int(pad * SAMPLE_RATE))
    return x[a:b]


def _envelope(x: np.ndarray, win: float = 0.01) -> np.ndarray:
    hop = int(SAMPLE_RATE * win)
    n = len(x) // hop
    if n == 0:
        return np.zeros(1, dtype=np.float32)
    frames = x[: n * hop].reshape(n, hop)
    return np.sqrt((frames ** 2).mean(axis=1))


def _threshold(env: np.ndarray) -> float:
    loud = np.percentile(env, 95) if len(env) else 0.0
    return max(1e-4, loud * 0.06)


def _pauses(x: np.ndarray, min_pause: float = 0.12) -> list[tuple[float, float]]:
    """(start, end) seconds of silent stretches inside the speech."""
    env = _envelope(x)
    quiet = env < _threshold(env)
    pauses, i, n = [], 0, len(quiet)
    while i < n:
        if quiet[i]:
            j = i
            while j < n and quiet[j]:
                j += 1
            if i > 0 and j < n and (j - i) * 0.01 >= min_pause:
                pauses.append((i * 0.01, j * 0.01))
            i = j
        else:
            i += 1
    return pauses


def _speech_span(x: np.ndarray) -> tuple[float, float]:
    env = _envelope(x)
    on = np.nonzero(env > _threshold(env))[0]
    if not len(on):
        return 0.0, len(x) / SAMPLE_RATE
    return on[0] * 0.01, (on[-1] + 1) * 0.01


def _weight(word: str) -> int:
    return max(1, len(_WORDCHAR_RE.findall(word)))


def align_words(text: str, audio: np.ndarray) -> list[dict]:
    """Estimate {word, start, end} for each whitespace word of `text` in `audio`."""
    words = [w for w in text.split() if _WORDCHAR_RE.search(w)]
    if not words:
        return []
    t0, t1 = _speech_span(audio)
    pauses = [p for p in _pauses(audio) if t0 < p[0] and p[1] < t1]

    # Phrases = runs of words ending in punctuation.
    phrases, cur = [], []
    for w in words:
        cur.append(w)
        if _PHRASE_END_RE.search(w):
            phrases.append(cur)
            cur = []
    if cur:
        phrases.append(cur)

    # Expected boundary times by length, snapped to the nearest unused pause.
    total_w = sum(_weight(w) for w in words)
    bounds, acc, used = [], 0, set()
    for ph in phrases[:-1]:
        acc += sum(_weight(w) for w in ph)
        guess = t0 + (t1 - t0) * acc / total_w
        best = None
        for k, (a, b) in enumerate(pauses):
            if k in used:
                continue
            d = abs((a + b) / 2 - guess)
            if d <= 0.9 and (best is None or d < best[0]):
                best = (d, k)
        if best is not None:
            used.add(best[1])
            a, b = pauses[best[1]]
            bounds.append((a, b))
        else:
            bounds.append((guess, guess))
    # Keep boundaries monotonic
    for k in range(1, len(bounds)):
        if bounds[k][0] < bounds[k - 1][1]:
            bounds[k] = (bounds[k - 1][1], max(bounds[k - 1][1], bounds[k][1]))

    out = []
    starts = [t0] + [b for (_, b) in bounds]
    ends = [a for (a, _) in bounds] + [t1]
    for ph, s, e in zip(phrases, starts, ends):
        tot = sum(_weight(w) for w in ph)
        t = s
        for w in ph:
            d = (e - s) * _weight(w) / tot
            out.append({"word": w, "start": round(t, 3), "end": round(t + d * 0.94, 3)})
            t += d
    return out


def settings_from_env(shorts: bool = False) -> dict:
    """API key, model, voice and style from the environment (.archon/.env)."""
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise GeminiTTSError("GEMINI_API_KEY is not set. Get a free key at https://aistudio.google.com/apikey "
                             "and add GEMINI_API_KEY=... to .archon/.env")
    style = os.environ.get("GEMINI_TTS_STYLE", DEFAULT_STYLE)
    if shorts:
        style = os.environ.get("GEMINI_TTS_STYLE_SHORTS", style + ", at a lively, brisk pace")
    return {
        "api_key": key,
        "model": os.environ.get("GEMINI_TTS_MODEL", DEFAULT_MODEL),
        "voice": os.environ.get("GEMINI_TTS_VOICE", DEFAULT_VOICE),
        "style": style,
    }


def write_wav(path, audio: np.ndarray) -> None:
    import wave
    pcm = (np.clip(audio, -1.0, 1.0) * 32767.0).astype("<i2").tobytes()
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(pcm)
