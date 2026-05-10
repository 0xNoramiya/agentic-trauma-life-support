# Agentic Trauma Life Support (ATLS)

A multilingual, agentic trauma triage decision-support tool. Input: chest X-ray + dictated vitals. Output: a structured ATLS primary survey (ABCDE) as JSON, plus an SBAR-style markdown handoff in **English or Bahasa Indonesia**.

Built for the **AMD Developer Hackathon, May 2026** by a practicing emergency physician. The model — Qwen2.5-VL-72B-Instruct in **full BF16, no quantization, no tensor parallelism** — runs on a single AMD Instinct MI300X (192 GB HBM3) via vLLM 0.17.1 ROCm.

> **Decision support — not diagnosis.** Not a regulated device. Not for unsupervised clinical use.

---

## Quick links

- **Live demo:** <https://huggingface.co/spaces/lablab-ai-amd-developer-hackathon/atls> *(MI300X powered down outside demo windows; see [`docs/BENCHMARKS.md`](docs/BENCHMARKS.md) and the recorded video for full live runs)*
- **Engineering blog post:** [`docs/BLOG_POST.md`](docs/BLOG_POST.md) — 2,400 words on the bring-up
- **Real benchmarks (single MI300X):** [`docs/BENCHMARKS.md`](docs/BENCHMARKS.md) — TTFT, throughput, peak VRAM, cold-start
- **ROCm feedback for AMD:** [`docs/ROCM_FEEDBACK.md`](docs/ROCM_FEEDBACK.md) — 7 numbered bring-up findings
- **Demo case index:** [`docs/DEMO_CASES.md`](docs/DEMO_CASES.md) — six clinical vignettes paired with chest films
- **Demo outputs:** [`docs/demo_outputs/SUMMARY.md`](docs/demo_outputs/SUMMARY.md) — one-page aggregate of all six cases

## The double meaning

ATLS is the global trauma protocol from the American College of Surgeons (Advanced Trauma Life Support). This project — **Agentic** Trauma Life Support — is the agentic AI realization of that protocol's primary survey. The acronym is intentional.

---

## Why this exists

Trauma is the leading cause of death between ages 1 and 44 worldwide. The ATLS primary survey — a structured walk through Airway → Breathing → Circulation → Disability → Exposure — works because someone trained walks it. In rural ERs and resource-limited settings, that "someone trained" is often a junior clinician, a nurse on a phone link, or a referral chain that takes hours.

This is a structured, citation-backed triage assistant that runs the protocol on a chest X-ray + a brief vignette and produces a Pydantic-validated primary-survey JSON plus an SBAR handoff — in the local language, in seconds.

## Architecture

```
chest X-ray + dictated vitals + retrieved excerpts
                     │
                     ▼
        ┌─────────────────────────┐
        │  Drafter                │   Qwen2.5-VL-72B BF16
        │  vision + text +        │   structured output via
        │  guideline excerpts     │   response_format=json_schema
        │  → TriageOutput JSON    │
        └─────────────────────────┘
                     │
                     ▼   re-shows the X-ray + the draft to the same model
        ┌─────────────────────────┐
        │  Verifier               │   "clinical-safety reviewer" prompt
        │  → patches + notes      │   patches applied to a deep copy
        └─────────────────────────┘
                     │
                     ▼
        ┌─────────────────────────┐
        │  Renderer               │   handoff_en.py · handoff_id.py
        │  → SBAR markdown        │   schema enums stay English
        │   (EN or ID)            │   so JSON validates either way
        └─────────────────────────┘
```

Both model calls hit the same vLLM server. Retrieval (FAISS over a curated guideline corpus) happens locally before the Drafter call. Section 6 of the engineering writeup ([`docs/BLOG_POST.md`](docs/BLOG_POST.md)) walks the pipeline in detail.

## Why a single MI300X

Qwen2.5-VL-72B-Instruct in BF16 is ~145 GB of weights. To serve it on a **single GPU** in full precision (no sharding, no quantizing, no CPU offload) you need **192 GB of HBM**. The shortlist:

| Hardware | VRAM | Fits 72B BF16? | $ / GPU-hr (cloud) |
|---|---:|---|---:|
| 1 × **AMD MI300X** | 192 GB HBM3 | ✓ (~78% util at idle, peak 96% under load) | **~$1.99** |
| 1 × NVIDIA H200 | 141 GB | ✗ | n/a |
| 1 × NVIDIA H100 | 80 GB | ✗ | n/a |
| 2 × NVIDIA H100 (NVLink, TP=2) | 160 GB | ✓ but TP-sharded | ~$4–5 |
| 1 × NVIDIA B200 | 192 GB HBM3e | ✓ | ~$5–8 |

