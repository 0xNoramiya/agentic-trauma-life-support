# Narration script — English

> Each scene's narration is below its time block. Total speaking ~80 s within the 180 s video; the rest is the live-demo clip + held-frame moments. Read aloud at ~150 wpm, calm and clinical — not announcer-y. The pacing should match the on-screen restraint: leave room around the words.

---

## Scene 1 — Cold open (0:00–0:08)

_No narration. The text on screen carries it._

> [text on screen, fades in slowly] *Most trauma deaths happen where there isn't a trauma surgeon on call.*

---

## Scene 2 — Title (0:08–0:18)

> This is **Agentic Trauma Life Support** — the agentic AI realization of the same protocol.

---

## Scene 3 — What it does (0:18–0:30)

> A clinician uploads a chest X-ray. Types the vitals. Picks a language. And in seconds, gets a structured ATLS primary survey.

---

## Scene 4 — Live demo (0:30–1:50)

_This scene plays the recorded screen capture. Either keep your original voiceover from the recording, or mute it and let the visual carry. Decision noted in `docs/VIDEO_PLAN.md` under Open Questions._

---

## Scene 5 — How it works (1:50–2:15)

> The pipeline is three agents on the same model. The Drafter reads the X-ray and writes a structured primary survey as JSON. The Verifier re-examines the same image and patches anything inconsistent. The Renderer turns it into an SBAR-style handoff.

---

## Scene 6 — Hardware story (2:15–2:35)

> Seventy-two billion parameters in BF16 is a hundred and forty-five gigabytes of weights. The model fits in full precision on a single AMD MI300X — the only sub-two-dollar-per-hour GPU that can hold it without sharding or quantizing.

---

## Scene 7 — Credibility (2:35–2:50)

> The verifier exists for one reason: don't invent findings. We have a test case where the chest X-ray is normal but the vitals are bad. The model has to say "look at the abdomen." It does.

---

## Scene 8 — Closing (2:50–3:00)

> Repo and live Space at the links below. Built for the AMD Developer Hackathon. Decision support — not diagnosis.

---

## Word count

- Scene 2: 13 words
- Scene 3: 22 words
- Scene 5: 50 words
- Scene 6: 41 words
- Scene 7: 39 words
- Scene 8: 19 words
- **Total: 184 words** → ~73 s at 150 wpm. Target was ~80 s. Comfortable.

## Read-aloud notes

- **"BF16"** — read as "B-F sixteen", not "bee-eff-sixteen"
- **"MI300X"** — read as "M-I three hundred X" (most natural cadence in EN)
- **"ATLS"** — read as four letters "A-T-L-S", not "atlas"
- **"SBAR"** — read as four letters "S-B-A-R"
- **"FAST"** — in scene 7 (case 05), read as the acronym "F-A-S-T" or "fast exam"
- Scene 6 numbers — emphasize: "*seventy-two billion* parameters … *a hundred and forty-five* gigabytes … *single* AMD MI300X". The cadence is: claim · evidence · claim.
- Scene 7 ends on the deliberate beat "It does." — half-second pause before the closing scene's transition.
