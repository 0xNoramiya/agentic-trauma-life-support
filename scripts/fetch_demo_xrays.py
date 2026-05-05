"""Fetch CC-licensed chest X-rays from NIH Open-i for the six demo cases.

Open-i (https://openi.nlm.nih.gov/) is a NIH service that surfaces images
from open-access biomedical literature. Most images are CC BY (verify the
parent article's license before public redistribution).

Usage:
    uv run python scripts/fetch_demo_xrays.py

Writes:
    assets/case_*.jpg              — the X-ray itself (gitignored)
    assets/sources.json            — attribution metadata (committed)

For each case we query Open-i, take the top chest-X-ray hit (it=xg), and
download the largest exposed size (imgLarge = 512 px). 512 px is small for
fine rib-fracture detail but plenty for the gross findings the demo cases
turn on (white-out, mediastinal shift, lobe consolidation).

If a case has no good Open-i match, the script logs a warning and skips
that file — the user can drop a manual download in afterwards.
"""

from __future__ import annotations

import io
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import httpx
from PIL import Image, UnidentifiedImageError

REPO_ROOT = Path(__file__).resolve().parent.parent
ASSETS = REPO_ROOT / "assets"

OPENI_BASE = "https://openi.nlm.nih.gov"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


@dataclass
class CaseQuery:
    case_id: str
    query: str
    avoid: tuple[str, ...] = ()
    candidate_n: int = 8  # higher than before, since we walk candidates

    def is_acceptable(self, record: dict) -> bool:
        """Reject only on `avoid` terms; trust the search ranking otherwise.

        We tried strict `must_contain` filtering first; it made Open-i return
        zero acceptable hits for several queries because keyword presence in
        Open-i's snippet field is unreliable.
        """
        haystack_parts = [
            record.get("Problems", ""),
            (record.get("image") or {}).get("caption", ""),
        ]
        outcomes = record.get("Outcome") or []
        for o in outcomes:
            if isinstance(o, dict):
                haystack_parts.append(o.get("#text", ""))
        haystack = " ".join(haystack_parts).lower()
        return not any(bad.lower() in haystack for bad in self.avoid)


CASES = [
    CaseQuery(
        case_id="case_01_tension_ptx",
        query="tension pneumothorax",
        avoid=("post-pneumonectomy", "transplant"),
    ),
    CaseQuery(
        case_id="case_02_massive_htx",
        query="hemothorax chest radiograph",
        avoid=("mesothelioma",),
    ),
    CaseQuery(
        case_id="case_03_flail_chest",
        query="rib fracture blunt trauma",
        avoid=("non-accidental", "abuse", "pediatric"),
    ),
    CaseQuery(
        case_id="case_04_pulm_contusion",
        query="pulmonary contusion blunt trauma",
    ),
    CaseQuery(
        case_id="case_05_normal_polytrauma",
        query="normal chest radiograph",
        avoid=("abnormal", "consolidation", "effusion", "pneumonia", "mass"),
    ),
    CaseQuery(
        case_id="case_06_pediatric_id",
        query="pediatric chest X-ray",
        avoid=("non-accidental", "abuse"),
    ),
]


def search_openi(client: httpx.Client, q: CaseQuery, attempts: int = 3) -> list[dict]:
    """Search Open-i with retries — its API throws frequent read timeouts."""
    last_exc: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            r = client.get(
                f"{OPENI_BASE}/api/search",
                params={"query": q.query, "it": "xg", "n": q.candidate_n},
                timeout=httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0),
            )
            r.raise_for_status()
            return r.json().get("list", [])
        except (httpx.HTTPError, ValueError) as exc:
            last_exc = exc
            if attempt < attempts:
                time.sleep(2 * attempt)  # backoff
    raise RuntimeError(f"Open-i failed after {attempts} attempts: {last_exc}")


def pick_best(q: CaseQuery, candidates: list[dict]) -> dict | None:
    for rec in candidates:
        if q.is_acceptable(rec):
            return rec
    return None


MIN_IMAGE_BYTES = 5_000  # anything smaller is an error page or non-image


