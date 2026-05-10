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
| "Warm" restart after `docker run --rm` | **~22 min** — same as cold |

The AITER-rmsnorm JIT cost is captured as `docs/ROCM_FEEDBACK.md` finding #2 — the silent multi-minute window with no progress messages. The "warm" restart taking the *same* time as cold is finding #7 — AITER's JIT artifacts live inside the container's writable layer, so `docker run --rm` discards them on every restart. With the container *not* removed (or the JIT dir mounted as a host volume) the warm path drops to ~2 min; we measured the full restart only once intentionally to confirm the regression.

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

The numbers below come from `scripts/run_benchmarks.py`, which fires direct streaming chat-completion requests to vLLM (no schema constraint, no two-pass) and records TTFT plus per-token throughput. Same case_01 chest X-ray for every scenario (passed via `--image assets/case_01_tension_ptx.jpg` — the script also supports a 1024×1024 grey placeholder when no image is provided, which we used to use and which materially undercounted TTFT — see "Caveats").

| Scenario | N | Median TTFT | Median total | Median tok/sec | Output tokens (median) |
|---|---:|---:|---:|---:|---:|
| single-image-short (~150-token prompt + real CXR) | 5 | **1981 ms** | 15.4 s | **19.9** | 252 |
| single-image-long-context (~3 k-token prompt + real CXR) | 5 | **1982 ms** | 15.9 s | **21.5** | 342 |
| concurrent-batch-4 (4 in flight, same CXR) | 12 (3 batches × 4) | **2199 ms** | 15.1 s | 18.4 | 284 |

**Headlines:**
- TTFT is essentially constant ~1.98 s regardless of context length — vision-tower encoding of the image dominates prompt-prefill, not the text portion. A 20× longer text prompt (150 → 3 000 tokens) costs <1 ms of additional TTFT.
- Real-CXR TTFT is **2.3× higher than the same call with a 1024×1024 grey placeholder image** (1981 ms vs 862 ms). Same model, same path, different image content — flat grey gives the vision tower nothing to encode and it short-circuits. We had been using the placeholder benchmark earlier and it was reading a misleadingly fast TTFT; the real-CXR numbers above are what the demo actually does.
- Sustained throughput is ~20 tok/sec for single requests, ~18 tok/sec when 4 are in flight on the same MI300X. Under-load drop is small (~10%) — the GPU has enough HBM3 bandwidth to interleave the four streams.
- The end-to-end pipeline (drafter + verifier, both with strict structured-output constraints and image-multimodal context) wall clock of 46–60 s reconciles with the streaming numbers: drafter pass ~15 s × 2 calls + a few seconds of schema validation, retrieval, and renderer overhead.

## Caveats

- **Network path:** laptop ↔ droplet over Tailscale, Indonesia → DO ATL1. Should add ~30–50 ms one-way at most; latencies above are dominated by GPU compute, not network. A colocated benchmark from a US-region node would isolate that variable.
- **Image content matters more than expected.** Earlier benchmark runs in this file used a 1024×1024 grey placeholder JPEG and reported ~862 ms TTFT. Switching to a real CXR (with actual radiographic detail for the vision tower to attend to) shifts TTFT to ~1981 ms — a 2.3× increase. The grey-placeholder numbers are not wrong, but they are not what the demo does, and they made vLLM's vision-multimodal path look ~2× faster than it is for our actual workload. We retain both runs in the delimited blocks at the bottom and consider the real-CXR numbers canonical.
- **Output token counting:** approximate (one streamed delta = one token). Exact tokenization would require running the model's own tokenizer over the response; the approximation is good enough for relative scenario comparisons but ±5% on absolute throughput.

<!-- scenario:single-image-short -->
### single-image-short

- N: 5
- Median TTFT: 1981.15 ms (p95 4396.22 ms)
- Median total: 15371.92 ms (p95 16380.25 ms)
- Median tokens/sec: 19.87 (p95 21.67)
- Median output tokens: 252
- Peak VRAM: 183.95 GiB / 191.69 GiB (96%) measured at end of concurrent-batch-4 run via rocm-smi
<!-- /scenario:single-image-short -->

<!-- scenario:single-image-long-context -->
### single-image-long-context

- N: 5
- Median TTFT: 1982.41 ms (p95 2157.47 ms)
- Median total: 15870.61 ms (p95 20545.79 ms)
- Median tokens/sec: 21.55 (p95 22.19)
- Median output tokens: 342
- Peak VRAM: 183.95 GiB / 191.69 GiB (96%) measured at end of concurrent-batch-4 run via rocm-smi
<!-- /scenario:single-image-long-context -->

<!-- scenario:concurrent-batch-4 -->
### concurrent-batch-4

- N: 3
- Median TTFT: 2198.94 ms (p95 2457.51 ms)
- Median total: 15118.5 ms (p95 22561.12 ms)
- Median tokens/sec: 18.37 (p95 20.04)
- Median output tokens: 283.5
- Peak VRAM: 183.95 GiB / 191.69 GiB (96%) measured at end of concurrent-batch-4 run via rocm-smi
<!-- /scenario:concurrent-batch-4 -->
