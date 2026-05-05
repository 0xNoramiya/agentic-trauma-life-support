"""FAISS index build/load helpers.

We use `IndexFlatIP` (inner product) over L2-normalized embeddings, which
is equivalent to cosine similarity. Index and metadata are stored side by
side: a `.faiss` file plus a `.jsonl` of chunk metadata in the same row
order as the index.
"""

from __future__ import annotations

import json
from pathlib import Path

import faiss

from ats.retrieval.embed import Embedder


def build_index(
    chunks: list[dict],
    embedder: Embedder,
    out_path: Path,
    meta_path: Path,
) -> None:
    """Embed `chunks` and write a flat IP FAISS index plus a JSONL metadata file.

    Each chunk must contain at least: id, text, source, section, url.
    """
    if not chunks:
        raise ValueError("build_index called with no chunks")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.parent.mkdir(parents=True, exist_ok=True)

    texts = [c["text"] for c in chunks]
    vecs = embedder.encode(texts)

    if vecs.shape[0] != len(chunks):
        raise RuntimeError(
            f"Embedding count {vecs.shape[0]} does not match chunk count {len(chunks)}"
        )

    index = faiss.IndexFlatIP(vecs.shape[1])
    index.add(vecs)
    faiss.write_index(index, str(out_path))

    with meta_path.open("w", encoding="utf-8") as f:
        for c in chunks:
            row = {
                "id": c["id"],
                "text": c["text"],
                "source": c["source"],
                "section": c["section"],
                "url": c.get("url"),
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_index(path: Path, meta_path: Path) -> tuple[faiss.Index, list[dict]]:
    """Load a previously-built FAISS index and its JSONL metadata."""
    index = faiss.read_index(str(path))
    meta: list[dict] = []
    with meta_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            meta.append(json.loads(line))
    if index.ntotal != len(meta):
        raise RuntimeError(f"Index size {index.ntotal} does not match metadata length {len(meta)}")
    return index, meta
