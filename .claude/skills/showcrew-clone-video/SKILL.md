---
name: showcrew-clone-video
description: Optional. Clone the structure of a reference video with the Hypit agent tool (separate install, run by the user). Ask first.
---

# Clone a reference video (optional, uses Hypit)

[Hypit](https://github.com/hypit-ai/hypit) gives an AI agent a workflow language for video: drop in a reference, and it builds footage, captions and B-roll anchored to words instead of seconds. Showcrew does **not** bundle or copy it.

1. **Ask first:** "Use Hypit to clone this reference?" Its licence (Apache-2.0 plus conditions) lets you run it yourself, including for client work. It does not allow offering it to third parties as a hosted service or reselling it. Read its `LICENSE`.
2. **Start free:** run `python3 showcrew breakdown <file|URL> <out dir>` (cuts, pacing, frame sheet) and let the Director propose 2-3 versions. Often that is enough.
3. **If the user wants Hypit:** tell them to install it themselves from its README (`npx skills add hypit-ai/hypit -g`; needs Node 22.15+). Hosted model services it can call cost money: apply the usual rule, ask with exact files, prompt and cost before any call.
4. Use it only on references the user may adapt; make new footage, never re-upload the original.
