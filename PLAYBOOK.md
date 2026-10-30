# The Video Playbook — how to make videos that work

This is the "training" part of AI Video Studio: the know-how an AI agent follows to **plan, script, direct,
review and fix** videos — not just generate them. Every rule here came from real production feedback. Read it
before making any video; `CLAUDE.md` holds the non-negotiable rules, this file holds the craft.

---

## 1. How the agent works with you

1. **Understand before making.** Ask what the video is for, who watches it, where it's posted, the language, and
   what the viewer should do after. Read the brand guide.
2. **Plan out loud.** Propose the structure (scenes or steps, rough timings, what's on screen, what's said) and the
   tools (free first). Agree before spending time or money.
3. **Show before committing.** Send stills or a short preview of anything risky (a new character, an edited
   screenshot, a transition) before the long render. Ask "what's wrong with this?" — then fix it.
4. **Approvals.** Nothing paid without an explicit request and a cost estimate. No photo or video leaves the
   machine (to any AI or upload service) without the owner seeing it first.
5. **Confirm feedback before rendering.** When the owner asks for changes, first reply with what you understood
   from each point and exactly what you'll change (scene, time, old → new), what stays the same and anything
   unclear, and ask if they have anything else to add or change. Render only after they approve.
6. **Re-rendering after a change.** Videos up to 1:30: just re-render. Longer videos: ask the owner first,
   explaining the trade-off: a full re-render uses the fewest tokens but takes longest (give the minutes);
   patching only the changed scene uses a few more tokens (splicing, checking the joins) but is much faster.
   Changes that shift timing (new or edited voice lines, scene length, reordering) always need a full render.
7. **Review like a director.** After rendering, check frames at every key moment, the audio edges and the sync,
   and say what was checked. Point out flaws yourself before the owner has to.

## 2. Universal craft rules

- **Hook in the first 2 seconds** (ads/Shorts): a question, a pain, or a surprising visual.
- **Say the brand name in the first line** of narration.
- **One idea per beat.** Lists reveal one item at a time, timed to the word that names it.
- **Never static for more than ~5 s** — add a new element, a highlight or a cut.
- **Captions on**, word-highlighted, in safe zones, big enough to read on a phone.
- **End on a still, on-brand frame** (logo, promise, call to action, store badge) held ≥ 1.5 s.
- **Sound design:** every pop-up (card, comment, notification, order, sticker) gets a short sound; voice always
  on top; music ducks under the voice.
- **Music by context:** tutorials → soft bed; ads → upbeat/funky; pitch → calm corporate; scenes with no voice
  (e.g. a live stream) → music carries the energy.
- **Consistency:** the same product, price and code everywhere it appears — app screenshots, product cards, AI
  footage and captions must all show the same item. If the footage shows a kameez, the app screens show the
  kameez, not the demo item that happened to be in the recording.
- **Real UI, recreated faithfully.** When showing a social post, comments must look like they're *on that post*
  (post header, photo, caption, reactions, then the comment sheet) — not a floating list.
- **Show the right screen for the words.** If the narration says "the app", show the app's home screen, not an
  unrelated setup page.

## 3. App tutorials (from a screen recording)

- The owner's notes describe what happens; **you design the steps**: merge related taps into 3–6 numbered steps.
- Cut loading, waiting (OTPs, spinners) and typing. Keep enough of each screen to show *where* you are.
- **Freeze on each tap** while the voice explains it; pop the tapped button out as an enlarged card (don't zoom
  the whole screen). Highlight boxes for areas, note cards for warnings ("allow this permission in settings").
- **Cues follow the spoken order.** Within a step, each tap, highlight or card appears while its words are
  spoken: if the line says "pick Device Camera… you can also use a photo or video… then tap Continue", the camera
  tap comes first, then the photo/video highlight, then Continue. Check the word timings against every cue.
- Explain *why* where it matters (e.g. "the title is only for you; the caption is what customers see").
- Show *all* options when the owner asks (e.g. swipe through every template).
- **Blur everything personal**: names, phone numbers, addresses, shop/page names, revenue, autofill pop-ups —
  check snapshots of every blurred moment, including scrolls. If a translucent pop-up lets old data show through,
  skip that moment and explain it on a clean screen instead.
