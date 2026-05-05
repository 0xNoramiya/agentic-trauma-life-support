"""Tests for the retrieval module's graceful-fallback behavior.

The retrieval module is best-effort: if the FAISS index doesn't exist,
or if the query is empty, it must return [] without raising — the rest
of the pipeline falls back to "(no citations available)".

These tests force-point the settings at non-existent index paths so they
pass whether or not the local environment has actually built an index.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import ats.retrieval.retrieve as retrieve_module
from ats.retrieval.retrieve import retrieve


@pytest.fixture(autouse=True)
def reset_retrieval_module_state(monkeypatch, tmp_path: Path):
    """Clear cached state and force the index paths to non-existent locations.

    The retrieval module caches at module-level after first call AND reads
    the global `settings` for the index path. Tests need a clean slate AND
    paths that definitely don't exist.
    """
    monkeypatch.setattr(retrieve_module, "_INDEX", None)
    monkeypatch.setattr(retrieve_module, "_META", None)
    monkeypatch.setattr(retrieve_module, "_EMBEDDER", None)
    monkeypatch.setattr(retrieve_module, "_LOAD_ATTEMPTED", False)
    # Point at tmp_path entries that we never create -> os.exists() is False.
    monkeypatch.setattr(
        retrieve_module.settings, "corpus_index_path", tmp_path / "missing.faiss"
    )
    monkeypatch.setattr(
        retrieve_module.settings, "corpus_meta_path", tmp_path / "missing.jsonl"
    )


def test_empty_query_returns_empty():
    assert retrieve("") == []
    assert retrieve("   ") == []


def test_missing_index_returns_empty_does_not_raise():
    # Index paths point at non-existent files (per the autouse fixture);
    # function should log a warning and return [].
    result = retrieve("tension pneumothorax")
    assert result == []


def test_load_attempt_is_cached():
    """The lazy-loader should set _LOAD_ATTEMPTED to True after one try."""
    assert retrieve_module._LOAD_ATTEMPTED is False
    retrieve("anything")
    assert retrieve_module._LOAD_ATTEMPTED is True
    # Subsequent call must not re-trigger the load attempt.
    retrieve("anything else")
    assert retrieve_module._LOAD_ATTEMPTED is True
