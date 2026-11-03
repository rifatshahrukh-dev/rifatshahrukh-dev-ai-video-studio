#!/bin/bash
D=${RUNPOD_WORK:?set RUNPOD_WORK to a scratch folder holding podid_job.txt and token_job.txt}
P=$(cat $D/podid_job.txt); T=$(cat $D/token_job.txt); U="https://$P-8000.proxy.runpod.net"
for f in "$@"; do until curl -s --max-time 30 -X POST --data-binary @"$f" "$U/upload?t=$T&name=$(basename "$f")" | grep -q ok; do sleep 10; done; echo "uploaded $f"; done
