"""Drafter validation-retry tests with a controllable stub client.

These tests don't hit the real model. They construct a small stub that
returns canned strings so we can exercise: (a) clean validation, (b)
one bad output that triggers a retry then succeeds, (c) two bad outputs
in a row that raise `DrafterValidationError`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ats.pipeline.drafter import DrafterValidationError, draft

FIXTURES = Path(__file__).parent / "fixtures"


class _StubClient:
    """Returns the next canned response per call."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self.call_count = 0

    def generate(self, messages, response_schema=None, **kwargs):  # noqa: ARG002
        self.call_count += 1
        if not self._responses:
            raise RuntimeError("StubClient ran out of canned responses")
        return self._responses.pop(0)


def _good_json() -> str:
    return (FIXTURES / "sample_case.json").read_text(encoding="utf-8")


def test_drafter_clean_validation_no_retry():
    client = _StubClient([_good_json()])
    out = draft(
        client=client,
        image_b64="b64",
        vitals_text="vitals",
        retrieved_chunks=[],
        lang="en",
        case_id="case_x",
    )
    assert client.call_count == 1
    assert out.case_id == "case_x"  # case_id is pinned by the drafter, not the model


def test_drafter_retry_recovers_after_one_bad_output():
    bad_json = '{"case_id": "x", "patient_brief": {"age": "not-an-int"}}'  # invalid
    client = _StubClient([bad_json, _good_json()])
    out = draft(
        client=client,
        image_b64="b64",
        vitals_text="vitals",
        retrieved_chunks=[],
        lang="en",
        case_id="case_y",
    )
    assert client.call_count == 2
    assert out.case_id == "case_y"


def test_drafter_raises_after_two_bad_outputs():
    bad1 = '{"case_id": "z"}'  # missing required fields
    bad2 = "not-even-json"
    client = _StubClient([bad1, bad2])
    with pytest.raises(DrafterValidationError) as exc:
        draft(
            client=client,
            image_b64="b64",
            vitals_text="vitals",
            retrieved_chunks=[],
            lang="en",
            case_id="case_z",
        )
    # The exception carries the last raw output for debugging.
    assert exc.value.raw_output == bad2
    assert client.call_count == 2


def test_drafter_pins_case_id_overriding_model():
    """The model may emit any case_id; the drafter overrides it with the caller's."""
    out = draft(
        client=_StubClient([_good_json()]),
        image_b64="b64",
        vitals_text="vitals",
        retrieved_chunks=[],
        lang="en",
        case_id="caller_pinned",
    )
    assert out.case_id == "caller_pinned"
