"""Pydantic v2 schema for the ATLS primary-survey output.

This is the contract the Drafter writes to via vLLM guided JSON decoding.
`TriageOutput.model_json_schema()` is fed directly to the server as the
`guided_json` constraint, so every `Field(description=...)` here doubles as
a hint to the model.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

ConcernLevel = Literal["low", "moderate", "high", "critical"]
Severity = Literal["mild", "moderate", "severe"]
Laterality = Literal["left", "right", "bilateral", "midline", "n/a"]
Priority = Literal["immediate", "urgent", "delayed", "expectant"]
Urgency = Literal["now", "<5min", "<15min", "<1hr"]
Confidence = Literal["high", "moderate", "low"]
Sex = Literal["M", "F"]


class PatientBrief(BaseModel):
    """Three-line patient summary at the top of the output."""

    age: int = Field(..., description="Patient age in years.", ge=0, le=120)
    sex: Sex = Field(..., description="Biological sex: 'M' or 'F'.")
    mechanism: str = Field(
        ...,
        description="Mechanism of injury, one short clause (e.g. 'motorbike vs car, ejected').",
    )


class ImagingFinding(BaseModel):
    """One finding extracted from the chest X-ray."""

    finding: str = Field(..., description="Concise finding, e.g. 'tension pneumothorax'.")
    laterality: Laterality = Field(
        ...,
        description="Side of the finding. Use 'n/a' for findings without a side.",
    )
    severity: Severity = Field(..., description="Clinical severity: mild / moderate / severe.")
    citation_id: str | None = Field(
        default=None,
        description="ID of a retrieved guideline chunk that supports interpreting this finding.",
    )


class AirwayAssessment(BaseModel):
    """A — Airway."""

    concern_level: ConcernLevel = Field(..., description="Overall concern for airway.")
    imaging_findings: list[ImagingFinding] = Field(
        default_factory=list,
        description="Imaging findings relevant to airway (e.g. tracheal deviation).",
    )
    actions_required: list[str] = Field(
        default_factory=list,
        description="Concrete airway actions in order of urgency.",
    )


class BreathingAssessment(BaseModel):
    """B — Breathing and ventilation."""

    concern_level: ConcernLevel = Field(..., description="Overall concern for breathing.")
    rr: int | None = Field(default=None, description="Respiratory rate (breaths per minute).")
    spo2: int | None = Field(default=None, description="Pulse oximetry, percent.")
    imaging_findings: list[ImagingFinding] = Field(
        default_factory=list,
        description="Imaging findings relevant to breathing (pneumothorax, hemothorax, etc.).",
    )
    actions_required: list[str] = Field(
        default_factory=list,
        description="Breathing actions, e.g. needle decompression, chest tube, supplemental O2.",
    )


class CirculationAssessment(BaseModel):
    """C — Circulation with hemorrhage control."""

    concern_level: ConcernLevel = Field(..., description="Overall concern for circulation.")
    hr: int | None = Field(default=None, description="Heart rate (beats per minute).")
    sbp: int | None = Field(default=None, description="Systolic blood pressure (mmHg).")
    dbp: int | None = Field(default=None, description="Diastolic blood pressure (mmHg).")
    imaging_findings: list[ImagingFinding] = Field(
        default_factory=list,
        description="Imaging findings relevant to circulation (widened mediastinum, etc.).",
    )
    actions_required: list[str] = Field(
        default_factory=list,
        description="Circulation actions, e.g. large-bore IV, blood, TXA, FAST.",
    )


class DisabilityAssessment(BaseModel):
    """D — Disability (neurological)."""

    concern_level: ConcernLevel = Field(..., description="Overall concern for disability.")
    gcs: int | None = Field(default=None, description="Glasgow Coma Scale (3-15).")
    actions_required: list[str] = Field(
        default_factory=list,
        description="Disability actions, e.g. CT head, neurosurgical consult.",
    )


class ExposureAssessment(BaseModel):
    """E — Exposure / environmental control."""

    concern_level: ConcernLevel = Field(..., description="Overall concern for exposure.")
    temp: float | None = Field(default=None, description="Temperature in degrees Celsius.")
    actions_required: list[str] = Field(
        default_factory=list,
        description="Exposure actions, e.g. warming blankets, log-roll, full skin survey.",
    )


class PrimarySurvey(BaseModel):
    """The five ABCDE assessments."""

    A_airway: AirwayAssessment = Field(..., description="Airway assessment.")
    B_breathing: BreathingAssessment = Field(..., description="Breathing assessment.")
    C_circulation: CirculationAssessment = Field(..., description="Circulation assessment.")
    D_disability: DisabilityAssessment = Field(..., description="Disability assessment.")
    E_exposure: ExposureAssessment = Field(..., description="Exposure assessment.")


class RecommendedAction(BaseModel):
    """One recommended action with rationale and a target time."""

    action: str = Field(..., description="The action, imperative (e.g. 'place 14G left chest').")
    rationale: str = Field(..., description="One-line justification rooted in the findings.")
    urgency: Urgency = Field(..., description="Target window: now / <5min / <15min / <1hr.")
    citation_id: str | None = Field(
        default=None, description="ID of a retrieved guideline chunk supporting this action."
    )


class Escalation(BaseModel):
    """Whom to call and how soon."""

    who: str = Field(
        ..., description="Service or role to escalate to, e.g. 'trauma surgery attending'."
    )
    when: Urgency = Field(..., description="Target window for the escalation call.")


class Disposition(BaseModel):
    """Where the patient goes next and what they need on the way."""

    priority: Priority = Field(
        ..., description="Triage priority: immediate / urgent / delayed / expectant."
    )
    recommended_actions: list[RecommendedAction] = Field(
        default_factory=list, description="Ordered list of recommended next actions."
    )
    escalation: Escalation = Field(..., description="Escalation target and timing.")
    additional_imaging: list[str] = Field(
        default_factory=list,
        description="Imaging studies that should be ordered next (e.g. CT chest, FAST).",
    )
    labs: list[str] = Field(
        default_factory=list,
        description="Labs to send (e.g. type and screen, lactate, ABG, troponin).",
    )


class RedFlag(BaseModel):
    """An urgent finding or pattern that requires an immediate response."""

    flag: str = Field(..., description="The red flag, e.g. 'tension physiology'.")
    evidence: list[str] = Field(
        default_factory=list,
        description="Concrete evidence (vitals, imaging features) backing the flag.",
    )
    immediate_action: str = Field(..., description="The immediate response to take.")


class Citation(BaseModel):
    """A retrieved guideline chunk that the model relied on."""

    id: str = Field(..., description="Citation ID matching the retrieved chunk id.")
    source: str = Field(..., description="Source, e.g. 'EAST PMG'.")
    section: str = Field(..., description="Section or page, e.g. 'page 12'.")
    quote: str = Field(..., description="Direct quote, trimmed.")
    url: str | None = Field(default=None, description="URL to the original source if available.")


class ModelMetadata(BaseModel):
    """Provenance and self-reported limitations for the run."""

    model: str = Field(..., description="Model identifier used.")
    confidence: Confidence = Field(..., description="Self-rated confidence: high/moderate/low.")
    limitations: list[str] = Field(
        ...,
        description=(
            "Concrete limitations of this run. Must be non-empty: the model is required to "
            "name at least one realistic limitation (e.g. 'single AP view, no lateral')."
        ),
    )
    disclaimer: str = Field(
        ...,
        description="Plain-language disclaimer, e.g. 'Decision support only. Not a diagnosis.'",
    )
    verifier_notes: list[str] = Field(
        default_factory=list,
        description="Notes appended by the verifier pass.",
    )

    @field_validator("limitations")
    @classmethod
    def _limitations_non_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("model_metadata.limitations must not be empty")
        return v


class TriageOutput(BaseModel):
    """Top-level output of the ATLS pipeline."""

    case_id: str = Field(..., description="Stable case identifier.")
    patient_brief: PatientBrief = Field(..., description="Patient summary.")
    primary_survey: PrimarySurvey = Field(..., description="ABCDE primary survey.")
    disposition: Disposition = Field(..., description="Disposition and recommended actions.")
    red_flags: list[RedFlag] = Field(
        default_factory=list, description="Red flags requiring immediate action."
    )
    citations: list[Citation] = Field(
        default_factory=list, description="Retrieved guideline chunks the model relied on."
    )
    model_metadata: ModelMetadata = Field(..., description="Provenance and self-reported limits.")


class Patch(BaseModel):
    """A single field-level patch produced by the verifier."""

    path: str = Field(
        ...,
        description=(
            "Dot-and-bracket path into TriageOutput, e.g. "
            "'primary_survey.B_breathing.imaging_findings[0].laterality'."
        ),
    )
    value: object = Field(..., description="Replacement value at the given path.")


class VerifierOutput(BaseModel):
    """Output of the verifier pass."""

    verifier_notes: list[str] = Field(
        default_factory=list,
        description="Plain-language notes from the verifier (one per concern).",
    )
    patches: list[Patch] = Field(
        default_factory=list,
        description="Field-level patches to apply to the draft.",
    )
