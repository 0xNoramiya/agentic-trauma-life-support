# First end-to-end pipeline run — case_02 (massive hemothorax)

Captured 2026-05-05 ~10:55 WITA, after Day 2 72B bring-up. This was the **first real end-to-end call** through the full Drafter → Verifier → Renderer pipeline against Qwen2.5-VL-72B-Instruct in BF16 on a single MI300X via Tailscale, with real RAG retrieval against the 281-chunk FAISS corpus.

## Setup

- Model: `Qwen/Qwen2.5-VL-72B-Instruct` on MI300X via vLLM 0.17.1 ROCm
- Pipeline: drafter (with `response_format={"type": "json_schema", ...}` guided decoding) → verifier (same constraint) → English SBAR renderer
- Image: `assets/case_02_massive_htx.jpg` (sourced from NIH Open-i — hemothorax search)
- Vignette: 45M fall from 5m onto rebar, RR 28 sat 92 HR 132 BP 78/42 GCS 14
- Total elapsed: **51.4s** (drafter + verifier, both calls vision-multimodal)
- Retrieved chunks: 5 (cosine over EAST PMG / ACS TQIP / WHO chunks)

## What the verifier caught

The Open-i hit for "hemothorax chest radiograph" turned out to be an intraoperative laparoscopic view from a *postoperative* hemothorax case (PMC4406011 — Gelpi retractor injury during scoliosis surgery), **not** a trauma chest X-ray. The drafter generated a plausible-looking ABCDE assessment anyway, including a "high" B_breathing concern with "insert large-bore chest tube on the left side now" as an action.

**The verifier flagged this correctly:**

> The image provided is not a chest X-ray but appears to be an intraoperative laparoscopic view. Imaging findings related to hemothorax cannot be confirmed from this image.
>
> The red flag for tension pneumothorax lacks concrete imaging evidence from the provided image.
>
> The limitations section should include the fact that the provided image is not a chest X-ray.

This is the **case-05 hallucination pattern** firing in real time: the model wanted to invent thoracic findings to match the shock vitals, and the verifier caught the structural issue (image-content mismatch) before it reached a clinician.

## Why this matters for the demo

It's a happy accident that the X-ray sourcing produced a wrong-modality image, because we got to demonstrate the verifier safety pattern *for real* on the very first end-to-end call — not just on a hand-crafted bad-case fixture. Document this as a live example in the engineering blog and the demo video voiceover.

## Action items

1. Re-source case_02 (and probably case_03, 04) from a stricter source — Open-i title text doesn't reliably indicate "this is a chest X-ray." Either filter by image-type more aggressively, or curate manually.
2. Keep this run as a verifier-demo artifact — see `case_02_massive_htx_first_run.json` (raw output) for the demo-video material.
