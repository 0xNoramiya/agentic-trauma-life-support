"""Run a benchmark scenario against the vLLM server and update docs/BENCHMARKS.md.

Scenarios:
  - single-image-short:        one chest X-ray + ~150-token vitals.
  - single-image-long-context: one chest X-ray + 5 retrieved excerpts (~3k tokens total).
  - concurrent-batch-4:        four single-image-short requests fired in parallel.

For each scenario we fire `--n` runs, record TTFT / total time / tokens-per-sec,
and append a markdown section to `docs/BENCHMARKS.md` (replacing any existing
section with the same delimiter).

A 1024x1024 grayscale placeholder image is generated on the fly. The numbers
are only representative when the script is pointed at a real X-ray locally —
see the comment in `_make_placeholder_image`.
"""

from __future__ import annotations

import argparse
import base64
import io
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from ats.config import settings  # noqa: E402
from ats.inference.benchmark import (  # noqa: E402
    aggregate,
    read_peak_vram_gb,
    time_completion,
)
from ats.inference.client import InferenceClient, build_image_message  # noqa: E402

SCENARIOS = ("single-image-short", "single-image-long-context", "concurrent-batch-4")

SHORT_VITALS = (
    "30M motorbike vs car, ejected. RR 32, SpO2 88%, HR 124, BP 92/60, GCS 14. "
    "Decreased breath sounds on the left, tracheal deviation right."
)

LONG_CONTEXT_EXTRA = "\n\n".join(
    [
        "[atls-c1-001] ACS ATLS — Chapter 1: \"Tension pneumothorax is a clinical diagnosis. "
        "Treatment must not be delayed for radiographic confirmation. Immediate decompression of "
        "the affected hemithorax is required.\"",
        "[east-ptx-002] EAST PMG — Pneumothorax: \"Tube thoracostomy is recommended after "
        "needle decompression for confirmed pneumothorax in the trauma patient.\"",
        "[acs-tqip-thoracic-001] ACS TQIP — Best Practices Thoracic Trauma: \"Initial fluid "
        "resuscitation in hemorrhagic shock should prioritize blood products over crystalloid.\"",
        "[east-rib-001] EAST PMG — Rib Fractures: \"Multimodal analgesia is recommended; "
        "consider regional analgesia in patients with three or more rib fractures.\"",
        "[who-imeesc-001] WHO IMEESC: \"In resource-limited settings, surgical airway equipment "
        "should be immediately available wherever advanced airway is attempted.\"",
    ]
)


def _make_placeholder_image() -> str:
    """Return a base64 JPEG of a 1024x1024 grey image.

    This script does not ship a real chest X-ray for licensing reasons. Point
    the script at a real image locally (or wire one in here) to get
    representative TTFT numbers — the placeholder is fine for relative
    comparisons but absolute throughput will be slightly optimistic.
    """
    img = Image.new("L", (1024, 1024), color=128)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _build_messages(image_b64: str, vitals: str) -> list[dict]:
    return [
        {
            "role": "system",
            "content": (
                "You are a trauma triage assistant. Produce a brief ATLS primary-survey "
                "summary in plain prose."
            ),
        },
        {
            "role": "user",
            "content": [
                build_image_message(image_b64),
                {"type": "text", "text": vitals},
            ],
        },
    ]


