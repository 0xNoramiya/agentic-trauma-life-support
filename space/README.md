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
  - Qwen/Qwen2.5-VL-72B-Instruct
tags:
  - medical
  - trauma
  - vision-language
  - gradio
  - decision-support
  - amd
  - mi300x
  - rocm
---

# Agentic Trauma Life Support (ATLS) — Live Demo

A multilingual, agentic trauma triage decision-support tool. The double entendre is intentional — ATLS is the global Advanced Trauma Life Support protocol from the American College of Surgeons, and this Space is the agentic AI realization of that protocol's primary survey.

**Decision support, not diagnosis. Not for unsupervised clinical use.**

---

## What this Space runs

This Space is a thin Gradio front-end. The actual model — **Qwen2.5-VL-72B-Instruct in BF16** — runs on a **single AMD MI300X** GPU (192 GB HBM3) over vLLM 0.17.1 ROCm with AITER kernels. **No tensor parallelism. No quantization.** Single-GPU, single-replica. The Space's `app.py` makes OpenAI-compatible chat-completions calls directly to that vLLM endpoint, so what you click is exactly what the production pipeline runs.

The pipeline implemented here:

1. **Drafter** — chest X-ray + dictated vitals → strict `TriageOutput` JSON via OpenAI-canonical `response_format={"type": "json_schema", ...}` enforced server-side by vLLM.
2. **Verifier** (optional toggle) — re-shows the image plus the draft to the same model in clinical-safety-reviewer mode and produces patches/notes that get applied to a deep copy of the draft.
3. **Renderer** — SBAR-style markdown handoff in English or Bahasa Indonesia. Schema enums stay in English so the JSON validates regardless of UI language.

## Why a single MI300X?

That is the entire pitch. 72B BF16 weights are ~144 GB; the MI300X's 192 GB HBM3 fits the model with margin for KV cache. The same model in BF16 will not fit on an H100 (80 GB) or H200 (141 GB) without sharding, quantizing, or pulling weights off-GPU — each of which adds engineering surface and tail latency. For an emergency physician building a triage tool solo, the simplest deployment shape that runs the strongest model wins, and on this generation of hardware that means MI300X.

## Demo cases worth trying

- **case_01 — tension pneumothorax (drama case).** Upload an X-ray showing a pneumothorax; type a vignette describing the mechanism + vitals. The model identifies tracheal deviation + decreased lung volume and recommends needle decompression with citation.
- **case_05 — normal CXR + concerning vitals (credibility case).** Upload a normal chest X-ray; type a vignette like *"34M MVC ejection, abdominal seatbelt sign, RR 22 sat 97 HR 118 BP 102/64."* The model **declines to invent a chest finding** and points the workup at FAST + CT abdomen. This is the safety pattern we built the verifier for.
- **case_06 — pediatric Indonesian.** Switch language to Bahasa Indonesia, upload a pediatric chest X-ray, type the vignette in Indonesian. Output renders in Indonesian; enum values stay English so the schema validates.

Sample vignettes and full case descriptions: see [`docs/DEMO_CASES.md`](https://github.com/0xNoramiya/agentic-trauma-life-support/blob/main/docs/DEMO_CASES.md) on the main repo.

## A note on availability

The MI300X droplet is powered down outside live-demo windows (cost: ~$1.99/hr active, ~$0.05/hr idle). If your click here returns a connection error, the box is asleep — the recorded demo video and the benchmarks (`docs/BENCHMARKS.md`) show full live runs.

## Repo + engineering blog + benchmarks + ROCm feedback

- **GitHub:** <https://github.com/0xNoramiya/agentic-trauma-life-support>
- **Engineering blog:** [`docs/BLOG_POST.md`](https://github.com/0xNoramiya/agentic-trauma-life-support/blob/main/docs/BLOG_POST.md)
- **Benchmarks (real numbers, single MI300X):** [`docs/BENCHMARKS.md`](https://github.com/0xNoramiya/agentic-trauma-life-support/blob/main/docs/BENCHMARKS.md)
- **ROCm bring-up feedback for AMD:** [`docs/ROCM_FEEDBACK.md`](https://github.com/0xNoramiya/agentic-trauma-life-support/blob/main/docs/ROCM_FEEDBACK.md)
- **Demo video:** _link added after recording_

Built by an emergency physician for the AMD Developer Hackathon, May 2026. MIT licensed.
