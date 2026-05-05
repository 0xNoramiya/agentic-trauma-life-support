# CLAUDE.md — ATLS hackathon project

This file is for Claude (and any other agent) working in this repo. Read it before touching code.

## Mission

Build a multilingual, agentic trauma triage decision-support tool for the AMD Developer Hackathon. The project is named **Agentic Trauma Life Support (ATLS)** — a deliberate double entendre with the global Advanced Trauma Life Support protocol from the American College of Surgeons. The product is the agentic AI realization of the ATLS primary survey.

Input: chest X-ray + dictated vitals/clinical context.
Output: structured ATLS primary survey (ABCDE) JSON, rendered as an SBAR-style handoff in the user's chosen language (English default, Indonesian for multilingual demo).

## Locked tech stack

- Python **3.12** (pinned via `requires-python = ">=3.12,<3.13"`).
- `uv` for env management.
- Pydantic v2 for schema (`src/ats/schema.py`).
- vLLM for serving on the MI300X droplet (separate machine). Local code is OpenAI-compatible client only — **do not install vLLM locally**.
- vLLM guided JSON decoding via `extra_body={"guided_json": schema}`.
- FAISS (CPU) + sentence-transformers (`BAAI/bge-m3`) for retrieval.
- PyMuPDF for PDF ingestion, tiktoken (`cl100k_base`) for chunk sizing.
- Gradio for the UI.
- pytest for tests, ruff for lint/format.
- License: MIT.

## Package name

The Python package is `ats` (lowercase, three letters). **Do not use the abbreviation `ATLS` in code identifiers.** It only appears in docs, prose, and UI strings.

## Single-MI300X constraint

The model runs on **one MI300X**. 192 GB HBM3 is enough for Qwen2.5-VL-72B in BF16 with margin. **Never reference `--tensor-parallel-size > 1` anywhere in the repo.** This constraint is load-bearing for the pitch (single-GPU 72B BF16 is the entire AMD-cost-accessibility argument).

## Schema location

`src/ats/schema.py` defines `TriageOutput` and friends. It's the contract the model writes to via vLLM guided JSON. When in doubt, read the schema first — everything in the pipeline is shaped around it.

## Mock mode

`Settings.mock_mode` defaults to `True`. In mock mode `InferenceClient.generate(...)` returns the `tests/fixtures/sample_case.json` fixture for `TriageOutput` requests and an empty `{verifier_notes: [], patches: []}` for verifier requests. This means the UI, tests, and demo script all run end-to-end without the MI300X. Set `MOCK_MODE=false` in `.env` once the droplet is up.

## Drafter / Verifier / Renderer

- **Drafter** (`src/ats/pipeline/drafter.py`): builds the system prompt for the chosen language, embeds the X-ray, vitals, and retrieved guideline chunks. Calls the model with guided JSON to produce a `TriageOutput`. Retries once on validation failure.
- **Verifier** (`src/ats/pipeline/verifier.py`): re-shows the image and the draft JSON to the same model in clinical-safety-reviewer mode. Returns `{verifier_notes, patches}`. Patches are applied to a deep copy of the draft via a small in-file path-walker.
- **Renderer** (`src/ats/render/handoff_en.py`, `handoff_id.py`): converts the `TriageOutput` to an SBAR-style markdown handoff. The Indonesian renderer keeps enum values in English (so the schema remains valid) and translates the section headers and labels.

Both model calls hit the same vLLM server.

## Corpus sources

The retrieval corpus is sourced from these documents (user must download them — none are committed because of size and licensing concerns; `.gitignore` excludes `*.pdf`):

- ACS TQIP (Trauma Quality Improvement Program) Best Practices guidelines.
- EAST PMG (Eastern Association for the Surgery of Trauma — Practice Management Guidelines).
- WHO Integrated Management for Emergency & Essential Surgical Care.
- StatPearls trauma chapters (NCBI Bookshelf).

See `src/ats/corpus/data/README.md` and the `manifest.json` format documented there.

## Demo cases

Six cases in `docs/DEMO_CASES.md`:

1. case_01_tension_ptx — tension pneumothorax (EN)
2. case_02_massive_htx — massive hemothorax + shock (EN)
3. case_03_flail_chest — flail chest (EN)
4. case_04_pulm_contusion — pulmonary contusion (EN)
5. case_05_normal_polytrauma — normal CXR but concerning vitals (EN). **THE CREDIBILITY CASE.** The model must NOT invent pathology. Chest must be explicitly described as unremarkable and the recommendation must escalate to abdominal imaging + FAST.
6. case_06_pediatric_id — pediatric trauma in Indonesian.

## Deadline & deliverables

- Deadline: **2026-05-11 03:00 WITA**.
- AMD-deliverable priorities, in order:
  1. Working end-to-end demo.
  2. Engineering blog post (`docs/BLOG_POST.md`).
  3. ROCm feedback document (`docs/ROCM_FEEDBACK.md`).
  4. Slide deck (created near deadline).
  5. Demo video.

## Do-not-do list

- Do not install vLLM locally. The local environment is the OpenAI client only.
- Do not download model weights or commit PDFs / chest X-rays.
- Do not reference `--tensor-parallel-size > 1` anywhere.
- Do not use the abbreviation `ATLS` in Python identifiers; the package is `ats`.
- Do not commit case images to `assets/` (gitignored).
- Do not turn off mock mode by default — local development runs in mock mode.
