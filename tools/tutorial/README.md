# Tutorial builder: screen recording → narrated 9:16 how-to video

`build_tutorial.py` turns a phone screen recording plus a small JSON spec into a finished HyperFrames project:
voiceover per step (Gemini TTS), cuts that skip waiting/typing, freezes on each tap while the voice explains it,
**pop-out cards** of the tapped button, highlight boxes, note cards, privacy blurs, word-synced captions,
intro/outro cards with your brand, music and a **notification sound on every pop-up**.

```bash
python3 tools/tutorial/build_tutorial.py tools/tutorial/specs/<slug>.json      # needs GEMINI_API_KEY
npx hyperframes lint     videos/<slug>
npx hyperframes snapshot videos/<slug> --at 5,12,20                             # check pops + blurs
npx hyperframes render   videos/<slug> -o videos/<slug>/out/<slug>.mp4
```

## Spec fields
| Field | Meaning |
|---|---|
| `slug`, `title`, `subtitle` | Project folder name, intro title (`*word*` = gradient highlight), subtitle |
| `source` | The raw screen recording (keep it in `source/`, which is gitignored: it shows personal data) |
| `voice`, `style` | Gemini voice name and a plain-language delivery direction |
| `blurs[]` | `{t:[from,to], box:[x,y,w,h]}` areas to blur (names, phone numbers, addresses, page names…) |
| `steps[]` | `kind: intro/outro`, or a screen step with `vo`, `title`, `ranges` (recording seconds to show), `taps`, `highlights`, `holds`, `note`; `"cont": true` continues the previous numbered step |
| `taps[]` | `{t, x, y, label, box, ring_from}`: tap ring at x,y; `box` = the button's area for the pop-out card |

## Guidelines that make tutorials good
- Merge actions into **3–6 numbered steps**; cut loading, waiting and typing.
- Say the brand name in the first line. Pop-out cards, not zooming the whole screen.
- Narration must never be cut off: every `videos/<slug>/audio/stepNN.wav` starts and ends ≤ −40 dB (the builder pads and fades clips).
- Blur all personal data, and check snapshots of every blurred moment, including scrolls.
