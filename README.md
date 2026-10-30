# AI Video Studio

**Turn screen recordings, screenshots and a short brief into finished, professional videos with an AI coding
agent.** App tutorials, social ads, investor/pitch explainers and YouTube Shorts, with natural AI voiceover in
many languages, captions synced to every word, privacy blurring, sound design, generated music and optional
AI-generated presenters. Works for any company, app, brand or creator.

> ### Credits
> This project is **built on [coleam00/hyperframes-ai-video-generation](https://github.com/coleam00/hyperframes-ai-video-generation)**
> by **Cole Medin ([@coleam00](https://github.com/coleam00))**, a one-command English YouTube Shorts generator
> powered by **[HyperFrames](https://hyperframes.heygen.com/)** (HeyGen's HTML + GSAP video framework,
> [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes)) and **[Archon](https://archon.diy)**
> (Cole Medin's workflow harness). The original Shorts workflow is kept intact in
> [`docs/shorts-workflow.md`](docs/shorts-workflow.md). Thank you, Cole!
>
> Also used: Google Gemini TTS, Kokoro TTS, Wan 2.2 (Wan-AI) on Kaggle, Playwright, GSAP, ffmpeg.

## More than a video generator: a trained AI video producer

Most AI video tools generate a clip and stop. This kit trains the agent to work like a **producer, director and
editor**:

- **Plans** the video with you: purpose, audience, platform, language, structure and timing, before making anything.
- **Writes** the script and on-screen text, natural in your language, with the brand named up front.
- **Directs** AI footage with production know-how: consistent faces, products swapped naturally, real-world sizes,
  transitions that never look fake.
- **Reviews its own work** frame by frame against a quality checklist (sync, blur, consistency, pacing, sound)
  and tells you what it checked and what it compromised on.
- **Takes feedback and fixes it**, and asks before anything costs money or leaves your machine.
- **Writes the post** for each platform (LinkedIn, Instagram, YouTube), knowing what shows before "see more".

All of this know-how is written down in **[`PLAYBOOK.md`](PLAYBOOK.md)** (the craft) and **[`CLAUDE.md`](CLAUDE.md)**
(the non-negotiable rules), learned from real production feedback.

## Get started (the easy way)

Open this repo in **[Claude Code](https://claude.ai/code)** (desktop app, terminal or claude.ai/code) and paste:

> _"Read SETUP.md and set everything up for me. Ask me whatever you need."_

The agent walks you through everything in [`SETUP.md`](SETUP.md): it installs tools, asks for your brand,
helps you create the free accounts and keys it needs (and tells you which are optional), and then makes your
first video. You answer questions; it does the work.

## What it makes

| Video type | Format | Input you give |
|---|---|---|
| **App how-to tutorials** | 9:16, ~40–90 s | A phone screen recording + what you did in it |
| **Social ads** (Reels/TikTok/Shorts) | 9:16, 10–30 s | Your product, the message, screenshots or footage |
| **Investor / pitch explainers** | 16:9, 30–60 s | What your product does + app screenshots |
| **Story ads with an AI presenter** | 9:16 | A description or photo of the presenter (free models, or paid Kling on request) |
| **Topic Shorts** | 9:16, 30–60 s | Just a topic (the original workflow) |

## Features

- **Voiceover in any language** (Bangla, Hindi, English, …) with Google **Gemini TTS** (free tier, very natural),
  Kokoro (free, offline) or ElevenLabs (paid). Word-synced captions; no line is ever cut off.
- **Tutorial builder** (`tools/tutorial/`): cuts waiting and typing out of a screen recording, freezes on each tap
  while the voice explains, pops the tapped button out as an enlarged card, highlights, notes, step titles.
- **Privacy blurring** of names, phone numbers, addresses, shop/page names and figures.
- **Screenshot editing** (`tools/screens/`): swap the product, price or text in real app screenshots so demos show
  what you want.
- **Recreated UI** (social posts, comment sheets, live-stream screens, notifications) animated frame by frame.
- **Sound design**: a notification sound on every pop-up, order chimes, pops (`shared/audio/sfx/`).
- **Music generated in code** (`tools/music/`): calm corporate or funky/groovy, so there are no licensing problems.
- **AI footage, free**: Wan 2.2 on Kaggle's free GPUs (`tools/kaggle/`), driven by the agent. **Paid** Kling AI
  only on your explicit request, with a cost estimate before every job.
- **Quality rules the agent follows** (`CLAUDE.md`): free tools first, approval before anything leaves your
  machine, voice/lip sync checks, pacing, typography, thumbnail-grade last frames.

## Repo layout

```
PLAYBOOK.md       the craft: how to plan, direct, review and post each kind of video
SETUP.md          step-by-step setup the agent runs with you
CLAUDE.md         standing rules (paid tools, approvals, sync, sounds, privacy)
brand/            your brand: brand.json (from brand.example.json), BRAND.md, logos/, fonts/
tools/tutorial/   screen recording → tutorial video builder (+ example spec)
tools/screens/    edit/blur app screenshots
tools/music/      generated music beds
tools/kaggle/     free-GPU AI video (Wan 2.2) notebook generator
scripts/          TTS engines (Gemini, Kokoro, ElevenLabs, Edge), SFX generator, helpers
templates/        Shorts templates (classic, archon, anthropic)
shared/audio/sfx/ sound effects
.claude/          skills + rules the agent follows
.archon/          the original topic-to-Short workflow
videos/<slug>/    one folder per video (gitignored by default)
```

## License
MIT. Original work © Cole Medin; extensions © their contributors.
