# Spike — Qwen2.5-VL-235B AWQ on a single MI300X

A Day 1 time-boxed experiment. The question: can we serve a 235B-class vision-language model in AWQ on a single MI300X? If yes, the demo upgrades. If no, we revert to the safer 72B BF16 path and report the failure mode in `docs/ROCM_FEEDBACK.md`.

## Hypothesis

_TODO: state the bet. Example: "Qwen2.5-VL-235B AWQ-int4 should fit in ~120-130 GB, leaving headroom on a 192 GB MI300X. We expect TTFT to be slower than 72B BF16 but tokens/sec to be in the same order of magnitude on AITER + MHA paths."_

## Sources tried

_TODO: list candidate weights. Examples to investigate: official Qwen AWQ repos on HF, community AWQ conversions, casperhansen builds, etc. Note the AWQ group size and quantization config for each._

## What loaded

_TODO: which checkpoint, with which `--quantization` flag and which `--dtype`. Time-to-first-load. Whether the multimodal vision tower loaded._

## What crashed

_TODO: paste the stack traces verbatim. Note ROCm version, vLLM container tag, and any env vars you set before the run._

## Decision

_TODO: one of:_

- **Proceed AWQ.** _Why: TTFT acceptable, no instability over a 30-minute soak. Update `scripts/serve_vllm.sh spike` to point at the working checkpoint._
- **Revert BF16 72B.** _Why: blocker reproduces, no working path inside the time-box. The pitch is unchanged — single MI300X, full BF16, no quantization is also a defensible story._

## Time spent

_TODO: hours._
