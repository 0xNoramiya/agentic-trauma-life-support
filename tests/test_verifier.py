"""Unit tests for the verifier patch-application logic.

We do not call the model here — we construct `VerifierOutput` directly and
exercise `apply_patches` against the bad-case fixture.
"""

from __future__ import annotations

from pathlib import Path

from ats.pipeline.verifier import _parse_path, apply_patches
from ats.schema import Patch, TriageOutput

FIXTURES = Path(__file__).parent / "fixtures"


def _load_bad() -> TriageOutput:
    raw = (FIXTURES / "bad_case.json").read_text(encoding="utf-8")
    return TriageOutput.model_validate_json(raw)


def test_parse_path_handles_index_segments():
    tokens = _parse_path("primary_survey.B_breathing.imaging_findings[0].laterality")
    assert tokens == ["primary_survey", "B_breathing", "imaging_findings", 0, "laterality"]


def test_parse_path_no_index():
    tokens = _parse_path("disposition.priority")
    assert tokens == ["disposition", "priority"]


def test_apply_patch_to_imaging_finding_laterality():
    draft = _load_bad()
    assert draft.primary_survey.B_breathing.imaging_findings[0].laterality == "n/a"

    patches = [
        Patch(
            path="primary_survey.B_breathing.imaging_findings[0].laterality",
            value="right",
        )
    ]
    patched = apply_patches(draft, patches)

    assert patched.primary_survey.B_breathing.imaging_findings[0].laterality == "right"
    # Original draft must be untouched (deep copy in apply_patches).
    assert draft.primary_survey.B_breathing.imaging_findings[0].laterality == "n/a"


def test_apply_patch_to_top_level_enum():
    draft = _load_bad()
    patches = [Patch(path="disposition.priority", value="urgent")]
    patched = apply_patches(draft, patches)
    assert patched.disposition.priority == "urgent"


def test_apply_patch_to_concern_level_then_revalidates():
    draft = _load_bad()
    patches = [
        Patch(path="primary_survey.C_circulation.concern_level", value="moderate"),
    ]
    patched = apply_patches(draft, patches)
    # apply_patches re-validates by round-tripping through model_dump/model_validate.
    assert patched.primary_survey.C_circulation.concern_level == "moderate"


def test_invalid_path_is_skipped_not_fatal():
    draft = _load_bad()
    patches = [
        Patch(path="primary_survey.does_not_exist.foo", value="x"),
        Patch(path="disposition.priority", value="urgent"),
    ]
    patched = apply_patches(draft, patches)
    # The bad path is ignored, the good path is applied.
    assert patched.disposition.priority == "urgent"
