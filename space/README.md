---
title: Agentic Trauma Life Support
emoji: 🩺
colorFrom: indigo
colorTo: red
sdk: gradio
sdk_version: 4.44.1
app_file: app.py
pinned: false
license: mit
short_description: Agentic ATLS primary survey on chest X-ray + dictated vitals
hf_oauth: false
models:
  - Qwen/Qwen2.5-VL-7B-Instruct
tags:
  - medical
  - trauma
  - vision-language
  - gradio
  - decision-support
---

# Agentic Trauma Life Support (ATLS) — Live Demo

A multilingual, agentic trauma triage decision-support tool. The double entendre is intentional — ATLS is the global Advanced Trauma Life Support protocol from the American College of Surgeons, and this Space is the agentic AI realization of that protocol's primary survey.

**Decision support, not diagnosis. Not for unsupervised clinical use.**

---

## What this Space runs

This Space serves the lighter **Qwen2.5-VL-7B-Instruct** path so the demo is clickable from any browser. The full hackathon pitch — **Qwen2.5-VL-72B in BF16 on a single AMD MI300X** — is what produced the recorded demo video and the benchmarks in the engineering blog. See the repo for the production serving setup (`scripts/serve_vllm.sh prod`).

The pipeline implemented here:

1. **Drafter** — chest X-ray + dictated vitals + retrieved guideline excerpts → strict `TriageOutput` JSON via the same Pydantic schema and prompts as the production setup.
2. **Verifier** (optional toggle in this Space) — re-shows the image plus the draft and produces clinical-safety patches/notes.
3. **Renderer** — SBAR-style markdown handoff in English or Bahasa Indonesia.

Backed by `huggingface_hub.InferenceClient`. Free-tier rate limits apply.

## Demo cases worth trying

- **case_01 — tension pneumothorax (drama case).** Upload an X-ray showing a pneumothorax; type a vignette describing the mechanism + vitals. The model identifies tracheal deviation + decreased lung volume and recommends needle decompression with citation.
- **case_05 — normal CXR + concerning vitals (credibility case).** Upload a normal chest X-ray; type a vignette like *"34M MVC ejection, abdominal seatbelt sign, RR 22 sat 97 HR 118 BP 102/64."* The model **declines to invent a chest finding** and points the workup at FAST + CT abdomen. This is the safety pattern we built the verifier for.
- **case_06 — pediatric Indonesian.** Switch language to Bahasa Indonesia, upload a pediatric chest X-ray, type the vignette in Indonesian. Output renders in Indonesian; enum values stay English so the schema validates.

Sample vignettes and full case descriptions: see [`docs/DEMO_CASES.md`](https://github.com/0xNoramiya/agentic-trauma-life-support/blob/main/docs/DEMO_CASES.md) on the main repo.

## Why this Space is on Qwen2.5-VL-7B and not 72B

The 192GB-class MI300X needed to hold Qwen2.5-VL-72B in BF16 isn't available on free HF Space tiers. The 7B variant is the largest one that fits the free path. For the *real* numbers (TTFT, throughput, peak VRAM) on the 72B production serve, see `docs/BENCHMARKS.md` in the main repo.

## Repo + engineering blog + demo video

- **GitHub:** <https://github.com/0xNoramiya/agentic-trauma-life-support>
- **Engineering blog:** [`docs/BLOG_POST.md`](https://github.com/0xNoramiya/agentic-trauma-life-support/blob/main/docs/BLOG_POST.md)
- **Benchmarks:** [`docs/BENCHMARKS.md`](https://github.com/0xNoramiya/agentic-trauma-life-support/blob/main/docs/BENCHMARKS.md)
- **ROCm feedback:** [`docs/ROCM_FEEDBACK.md`](https://github.com/0xNoramiya/agentic-trauma-life-support/blob/main/docs/ROCM_FEEDBACK.md)
- **Demo video:** _link added after recording_

Built by an emergency physician for the AMD Developer Hackathon, May 2026. MIT licensed.
