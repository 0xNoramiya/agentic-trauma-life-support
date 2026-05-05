"""English SBAR-style markdown renderer for `TriageOutput`."""

from __future__ import annotations

from ats.schema import (
    AirwayAssessment,
    BreathingAssessment,
    CirculationAssessment,
    DisabilityAssessment,
    ExposureAssessment,
    TriageOutput,
)

_CONCERN_RANK = {"low": 0, "moderate": 1, "high": 2, "critical": 3}


def _highest_concern(draft: TriageOutput) -> str:
    levels = [
        draft.primary_survey.A_airway.concern_level,
        draft.primary_survey.B_breathing.concern_level,
        draft.primary_survey.C_circulation.concern_level,
        draft.primary_survey.D_disability.concern_level,
        draft.primary_survey.E_exposure.concern_level,
    ]
    return max(levels, key=lambda lv: _CONCERN_RANK.get(lv, 0))


def _fmt_actions(actions: list[str]) -> str:
    if not actions:
        return "no specific actions"
    return "; ".join(actions)


def _fmt_letter(label: str, assessment) -> str:
    extras: list[str] = []
    if isinstance(assessment, BreathingAssessment):
        if assessment.rr is not None:
            extras.append(f"RR {assessment.rr}")
        if assessment.spo2 is not None:
            extras.append(f"SpO2 {assessment.spo2}%")
    elif isinstance(assessment, CirculationAssessment):
        if assessment.hr is not None:
            extras.append(f"HR {assessment.hr}")
        if assessment.sbp is not None and assessment.dbp is not None:
            extras.append(f"BP {assessment.sbp}/{assessment.dbp}")
    elif isinstance(assessment, DisabilityAssessment):
        if assessment.gcs is not None:
            extras.append(f"GCS {assessment.gcs}")
    elif isinstance(assessment, ExposureAssessment):
        if assessment.temp is not None:
            extras.append(f"Temp {assessment.temp}°C")
    elif isinstance(assessment, AirwayAssessment):
        pass  # no scalar vitals on airway

    extra_str = f" ({', '.join(extras)})" if extras else ""
    return (
        f"- **{label}**: {assessment.concern_level}{extra_str} — "
        f"{_fmt_actions(assessment.actions_required)}"
    )


def render_en(draft: TriageOutput) -> str:
    """Render `draft` as an English SBAR-style markdown handoff."""
    pb = draft.patient_brief
    ps = draft.primary_survey
    md = draft.model_metadata

    lines: list[str] = []
    lines.append(f"# ATLS Primary Survey — Case {draft.case_id}")
    lines.append("")
    lines.append(f"**Patient:** {pb.age} {pb.sex}, {pb.mechanism}")
    lines.append("")

    # Situation
    lines.append("## Situation")
    lines.append(f"- Highest concern: **{_highest_concern(draft)}**")
    lines.append(f"- Disposition priority: **{draft.disposition.priority}**")
    lines.append(
        f"- Escalation: {draft.disposition.escalation.who} ({draft.disposition.escalation.when})"
    )
    lines.append("")

    # Background — ABCDE
    lines.append("## Background")
    lines.append(_fmt_letter("A (airway)", ps.A_airway))
    lines.append(_fmt_letter("B (breathing)", ps.B_breathing))
    lines.append(_fmt_letter("C (circulation)", ps.C_circulation))
    lines.append(_fmt_letter("D (disability)", ps.D_disability))
    lines.append(_fmt_letter("E (exposure)", ps.E_exposure))
    lines.append("")

    # Imaging findings (consolidated across ABCDE)
    lines.append("## Imaging findings")
    findings = (
        list(ps.A_airway.imaging_findings)
        + list(ps.B_breathing.imaging_findings)
        + list(ps.C_circulation.imaging_findings)
    )
    if findings:
        for f in findings:
            cite = f" [cite: {f.citation_id}]" if f.citation_id else ""
            lines.append(f"- {f.finding} ({f.laterality}, {f.severity}){cite}")
    else:
        lines.append("- No discrete imaging findings on this view.")
    lines.append("")

    # Red flags
    lines.append("## Red flags")
    if draft.red_flags:
        for rf in draft.red_flags:
            ev = "; ".join(rf.evidence) if rf.evidence else "no concrete evidence listed"
            lines.append(f"- ⚠ **{rf.flag}** — {rf.immediate_action} _(evidence: {ev})_")
    else:
        lines.append("- None")
    lines.append("")

    # Recommended actions
    lines.append("## Recommended actions")
    if draft.disposition.recommended_actions:
        for a in draft.disposition.recommended_actions:
            cite = f" [cite: {a.citation_id}]" if a.citation_id else ""
            lines.append(f"- ({a.urgency}) {a.action} — {a.rationale}{cite}")
    else:
        lines.append("- None listed.")

    if draft.disposition.additional_imaging:
        lines.append("")
        lines.append("**Additional imaging:** " + ", ".join(draft.disposition.additional_imaging))
    if draft.disposition.labs:
        lines.append("**Labs:** " + ", ".join(draft.disposition.labs))
    lines.append("")

    # Citations
    lines.append("## Citations")
    if draft.citations:
        for c in draft.citations:
            url = f" {c.url}" if c.url else ""
            lines.append(f'- [{c.id}] {c.source}, {c.section}: "{c.quote}"{url}')
    else:
        lines.append("- None")
    lines.append("")

    # Model metadata
    lines.append("## Model metadata")
    lines.append(f"- Model: {md.model}")
    lines.append(f"- Confidence: {md.confidence}")
    lines.append(f"- Limitations: {'; '.join(md.limitations)}")
    lines.append(f"- Disclaimer: {md.disclaimer}")
    if md.verifier_notes:
        lines.append("- Verifier notes:")
        for n in md.verifier_notes:
            lines.append(f"  - {n}")
    else:
        lines.append("- Verifier notes: (none)")

    return "\n".join(lines)
