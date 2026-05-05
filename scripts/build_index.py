"""Build the FAISS retrieval index from PDFs listed in a manifest.

Usage:
    python scripts/build_index.py
    python scripts/build_index.py --manifest path/to/manifest.json \
        --out-index .../index.faiss --out-meta .../meta.jsonl

If the manifest is missing, the script prints a friendly note and exits 0.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Make `import ats.*` work when running this script directly.
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from ats.config import settings  # noqa: E402
from ats.corpus.ingest import ingest_directory  # noqa: E402
from ats.retrieval.embed import Embedder  # noqa: E402
from ats.retrieval.index import build_index  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=REPO_ROOT / "src" / "ats" / "corpus" / "data" / "raw" / "manifest.json",
        help="Path to the manifest.json that lists PDFs to ingest.",
    )
    parser.add_argument(
        "--out-index",
        type=Path,
        default=settings.corpus_index_path,
        help="Output path for the FAISS index file.",
    )
    parser.add_argument(
        "--out-meta",
        type=Path,
        default=settings.corpus_meta_path,
        help="Output path for the JSONL metadata file.",
    )
    args = parser.parse_args()

    if not args.manifest.exists():
        print(
            f"No manifest at {args.manifest}.\n"
            "See src/ats/corpus/data/README.md for how to source PDFs and write a manifest.",
            file=sys.stderr,
        )
        return 0

    manifest_dir = args.manifest.parent
    print(f"Ingesting PDFs from {manifest_dir} ...", flush=True)
    chunks = ingest_directory(manifest_dir)
    if not chunks:
        print("Manifest produced 0 chunks. Aborting.", file=sys.stderr)
        return 1

    # Counts per source.
    counts: dict[str, int] = {}
    for c in chunks:
        counts[c["source"]] = counts.get(c["source"], 0) + 1
    print("Chunks per source:")
    for src, n in sorted(counts.items()):
        print(f"  {src}: {n}")
    print(f"Total chunks: {len(chunks)}")

    print("Embedding and building index ...", flush=True)
    embedder = Embedder()
    build_index(chunks, embedder, args.out_index, args.out_meta)
    print(f"Wrote {args.out_index}")
    print(f"Wrote {args.out_meta}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