def _run_scenario(client: InferenceClient, scenario: str, n: int) -> list[dict]:
    image_b64 = _make_placeholder_image()
    if scenario == "single-image-short":
        messages = _build_messages(image_b64, SHORT_VITALS)
        return [time_completion(client, messages, max_tokens=512) for _ in range(n)]

    if scenario == "single-image-long-context":
        long_vitals = SHORT_VITALS + "\n\nRetrieved excerpts:\n" + LONG_CONTEXT_EXTRA
        messages = _build_messages(image_b64, long_vitals)
        return [time_completion(client, messages, max_tokens=512) for _ in range(n)]

    if scenario == "concurrent-batch-4":
        # Wall-clock for batches of 4 fired in parallel. Per-request stats are
        # still recorded; we add a `wall_ms` field to capture batch latency.
        samples: list[dict] = []
        messages = _build_messages(image_b64, SHORT_VITALS)
        for _ in range(n):
            start = time.perf_counter()
            with ThreadPoolExecutor(max_workers=4) as pool:
                futures = [pool.submit(time_completion, client, messages, 512) for _ in range(4)]
                batch = [f.result() for f in futures]
            wall = (time.perf_counter() - start) * 1000
            for s in batch:
                s["wall_ms"] = round(wall, 2)
                samples.append(s)
        return samples

    raise ValueError(f"Unknown scenario: {scenario}")


def _summarize(samples: list[dict]) -> dict:
    return {
        "ttft_ms": aggregate(samples, "ttft_ms"),
        "total_ms": aggregate(samples, "total_ms"),
        "tokens_per_sec": aggregate(samples, "tokens_per_sec"),
        "output_tokens": aggregate(samples, "output_tokens"),
    }


def _format_markdown(scenario: str, n: int, samples: list[dict], vram_gb: float | None) -> str:
    summary = _summarize(samples)
    vram_line = f"- Peak VRAM: {vram_gb} GB" if vram_gb is not None else "- Peak VRAM: n/a"

    lines = [
        f"<!-- scenario:{scenario} -->",
        f"### {scenario}",
        "",
        f"- N: {n}",
        f"- Median TTFT: {summary['ttft_ms']['median']} ms (p95 {summary['ttft_ms']['p95']} ms)",
        f"- Median total: {summary['total_ms']['median']} ms"
        f" (p95 {summary['total_ms']['p95']} ms)",
        f"- Median tokens/sec: {summary['tokens_per_sec']['median']}"
        f" (p95 {summary['tokens_per_sec']['p95']})",
        f"- Median output tokens: {summary['output_tokens']['median']}",
        vram_line,
        f"<!-- /scenario:{scenario} -->",
    ]
    return "\n".join(lines)


def _splice_section(doc: str, scenario: str, new_block: str) -> str:
    """Replace `<!-- scenario:NAME -->...<!-- /scenario:NAME -->` if present, else append."""
    pattern = re.compile(
        rf"<!-- scenario:{re.escape(scenario)} -->.*?<!-- /scenario:{re.escape(scenario)} -->",
        re.DOTALL,
    )
    if pattern.search(doc):
        return pattern.sub(new_block, doc)
    if not doc.endswith("\n"):
        doc += "\n"
    return doc + "\n" + new_block + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=SCENARIOS, required=True)
    parser.add_argument("--n", type=int, default=5, help="Number of runs.")
    parser.add_argument(
        "--out",
        type=Path,
        default=REPO_ROOT / "docs" / "BENCHMARKS.md",
        help="Markdown file to update in place.",
    )
    args = parser.parse_args()

    client = InferenceClient(settings)
    if client.mock_mode:
        print(
            "MOCK_MODE is true. Set MOCK_MODE=false in .env and point VLLM_BASE_URL "
            "at the MI300X droplet before running benchmarks.",
            file=sys.stderr,
        )
        return 1

    if not client.health_check():
        print(
            f"vLLM server at {client.base_url} did not respond to /models. Aborting.",
            file=sys.stderr,
        )
        return 2

    print(f"Running scenario={args.scenario} n={args.n} ...", flush=True)
    samples = _run_scenario(client, args.scenario, args.n)
    vram_gb = read_peak_vram_gb()

    block = _format_markdown(args.scenario, args.n, samples, vram_gb)

    out_path: Path = args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        existing = out_path.read_text(encoding="utf-8")
    else:
        existing = "# Benchmarks\n\nMI300X benchmark numbers for ATLS.\n"
    out_path.write_text(_splice_section(existing, args.scenario, block), encoding="utf-8")
    print(f"Updated {out_path}")
    print(block)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
