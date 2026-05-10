# Demo video — plan & storyboard

3-minute video for the lablab.ai submission. Built with the [`hyperframes`](https://github.com/anthropics/skills) skill — HTML+GSAP compositions rendered to MP4. The recorded live-demo clip slots into the centered scene; everything else is HyperFrames-rendered.

> **Read this before approving the script.** Once you sign off on the narration, I'll write the HyperFrames HTML, generate the EN audio via ElevenLabs TTS, dub it to ID, and render two MP4 outputs.

## Narrative arc

The video answers four questions in order, with the live demo as the proof at the center:

1. **Why does this exist?** (8 s) — Trauma is the leading cause of death age 1–44; most deaths happen where there's no trauma surgeon on call.
2. **What is it?** (10 s + 12 s) — Title + product action loop.
3. **Does it actually work?** (80 s) — Your live-demo recording, centered.
4. **How does it work?** (25 s + 20 s) — Drafter → Verifier → Renderer + the single-MI300X 72B BF16 hardware story.
5. **Why should you trust it?** (15 s) — The credibility moment (case_05).
6. **Where is it?** (10 s) — Repo + Space links.

Total: **180 s**. Narration ~200 words at 150 wpm = ~80 s of speech, leaving ~100 s for breathing room and the live demo.

## Scene-by-scene

| # | Time | Duration | Scene | On-screen | Narration (EN) |
|---|---|---|---|---|---|
| 1 | 0:00 | 8 s | **Cold open** | Off-white canvas. Single line of serif text fades in: "Most trauma deaths happen where there isn't a trauma surgeon on call." | _none — let the text breathe. Audio: subtle ambient pad._ |
| 2 | 0:08 | 10 s | **Title** | Wordmark "Agentic Trauma Life Support" centered. Subtitle below: "the agentic AI realization of the ATLS primary survey." | "This is Agentic Trauma Life Support — the agentic AI realization of the same protocol." |
| 3 | 0:18 | 12 s | **What it does** | Four icons appearing in sequence with caption below each: chest X-ray, vitals (typed text), language toggle EN/ID, structured handoff document. Sage-green accent on the language toggle. | "A clinician uploads a chest X-ray. Types the vitals. Picks a language. And in seconds, gets a structured ATLS primary survey." |
| 4 | 0:30 | 80 s | **Live demo** ⚪ centered slot | Your recorded screen capture, centered in a soft-edged rounded frame (~1600×900 inside the 1920×1080 canvas). Caption pinned below the frame: *Qwen2.5-VL-72B in BF16 · single AMD MI300X · vLLM 0.17.1 ROCm*. | _user's voiceover in the recording (or muted if you want only TTS to play over it)_ |
| 5 | 1:50 | 25 s | **How it works** | Three labeled boxes in a row, connected by arrows: **Drafter** → **Verifier** → **Renderer**. Boxes fade in one at a time as narrated. Underneath each, one-line caption (drafter: "writes the JSON" / verifier: "re-checks the image" / renderer: "SBAR handoff"). | "The pipeline is three agents on the same model. The Drafter reads the X-ray and writes a structured primary survey as JSON. The Verifier re-examines the same image and patches anything inconsistent. The Renderer turns it into an SBAR-style handoff." |
| 6 | 2:15 | 20 s | **Hardware story** | Three vertical bars (memory math): H100 80 GB / H200 141 GB / **MI300X 192 GB** — first two greyed out, third highlighted in the accent color with a checkmark. Cost overlay: "$1.99/hr". | "Seventy-two billion parameters in BF16 is a hundred and forty-five gigabytes. The model fits in full precision on a single AMD MI300X — the only sub-two-dollar-per-hour GPU that can hold it without sharding or quantizing." |
| 7 | 2:35 | 15 s | **Credibility moment** | Pull-quote-styled clinical prose, large serif: *"Imaging unremarkable. Recommend FAST and CT abdomen."* Below in small caps: *case_05 — normal CXR, hypotension. Model declined to invent.* | "The verifier exists for one reason: don't invent findings. We have a test case where the chest X-ray is normal but the vitals are bad. The model has to say 'look at the abdomen.' It does." |
| 8 | 2:50 | 10 s | **Closing** | Wordmark again. Three lines: GitHub URL · HF Space URL · "MIT · Built by an emergency physician for the AMD Developer Hackathon, May 2026". | "Repo and live Space at the links below. Built for the AMD Developer Hackathon. Decision support, not diagnosis." |

## Visual identity (in `video/DESIGN.md`)

**Aesthetic:** clinical editorial. Off-white canvas, deep ink, single muted-sage accent. Serif headlines, geometric sans body. Generous negative space. No gradients on dark backgrounds. No flat-design illustrations. No bouncy easing.

Inspired by *Velvet Standard* (architectural symmetry, single accent, ALL-CAPS subheads) but in a light/clinical palette rather than luxury black/gold.

| | |
|---|---|
| Canvas | `#F8F7F4` (warm paper) |
| Primary text | `#1A1F2E` (deep ink) |
| Secondary text | `#5A6273` (slate) |
| Accent | `#3A7A6E` (medical sage) |
| Critical highlight (red flags only, used once) | `#B8463A` (terracotta) |
| Display headline | Source Serif 4 (or Tinos / EB Garamond) |
| Body / labels | Inter |
| Numerals (bench numbers, "192 GB") | `font-variant-numeric: tabular-nums` |

## File structure

```
video/
├── DESIGN.md                    visual identity (canvas, palette, type, anti-patterns)
├── SCRIPT_EN.md                 narration script EN (one block per scene)
├── SCRIPT_ID.md                 narration script ID (you fill — bilingual review)
├── elevenlabs.md                dubbing pipeline + .env keys
├── compositions/
│   ├── scene-01-cold-open.html
│   ├── scene-02-title.html
│   ├── scene-03-what.html
│   ├── scene-05-pipeline.html
│   ├── scene-06-hardware.html
│   ├── scene-07-credibility.html
│   └── scene-08-closing.html
├── audio/
│   ├── narration_en.mp3         generated by ElevenLabs TTS from SCRIPT_EN.md
│   └── narration_id.mp3         generated after you confirm the ID translation
├── live_demo.mp4                your recorded screen capture (drop in)
└── index.html                   root composition that orchestrates the 8 scenes
```

## ElevenLabs dub flow (full detail in `video/elevenlabs.md`)

Two languages, one voice, two MP3s, two final video renders:

```
SCRIPT_EN.md ──TTS──> narration_en.mp3 ──┐
                                          ├──> render demo_en.mp4
              live_demo.mp4 ──────────────┤
                                          │
SCRIPT_ID.md ──TTS──> narration_id.mp3 ──┐
                                          ├──> render demo_id.mp4
   live_demo_dubbed.mp4 ─Dubbing API─────┤
       (only if you want to dub the      │
       recorded screen capture audio too)
```

**Decision:** for the recorded screen capture in scene 4 (your voice over your own demo), do you want it (a) preserved as-is in both EN and ID renders, (b) muted and overlaid with TTS narration in both languages, or (c) preserved in EN, dubbed by ElevenLabs Dubbing API in ID?

I'd default to (a) for EN and (c) for ID — keeps the EN version authentically yours, and the ID version stays consistent (your dubbed voice over your own screen).

## Open questions (need answers before HTML)

1. **Voice**: which ElevenLabs voice ID? Defaults I'd suggest:
   - For EN narration: `Brian` (calm, professional, English) or `Daniel` (clinical, lower)
   - For multilingual: a voice with `eleven_multilingual_v2` capability (e.g., `Adam`, `Charlotte`, `Liam`) — same voice speaks both EN and ID. Recommended: pick one multilingual voice for both renders.
2. **Scene 4 audio handling** — see decision (a/b/c) above.
3. **Aspect ratio** — 1920×1080 (horizontal, lablab default) or 1080×1920 (vertical, social)? I'd default to **1920×1080**.
4. **Live demo recording status** — is `video/live_demo.mp4` ready to drop in, or still being edited? If durations differ from 80 s, I'll re-time scene 4.
5. **Indonesian translation** — you'll write `SCRIPT_ID.md` based on the EN script (I can't safely translate clinical Indonesian — wrong word can break credibility), or do you want me to draft and have you correct it?

## What happens after you approve

1. I write `video/DESIGN.md` + the 7 HyperFrames composition HTML files (scenes 1, 2, 3, 5, 6, 7, 8).
2. You drop `live_demo.mp4` into `video/`.
3. You provide ElevenLabs API key → I generate `narration_en.mp3` from `SCRIPT_EN.md`.
4. We slot audio into the timeline, render `demo_en.mp4`.
5. You write/correct `SCRIPT_ID.md` → I generate `narration_id.mp3`, render `demo_id.mp4`.
6. (Optional) Dub the recorded screen capture for the ID version.
7. Both MP4s ready to upload to YouTube unlisted; paste URLs into `docs/SUBMISSION.md`.

Estimated time end-to-end after sign-off: ~2 hours of my work + your live demo recording + ID translation review. Well within the deadline.