For the global-health, resource-limited-deployment use case, **the MI300X is the only sub-$2/hr option that fits 72B in BF16 on a single GPU**. Two H100s with NVLink work but cost 2–3× more per deployment and add tensor-parallel operational complexity (NCCL versioning, partial-failure handling, longer cold starts). The single-GPU shape is *the entire pitch* — the engineering blog post argues this in depth.

## Real benchmarks (single MI300X)

From `scripts/run_benchmarks.py`, n=5 per scenario, real chest X-ray (`assets/case_01_tension_ptx.jpg`), streaming chat-completion against the live vLLM server:

| Scenario | TTFT (median) | Throughput | Total wall (median) |
|---|---:|---:|---:|
| Single image + ~150-token prompt | **1981 ms** | 19.9 tok/s | 15.4 s |
| Single image + ~3 k-token retrieved-context prompt | 1982 ms | 21.5 tok/s | 15.9 s |
| Concurrent batch of 4 | 2199 ms | 18.4 tok/s | 15.1 s |

**Peak VRAM under concurrent batch of 4: 183.95 GiB / 191.69 GiB (96%)** — sits exactly at the `--gpu-memory-utilization 0.95` budget.

**Cold start:** ~22 minutes on first run after a fresh container — ~94 s of weight load (137 GiB into VRAM) plus ~20 minutes of AITER kernel JIT compile. The AITER cost is captured as ROCm finding #2 (silent multi-minute window with no progress messages) and finding #7 (the JIT cache lives inside the container's writable layer, so `docker run --rm` discards 414 MB of compiled kernels on every restart).

Full numbers, per-case end-to-end timings, and operational evidence (vLLM log, rocm-smi snapshots, AITER cache listing) in [`docs/BENCHMARKS.md`](docs/BENCHMARKS.md) and [`docs/logs/`](docs/logs).

## The six demo cases

Six clinical vignettes paired with real chest films. Five English, one Indonesian. Two cases (case_02 laterality, case_03 over-call) demonstrate the verifier catching a drafter error. **Case 05 is the credibility test:** a normal chest X-ray paired with hypotension — the model must NOT invent a chest finding to "justify" the vitals; it must escalate to FAST + CT abdomen. It does.

| Case | Pathology | Lang | What it tests |
|---|---|---|---|
| `case_01_tension_ptx` | Tension pneumothorax | EN | Drama case — drafter calls the right action |
| `case_02_massive_htx` | Massive hemothorax + shock | EN | Verifier catches drafter laterality error |
| `case_03_flail_chest` | Flail chest | EN | Verifier downgrades drafter over-call |
| `case_04_pulm_contusion` | Bilateral pulmonary contusion | EN | Multi-panel image, ICU disposition |
| `case_05_normal_polytrauma` | **Normal CXR**, abdominal injury | EN | **Credibility test — don't invent** |
| `case_06_pediatric_id` | Pediatric blunt thoracic trauma | ID | Multilingual rendering, verifier on shock attribution |

Per-case vignettes + image source URLs in [`docs/DEMO_CASES.md`](docs/DEMO_CASES.md). Aggregated outputs in [`docs/demo_outputs/SUMMARY.md`](docs/demo_outputs/SUMMARY.md). Two narrative write-ups of first real-runs in [`docs/demo_outputs/case_02_massive_htx_first_run.md`](docs/demo_outputs/case_02_massive_htx_first_run.md) and [`docs/demo_outputs/case_05_normal_polytrauma_first_real_run.md`](docs/demo_outputs/case_05_normal_polytrauma_first_real_run.md).

---

## Quickstart (local, mock mode)

The project runs end-to-end in mock mode — no MI300X needed. The `InferenceClient` returns the `tests/fixtures/sample_case.json` fixture for triage requests and an empty patch envelope for verifier requests, so the UI, tests, and demo script all work without a vLLM server.

```bash
# 1. Install — Python 3.12 + uv
uv sync

# 2. Configure — defaults are fine for mock mode
cp .env.example .env

# 3. Build the corpus index (optional; the app runs without it)
#    Source the PDFs first per src/ats/corpus/data/README.md, then:
uv run python scripts/build_index.py

# 4. Launch the Gradio UI on http://127.0.0.1:7860
uv run python -m ats.ui.app
```

To **point at a live vLLM server**, edit `.env`:

```bash
MOCK_MODE=false
VLLM_BASE_URL=http://<droplet-ip>:8000/v1
VLLM_API_KEY=sk-atls-...           # must match --api-key on the server
MODEL_NAME=Qwen/Qwen2.5-VL-72B-Instruct
```

