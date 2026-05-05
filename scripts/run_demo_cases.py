"""Run a single demo case end-to-end and print the rendered handoff.

Cases live in `tests/fixtures/cases/{case_id}.json` (these are decision-support
fixtures parsed easily by the script). The corresponding image is loaded from
`assets/{case_id}.jpg`; if it's missing, a placeholder grey image is used so
the script still runs in mock mode.

The JSON output is written to `docs/demo_outputs/{case_id}.json` for the report.

Usage:
    python scripts/run_demo_cases.py --case case_01_tension_ptx
    python scripts/run_demo_cases.py --case case_06_pediatric_id --lang id
    python scripts/run_demo_cases.py --case case_05_normal_polytrauma --show-citations
    python scripts/run_demo_cases.py --case case_01_tension_ptx --no-verifier --show-json
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from ats.config import settings  # noqa: E402
from ats.inference.client import InferenceClient  # noqa: E402
from ats.pipeline.run import run_triage  # noqa: E402

CASES_DIR = REPO_ROOT / "tests" / "fixtures" / "cases"
ASSETS_DIR = REPO_ROOT / "assets"
DEMO_OUT_DIR = REPO_ROOT / "docs" / "demo_outputs"


def _load_case(case_id: str) -> dict:
    path = CASES_DIR / f"{case_id}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"No case fixture at {path}. See docs/DEMO_CASES.md for the case set."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def _load_image_bytes(case_id: str) -> bytes:
    img_path = ASSETS_DIR / f"{case_id}.jpg"
    if img_path.exists():
        return img_path.read_bytes()
    print(
        f"WARNING: no image at {img_path}. Using grey placeholder. "
        f"See docs/DEMO_CASES.md for the source URL.",
        file=sys.stderr,
    )
    placeholder = Image.new("L", (1024, 1024), color=128)
    buf = io.BytesIO()
    placeholder.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def _vitals_text_from_case(case: dict) -> str:
    v = case.get("vitals", {})
    parts: list[str] = []
    if "rr" in v:
        parts.append(f"RR {v['rr']}")
    if "spo2" in v:
        parts.append(f"SpO2 {v['spo2']}%")
    if "hr" in v:
        parts.append(f"HR {v['hr']}")
    if "sbp" in v and "dbp" in v:
        parts.append(f"BP {v['sbp']}/{v['dbp']}")
    if "gcs" in v:
        parts.append(f"GCS {v['gcs']}")
    if "temp" in v:
        parts.append(f"Temp {v['temp']}°C")
    vitals_block = ", ".join(parts) if parts else "(no vitals provided)"
    vignette = case.get("clinical_vignette", "").strip()
    return f"{vignette}\nVitals: {vitals_block}".strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True, help="Case ID, e.g. case_01_tension_ptx.")
    parser.add_argument(
        "--lang",
        choices=["en", "id"],
        default=None,
        help="Override language. Defaults to the case's language field.",
    )
    parser.add_argument(
        "--verifier",
        dest="verifier",
        action="store_true",
        default=True,
        help="Run the verifier pass (default).",
    )
    parser.add_argument(
        "--no-verifier",
        dest="verifier",
        action="store_false",
        help="Skip the verifier pass.",
    )
    parser.add_argument(
        "--show-citations",
        action="store_true",
        help="Print only the citations section of the result.",
    )
    parser.add_argument(
        "--show-json",
        action="store_true",
        help="Also print the full TriageOutput JSON.",
    )
    args = parser.parse_args()

    case = _load_case(args.case)
    lang = args.lang or case.get("language", "en")
    image_bytes = _load_image_bytes(args.case)
    vitals_text = _vitals_text_from_case(case)

    client = InferenceClient(settings)
    result = run_triage(
        client=client,
        image_bytes=image_bytes,
        vitals_text=vitals_text,
        lang=lang,
        case_id=args.case,
        use_verifier=args.verifier,
    )

    DEMO_OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DEMO_OUT_DIR / f"{args.case}.json"
    out_path.write_text(
        json.dumps(result["json"], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    if args.show_citations:
        for c in result["json"].get("citations", []):
            url = f" {c['url']}" if c.get("url") else ""
            print(f'[{c["id"]}] {c["source"]}, {c["section"]}: "{c["quote"]}"{url}')
    else:
        print(result["handoff"])

    if args.show_json:
        print()
        print("---")
        print(json.dumps(result["json"], indent=2, ensure_ascii=False))

    print(f"\n(JSON written to {out_path})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
