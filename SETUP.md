# SETUP — read this if you are the AI agent setting up AI Video Studio

You (the coding agent: Claude Code or similar) are setting this kit up for a user who may not be technical.
Work through the steps **in order**. **Ask, don't assume.** Explain each thing in one or two plain sentences, do
the work yourself, and only ask the user for what only they can do (create an account, approve something, send
a file). Keep a short checklist in your replies so the user always knows where they are.

Items are marked **MANDATORY** (the kit can't make videos without it) or **OPTIONAL** (nice to have; say what it
adds and let the user skip it).

**Security rules for you, from step 1:**
- Never ask the user to paste an API key into the chat. Tell them where to put it (`.archon/.env`, which is
  gitignored, or the cloud environment's secrets), or how to type it into a file themselves.
- Never commit keys, raw screen recordings or personal data. `source/` and `.archon/.env` are gitignored.
- Never use a paid service without the user's explicit request and a cost estimate (see `CLAUDE.md`).
- Before sending any photo or video to an outside service (even a free one), show it to the user and get approval.

---

## Step 1 — Ask what they want (MANDATORY)

Ask these together, in one message:
1. What do you want to make first? (app tutorial / social ad / investor or pitch video / topic Short / not sure)
2. Which language should the voiceover and captions be in? (any: English, Bangla, Hindi, Spanish, …)
3. Where will it be posted? (Instagram/TikTok/YouTube Shorts = vertical 9:16; YouTube/LinkedIn/pitch deck = 16:9)
4. What is the brand, company or app called?

## Step 2 — Install the tools (MANDATORY)

Check what's there before installing. Needed:
| Tool | Why | Install |
|---|---|---|
| Node.js ≥ 22 | HyperFrames (rendering) | nodejs.org, `brew install node`, `winget install OpenJS.NodeJS` |
| Python ≥ 3.10 | voice, tutorial builder, music | python.org, `brew install python`, `winget install Python.Python.3.12` |
| ffmpeg | cutting, mixing, encoding | `brew install ffmpeg`, `winget install Gyan.FFmpeg`, `sudo apt install ffmpeg` |
| Python packages | | `pip install numpy pillow python-dotenv` |
| Playwright + Chromium | screenshot editing, UI recreations | `npm i -D playwright && npx playwright install chromium` |
| HyperFrames CLI | lint / preview / render | runs through `npx hyperframes …` (no install) |

Then: `cp .env.example .archon/.env` and `npx hyperframes doctor`.

A normal laptop is enough: rendering needs no GPU. (AI-generated footage uses free cloud GPUs, Step 6.)

## Step 3 — Voice (MANDATORY for narrated videos; pick one)

- **Google Gemini TTS (RECOMMENDED, free tier):** the most natural voices, 20+ languages, steerable delivery.
  1. Ask the user to open https://aistudio.google.com/apikey, sign in with Google, click **Create API key**.
  2. They add one line to `.archon/.env`: `GEMINI_API_KEY=…` (open the file for them; they type the key).
  3. Test: `python3 scripts/gemini-tts.py --help`, then synthesize one short sentence in their language and play it.
  4. Ask them to pick a voice (play 2–3 samples: e.g. *Sulafat* warm female, *Kore* clear female,
     *Achird* friendly male, *Puck* upbeat male) and save it in `brand/brand.json`.
- **Kokoro (free, offline, English and a few languages):** no key; `pip install kokoro soundfile` + espeak-ng.
- **ElevenLabs (paid):** only if the user asks. Needs `ELEVENLABS_API_KEY`.

## Step 4 — Brand (name MANDATORY, the rest OPTIONAL)

Create `brand/brand.json` from `brand/brand.example.json` and `brand/BRAND.md` (a short human-readable guide).
Ask for, one group at a time:
| Item | Status | If they don't have it |
|---|---|---|
| Brand / app name | **MANDATORY** | — |
| Logo (PNG, transparent background; a wide and a square version) | OPTIONAL | a clean text logo is generated from the name |
| Brand colours (2–4 hex codes or "use the logo's colours") | OPTIONAL | pick a palette from the logo or a neutral one; show it to them |
| Font | OPTIONAL | Noto Sans (ships in `brand/fonts`, supports many scripts) |
| Tagline, call to action ("Download today"), website, app store link | OPTIONAL | leave out of the end card |
| Tone (friendly / premium / playful / formal) | OPTIONAL | friendly and clear |

**If it's an app:** ask which videos need the app on screen, and request:
| Item | Status | Notes |
|---|---|---|
| Screen recordings of each flow (one per tutorial) | **MANDATORY for tutorials** | Phone's built-in screen recorder. Do the flow slowly; it's fine to pause. Then send the file plus a short note of each step ("1. tap Products, 2. tap +, …"). |
| Screenshots of key screens | OPTIONAL (ads, pitch videos) | Home, product page, checkout, notifications |
| A demo account with fake data | OPTIONAL but **strongly recommended** | Less to blur |
| Product photos (clean background) | OPTIONAL | Used in product cards and demos |

Explain that personal data (names, phone numbers, addresses, page/shop names, revenue) is always blurred.
Store raw recordings in `source/` (gitignored).

## Step 5 — Style choices (OPTIONAL, defaults are good)

Ask once, offer the defaults:
- **Music:** tutorials → soft background bed; ads → upbeat/funky; pitch → calm corporate. Generated in code by
  `tools/music/make_music.py` (no licensing). They can also give their own licensed track.
- **Pop-up sounds:** on by default: a notification "ding" on every card/comment, a chime on orders/success, pops
  on quick UI elements. They can turn this off in `brand/brand.json` (`popup_sounds`).
- **Captions:** on (word-highlighted). **Length:** tutorials 40–90 s, ads 10–30 s, pitch 30–60 s.

## Step 6 — AI-generated presenters / footage (OPTIONAL)

Only needed for ads that show a person (e.g. a seller on a live stream). Explain the options honestly:
1. **Real footage (best and free):** film a team member or friend with a phone on a tripod. Offer a shot list.
2. **Free stock footage:** Pexels / Pixabay / Mixkit (check the licence of each clip).
3. **Free AI video on Kaggle** (Wan 2.2): decent for short scenes, can look AI-made. Setup:
   1. The user creates a free account at https://www.kaggle.com and **verifies a phone number**
      (Settings → Phone verification), required for GPUs (about 30 free GPU hours per week).
   2. Settings → API → **Create New Token**. On a laptop: save it as `~/.kaggle/kaggle.json`. In a Claude
      cloud session: add it as a network secret / environment variable for `www.kaggle.com` (see the docs on
      cloud environments). Never in the chat.
   3. Make a notebook with `tools/kaggle/make_wan_clips.py <config.json>`, push it with the Kaggle API
      (`POST https://www.kaggle.com/api/v1/kernels/push`, GPU + internet on), poll its status, download the clips.
4. **Kling AI (PAID, most realistic):** only on the user's request. Connect the Kling connector in Claude, check
   the credit balance, and before **every** job show the exact inputs, settings and expected credits.

## Step 7 — Cloud sessions only: allowed network domains

If you run in a Claude cloud session (claude.ai/code), the environment's network policy must allow the hosts the
kit uses. Tell the user to add them under the environment's **Network access → Allowed domains**:
| Host | For | Status |
|---|---|---|
| `generativelanguage.googleapis.com` | Gemini voices | **MANDATORY** (if using Gemini) |
| `cdn.jsdelivr.net` | GSAP / fonts for rendering | **MANDATORY** |
| package managers (npm, PyPI) | installs | **MANDATORY** (keep "allow package managers" on) |
| `www.kaggle.com`, `www.kaggleusercontent.com` | free AI video | OPTIONAL |
| `huggingface.co`, `*.hf.space` | free image editing Spaces, transcription models | OPTIONAL |
| `kling.ai`, `*.klingai.com` | paid Kling AI | OPTIONAL |
| `pexels.com`, `pixabay.com`, `mixkit.co` (+ their CDNs) | stock footage | OPTIONAL |

## Step 8 — GitHub (OPTIONAL but recommended)

Suggest a **private** repo for the user's own brand material and finished videos. Connect GitHub to Claude
(https://claude.ai/connect-github, install the Claude GitHub App on that repo). Keys never go in git: keep an
`ACCOUNTS.md` that lists services and *where* each key lives, without the values.

## Step 9 — Make the first video (MANDATORY)

Summarise what's set up (✓ / skipped) and start the video they chose in Step 1:
- **Tutorial:** study the recording (1 fps contact sheets; scene-change times; tap coordinates on a grid),
  write `tools/tutorial/specs/<slug>.json` (see `tools/tutorial/README.md`), build, lint, snapshot, render.
- **Ad / pitch video:** write the script with the user, generate the voice, build a HyperFrames composition in
  `videos/<slug>/`, add music + pop-up sounds, lint, snapshot key frames, render.
- **Topic Short:** follow `docs/shorts-workflow.md`.

Before sending any video: run the **sync check** from `CLAUDE.md` (voice clip edges ≤ −40 dB, captions on the
words, lip sync if someone speaks on camera) and tell the user what you checked. Then ask what to change.

---

### Summary: mandatory vs optional
| | Status |
|---|---|
| Claude Code, Node, Python, ffmpeg, Playwright | **MANDATORY** |
| A voice engine (Gemini key recommended, or Kokoro) | **MANDATORY** for narrated videos |
| Brand name | **MANDATORY** |
| Screen recordings | **MANDATORY** for app tutorials |
| Logo, colours, font, tagline, store link, product photos | OPTIONAL |
| Music / pop-up sound preferences | OPTIONAL (good defaults) |
| Kaggle account + token (free AI footage) | OPTIONAL |
| Hugging Face token, stock-footage sites | OPTIONAL |
| Kling (paid) | OPTIONAL, only on explicit request |
| Allowed network domains | **MANDATORY** in Claude cloud sessions (the mandatory rows of Step 7) |
| GitHub repo | OPTIONAL |
