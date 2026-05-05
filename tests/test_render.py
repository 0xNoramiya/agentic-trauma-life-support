"""Tests for the English and Indonesian SBAR renderers."""

from __future__ import annotations

from pathlib import Path

from ats.render.handoff_en import render_en
from ats.render.handoff_id import render_id
from ats.schema import TriageOutput

FIXTURES = Path(__file__).parent / "fixtures"


def _load_sample() -> TriageOutput:
    raw = (FIXTURES / "sample_case.json").read_text(encoding="utf-8")
    return TriageOutput.model_validate_json(raw)


def test_render_en_has_expected_sections():
    draft = _load_sample()
    md = render_en(draft)
    assert md.strip(), "render_en returned empty markdown"
    for section in (
        "# ATLS Primary Survey",
        "## Situation",
        "## Background",
        "## Imaging findings",
        "## Red flags",
        "## Recommended actions",
        "## Citations",
        "## Model metadata",
    ):
        assert section in md, f"missing section header: {section}"
    # Red flag glyph is load-bearing.
    assert "⚠" in md
    # Citation id from the fixture should round-trip.
    assert "atls-c1-001" in md or "east-ptx-002" in md


def test_render_id_has_indonesian_section_headers():
    draft = _load_sample()
    md = render_id(draft)
    assert md.strip(), "render_id returned empty markdown"
    for section in (
        "# Survei Primer ATLS",
        "## Situasi",
        "## Latar Belakang",
        "## Temuan Pencitraan",
        "## Tanda Bahaya",
        "## Tindakan yang Direkomendasikan",
        "## Sitasi",
        "## Metadata Model",
    ):
        assert section in md, f"missing section header: {section}"
    # Enum values stay in English regardless of language.
    assert "critical" in md
    assert "immediate" in md