def download_image(
    client: httpx.Client,
    rec: dict,
    out_path: Path,
    attempts: int = 3,
) -> int:
    """Download an image with retries + content validation.

    Open-i's image CDN throws frequent server-disconnect errors and
    occasionally serves an HTML error page in response to image URLs.
    We retry on transport errors AND validate that the downloaded bytes
    parse as a real image before writing them to disk.
    """
    img_path = rec.get("imgLarge") or rec.get("imgThumbLarge") or rec.get("imgThumb")
    if not img_path:
        raise RuntimeError(f"No image path in record uid={rec.get('uid')}")
    url = OPENI_BASE + img_path
    last_exc: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            r = client.get(
                url,
                timeout=httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0),
            )
            r.raise_for_status()
            data = r.content
            if len(data) < MIN_IMAGE_BYTES:
                raise RuntimeError(
                    f"response too small ({len(data)}b), likely an error page"
                )
            # PIL must be able to identify the bytes as an image.
            Image.open(io.BytesIO(data)).verify()
            out_path.write_bytes(data)
            return len(data)
        except (httpx.HTTPError, OSError, UnidentifiedImageError, RuntimeError) as exc:
            last_exc = exc
            if attempt < attempts:
                time.sleep(2 * attempt)
    raise RuntimeError(f"Image download failed after {attempts} attempts: {last_exc}")


def main() -> int:
    ASSETS.mkdir(exist_ok=True)
    sources_path = ASSETS / "sources.json"

    sources: dict[str, dict] = {}
    if sources_path.exists():
        loaded = json.loads(sources_path.read_text())
        # Tolerate the legacy `{"sources": {...}}` envelope from earlier runs.
        if isinstance(loaded, dict) and "sources" in loaded and isinstance(
            loaded["sources"], dict
        ):
            sources = loaded["sources"]
            # Unwrap nested envelope if present (legacy bug).
            if "sources" in sources and isinstance(sources["sources"], dict):
                inner = sources.pop("sources")
                sources.update(inner)
        else:
            sources = loaded

    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    skipped: list[str] = []

    with httpx.Client(headers=headers, follow_redirects=True) as client:
        for q in CASES:
            out_jpg = ASSETS / f"{q.case_id}.jpg"
            if out_jpg.exists() and sources.get(q.case_id):
                print(f"[skip] {q.case_id}: already have {out_jpg.name}")
                continue

            print(f"[search] {q.case_id}: {q.query!r}")
            try:
                candidates = search_openi(client, q)
            except (httpx.HTTPError, RuntimeError) as exc:
                print(f"  search failed: {exc}", file=sys.stderr)
                skipped.append(q.case_id)
                continue

            # Walk candidates in ranked order until one downloads cleanly.
            picked: dict | None = None
            size: int = 0
            for cand in candidates:
                if not q.is_acceptable(cand):
                    continue
                try:
                    size = download_image(client, cand, out_jpg)
                    picked = cand
                    break
                except (httpx.HTTPError, OSError, RuntimeError) as exc:
                    uid = cand.get("uid")
                    print(
                        f"  candidate {uid} download failed: {exc} — trying next",
                        file=sys.stderr,
                    )
                    continue

            if picked is None:
                print(
                    f"  no acceptable+downloadable match in top {len(candidates)}; skipping"
                )
                skipped.append(q.case_id)
                continue

            uid = picked.get("uid")
            title = (picked.get("title") or "").strip()
            caption = (picked.get("image") or {}).get("caption", "").strip()
            pmc_url = picked.get("pmc_url") or ""

            sources[q.case_id] = {
                "case_id": q.case_id,
                "filename": out_jpg.name,
                "openi_uid": uid,
                "title": title,
                "caption": caption,
                "pmc_url": pmc_url,
                "openi_query": q.query,
                "fetched_at": time.strftime("%Y-%m-%d", time.gmtime()),
                "license_note": (
                    "Sourced via NIH Open-i (https://openi.nlm.nih.gov). "
                    "License is the parent PMC article's — most are CC BY; "
                    "verify before public redistribution."
                ),
            }
            print(f"  OK ({size:,} bytes) — {title[:60]}")

    sources_path.write_text(json.dumps({"sources": sources}, indent=2))
    print(f"\nWrote {sources_path}")
    if skipped:
        print(f"Skipped (need manual sourcing): {', '.join(skipped)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
