#!/usr/bin/env bash
# Pod self-destruct: deletes THIS pod after N minutes, even if the agent or its session is gone.
#   bash guard.sh 45        (run inside the pod, first thing in its start command)
# Uses the pod's own RUNPOD_POD_ID / RUNPOD_API_KEY (set by Runpod). Verified 3 Nov 2026 on a CPU pod: with a 1-minute timer the pod was gone about 100 s after start (curl fallback; runpodctl not in the test image).
MIN=${1:?minutes}
nohup bash -c "sleep $((MIN * 60)); runpodctl remove pod \"\$RUNPOD_POD_ID\" || curl -s -X DELETE -H \"Authorization: Bearer \$RUNPOD_API_KEY\" \"https://rest.runpod.io/v1/pods/\$RUNPOD_POD_ID\"" >/tmp/guard.log 2>&1 &
echo "guard: pod ${RUNPOD_POD_ID:-?} self-deletes in $MIN min (pid $!)"
