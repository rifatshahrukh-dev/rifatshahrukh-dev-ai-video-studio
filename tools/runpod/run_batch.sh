#!/bin/bash
# usage: run_batch.sh jobs.json  -> waits for pod server, posts jobs, reports progress, exits when all done or on error
D=${RUNPOD_WORK:?set RUNPOD_WORK to a scratch folder holding podid_job.txt and token_job.txt}
P=$(cat $D/podid_job.txt); T=$(cat $D/token_job.txt); U="https://$P-8000.proxy.runpod.net"
J=$1; names=$(python3 -c "import json,sys;print(' '.join(j['name'] for j in json.load(open(sys.argv[1]))))" $J)
posted=0; last=""
for i in $(seq 1 240); do
  s=$(curl -s --max-time 20 "$U/log?t=$T")
  if echo "$s" | grep -q '^stage:'; then
    if [ "$2" = "nopost" ]; then posted=1; fi
    if [ $posted = 0 ]; then curl -s --max-time 30 -X POST --data-binary @$J "$U/jobs?t=$T" >/dev/null && posted=1 && echo "$(date -u +%H:%M:%S) server up; jobs posted: $names"; fi
    st=$(echo "$s" | head -2 | tr '\n' ' ')
    if [ "$st" != "$last" ]; then echo "$(date -u +%H:%M:%S) $st"; last="$st"; fi
    echo "$s" > $D/last_log_job.txt
    echo "$s" | grep -q -E "SETUP ERROR|JOB ERROR" && { echo "ERROR seen:"; echo "$s" | grep -A6 -E "ERROR" | head -12; exit 1; }
    done_list=$(echo "$s" | sed -n 2p); all=1; for n in $names; do echo "$done_list" | grep -q "\b$n\b" || all=0; done
    [ $all = 1 ] && { echo "ALL DONE"; exit 0; }
  fi
  sleep 20
done
echo "timeout"
