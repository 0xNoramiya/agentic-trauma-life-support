---
title: ATLS — AMD Hackathon Submission
emoji: 🏥
colorFrom: indigo
colorTo: blue
sdk: gradio
sdk_version: 6.14.0
python_version: "3.12"
app_file: app.py
pinned: false
license: mit
short_description: AMD Developer Hackathon — 72B VL on a single MI300X
hf_oauth: false
models:
  - Qwen/Qwen2.5-VL-72B-Instruct
tags:
  - gradio
  - vision-language
  - amd
  - mi300x
  - rocm
---

# ATLS — AMD Developer Hackathon Submission

A submission for the **AMD Developer Hackathon, May 2026**. The demo runs **Qwen2.5-VL-72B in BF16 on a single AMD MI300X** (192 GB HBM3) via vLLM 0.17.1 ROCm — no model parallelism, no quantization, no tensor sharding. The Space is a thin Gradio front-end that calls the production vLLM endpoint directly, so what you click is exactly what the production pipeline runs.

## What this Space demonstrates

A clinical-decision-support research prototype. Given a chest X-ray and a brief vitals/clinical vignette, it produces a structured primary-survey JSON (Pydantic-validated) plus an SBAR-style markdown handoff. Multilingual (English / Bahasa Indonesia). Drafter → Verifier → Renderer pipeline using OpenAI-canonical structured output (`response_format={"type": "json_schema", ...}`) enforced server-side by vLLM.

Engineering writeup, benchmarks, prompts, schema, and corpus details: see the **GitHub repo** at <https://github.com/0xNoramiya/agentic-trauma-life-support>.

## Why a single MI300X

72B BF16 weights are ~144 GB. The MI300X's 192 GB HBM3 fits the model with margin for KV cache. The same model in BF16 does not fit on an H100 (80 GB) or H200 (141 GB) without sharding, quantizing, or pulling weights off-GPU — each adds engineering surface and tail latency. For a single-developer submission, the simplest deployment shape that runs the strongest model wins, and on this generation of hardware that means MI300X.

## A note on availability

The MI300X is powered down outside live-demo windows to keep costs low. If your click returns a backend-unreachable error, the box is asleep — the recorded demo video and the live benchmarks (`docs/BENCHMARKS.md` in the repo) show full runs.

---

**Decision support only — not diagnosis. Not for unsupervised clinical use.** Built by a physician for the AMD Developer Hackathon, May 2026. MIT licensed.
