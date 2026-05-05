"""End-to-end triage pipeline: retrieve -> draft -> verify -> render."""

from __future__ import annotations

import base64
import logging
from typing import Any

from ats.inference.client import InferenceClient
from ats.pipeline.drafter import DrafterValidationError
from ats.pipeline.drafter import draft as drafter_draft
from ats.pipeline.verifier import verify as verifier_verify
from ats.render.handoff_en import render_en
from ats.render.handoff_id import render_id
from ats.retrieval.retrieve import retrieve
from ats.schema import (
    AirwayAssessment,
    BreathingAssessment,
    CirculationAssessment,
    DisabilityAssessment,
    Disposition,
    Escalation,
    ExposureAssessment,
    ModelMetadata,
    PatientBrief,
    PrimarySurvey,
    TriageOutput,
)

logger = logging.getLogger(__name__)


def run_triage(
    client: InferenceClient,
    image_bytes: bytes,
    vitals_text: str,
    lang: str = "en",
    case_id: str = "anon",
    use_verifier: bool = True,
) -> dict[str, Any]:
    """Run the full pipeline.

    Returns: {"json": <TriageOutput as plain JSON-serializable dict>,
              "handoff": <markdown string>,
              "retrieved_count": <int>}.

    On a drafter validation failure, returns a partial result with a useful
    handoff string and `model_metadata.limitations` populated.
    """
    image_b64 = base64.b64encode(image_bytes).decode("ascii")

    retrieved = retrieve(vitals_text, k=5)

    try:
        draft = drafter_draft(
            client=client,
            image_b64=image_b64,
            vitals_text=vitals_text,
            retrieved_chunks=retrieved,
            lang=lang,
            case_id=case_id,
        )
    except DrafterValidationError as exc:
        logger.error("Drafter failed validation: %s", exc)
        partial = _empty_triage_output(case_id, str(exc))
        return {
            "json": partial.model_dump(mode="json"),
            "handoff": f"Draft failed: {exc}",
            "retrieved_count": len(retrieved),
        }
    except Exception as exc:  # noqa: BLE001 - capture any inference failure
        logger.exception("Drafter raised an unexpected error")
        partial = _empty_triage_output(case_id, f"unexpected drafter error: {exc}")
        return {
            "json": partial.model_dump(mode="json"),
            "handoff": f"Draft failed: {exc}",
            "retrieved_count": len(retrieved),
        }

    if use_verifier:
        try:
            draft = verifier_verify(client=client, draft=draft, image_b64=image_b64)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Verifier raised; using unverified draft: %s", exc)

    handoff = render_id(draft) if lang == "id" else render_en(draft)

    return {
        "json": draft.model_dump(mode="json"),
        "handoff": handoff,
        "retrieved_count": len(retrieved),
    }


def _empty_triage_output(case_id: str, error_msg: str) -> TriageOutput:
    """Build a minimal valid `TriageOutput` shell when the drafter fails.

    This exists so the UI / downstream consumers always get a parseable
    object with the failure surfaced in `model_metadata.limitations`.
    """
    return TriageOutput(
        case_id=case_id,
        patient_brief=PatientBrief(age=0, sex="M", mechanism="unknown — draft failed"),
        primary_survey=PrimarySurvey(
            A_airway=AirwayAssessment(concern_level="low"),
            B_breathing=BreathingAssessment(concern_level="low"),
            C_circulation=CirculationAssessment(concern_level="low"),
            D_disability=DisabilityAssessment(concern_level="low"),
            E_exposure=ExposureAssessment(concern_level="low"),
        ),
        disposition=Disposition(
            priority="delayed",
            recommended_actions=[],
            escalation=Escalation(who="senior clinician", when="<5min"),
            additional_imaging=[],
            labs=[],
        ),
        red_flags=[],
        citations=[],
        model_metadata=ModelMetadata(
            model="(none — drafter failed)",
            confidence="low",
            limitations=[
                "Drafter did not produce a valid output.",
                f"Underlying error: {error_msg}",
            ],
            disclaimer="Decision support only. Not a diagnosis. Not for unsupervised clinical use.",
            verifier_notes=[],
        ),
    )
