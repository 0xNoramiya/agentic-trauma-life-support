#!/usr/bin/env bash
# serve_vllm.sh — launch vLLM on a single AMD MI300X via the rocm/vllm-dev:nightly container.
#
# Usage:
#   ./scripts/serve_vllm.sh dev     # 7B for fast iteration / HF Space deploy
#   ./scripts/serve_vllm.sh prod    # 72B BF16 for the demo (single MI300X)
#   ./scripts/serve_vllm.sh spike   # placeholder for the 235B-AWQ spike
#
# Hard rule: this is a single-GPU project. We never set --tensor-parallel-size > 1.
#
# Required on the host:
#   - Docker with --device=/dev/kfd --device=/dev/dri (ROCm passthrough).
#   - HuggingFace cache mounted at /root/.cache/huggingface.
#
# Override the mode via the first arg or the MODE env var. Default: dev.

set -euo pipefail

MODE="${1:-${MODE:-dev}}"

# ---- Common flags shared across all modes -----------------------------------
# vLLM ROCm tuning toggles, all set via env into the container:
#   VLLM_ROCM_USE_AITER=1       — use AITER kernels (fastest path on MI300X).
#   VLLM_ROCM_USE_AITER_MHA=1   — multi-head attention via AITER.
#   SAFETENSORS_FAST_GPU=1      — direct safetensors->GPU load, faster bring-up.
#   MIOPEN_FIND_MODE=FAST       — skip exhaustive autotune to cut cold start.
COMMON_ENV=(
  -e "VLLM_ROCM_USE_AITER=1"
  -e "VLLM_ROCM_USE_AITER_MHA=1"
  -e "SAFETENSORS_FAST_GPU=1"
  -e "MIOPEN_FIND_MODE=FAST"
  -e "HF_HOME=/root/.cache/huggingface"
)

# Container image — ROCm vLLM nightly. Pin a digest for the demo run.
IMAGE="rocm/vllm-dev:nightly"

# Docker run prelude with ROCm device passthrough.
DOCKER_RUN=(
  docker run --rm
  --network=host
  --ipc=host
  --device=/dev/kfd
  --device=/dev/dri
  --group-add=video
  --security-opt seccomp=unconfined
  --shm-size=16g
  -v "$HOME/.cache/huggingface:/root/.cache/huggingface"
  "${COMMON_ENV[@]}"
)

case "$MODE" in
  dev)
    # ---- Dev iteration: Qwen2.5-VL-7B-Instruct -----------------------------
    # Goal: fast iteration, low VRAM. Also the HF Space deployment target.
    echo "[serve_vllm] mode=dev — Qwen2.5-VL-7B-Instruct"
    MODEL="Qwen/Qwen2.5-VL-7B-Instruct"
    "${DOCKER_RUN[@]}" "$IMAGE" \
      vllm serve "$MODEL" \
        --port 8000 \
        --api-key EMPTY \
        --max-model-len 8192 \
        --max-num-seqs 8 \
        --gpu-memory-utilization 0.85 \
        --trust-remote-code \
        --limit-mm-per-prompt video=0
    ;;

  prod)
    # ---- Production: Qwen2.5-VL-72B-Instruct in BF16 -----------------------
    # Single MI300X, 192 GB HBM3. ~144 GB weights; ~95% util leaves headroom
    # for KV cache. --max-model-len 16384 fits one X-ray + vitals + retrieved
    # excerpts comfortably. --max-num-seqs 4 is conservative for a hackathon
    # demo where p95 latency matters more than throughput.
    echo "[serve_vllm] mode=prod — Qwen2.5-VL-72B-Instruct (BF16, single MI300X)"
    MODEL="Qwen/Qwen2.5-VL-72B-Instruct"
    "${DOCKER_RUN[@]}" "$IMAGE" \
      vllm serve "$MODEL" \
        --port 8000 \
        --api-key EMPTY \
        --max-model-len 16384 \
        --max-num-seqs 4 \
        --gpu-memory-utilization 0.95 \
        --trust-remote-code \
        --limit-mm-per-prompt video=0
    ;;

  spike)
    # ---- Stretch: 235B AWQ Day 1 spike ------------------------------------
    # See docs/SPIKE_235B_AWQ.md for the experiment plan, sources tried, and
    # the proceed/revert decision. This branch is intentionally not wired up
    # to a model name yet — fill that in once the spike picks a candidate.
    echo "[serve_vllm] mode=spike — see docs/SPIKE_235B_AWQ.md"
    echo "  This is a placeholder. The 235B-AWQ spike runs through the same"
    echo "  container with a different model id, but landing it depends on"
    echo "  what loads cleanly on MI300X. Edit this branch when you decide."
    exit 2
    ;;

  *)
    echo "Unknown mode: $MODE" >&2
    echo "Usage: $0 {dev|prod|spike}" >&2
    exit 64
    ;;
esac
