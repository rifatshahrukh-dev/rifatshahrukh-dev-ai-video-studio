#!/usr/bin/env bash
# Small images for checking a video, one sheet per check (cheap to look at).
#   frames.sh sheet <video> <out.png> <t1> [t2 ...]          frames at those times, labelled, in one row-wrapped sheet
#   frames.sh strip <video> <out.png> <start> <dur> [fps] [crop]   e.g. mouth strip: ... 18.0 2.5 6 300:300:360:560
# Env: W = thumbnail width (default 180), COLS = sheet columns (default 8).
set -euo pipefail
mode=$1 in=$2 out=$3; shift 3
W=${W:-180}; COLS=${COLS:-8}
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
if [ "$mode" = sheet ]; then
  i=0
  for t in "$@"; do
    ffmpeg -loglevel error -y -ss "$t" -i "$in" -frames:v 1 \
      -vf "scale=$W:-2,drawtext=text='$t':x=4:y=4:fontsize=$((W/8)):fontcolor=yellow:box=1:boxcolor=black" \
      "$tmp/$(printf %04d $i).png"; i=$((i+1))
  done
  cols=$(( i < COLS ? i : COLS )); rows=$(( (i + cols - 1) / cols ))
  ffmpeg -loglevel error -y -framerate 1 -i "$tmp/%04d.png" -vf "tile=${cols}x${rows}" -frames:v 1 "$out"
elif [ "$mode" = strip ]; then
  start=$1 dur=$2 fps=${3:-6} crop=${4:-}
  n=$(python3 -c "import math;print(max(1,math.ceil($dur*$fps)))"); cols=$(( n < COLS*2 ? n : COLS*2 )); rows=$(( (n + cols - 1) / cols ))
  ffmpeg -loglevel error -y -ss "$start" -t "$dur" -i "$in" \
    -vf "fps=$fps,${crop:+crop=$crop,}scale=$W:-2,tile=${cols}x${rows}" -frames:v 1 "$out"
else
  echo "usage: frames.sh sheet|strip ..." >&2; exit 2
fi
echo "$out"
