"""End-to-end pipeline tests in mock mode.

Drives `run_triage` through the same code path the Gradio UI uses, with
the mock-mode `InferenceClient` substituting fixture content for both the
drafter and verifier responses. Verifies that EN and ID renderers produce
non-trivial handoffs and that retrieval degrades gracefully when no index
exists.

Tests force `mock_mode=True` via a fresh Settings instance so they pass
regardless of what `.env` says — useful when local `.env` is pointed at
a real droplet.
"""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from PIL import Image

from ats.config import Settings
from ats.inference.client import InferenceClient
from ats.pipeline.run import run_triage


@pytest.fixture(scope="module")
def mock_settings() -> Settings:
    # Build settings ignoring `.env` so tests are reproducible in any local config.
    return Settings(_env_file=None, mock_mode=True)


@pytest.fixture(scope="module")
def mock_client(mock_settings: Settings) -> InferenceClient:
    return InferenceClient(mock_settings)


@pytest.fixture(scope="module")
def synthetic_jpeg_bytes() -> bytes:
    img = Image.new("L", (256, 256), 30)
    buf = io.BytesIO()
    img.save(buf, "JPEG")
    return buf.getvalue()


def test_run_triage_en_returns_full_payload(
    mock_client: InferenceClient, synthetic_jpeg_bytes: bytes
):
    res = run_triage(
        client=mock_client,
        image_bytes=synthetic_jpeg_bytes,
        vitals_text="30M motorbike, RR 32 sat 88 BP 92/60",
        lang="en",
        case_id="t_en",
    )

    assert set(res.keys()) == {"json", "handoff", "retrieved_count"}
    # Mock mode short-circuits to the fixture; case_id is pinned by the pipeline.
    assert res["json"]["case_id"] == "t_en"
    # English renderer has SBAR-style headers.
    for header in ("Situation", "Background", "Imaging findings", "Disposition"):
        assert header in res["handoff"], f"missing header: {header}"
    assert len(res["handoff"]) > 500


def test_run_triage_id_uses_indonesian_headers(
    mock_client: InferenceClient, synthetic_jpeg_bytes: bytes
):
    res = run_triage(
        client=mock_client,
        image_bytes=synthetic_jpeg_bytes,
        vitals_text="anak 8 tahun, KLL motor",
        lang="id",
        case_id="t_id",
    )
    for header in ("Situasi", "Latar Belakang", "Temuan Pencitraan"):
        assert header in res["handoff"], f"missing ID header: {header}"
    assert res["json"]["case_id"] == "t_id"


def test_run_triage_no_verifier_skips_verifier_pass(
    mock_client: InferenceClient, synthetic_jpeg_bytes: bytes
):
    # Both with and without verifier should still return a renderable handoff.
    res = run_triage(
        client=mock_client,
        image_bytes=synthetic_jpeg_bytes,
        vitals_text="vitals here",
        lang="en",
        case_id="t_no_verify",
        use_verifier=False,
    )
    assert "Situation" in res["handoff"]


def test_run_triage_retrieved_count_zero_without_index(
    mock_client: InferenceClient,
    mock_settings: Settings,
    synthetic_jpeg_bytes: bytes,
):
    # No FAISS index built in the test environment; retrieval must return 0.
    assert not Path(mock_settings.corpus_index_path).exists(), (
        "Test assumes no FAISS index exists; remove it or run in a clean tree"
    )
    res = run_triage(
        client=mock_client,
        image_bytes=synthetic_jpeg_bytes,
        vitals_text="something",
        lang="en",
        case_id="t_retrieve",
    )
    assert res["retrieved_count"] == 0
