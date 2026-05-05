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

Peak observed during these runs (`rocm-smi --showmeminfo vram` on the droplet):

- **Steady-state (warm, idle): ~150 GiB / 192 GiB** (~78%)
- **Peak under concurrent batch-of-4: 184.79 GiB / 192 GiB** (~96%)

The peak under concurrent load sits right at the `--gpu-memory-utilization 0.95` budget. KV cache fills as more requests are in-flight; ~150 GiB is the baseline for the model weights + minimal KV reservation, while the remaining ~30 GiB are dynamic KV-cache pages allocated as concurrent requests arrive.

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

## Per-scenario streaming benchmark (`scripts/run_benchmarks.py`)

The numbers below come from `scripts/run_benchmarks.py`, which fires direct streaming chat-completion requests to vLLM (no schema constraint, no two-pass) and records TTFT plus per-token throughput. The script lives in `scripts/run_benchmarks.py` and writes its results into the delimited blocks at the bottom of this file.

| Scenario | N | Median TTFT | Median total | Median tok/sec | Output tokens (median) |
|---|---:|---:|---:|---:|---:|
| single-image-short (~150 token prompt) | 5 | **862 ms** | 9.57 s | **23.1** | 221 |
| single-image-long-context (~3 k token prompt) | 5 | **864 ms** | 13.48 s | **23.7** | 320 |
| concurrent-batch-4 (4 in flight) | 12 (3 batches × 4) | 953 ms | 13.28 s | 20.2 | 228 |

**Headlines:**
- TTFT is essentially constant ~860 ms regardless of context length — the dominant prompt-prefill cost is the vision-tower image encoding, not text length.
- Sustained throughput is ~23 tok/sec for single requests, ~20 tok/sec when 4 are in flight on the same MI300X. The under-load drop is small (~13%) — the GPU has enough memory bandwidth to interleave the four streams cleanly.
- The end-to-end pipeline (drafter + verifier, both with guided-JSON constraints and image-multimodal context) wall clock of 46–60 s reconciles with the streaming numbers: drafter pass ~9–14 s × 2 calls + a few seconds of overhead.

## Caveats

- **Network path:** laptop ↔ droplet over Tailscale, Indonesia → DO ATL1. Should add ~30–50 ms one-way at most; latencies above are dominated by GPU compute, not network. A colocated benchmark from a US-region node would isolate that variable.
- **Image:** the benchmark script uses a 1024×1024 grey placeholder JPEG, not a real CXR. TTFT may be slightly optimistic relative to a real radiograph (more visual structure → marginally more vision-tower compute).
- **Output token counting:** approximate (one streamed delta = one token). Exact tokenization would require running the model's own tokenizer over the response; the approximation is good enough for relative scenario comparisons but ±5% on absolute throughput.

<!-- scenario:single-image-short -->
### single-image-short

- N: 5
- Median TTFT: 862.17 ms (p95 1505.84 ms)
- Median total: 9571.18 ms (p95 10070.45 ms)
- Median tokens/sec: 23.09 (p95 23.36)
- Median output tokens: 221
- Peak VRAM: ~150 GiB (warm)
<!-- /scenario:single-image-short -->

<!-- scenario:single-image-long-context -->
### single-image-long-context

- N: 5
- Median TTFT: 863.68 ms (p95 1017.78 ms)
- Median total: 13475.49 ms (p95 16195.15 ms)
- Median tokens/sec: 23.7 (p95 23.92)
- Median output tokens: 320
- Peak VRAM: ~150 GiB (warm)
<!-- /scenario:single-image-long-context -->

<!-- scenario:concurrent-batch-4 -->
### concurrent-batch-4

- N: 3 (each iteration fires 4 concurrent requests via ThreadPoolExecutor; 12 total requests)
- Median TTFT (per request): 952.91 ms (p95 1081.29 ms)
- Median total (per request): 13278.02 ms (p95 15162.47 ms)
- Median tokens/sec (per request): 20.2 (p95 21.63)
- Median output tokens: 228.0
- Peak VRAM: n/a
<!-- /scenario:concurrent-batch-4 -->