## Production serving (MI300X + vLLM)

The vLLM server runs on a separate ROCm host. The canonical Docker invocation is in [`scripts/serve_vllm.sh`](scripts/serve_vllm.sh):

```bash
# Three modes:
./scripts/serve_vllm.sh dev    # Qwen2.5-VL-7B-Instruct  (fast iteration)
./scripts/serve_vllm.sh prod   # Qwen2.5-VL-72B-Instruct (BF16, single MI300X)
./scripts/serve_vllm.sh spike  # placeholder for the 235B-AWQ Day-1 spike
```

Key flags (`prod` mode):

```
--max-model-len 16384  --max-num-seqs 4  --gpu-memory-utilization 0.95
--api-key $VLLM_API_KEY
VLLM_ROCM_USE_AITER=1  VLLM_ROCM_USE_AITER_MHA=1
SAFETENSORS_FAST_GPU=1  MIOPEN_FIND_MODE=FAST
```

`--tensor-parallel-size` is intentionally not set — single GPU is the entire architectural argument. The container image is `vllm/vllm-openai-rocm:v0.17.1`, which ships preloaded on DigitalOcean's ROCm Quick Start image and is version-pinned for reproducibility.

For the southeast-Asia bring-up path (Tailscale overlay around an ISP that MITMs SSH on port 22), see [`docs/ROCM_FEEDBACK.md`](docs/ROCM_FEEDBACK.md) finding #5.

---

## Schema (the contract)

`src/ats/schema.py` defines the strict Pydantic v2 schema the model writes to via vLLM's `response_format={"type": "json_schema", ...}`. Top-level shape:

```python
class TriageOutput(BaseModel):
    case_id: str
    patient_brief: PatientBrief             # age, sex, mechanism
    primary_survey: PrimarySurvey           # A_airway / B_breathing / C_circulation / D_disability / E_exposure
    red_flags: list[RedFlag]                # each with `flag`, `evidence` list, `immediate_action`
    disposition: Disposition                # priority, target unit, rationale
    citations: list[Citation]               # back into the retrieved corpus
    model_metadata: ModelMetadata           # confidence, limitations, disclaimer, verifier_notes
```

Every per-section assessment carries `concern_level` ∈ `{none, low, moderate, high}` with the discipline that the **section that's wrong drives the urgency** — the credibility-case test. Imaging findings are tagged with `laterality` and `severity` enums. Recommended actions carry `urgency_window` ∈ `{now, within_5_min, within_15_min, within_60_min, …}`. Read the schema; everything in the pipeline is shaped around it.

## Corpus + retrieval

`src/ats/corpus/` holds the FAISS-CPU index over a curated guideline corpus. Sources (PDFs not committed; download per `src/ats/corpus/data/README.md`):

- ACS TQIP Best Practices guidelines
- EAST PMG (Practice Management Guidelines)
- WHO Integrated Management for Emergency & Essential Surgical Care
- StatPearls trauma chapters

Pipeline: PyMuPDF page text → tiktoken `cl100k_base` chunking (500 tokens, 50 overlap, bibliography filter — see `src/ats/corpus/ingest.py`) → `BAAI/bge-m3` embeddings (1024-dim, multilingual) → FAISS cosine. The shipped index has **191 chunks** post-bibliography-filter.

The drafter prompt embeds the top-k chunks with their `[citation_id]` tags so the model can reference them with verbatim `quote` fields in `citations[]`. Citations are checked at validation time.

## Tests

```bash
uv run pytest -q
```

27 tests covering: schema validation (incl. enum boundaries and required-field discipline), renderer output (EN + ID, with verifier notes inlined), verifier patch path-walker (paths into nested dicts and list elements), drafter validation-retry, retrieval edges (missing index → empty results, no exception), end-to-end pipeline (mock mode), corpus chunking (bibliography filter on/off).