- **Replace demo data** that doesn't match the story (e.g. electronics in a clothing demo): render tiles in the
  app's own style and overlay them at the right times; double-check they disappear when the screen changes.
- Narration clips never cut off: pad and fade every clip; edges ≤ −40 dB.

## 4. Social ads (10–30 s, vertical)

- Structure: **hook (pain) → product in action → result → end card**. 10–16 s works well.
- Comments, chats and notifications should read like real customers: **natural local language**, short, and
  **about the exact product on screen** ("I'll take the kameez 😍", "price?", "do you have it in L?"). No codes or
  robotic phrasing unless that's genuinely how people comment.
- Show the outcome visually: comment → "New order!" toast → counter going up, each with a sound.
- If a person on screen moves their lips but you can't sync a voice to them, **don't put voice over them** — use
  music, on-screen text and captions instead; keep narration to the hook and the end card.

## 5. Investor / pitch explainers (16:9, 30–60 s)

- Arc: **market → problem → product (how it works) → impact → closing card**.
- Market: name the home market **and** the global opportunity.
- Show the problem in the real UI (e.g. a flood of unanswered comments under a post, "No reply" tags).
- How it works: 3 short beats with real app screens in a phone mockup, one product used consistently.
- Add a **social-impact** beat if relevant (who it helps: small businesses, women, students…).
- **No business numbers** unless the owner provides and approves them.
- Calm music, clean light design, one phrase on screen per narration sentence.

## 6. AI-generated people and footage

- **Free first** (Wan on free cloud GPUs), but be honest: at low resolution it can look AI-made. If the owner says
  it looks fake, offer: real filming (best), stock footage, or paid (Kling) with a cost estimate.
- **Approved start frame.** Generate/approve a still of the person first; every clip starts from a real frame of
  that person. Restart chains from known-good frames; never chain off a frame where the face has drifted.
- **Eye line:** for live-stream / talking-to-camera shots, the start photo must already look into the lens.
- **Never cover the lens** with a product — the model loses the person's identity. **Swap products below the
  frame:** lower the item out of the bottom edge, lift the next one up from below. Hands leave the frame with the
  item so nothing appears from nowhere.
- **Proportions:** state real garment/product sizes in the prompt ("full-length kameez, shoulder to below the
  knee"; "regular adult top, shoulder-wide").
- **Match the product photo** exactly (pass it as a reference when the model supports it).
- **Check generated audio.** Some models add speech in English; strip it, and remember the lips now move in that
  language.
- **Transitions between AI clips:** never cross-fade the same person (the old product ghosts through) and avoid
  hard cuts (look unnatural). Hide the change behind an on-screen element — e.g. the next product card sweeps
  across the frame, the camera changes behind it, then the card settles into its slot.
- **Paid tools:** typical cost to expect, e.g. ~10 credits per second at 1080p on a turbo model; confirm before
  every job, report the real cost after.
- Frame-by-frame review: identity (face crops side by side), hands, product shape/colour/size, background, swaps
  (6 fps strip), and anything appearing from nowhere.

## 7. Voice and sync

- Natural voices (Gemini TTS) with a plain-language style ("warm, friendly, normal pace"); pick per role
  (narrator vs on-screen character).
- Captions and visual beats land on the spoken words (use word timings).
- On-screen speakers: measure mouth movement (6 fps face strip) and place lines inside it; shorten the line rather
  than letting it run over a closed mouth.
- Check the final render: frames at each voice line's start and end, clip edges, overall loudness.

## 8. Final checklist before sending a video

- [ ] Hook in 2 s; brand named in line 1; ends on a still branded frame
- [ ] Same product/price/code everywhere; right screen for each narration line
- [ ] Every pop-up has a sound; music right for the context and under the voice
- [ ] Voice clips start/end ≤ −40 dB; captions on the words; no voice over unsynced lips
- [ ] Personal data blurred in every frame (check snapshots, scrolls, pop-ups)
- [ ] AI footage: same face throughout, nothing appears from nowhere, no ghosting, real proportions
- [ ] Length fits the platform; aspect ratio right (9:16 social, 16:9 pitch/YouTube)
- [ ] Told the owner exactly what was checked, and any known compromise
