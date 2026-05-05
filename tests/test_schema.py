"""Schema-level round-trip and validation tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from ats.schema import TriageOutput

FIXTURES = Path(__file__).parent / "fixtures"


def test_sample_case_round_trips():
    raw = (FIXTURES / "sample_case.json").read_text(encoding="utf-8")
    parsed = TriageOutput.model_validate_json(raw)
    # Round-trip back to JSON and re-parse: should be stable.
    again = TriageOutput.model_validate_json(parsed.model_dump_json())
    assert again.case_id == parsed.case_id
    assert again.primary_survey.B_breathing.concern_level == "critical"
    assert len(again.citations) >= 1
    assert len(again.red_flags) >= 1
    assert len(again.disposition.recommended_actions) >= 1
    assert len(again.model_metadata.limitations) >= 1


def test_empty_limitations_rejected():
    raw = (FIXTURES / "sample_case.json").read_text(encoding="utf-8")
    data = json.loads(raw)
    data["model_metadata"]["limitations"] = []
    with pytest.raises(ValidationError) as excinfo:
        TriageOutput.model_validate(data)
    assert "limitations" in str(excinfo.value).lower()


def test_unknown_concern_level_rejected():
    raw = (FIXTURES / "sample_case.json").read_text(encoding="utf-8")
    data = json.loads(raw)
    data["primary_survey"]["A_airway"]["concern_level"] = "panic"
    with pytest.raises(ValidationError):
        TriageOutput.model_validate(data)


def test_bad_case_still_validates_as_schema():
    """The bad_case.json fixture is *clinically* inconsistent but *schematically* valid.

    Verifier behavior is what catches the inconsistencies — the schema itself
    cannot tell that 'pneumothorax with laterality n/a' is wrong.
    """
    raw = (FIXTURES / "bad_case.json").read_text(encoding="utf-8")
    parsed = TriageOutput.model_validate_json(raw)
    assert parsed.primary_survey.B_breathing.imaging_findings[0].laterality == "n/a"
