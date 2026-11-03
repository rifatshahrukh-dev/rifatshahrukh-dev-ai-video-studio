# AI footage on a rented GPU (LTX-2.5, Runpod)

Costs money. The Cinematographer must ask first: GPU, time limit, cost, and the exact inputs and prompt.

- `srv_job.py` runs inside the pod: installs LTX-2, downloads the models, then serves token-protected HTTP on port 8000
  (`/upload`, `/jobs`, `/log`, `/file`). Pass it base64 in env `SCRIPT_B64` with a random `TOKEN` and your `HF_TOKEN`.
  Start command: `bash -c "bash /guard.sh 30 & echo $SCRIPT_B64 | base64 -d > /srv.py && python -u /srv.py"`.
  Image `runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404`, A100 80 GB, CUDA 12.8+, port `8000/http`.
- `upload.sh <files>` sends start frames. `run_batch.sh <jobs.json>` posts jobs and waits. Both read `$RUNPOD_WORK/podid_job.txt`
  and `$RUNPOD_WORK/token_job.txt` (keep those out of git).
- Job: `{"name","prompt","frames","seed","images":[["x.jpg", frame_idx, strength]]}`. Frames must be 8k+1 (121 = 5 s). Default 768x1344.
- `guard.sh <minutes>` makes the pod delete itself. Always set it to the approved hard limit.
- Delete the pod right after downloading the clip and confirm spend is $0/hr.
