#!/usr/bin/env bash
# Build and render every hook variant in variants.json, then restore the default video.
# Copy next to a video's builders. They must read the VARIANT env var (unset = default video).
#   bash make_variants.sh [A B C]   -> out/<name>-<id>.mp4
set -euo pipefail
cd "$(dirname "$0")"
name=$(basename "$PWD")
ids=${*:-$(python3 -c "import json;print(' '.join(json.load(open('variants.json'))))")}
for id in $ids; do
  VARIANT=$id python3 build_narration.py >/dev/null
  # self-check: add a quick assert here that any on-screen beat still lands on its spoken word (word timings)
  VARIANT=$id python3 build_index.py >/dev/null
  npx hyperframes lint . >/dev/null
  npx hyperframes render . -o "out/$name-$id.mp4" 2>&1 | grep -E "MB|rror" || true
done
python3 build_narration.py >/dev/null && python3 build_index.py >/dev/null   # restore default
