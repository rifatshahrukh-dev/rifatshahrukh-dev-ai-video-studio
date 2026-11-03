# Setup, step by step

Easiest way: paste the repo link into your AI coding tool (for example Claude Code) and say "set this up". The AI reads
`AGENTS.md` and walks you through the steps below. You can also do them yourself.

## Step 1. Check what is missing
```
python3 showcrew setup      # installs 3 small Python packages, then runs the check
python3 showcrew doctor     # tools, keys and domains: ok / MISSING, with the fix
```
Needs `python3`, `node` (with `npx`), `ffmpeg` and `ffprobe` on your machine. Install them with your system's package manager.

## Step 2. Allow the domains
Your environment may block the internet by default. `python3 showcrew domains` lists the hosts. Core ones are needed for every
video; optional ones only for the feature named next to them.

**Claude Code on the web:** open the environment menu in the session title bar, choose **Edit**, open **Network access**,
pick **Limited**, add each host under **Allowed domains**, keep **Allow package managers** ticked, save, then start a new session.
**Anything else:** add the hosts to your firewall, proxy or sandbox allow-list.

| Level | Host | Used for |
|---|---|---|
| core | github.com, raw.githubusercontent.com | download the project and tools |
| core | registry.npmjs.org | `npx hyperframes`, the video renderer |
| core | pypi.org, files.pythonhosted.org | Python packages |
| core | cdn.jsdelivr.net | animation library used by compositions |
| core | generativelanguage.googleapis.com | Gemini voice-over |
| optional | api.elevenlabs.io | ElevenLabs voices |
| optional | huggingface.co | Kokoro voice and model files |
| optional | www.kaggle.com | free GPU clips |
| optional | api.runpod.io, rest.runpod.io | rented GPU |
| optional | api.pexels.com | free stock footage |
| optional | cdn.playwright.dev | browser download for screenshots |

## Step 3. Add your keys (secrets)
`python3 showcrew secrets` lists them with where to get each one. **Never paste a key into the chat.**

| Level | Name | Get it |
|---|---|---|
| core | `GEMINI_API_KEY` | aistudio.google.com/apikey (free tier) |
| optional | `ELEVENLABS_API_KEY` | elevenlabs.io, Profile, API keys |
| optional | `KAGGLE_USERNAME`, `KAGGLE_KEY` | kaggle.com, Settings, API, Create new token |
| optional | `RUNPOD_API_KEY` | runpod.io, Settings, API Keys |
| optional | `HF_TOKEN` | huggingface.co, Settings, Access Tokens (read) |
| optional | `PEXELS_API_KEY` | pexels.com/api |

**Claude Code on the web:** environment menu, **Edit**, **Network secrets** (or **Environment variables**), add `NAME=value`, save,
start a new session.
**Local:** `cp .env.example .env`, fill in the values. `.env` is git-ignored.

## Step 4. Brief the Marketing Manager
Run `python3 showcrew doctor` again. When core shows ok, tell the AI what you want to promote. It asks its questions once, writes a
one-page plan, and waits for your approval before anything is made.

## Rented GPUs (optional, costs money)
The AI always asks first and states GPU, time and cost. Every pod gets a self-destruct timer (`tools/runpod/guard.sh <minutes>`) so it
cannot keep billing if the AI session ends.
