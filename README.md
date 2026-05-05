# Agentic Trauma Life Support (ATLS)

A multilingual, agentic trauma triage decision-support tool. Input: chest X-ray plus dictated vitals. Output: a structured ATLS primary survey (ABCDE) and an SBAR-style handoff in English or Bahasa Indonesia.

## What it is

ATLS is a small, focused web app that performs the **Advanced Trauma Life Support primary survey** on a chest X-ray and a brief clinical vignette. It runs a Drafter -> Verifier -> Renderer pipeline against Qwen2.5-VL-72B-Instruct in full BF16 on a single AMD MI300X.

## The double meaning

ATLS is the global trauma protocol from the American College of Surgeons (Advanced Trauma Life Support). This project — Agentic Trauma Life Support — is the agentic AI realization of that protocol's primary survey. The acronym is intentional.

## Demo

- Live demo: _placeholder, populate after deploy_
- Demo video: _placeholder, populate after recording_
- Sample outputs: see [`docs/demo_outputs/`](docs/demo_outputs)

## Architecture

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). Short version:

```
chest x-ray + vitals
        |
        v
   Retriever (FAISS over ATLS/EAST/WHO/StatPearls excerpts)
        |
        v
     Drafter (Qwen2.5-VL-72B, guided JSON -> TriageOutput)
        |
        v
    Verifier (same model, returns patches + notes)
        |
        v
    Renderer (SBAR markdown, EN or ID)
```

Both model calls hit the same vLLM server.

## Why MI300X

Qwen2.5-VL-72B-Instruct in BF16 is roughly 144 GB of weights. It does not fit in 80 GB H100 or 141 GB H200. It does fit in **a single MI300X (192 GB HBM3)**, which is the most cost-accessible GPU in that class (sub-$2/hr on most clouds vs. several dollars per hour for B200). No quantization, no CPU offload, no tensor parallelism. One GPU, one container, full precision.

That accessibility is what makes this deployable in resource-limited settings — and that's the point of the use case.

## Quickstart

```bash
# 1. Install
uv sync

# 2. Configure
cp .env.example .env
# (defaults work for mock mode; edit VLLM_BASE_URL when pointing at the droplet)

# 3. Build the corpus index (optional; the app runs without it)
#    Source the PDFs first per src/ats/corpus/data/README.md, then:
python scripts/build_index.py

# 4. Launch the UI
python -m ats.ui.app
```

The UI runs at `http://127.0.0.1:7860`.

## Serving on MI300X

The vLLM server runs separately on the MI300X droplet. See [`scripts/serve_vllm.sh`](scripts/serve_vllm.sh) for the canonical Docker invocation. Three modes are wired up:

- `./scripts/serve_vllm.sh dev` — Qwen2.5-VL-7B-Instruct for fast iteration.
- `./scripts/serve_vllm.sh prod` — Qwen2.5-VL-72B-Instruct in BF16 (single MI300X).
- `./scripts/serve_vllm.sh spike` — placeholder for the Day 1 235B-AWQ spike.

## Status

This is a hackathon project and **decision support only**. It is not a diagnostic device. It is not cleared by any regulator. It is not for clinical use. Every output ships with a disclaimer to that effect.

## License

MIT. See [`LICENSE`](LICENSE).

## Acknowledgments

- AMD Developer Hackathon for the MI300X access and the prompt to prove ROCm out.
- The Qwen team for Qwen2.5-VL.
- The vLLM project and the ROCm fork maintainers.
- The American College of Surgeons (ATLS / TQIP), EAST (Practice Management Guidelines), the WHO (Integrated Management for Emergency and Essential Surgical Care), and StatPearls — the open clinical corpus that this project retrieves over.
- Radiopaedia for openly-licensed teaching cases used in the demo set.
