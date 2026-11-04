#!/usr/bin/env bash
# Make a face video match a new voice line with LatentSync (ByteDance, Apache-2.0). Run on a GPU machine or pod.
#   bash latentsync_job.sh face.mp4 voice.wav out.mp4 [1.5|1.6]
# Needs an NVIDIA GPU: 8 GB VRAM for 1.5, 18 GB for 1.6 (a 24 GB card such as an RTX 4090 is enough). Costs money on a rented GPU:
# the Cinematographer must ask first (GPU, time limit, cost, the exact face video and audio). Pair it with guard.sh.
# STATUS: ran end to end on an RTX PRO 6000 Blackwell (96 GB) in about 12 min including setup: 5 s face clip + 3 s voice line gave a clip whose mouth opens and closes with the speech (checked by eye). Check results on a frame strip.
set -euo pipefail
export HF_HUB_ENABLE_HF_TRANSFER=0   # some GPU images enable hf_transfer without installing it
FACE=$(realpath "${1:?face video}"); VOICE=$(realpath "${2:?voice wav}"); OUT=$(realpath -m "${3:?output mp4}"); V=${4:-1.6}
W=${LATENTSYNC_DIR:-$HOME/LatentSync}
[ -d "$W" ] || git clone -q --depth 1 https://github.com/bytedance/LatentSync "$W"
cd "$W"
command -v apt-get >/dev/null && [ "$(id -u)" = 0 ] && apt-get install -y -qq libgl1 libglib2.0-0 ffmpeg >/dev/null 2>&1 || true
[ -d .venv ] || { pip install -q uv && uv venv -q --python 3.10 .venv && uv pip install -q --python .venv/bin/python -r requirements.txt huggingface_hub
  # Blackwell cards (compute capability 12+) have no kernels in the old pinned torch: use a CUDA 12.8 build
  CAP=$(nvidia-smi --query-gpu=compute_cap --format=csv,noheader | head -1)
  [ "${CAP%%.*}" -ge 12 ] && uv pip install -q --python .venv/bin/python torch==2.8.0 torchvision==0.23.0 --index-url https://download.pytorch.org/whl/cu128
  true; }   # upstream targets Python 3.10
[ -f checkpoints/latentsync_unet.pt ] || .venv/bin/huggingface-cli download "ByteDance/LatentSync-$V" latentsync_unet.pt whisper/tiny.pt --local-dir checkpoints
.venv/bin/python -m scripts.inference --unet_config_path configs/unet/stage2_512.yaml --inference_ckpt_path checkpoints/latentsync_unet.pt \
  --inference_steps 20 --guidance_scale 1.5 --enable_deepcache --video_path "$FACE" --audio_path "$VOICE" --video_out_path "$OUT"
echo "wrote $OUT"