Lint: `uv run ruff check src/ tests/ scripts/ space/` — pinned per-file E501 ignores for the prompt strings (long natural-language strings don't get hard-wrapped).

## ROCm bring-up findings

Every non-trivial bring-up issue we hit on `vllm/vllm-openai-rocm:v0.17.1` + MI300X is captured in [`docs/ROCM_FEEDBACK.md`](docs/ROCM_FEEDBACK.md) — seven numbered findings with severity, repro steps, suggested fixes, and log artifacts:

1. **DigitalOcean ROCm Quick Start image silently grabs port 8000** with a JupyterLab container before vLLM starts.
2. **AITER first-run JIT compile is silent for 10+ minutes** — last log line is `[aiter] start build [module_rmsnorm]`, then 1188 s of nothing.
3. `--trust-remote-code` is **accepted but silently ignored** on v0.17.1.
4. **`rocm/vllm-dev:nightly` and `vllm/vllm-openai-rocm:vX.Y.Z` take different command shapes** — different entrypoints.
5. **SE-Asia ISP MITMs SSH on port 22 to DO public IPs** — fix is an overlay network (Tailscale, free tier).
6. **`--limit-mm-per-prompt video=0` argparse-crashes on v0.17.1** — JSON syntax now required.
7. **AITER's JIT kernel cache lives inside the container's writable layer** at `/usr/local/lib/python3.12/dist-packages/aiter/jit/build/` (414 MB in our case). `docker run --rm` discards it on every restart, costing ~20 minutes on every cold start.

Engineering blog post (`docs/BLOG_POST.md`) walks through these as "what we'd want from AMD next."

---

## Repository structure

```
.
├── src/ats/                  Python package (lowercase, NOT "ATLS" — see CLAUDE.md)
│   ├── schema.py             Pydantic v2 contract — read this first
│   ├── prompts/              drafter.py, verifier.py, examples.py
│   ├── pipeline/             drafter.py, verifier.py, run.py
│   ├── render/               handoff_en.py, handoff_id.py
│   ├── retrieval/            FAISS query layer
│   ├── inference/            OpenAI-compatible vLLM client
│   ├── corpus/               PyMuPDF ingest + chunking + embedding
│   └── ui/                   Gradio app (build_ui, main)
├── tests/                    27 tests, pytest
├── scripts/
│   ├── serve_vllm.sh         Canonical vLLM Docker invocation (dev / prod / spike)
│   ├── build_index.py        Build/rebuild the FAISS retrieval index
│   ├── run_benchmarks.py     TTFT, throughput, VRAM (takes --image)
│   ├── run_demo_cases.py     Run a named case end-to-end
│   └── fetch_demo_xrays.py   Source the six demo X-rays
├── space/                    HF Spaces front-end (Gradio + OpenAI client → vLLM)
├── docs/
│   ├── BLOG_POST.md          2,400-word engineering blog post — start here
│   ├── BENCHMARKS.md         Real numbers + cold-start + caveats
│   ├── ROCM_FEEDBACK.md      Seven numbered bring-up findings (for AMD)
│   ├── DEMO_CASES.md         The six clinical vignettes
│   ├── SPIKE_235B_AWQ.md     The Day-1 stretch experiment (skipped, with rationale)
│   ├── demo_outputs/         Per-case JSON + SUMMARY.md + first-real-run write-ups
│   └── logs/                 vLLM startup, rocm-smi, AITER cache listing
├── assets/                   Six demo X-rays (gitignored except sources.json + README)
├── tests/fixtures/           Sample TriageOutput + per-case vignettes
├── pyproject.toml            Python 3.12, uv-managed
├── CLAUDE.md                 Project conventions (must read before touching the code)
└── LICENSE                   MIT
```

`assets/` (X-ray binaries), `video/` (HyperFrames composition for the demo video — local build infrastructure), and the live-demo / final-render MP4s are all gitignored.

## Project conventions (read before contributing)

- **Python package is `ats`** (lowercase, three letters). The string `ATLS` only appears in docs/UI prose.
- **Single-MI300X discipline:** never reference `--tensor-parallel-size > 1` anywhere. The single-GPU shape is load-bearing.
- **Mock mode default:** `Settings.mock_mode = True`. Local development runs in mock mode; only the live droplet flips it off.
- **No PDF / X-ray binaries in git.** Source the corpus PDFs locally per `src/ats/corpus/data/README.md`.
- **vLLM never installed locally** — local code is the OpenAI client only.

Full conventions in [`CLAUDE.md`](CLAUDE.md).

---

## Status & disclaimer

This is a hackathon project. **Decision support only.** Not a diagnostic device. Not regulated. Not for unsupervised clinical use. Every output ships with a disclaimer to that effect. The clinical content is reviewed by the author (a practicing emergency physician) but is no substitute for a trained trauma team.

## License

MIT. See [`LICENSE`](LICENSE).

## Acknowledgments

- **AMD Developer Hackathon** for the MI300X access and the prompt to prove ROCm out
- **The Qwen team** for Qwen2.5-VL-72B-Instruct
- **vLLM** and the **ROCm fork** maintainers
- **American College of Surgeons (ATLS / TQIP)**, **EAST** (Practice Management Guidelines), the **WHO** (Integrated Management for Emergency and Essential Surgical Care), and **StatPearls** — the open clinical corpus this project retrieves over
- **Radiopaedia** and **NIH Open-i** for openly-licensed teaching cases used in the demo set
