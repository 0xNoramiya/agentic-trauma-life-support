"""Top-k retrieval over the FAISS corpus index.

The index and embedder are loaded lazily on first `retrieve(...)` call so
that mock-mode UI startup stays fast. If the index file does not exist,
`retrieve` returns an empty list and logs a warning — the rest of the
pipeline degrades gracefully.
"""

from __future__ import annotations

import logging
from typing import Optional

import faiss

from ats.config import settings
from ats.retrieval.embed import Embedder
from ats.retrieval.index import load_index

logger = logging.getLogger(__name__)

_INDEX: Optional[faiss.Index] = None
_META: Optional[list[dict]] = None
_EMBEDDER: Optional[Embedder] = None
_LOAD_ATTEMPTED = False


def _get_index() -> tuple[Optional[faiss.Index], Optional[list[dict]], Optional[Embedder]]:
    """Lazy-load and cache the FAISS index, metadata, and embedder."""
    global _INDEX, _META, _EMBEDDER, _LOAD_ATTEMPTED

    if _LOAD_ATTEMPTED:
        return _INDEX, _META, _EMBEDDER

    _LOAD_ATTEMPTED = True

    index_path = settings.corpus_index_path
    meta_path = settings.corpus_meta_path

    if not index_path.exists() or not meta_path.exists():
        logger.warning(
            "Corpus index not found at %s / %s. Retrieval will return no chunks. "
            "Run scripts/build_index.py to build it.",
            index_path,
            meta_path,
        )
        return None, None, None

    try:
        index, meta = load_index(index_path, meta_path)
    except (OSError, RuntimeError) as exc:
        logger.warning("Failed to load corpus index: %s", exc)
        return None, None, None

    _INDEX = index
    _META = meta
    _EMBEDDER = Embedder()
    return _INDEX, _META, _EMBEDDER


def retrieve(query: str, k: int = 5) -> list[dict]:
    """Return the top-k retrieved chunks for the query.

    Each entry: {id, text, source, section, url, score}. If the index is
    not available, returns [].
    """
    if not query or not query.strip():
        return []

    index, meta, embedder = _get_index()
    if index is None or meta is None or embedder is None:
        return []

    vec = embedder.encode([query])
    if vec.shape[0] == 0:
        return []

    k_eff = min(k, len(meta))
    if k_eff == 0:
        return []

    scores, indices = index.search(vec, k_eff)

    results: list[dict] = []
    for score, idx in zip(scores[0].tolist(), indices[0].tolist()):
        if idx < 0 or idx >= len(meta):
            continue
        row = meta[idx]
        results.append(
            {
                "id": row["id"],
                "text": row["text"],
                "source": row["source"],
                "section": row["section"],
                "url": row.get("url"),
                "score": float(score),
            }
        )
    return results
