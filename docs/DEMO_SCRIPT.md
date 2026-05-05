# Demo video script (3 min target)

Recording approach: don't try to do it in one take. Record the screen-capture segments separately from the voiceover and stitch in DaVinci Resolve / Shotcut. Voiceover should be cleanly read, not improvised. The discipline is **every demo video that runs over 3 minutes loses judges.**

Tools: OBS Studio for screen capture (1080p, 30fps is plenty), DaVinci Resolve free or Shotcut for cuts, a quiet room and a half-decent USB mic. Upload to YouTube unlisted, paste URL into the lablab submission.

The script below is timed. The narrator is the user (an emergency physician); the voice should be calm and matter-of-fact, not promotional.

---

## 0:00 – 0:30 — Problem framing (voiceover over title + slide 2)

> "Trauma kills more people aged one to forty-four than any other cause. The global standard for managing it — Advanced Trauma Life Support, or ATLS — is a structured walk through Airway, Breathing, Circulation, Disability, and Exposure. It works because someone trained walks it. In rural ERs and resource-limited settings, that's often not who's there.
>
> We built **Agentic Trauma Life Support** — a tool that runs the ATLS primary survey on a chest X-ray and dictated vitals, and produces a structured handoff. Built by an emergency physician. Served by Qwen2.5-VL-72B on a single AMD MI300X."

**Shot list:**
- 0:00–0:08 — Title card (slide 1) with project name
- 0:08–0:22 — Slide 2 (the problem). Static slide, voiceover plays
- 0:22–0:30 — Quick fade to the architecture diagram (slide 5). Hold for ~2s before cut.

---

## 0:30 – 1:30 — Live demo (screen capture)

**Case 01 — tension pneumothorax (English)** — 0:30–0:55

Voice: "First case. Thirty-year-old male, motorbike versus car, ejected. Decreased breath sounds on the right, RR 32, SpO2 88, BP 92 over 60."

On screen:
- Upload the case_01_tension_ptx X-ray
- Type or paste the vignette
- Click Generate
- (Cut the wait — show "Generating..." for 1s, then the rendered handoff)
- Pan over the rendered handoff. Highlight: **B critical**, **tension physiology** flagged as a red flag, **immediate priority**, **needle decompression** as the first action with EAST PMG citation.

Voice while panning: "Critical breathing, tension physiology flagged, needle decompression with the EAST citation as the first action, chest tube subsequent. The pipeline ran two model calls — the drafter generated the structured assessment, the verifier re-checked it against the same image."

**Case 05 — the credibility case** — 0:55–1:15

Voice: "Second case. Thirty-four-year-old MVC ejection, abdominal seatbelt sign. RR 22, sat 97, HR 118, BP 102 over 64. The chest X-ray is normal."

On screen:
- Upload the case_05 X-ray (normal CXR)
- Paste the vignette
- Click Generate
- Show the handoff

Voice: "The model correctly identifies that the chest is clear and the issue is likely abdominal. Imaging unremarkable. Recommend CT abdomen-pelvis and FAST. **It declines to invent pathology to match the clinical picture.** That's the hardest thing to get right, and the most important."

**Case 06 — Indonesian** — 1:15–1:30

Voice: "Third case. Pediatric trauma in Bahasa Indonesia."

On screen:
- Switch language to Bahasa Indonesia
- Upload the pediatric X-ray
- Type the Indonesian vignette
- Show the rendered handoff entirely in Indonesian

Voice: "Same pipeline. Same model. Output entirely in Indonesian. The protocol is the same everywhere — the language at the bedside is not."

---

## 1:30 – 2:15 — Architecture and the MI300X argument (voiceover over slides 5 + 6)

> "Under the hood: Drafter, Verifier, Renderer. Two calls to the same model on the same MI300X. The Drafter generates the ATLS JSON via vLLM's guided JSON decoding. The Verifier re-examines the image against the draft and flags inconsistencies. We catch hallucinated findings before they reach the clinician.
>
> Why MI300X? Qwen2.5-VL-72B in full BF16 is roughly 145 gigabytes of weights. The H100 with 80 gigs can't fit it. The H200 with 141 gigs can't fit it. **The MI300X with 192 gigs can — and at sub-$2 per hour, it's the only option that combines 'fits the model' with 'the rural-ER cost story doesn't fall apart.'** The B200 fits, but at three to five times the cost."

**Shot list:**
- 1:30–1:45 — Slide 5 (architecture). Hold the diagram, voiceover plays
- 1:45–2:15 — Slide 6 (memory math table). Highlight the MI300X row with a soft callout

---

## 2:15 – 2:45 — Benchmarks (voiceover over slide 7)

_Until real numbers are in, this section may need to drop to ~15 seconds with a placeholder line. With real numbers, expand to a full 30 seconds._

> "On a single MI300X we measured _[X]_ tokens per second sustained, _[Y]_ millisecond time-to-first-token, _[Z]_ gigabytes peak VRAM under a batch of four concurrent requests. The same workload on NVIDIA hardware needs two H100s with NVLink, at roughly two-and-a-half times the per-hour cost — plus the operational complexity of tensor-parallel serving across two GPUs. For rural ERs and global health applications, that difference is the difference between deployable and not deployable."

**Shot list:**
- 2:15–2:45 — Slide 7 (benchmarks table). If real numbers exist, animate them in one by one.

---

## 2:45 – 3:00 — Closing (voiceover over slide 12)

> "Repo, demo, blog post, and ROCm feedback all linked below. MIT licensed. Built for the AMD Developer Hackathon. **Decision support, not diagnosis.** Thanks."

**Shot list:**
- 2:45–3:00 — Slide 12 (closing). Hold static. Fade to black at 3:00 sharp.

---

## Recording checklist

- [ ] OBS configured for 1080p / 30fps / mp4 / NVENC or AMD VCN encoder
- [ ] Microphone is the USB mic (not laptop built-in). Quiet room.
- [ ] Browser zoom set to 110-125% so the UI is legible at 1080p
- [ ] Hide bookmarks bar, mute notifications, full-screen the browser
- [ ] Close the AMD Developer Cloud tab — no incidental cost figures should appear
- [ ] Record each case demo twice; pick the cleaner take
- [ ] If the model takes >10s to respond on a case, cut the dead time in editing — don't show the loading
- [ ] Voiceover recorded as a single clean read per segment; cut the breaths between segments
- [ ] Final pass: verify total runtime is **≤ 3:00**. Trim relentlessly.
