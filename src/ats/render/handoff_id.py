"""Indonesian SBAR-style markdown renderer for `TriageOutput`.

Section headers and labels are translated. Narrative content fields
(`actions_required`, `flag`, `quote`, `limitations`, `disclaimer`, etc.) are
rendered as-is from the draft — they will already be in Indonesian when the
drafter ran with `lang="id"`. Enum values stay in English so the schema
validates.
"""

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
        return "tidak ada tindakan spesifik"
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
            extras.append(f"Nadi {assessment.hr}")
        if assessment.sbp is not None and assessment.dbp is not None:
            extras.append(f"TD {assessment.sbp}/{assessment.dbp}")
    elif isinstance(assessment, DisabilityAssessment):
        if assessment.gcs is not None:
            extras.append(f"GCS {assessment.gcs}")
    elif isinstance(assessment, ExposureAssessment):
        if assessment.temp is not None:
            extras.append(f"Suhu {assessment.temp}°C")
    elif isinstance(assessment, AirwayAssessment):
        pass

    extra_str = f" ({', '.join(extras)})" if extras else ""
    return (
        f"- **{label}**: {assessment.concern_level}{extra_str} — "
        f"{_fmt_actions(assessment.actions_required)}"
    )


def render_id(draft: TriageOutput) -> str:
    """Render `draft` as an Indonesian SBAR-style markdown handoff."""
    pb = draft.patient_brief
    ps = draft.primary_survey
    md = draft.model_metadata

    lines: list[str] = []
    lines.append(f"# Survei Primer ATLS — Kasus {draft.case_id}")
    lines.append("")
    lines.append(f"**Pasien:** {pb.age} {pb.sex}, {pb.mechanism}")
    lines.append("")

    # Situasi
    lines.append("## Situasi")
    lines.append(f"- Tingkat kekhawatiran tertinggi: **{_highest_concern(draft)}**")
    lines.append(f"- Prioritas disposisi: **{draft.disposition.priority}**")
    lines.append(
        f"- Eskalasi: {draft.disposition.escalation.who} ({draft.disposition.escalation.when})"
    )
    lines.append("")

    # Latar Belakang — ABCDE
    lines.append("## Latar Belakang")
    lines.append(_fmt_letter("A (jalan napas)", ps.A_airway))
    lines.append(_fmt_letter("B (pernapasan)", ps.B_breathing))
    lines.append(_fmt_letter("C (sirkulasi)", ps.C_circulation))
    lines.append(_fmt_letter("D (disabilitas)", ps.D_disability))
    lines.append(_fmt_letter("E (paparan)", ps.E_exposure))
    lines.append("")

    # Temuan Pencitraan
    lines.append("## Temuan Pencitraan")
    findings = (
        list(ps.A_airway.imaging_findings)
        + list(ps.B_breathing.imaging_findings)
        + list(ps.C_circulation.imaging_findings)
    )
    if findings:
        for f in findings:
            cite = f" [sitasi: {f.citation_id}]" if f.citation_id else ""
            lines.append(f"- {f.finding} ({f.laterality}, {f.severity}){cite}")
    else:
        lines.append("- Tidak ada temuan pencitraan yang menonjol pada proyeksi ini.")
    lines.append("")

    # Tanda Bahaya
    lines.append("## Tanda Bahaya")
    if draft.red_flags:
        for rf in draft.red_flags:
            ev = "; ".join(rf.evidence) if rf.evidence else "tidak ada bukti konkret yang dicatat"
            lines.append(f"- ⚠ **{rf.flag}** — {rf.immediate_action} _(bukti: {ev})_")
    else:
        lines.append("- Tidak ada")
    lines.append("")

    # Tindakan yang Direkomendasikan
    lines.append("## Tindakan yang Direkomendasikan")
    if draft.disposition.recommended_actions:
        for a in draft.disposition.recommended_actions:
            cite = f" [sitasi: {a.citation_id}]" if a.citation_id else ""
            lines.append(f"- ({a.urgency}) {a.action} — {a.rationale}{cite}")
    else:
        lines.append("- Tidak ada")

    if draft.disposition.additional_imaging:
        lines.append("")
        lines.append(
            "**Pencitraan tambahan:** " + ", ".join(draft.disposition.additional_imaging)
        )
    if draft.disposition.labs:
        lines.append("**Laboratorium:** " + ", ".join(draft.disposition.labs))
    lines.append("")

    # Sitasi
    lines.append("## Sitasi")
    if draft.citations:
        for c in draft.citations:
            url = f" {c.url}" if c.url else ""
            lines.append(f'- [{c.id}] {c.source}, {c.section}: "{c.quote}"{url}')
    else:
        lines.append("- Tidak ada")
    lines.append("")

    # Metadata Model
    lines.append("## Metadata Model")
    lines.append(f"- Model: {md.model}")
    lines.append(f"- Kepercayaan: {md.confidence}")
    lines.append(f"- Keterbatasan: {'; '.join(md.limitations)}")
    lines.append(f"- Disclaimer: {md.disclaimer}")
    if md.verifier_notes:
        lines.append("- Catatan verifier:")
        for n in md.verifier_notes:
            lines.append(f"  - {n}")
    else:
        lines.append("- Catatan verifier: (tidak ada)")

    return "\n".join(lines)
