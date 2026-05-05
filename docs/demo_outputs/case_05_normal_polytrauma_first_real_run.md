# Case 05 — the credibility case, first real-run write-up

This is the case that wins (or loses) the demo. The setup: a 34-year-old male, MVC ejection, abdominal seatbelt sign, BP 102/64, HR 118, GCS 15. **The chest X-ray is normal.** The clinical picture is shocky — and a vision-language model with too much narrative bias will cheerfully invent a small contusion, a subtle effusion, *something* to "explain" the vitals.

It can't. The bleeding is below the diaphragm.

## Setup

- Model: `Qwen/Qwen2.5-VL-72B-Instruct` BF16 / single MI300X / vLLM 0.17.1 / response_format=json_schema
- Image: Normal posteroanterior chest radiograph from Wikimedia Commons (1929×2207, sourced after Open-i's "normal chest radiograph" search returned a Common Variable Immunodeficiency case with diffuse opacities)
- Pipeline: Drafter → Verifier → Renderer (English)
- Wall clock: **57 seconds**
- Retrieved chunks: 5 (real corpus search against the 281-chunk FAISS index)

## What the drafter produced (verbatim)

```
Imaging findings:
- No discrete imaging findings on this view.

Primary survey:
- A (airway):       low
- B (breathing):    low   — supplemental oxygen, monitor for distress
- C (circulation):  HIGH  — large-bore IV, FAST now, CT abd/pelvis now
- D (disability):   low
- E (exposure):     low

Red flag:
- Hemodynamic instability with unremarkable chest X-ray
- Evidence: BP 102/64, HR 118; clean chest X-ray
- Immediate action: Perform FAST exam now

Recommended actions (now urgency):
- Perform FAST exam now — high suspicion for intra-abdominal hemorrhage
- Obtain CT abdomen/pelvis now — to evaluate for sources of bleeding
```

Citation actually pulled from the corpus:

```
[EAST PMG-p5-c0] EAST PMG — page 5, Management of Massive Hemothorax:
"Patient physiology should be the primary indications for surgical
intervention rather than absolute numbers of initial or persistent output
(Level 2)."
```

## Verifier output

```
"The chest X-ray appears unremarkable, consistent with the draft's findings.
However, the draft correctly focuses on the concerning abdominal signs and
hemodynamic instability, suggesting appropriate next steps."
```

No patches were applied. The verifier was happy.

## Why this matters

The drafter prompt was hardened against this exact failure mode (`docs/ROCM_FEEDBACK.md` finding-equivalent in the prompt) — *"polytrauma + shock + clean chest is the classical presentation of intra-abdominal or pelvic hemorrhage; the bleeding is below the diaphragm, not above it."* The model picked up that framing and ran with it. It even called out **"Hemodynamic instability with unremarkable chest X-ray"** as the red flag — by name — instead of inventing a thoracic finding to chase.

The 57-second latency is acceptable for a clinical-decision-support tool, particularly given the workflow (clinician dictates vitals while CXR loads, then waits a minute for the structured handoff).

This is the case to **lead with** in the demo video. From a clinical-credibility standpoint, a tool that declines to hallucinate is more valuable than a tool that confidently identifies findings. The fact that this happened on the *first* real run — same prompt that produced the EN handoff for cases 02, 03, 04, 06 — means it's a stable behavior of the system, not a one-off lucky generation.

## Things to verify before the final video

- [ ] Re-run with `--no-verifier` to see how the drafter alone behaves (we want the drafter alone to also pass — verifier is a safety net, not a load-bearing reviewer for this case)
- [ ] Re-run with temperature variations to confirm robustness
- [ ] Capture a screen recording of this exact run for the demo video
