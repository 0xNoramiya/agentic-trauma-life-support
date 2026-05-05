"""Benchmark helpers for the vLLM server.

These functions are called by `scripts/run_benchmarks.py`. Both paths assume
the client is talking to a real server — `time_completion` raises if the
client is in mock mode, since mock numbers are meaningless.
"""

from __future__ import annotations

import json
import shutil
import statistics
import subprocess
import time
from typing import Iterable

from ats.inference.client import InferenceClient


def time_completion(
    client: InferenceClient,
    messages: list[dict],
    max_tokens: int = 512,
) -> dict:
    """Stream a single completion and measure TTFT, total time, and tokens/sec.

    Returns a dict with keys: ttft_ms, total_ms, output_tokens, tokens_per_sec.
    """
    if client.mock_mode:
        raise RuntimeError(
            "time_completion requires a real vLLM server. Set MOCK_MODE=false."
        )

    start = time.perf_counter()
    first_token_at: float | None = None
    output_tokens = 0

    stream = client.client.chat.completions.create(
        model=client.model_name,
        messages=messages,
        max_tokens=max_tokens,
        temperature=0.2,
        stream=True,
    )

    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        token_text = getattr(delta, "content", None)
        if token_text:
            if first_token_at is None:
                first_token_at = time.perf_counter()
            # Approximate token count: vLLM streams roughly one token per chunk
            # for this provider. For an exact count we'd need to re-tokenize;
            # the approximation is good enough for relative benchmarking.
            output_tokens += 1

    end = time.perf_counter()
    total_s = end - start
    ttft_s = (first_token_at - start) if first_token_at is not None else total_s
    tokens_per_sec = output_tokens / total_s if total_s > 0 else 0.0

    return {
        "ttft_ms": round(ttft_s * 1000, 2),
        "total_ms": round(total_s * 1000, 2),
        "output_tokens": output_tokens,
        "tokens_per_sec": round(tokens_per_sec, 2),
    }


def aggregate(samples: Iterable[dict], key: str) -> dict:
    """Compute median and p95 over a sequence of sample dicts for one key."""
    vals = [s[key] for s in samples if key in s]
    if not vals:
        return {"median": None, "p95": None}
    vals_sorted = sorted(vals)
    median = statistics.median(vals_sorted)
    # p95 with linear interpolation
    if len(vals_sorted) == 1:
        p95 = vals_sorted[0]
    else:
        rank = 0.95 * (len(vals_sorted) - 1)
        lo = int(rank)
        hi = min(lo + 1, len(vals_sorted) - 1)
        frac = rank - lo
        p95 = vals_sorted[lo] + frac * (vals_sorted[hi] - vals_sorted[lo])
    return {"median": round(median, 2), "p95": round(p95, 2)}


def read_peak_vram_gb() -> float | None:
    """Best-effort VRAM read via `rocm-smi --showmeminfo vram --json`.

    Returns peak VRAM used in GB across all visible GPUs, or None if rocm-smi
    is not on PATH (e.g. when this is being run on a developer laptop). The
    benchmark caller is expected to read VRAM from the MI300X droplet via SSH
    when running locally; this helper exists so the same script can be run
    on the droplet itself.
    """
    if shutil.which("rocm-smi") is None:
        return None

    try:
        result = subprocess.run(
            ["rocm-smi", "--showmeminfo", "vram", "--json"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (subprocess.SubprocessError, OSError):
        return None

    if result.returncode != 0 or not result.stdout.strip():
        return None

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None

    peak_bytes = 0
    for card in data.values():
        if not isinstance(card, dict):
            continue
        for key, val in card.items():
            # rocm-smi exposes keys like "VRAM Total Used Memory (B)" depending
            # on version. Look for any entry mentioning "used" and "(B)".
            klow = key.lower()
            if "used" in klow and "(b)" in klow:
                try:
                    peak_bytes = max(peak_bytes, int(val))
                except (ValueError, TypeError):
                    continue

    if peak_bytes == 0:
        return None
    return round(peak_bytes / (1024**3), 2)
