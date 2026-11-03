---
name: showcrew-ai-marks
description: Optional and opt-in. Only when the user asks to remove AI provenance marks (invisible Unicode, C2PA and other metadata) from a file. Always ask first and warn about AI-labelling rules.
---

# AI marks cleaner (opt-in, off by default)

1. **Ask first.** Never run this on your own. Ask: "Do you want the AI provenance marks removed from this file? Many platforms and some laws require AI-generated content to be labelled; you are responsible for following them."
2. **Only on files the user owns** or has the right to edit. Never to pass AI content off as real where disclosure is required.
3. The tool is not bundled. Install it on request from its author: `git clone --depth 1 https://github.com/guillaumemeyer/watermarks-remover` (MIT licence, credit Guillaume Meyer) and follow its README.
4. Tell the user exactly what was removed and what could not be removed.
