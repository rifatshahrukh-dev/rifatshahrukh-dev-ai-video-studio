#!/usr/bin/env bash
# Make a face video match a new voice line with LatentSync (ByteDance, Apache-2.0). Run on a GPU machine or pod.
#   bash latentsync_job.sh face.mp4 voice.wav out.mp4 [1.5|1.6]
# Needs an NVIDIA GPU: 8 GB VRAM for 1.5, 18 GB for 1.6 (a 24 GB card such as an RTX 4090 is enough). Costs money on a rented GPU:
# the Cinematographer must ask first (GPU, time limit, cost, the exact face video and audio). Pair it with guard.sh.
# STATUS: written from the upstream README, not yet run end to end. Check the result with lipsync_check.py.
set -euo pipefail
FACE=$(realpath "${1:?face video}"); VOICE=$(realpath "${2:?voice wav}"); OUT=$(realpath -m "${3:?output mp4}"); V=${4:-1.6}
W=${LATENTSYNC_DIR:-$HOME/LatentSync}
[ -d "$W" ] || git clone -q --depth 1 https://github.com/bytedance/LatentSync "$W"
cd "$W"
[ -d .venv ] || { python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt huggingface_hub; }   # upstream also offers setup_env.sh
[ -f checkpoints/latentsync_unet.pt ] || .venv/bin/huggingface-cli download "ByteDance/LatentSync-$V" latentsync_unet.pt whisper/tiny.pt --local-dir checkpoints
.venv/bin/python -m scripts.inference --unet_config_path configs/unet/stage2_512.yaml --inference_ckpt_path checkpoints/latentsync_unet.pt \
  --inference_steps 20 --guidance_scale 1.5 --enable_deepcache --video_path "$FACE" --audio_path "$VOICE" --video_out_path "$OUT"
echo "wrote $OUT"
