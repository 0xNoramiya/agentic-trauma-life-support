# Slide deck — Agentic Trauma Life Support

12 slides, ~2.5 min reading time live. Export to PDF for the lablab submission. The numbers slide and the closing slide are the only ones that need real benchmark / final-link content; everything else is shippable now.

The intended visual style is plain — code, schema, rocm-smi screenshots, and one or two real handoffs from the demo. No stock photography, no flat-design illustrations. The credibility comes from showing the actual outputs.

---

## Slide 1 — Title

**Agentic Trauma Life Support**

The agentic AI realization of the ATLS primary survey, served by Qwen2.5-VL-72B in BF16 on a single AMD Instinct MI300X.

Built by an emergency physician for the AMD Developer Hackathon, May 2026.

_Visual: clean text. No subtitle decoration._

---

## Slide 2 — The problem

Trauma is the **leading cause of death age 1–44** worldwide (WHO).

The global standard for managing it — Advanced Trauma Life Support (ATLS) from the American College of Surgeons — is a structured, time-pressured walk through ABCDE:

> Airway → Breathing → Circulation → Disability → Exposure

ATLS works because someone trained walks it. **In rural ERs and LMIC casualty departments, "someone trained" often isn't there.**

_Visual: simple ABCDE column. Stat callout for trauma deaths if available._

---

## Slide 3 — The product

Chest X-ray + dictated vitals **in**.

Structured ATLS primary survey + SBAR handoff **out**, in English or Bahasa Indonesia, with citations to ACS TQIP / EAST / WHO / StatPearls.

Drafter / Verifier / Renderer agentic pipeline for clinical safety.

**Decision support, not diagnosis. Not for unsupervised clinical use.**

_Visual: screenshot of the Gradio UI on the left, rendered SBAR markdown on the right — case 01 (tension pneumothorax) is the cleanest demo._

---

## Slide 4 — Demo screenshot — case 01

A real run: 30M motorbike vs car, ejected. RR 32, SpO2 88%, BP 92/60, HR 124.

Highlights to call out:
- **B (breathing): critical** — left tension pneumothorax flagged
- **Red flag**: tension physiology, with concrete evidence list
- **Disposition: immediate** — needle decompression at left 5th ICS, mid-axillary line, citing EAST PMG
- **Citations** trace back to retrieved guideline excerpts with verbatim quotes
- **`model_metadata.limitations`** is non-empty — single AP view, no lateral

_Visual: large screenshot of the rendered handoff. Annotate with arrows to the four highlights above._

---

## Slide 5 — Architecture

```
chest x-ray + vitals
        │
        ▼
   Retriever (FAISS over ATLS / EAST / WHO / StatPearls excerpts)
        │
        ▼
     Drafter (Qwen2.5-VL-72B, guided JSON → TriageOutput)
        │
        ▼
    Verifier (same model, returns patches + notes on the same image)
        │
        ▼
    Renderer (SBAR markdown, EN or ID)
```

**Both model calls hit the same vLLM server.** No model-router, no second GPU.

_Visual: the diagram above, large. Maybe colorize the Drafter/Verifier boxes._

---

## Slide 6 — Why MI300X (the memory math)

Qwen2.5-VL-72B-Instruct in BF16 = **~145 GB of weights** (137 GB measured on disk after HF download). Add KV cache for `--max-model-len 16384` and `--max-num-seqs 4` and you're at ~170-180 GB.

The 192GB-class single-GPU options:

| GPU              | VRAM   | Fits 72B BF16 | $ / hr cloud |
|------------------|--------|---------------|--------------|
| **MI300X**       | 192 GB | ✅            | **~$1.99**   |
| H200             | 141 GB | ❌            | n/a          |
| H100             | 80 GB  | ❌            | n/a          |
| B200             | 192 GB | ✅            | ~$5–8        |
| MI325X / MI355X  | 256+   | ✅            | harder access|

**For a global health use case, "cost-accessible 192GB-class" is the constraint.**

_Visual: the table above. Highlight MI300X row. The whole slide is the table._

