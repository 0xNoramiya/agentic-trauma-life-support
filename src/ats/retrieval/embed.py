"""Wrapper around sentence-transformers for L2-normalized embeddings.

`BAAI/bge-m3` produces 1024-dim multilingual embeddings, which is what we
use as the FAISS index dimension.
"""

from __future__ import annotations

import numpy as np

from ats.config import settings


class Embedder:
    """Lazy-loaded sentence-transformers wrapper.

    The model is large (~2.3 GB) and slow to import, so we defer loading
    until the first `encode` call. This keeps `python -m ats.ui.app` import
    fast in mock mode, where retrieval may never run.
    """

    EMBED_DIM = 1024  # BAAI/bge-m3

    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or settings.embed_model
        self._model = None

    def _load(self):
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(self.model_name)
        return self._model

    def encode(self, texts: list[str]) -> np.ndarray:
        """Encode a list of strings to L2-normalized float32 vectors."""
        if not texts:
            return np.zeros((0, self.EMBED_DIM), dtype=np.float32)
        model = self._model if self._model is not None else self._load()
        vecs = model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return vecs.astype(np.float32, copy=False)
