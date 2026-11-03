"""Word-anchored timing: place on-screen items on spoken words instead of seconds.

    python3 tools/wordsync/wordsync.py transcript.json plan.json > timings.json

transcript.json: [{"word": "Start", "start": 0.4, "end": 0.7}, ...]  (what the TTS scripts write)
plan.json:       [{"id": "price-card", "word": "free", "nth": 1, "offset": -0.1, "hold": 1.5}, ...]
                 word = spoken word (case and punctuation ignored); nth = which match (default 1);
                 offset = seconds relative to the word start (default 0); hold = seconds to stay (default 1).
Output: {"price-card": {"start": 2.3, "end": 3.8}, ...}. Put "start" into data-start / the GSAP timeline.
A word that is not found is an error, so a rewritten script can never leave an item at a stale time.
"""
import json
import re
import sys


def norm(w):
    return re.sub(r"[^\w]", "", w).lower()


def wordsync(words, plan):
    out = {}
    for item in plan:
        hits = [w for w in words if norm(w["word"]) == norm(item["word"])]
        n = item.get("nth", 1)
        if len(hits) < n:
            raise SystemExit(f"{item['id']}: word '{item['word']}' #{n} not in the transcript")
        start = max(0.0, round(hits[n - 1]["start"] + item.get("offset", 0), 3))
        out[item["id"]] = {"start": start, "end": round(start + item.get("hold", 1), 3)}
    return out


if __name__ == "__main__":
    t, p = (json.load(open(f)) for f in sys.argv[1:3])
    print(json.dumps(wordsync(t["words"] if isinstance(t, dict) else t, p), indent=1))