---

## Slide 7 — Benchmarks (single MI300X)

Real numbers from `scripts/run_benchmarks.py`:

- **TTFT (single image, short context)**: _pending real run_
- **Throughput (single-image-long-context)**: _pending real run_
- **Peak VRAM** under `--max-num-seqs 4`: _pending real run_
- **Concurrent batch-of-4 wall latency**: _pending real run_

**Cost-per-deployment comparison:**
- 1× MI300X: 72B BF16 fits, ~$1.99/hr
- 2× H100 + NVLink: same workload, ~$4-5/hr, plus tensor-parallel operational complexity
- 1× H200: cannot serve this model in BF16

_Visual: bar chart of TTFT / throughput once real numbers are in. Until then, this is a numbers-and-table slide._

---

## Slide 8 — The credibility moment (case 05)

Normal chest X-ray. **Concerning vitals.** 34M MVC ejection, abdominal seatbelt sign. RR 22, sat 97 RA, HR 118, BP 102/64.

**The wrong answer:** invent a "small left pleural effusion" or "mild contusion" to "explain" the shock.

**The right answer:** chest is unremarkable. The bleeding is below the diaphragm. **Recommend FAST + CT abdomen/pelvis.**

This is the case the model has to get right. A vision-language triage tool that hallucinates findings to match the clinical picture is **worse than no tool**. A tool that correctly defers to the clinician's judgment is the entire pitch for clinical credibility.

_Visual: side-by-side. Left: the normal CXR. Right: the rendered handoff showing "imaging unremarkable" and the abdominal-imaging recommendation._

---

## Slide 9 — Multilingual (case 06, Indonesian)

Anak 8 tahun, KLL motor vs mobil, terlempar 3 m. RR 35, SpO2 91%, nadi 130, TD 90/60, GCS 14.

Same pipeline. Same model. **Output entirely in Bahasa Indonesia**, with pediatric-appropriate vital interpretation.

This is the global-health angle: the protocol is the same everywhere; the language at the bedside is not.

_Visual: screenshot of the Indonesian rendered handoff. Highlight that enum values stay in English (concern_level: critical) so the schema validates, while every narrative field (mechanism, finding, action, rationale) is in Indonesian._

---

## Slide 10 — What we built

- **Public repo:** <https://github.com/0xNoramiya/agentic-trauma-life-support> — MIT licensed
- **Live demo (7B):** _pending HF Space deploy_
- **Engineering blog:** [`docs/BLOG_POST.md`](BLOG_POST.md) — 2400 words on bring-up + the cost-accessibility argument
- **ROCm feedback:** [`docs/ROCM_FEEDBACK.md`](ROCM_FEEDBACK.md) — 5 numbered findings from Day 1 bring-up
- **235B-AWQ spike writeup:** [`docs/SPIKE_235B_AWQ.md`](SPIKE_235B_AWQ.md) — skipped, with rationale
- **23 tests passing.** Mock-mode UI verified end-to-end before any GPU was provisioned.

_Visual: the bullet list with hyperlinks._

---

## Slide 11 — What's next

- Secondary survey expansion (head, abdomen, pelvis, extremities)
- Multimodal beyond CXR: FAST scan, CT chest/abdomen
- On-device deployment with Radeon AI PRO for offline rural use
- Honest IRB pathway for clinical evaluation. _This is the gating step for any real-world use._
- A "second-language pack" — the Indonesian path generalizes to any low-resource language with a competent open VLM.

_Visual: a bulleted roadmap. Lean. The IRB line should probably be visually emphasized — that's the responsible-AI signal._

---

## Slide 12 — Closing

**Built by a practicing emergency physician.**

**Decision support, not diagnosis.**

**MIT licensed.**

For the AMD Developer Hackathon, May 2026.

Thanks to AMD AI Developer Cloud, the Qwen team, the vLLM project, the ROCm fork maintainers, ACS TQIP / EAST / WHO / StatPearls, and Radiopaedia.

_Visual: clean. Same minimal style as slide 1._
