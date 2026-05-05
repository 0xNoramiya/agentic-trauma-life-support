"""Tests for the retrieval module's graceful-fallback behavior.

The retrieval module is best-effort: if the FAISS index doesn't exist,
or if the query is empty, it must return [] without raising — the rest
of the pipeline falls back to "(no citations available)".
"""

from __future__ import annotations

import pytest

import ats.retrieval.retrieve as retrieve_module
from ats.retrieval.retrieve import retrieve


@pytest.fixture(autouse=True)
def reset_retrieval_module_state(monkeypatch):
    """Clear cached index/embedder state between tests.

    The module caches at module-level after first call; tests need a clean
    slate so each one exercises the load path independently.
    """
    monkeypatch.setattr(retrieve_module, "_INDEX", None)
    monkeypatch.setattr(retrieve_module, "_META", None)
    monkeypatch.setattr(retrieve_module, "_EMBEDDER", None)
    monkeypatch.setattr(retrieve_module, "_LOAD_ATTEMPTED", False)


def test_empty_query_returns_empty():
    assert retrieve("") == []
    assert retrieve("   ") == []


def test_missing_index_returns_empty_does_not_raise():
    # No corpus index built in the test environment — function should
    # log a warning and return [].
    result = retrieve("tension pneumothorax")
    assert result == []


def test_load_attempt_is_cached(monkeypatch):
    """The lazy-loader should set _LOAD_ATTEMPTED to True after one try."""
    assert retrieve_module._LOAD_ATTEMPTED is False
    retrieve("anything")
    assert retrieve_module._LOAD_ATTEMPTED is True
    # Subsequent call must not re-trigger the load attempt.
    retrieve("anything else")
    assert retrieve_module._LOAD_ATTEMPTED is True
