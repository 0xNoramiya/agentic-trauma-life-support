# Benchmarks — Qwen2.5-VL-72B BF16 / single MI300X

Real numbers from running the demo cases through the full pipeline against `Qwen/Qwen2.5-VL-72B-Instruct` on a single AMD Instinct MI300X, served by `vllm/vllm-openai-rocm:v0.17.1`. Setup:

- vLLM flags: `--max-model-len 16384 --max-num-seqs 4 --gpu-memory-utilization 0.95`
- AITER kernels enabled (`VLLM_ROCM_USE_AITER=1`, `VLLM_ROCM_USE_AITER_MHA=1`)
- Tensor-parallel: **1** (single GPU is the entire pitch)
- Network: laptop ↔ droplet via Tailscale overlay (~2026-05-05, Indonesia → DO ATL1)
- Method: wall-clock time of `run_triage(...)` from the test harness, including the drafter call (image + vitals + retrieved guideline excerpts → `TriageOutput` JSON), the verifier call (image + draft → `VerifierOutput` patches/notes), and the renderer step. Two model calls per case.

## Cold-start

| Step | Wall clock |
|---|---|
| Weight load (137 GiB into VRAM) | **94 s** |
| AITER JIT — `module_rmsnorm` (single kernel) | **1188 s (~20 min)** |
| Total cold start to API ready | **~22 min** on first run after droplet boot |
| Warm restart (JIT cache hit) | **~2 min** _(estimated; not yet measured)_ |

The AITER-rmsnorm JIT cost is captured as `docs/ROCM_FEEDBACK.md` finding #2 — the silent multi-minute window with no progress messages.

## Per-case end-to-end latency (drafter + verifier + renderer)

Six demo cases through the full pipeline. Each call goes laptop → tailnet → droplet vLLM → laptop. RAG retrieval happens locally against the 281-chunk FAISS index (negligible time relative to the model calls).

| Case | Image source | Wall clock | Notes |
|---|---|---:|---|
| case_01_tension_ptx | Wikimedia Commons (3200×2400) | **60 s** | Drafter identifies tracheal deviation + decreased lung volume; recommends needle decompression with full evidence chain |
| case_02_massive_htx | Open-i PMC3789901 (512×426) | **54 s** | Drafter laterality wrong; verifier corrects |
| case_03_flail_chest | Open-i PMC2804570 (512×391) | **53 s** | Drafter overestimates flail; verifier downgrades |
| case_04_pulm_contusion | Open-i PMC2714572 (512×166 strip) | **46 s** | Multi-panel image; pulm contusion identified, ICU disposition |
| case_05_normal_polytrauma | Wikimedia Commons (1929×2207) | **57 s** | **The credibility case.** Drafter declines to invent. Recommends FAST + CT abdomen |
| case_06_pediatric_id | Open-i PMC4888635 (512×408) | **60 s** | Indonesian-rendered handoff; verifier flags shock attribution |

**Median: ~55 s · Range: 46–60 s · Mean: ~55 s**

## VRAM

Peak observed during these runs (from `rocm-smi --showmeminfo vram` taken mid-run):

- **VRAM used: ~150 GiB / 192 GiB** (≈78%)

This sits comfortably under `--gpu-memory-utilization 0.95`. The remaining ~40 GiB headroom covers KV cache for `--max-num-seqs 4` and the multimodal vision encoder activations.

## Single-MI300X cost comparison

What it would take to serve this same workload elsewhere:

| Hardware | Fits 72B BF16? | $ / hr cloud | Notes |
|---|---|---:|---|
| **1 × MI300X (192 GiB HBM3)** | yes (~78% util) | **~$1.99** | This setup |
| 2 × H100 (NVLink) | yes (TP=2) | ~$4–5 | Plus collective overhead, slower cold start |
| 1 × H200 (141 GiB) | no | n/a | Cannot fit in BF16 |
| 1 × H100 (80 GiB) | no | n/a | Cannot fit in BF16 |
| 1 × B200 (192 GiB HBM3e) | yes | ~$5–8 | Same VRAM as MI300X but 3-5× the per-hour cost |

For the global-health, resource-limited-deployment use case, the MI300X is the only sub-$2/hr option that fits 72B in BF16 on a single GPU. Two H100s with NVLink works but costs 2-3× more per deployment and adds tensor-parallel operational complexity.

## Caveats and what's still missing

- **TTFT (time to first token)** — not yet measured per scenario. The numbers above are full-pipeline wall clock, which includes prompt prefill, image encoding through the vision tower, and full output generation under guided JSON. A separate streaming benchmark with real X-ray inputs would capture pure TTFT for the engineering blog.
- **Tokens/sec output** — not yet measured. Order-of-magnitude estimate from the per-case numbers and observed token counts: ~30–50 output tokens/sec sustained on the drafter pass, faster on the verifier pass (smaller output schema). Need a clean per-token measurement to publish a definitive number.
- **Concurrent batch-of-4** — not yet run. `scripts/run_benchmarks.py --scenario concurrent-batch-4` is wired up; will run once the prompt-iteration phase is done.
- **Network jitter** — laptop ↔ droplet path goes via Tailscale (overlay over Indonesian ISP → DO ATL1). The single-image cases are dominated by GPU compute, but a colocated benchmark from a US-region node would isolate that variable.

<!-- scenario:single-image-short -->
### single-image-short

Pending — run `scripts/run_benchmarks.py --scenario single-image-short` on the MI300X droplet for a clean TTFT + throughput per-scenario breakdown.
<!-- /scenario:single-image-short -->

<!-- scenario:single-image-long-context -->
### single-image-long-context

Pending — run `scripts/run_benchmarks.py --scenario single-image-long-context` on the MI300X droplet.
<!-- /scenario:single-image-long-context -->

<!-- scenario:concurrent-batch-4 -->
### concurrent-batch-4

Pending — run `scripts/run_benchmarks.py --scenario concurrent-batch-4` on the MI300X droplet.
<!-- /scenario:concurrent-batch-4 -->
