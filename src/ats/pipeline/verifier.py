"""Verifier pipeline step: review the draft and apply field-level patches.

The verifier is the same model in clinical-safety-reviewer mode. It is shown
the original X-ray and the draft JSON, and returns a `VerifierOutput` with
notes and patches. Patches are applied to a deep copy of the draft via a
small in-file path-walker that handles dot-and-bracket notation, e.g.
`primary_survey.B_breathing.imaging_findings[0].laterality`.
"""

from __future__ import annotations

import copy
import logging
import re
from typing import Any

from pydantic import ValidationError

from ats.inference.client import InferenceClient, build_image_message
from ats.prompts.verifier import VERIFIER_SYSTEM, get_verifier_prompt
from ats.schema import TriageOutput, VerifierOutput

logger = logging.getLogger(__name__)

# Tokenize a path like "primary_survey.B_breathing.imaging_findings[0].laterality"
# into ["primary_survey", "B_breathing", "imaging_findings", 0, "laterality"].
_TOKEN_RE = re.compile(r"([^.\[\]]+)|\[(\d+)\]")


def _parse_path(path: str) -> list[str | int]:
    """Parse a dot-and-bracket path into a list of attribute / index tokens."""
    tokens: list[str | int] = []
    for match in _TOKEN_RE.finditer(path):
        name, idx = match.group(1), match.group(2)
        if name is not None:
            tokens.append(name)
        elif idx is not None:
            tokens.append(int(idx))
    if not tokens:
        raise ValueError(f"Could not parse patch path: {path!r}")
    return tokens


def _set_at_path(root: Any, path: str, value: Any) -> None:
    """Walk `path` on `root` and set the leaf to `value`.

    Supports attribute access on Pydantic models and indexed access on lists.
    """
    tokens = _parse_path(path)
    target = root
    for tok in tokens[:-1]:
        if isinstance(tok, int):
            target = target[tok]
        else:
            target = getattr(target, tok)

    leaf = tokens[-1]
    if isinstance(leaf, int):
        target[leaf] = value
    else:
        setattr(target, leaf, value)


def apply_patches(draft: TriageOutput, patches: list) -> TriageOutput:
    """Apply a list of `Patch` objects to a deep copy of `draft`."""
    patched = copy.deepcopy(draft)
    for p in patches:
        path = p.path if hasattr(p, "path") else p["path"]
        value = p.value if hasattr(p, "value") else p["value"]
        try:
            _set_at_path(patched, path, value)
        except (AttributeError, IndexError, KeyError, ValueError) as exc:
            logger.warning("Skipping invalid verifier patch %r: %s", path, exc)
            continue
    # Re-validate by round-tripping; this catches enum violations introduced by
    # the patches and surfaces them early.
    return TriageOutput.model_validate(patched.model_dump())


def verify(
    client: InferenceClient,
    draft: TriageOutput,
    image_b64: str,
) -> TriageOutput:
    """Run the verifier and return the patched draft.

    On any verifier-side error (model failure, parse error, validation error
    after patching), this function logs the issue and returns the original
    draft unchanged — the verifier is best-effort safety, not a hard gate.
    """
    user_content = [
        build_image_message(image_b64),
        {"type": "text", "text": get_verifier_prompt(draft)},
    ]
    messages = [
        {"role": "system", "content": VERIFIER_SYSTEM},
        {"role": "user", "content": user_content},
    ]

    try:
        raw = client.generate(messages, response_schema=VerifierOutput)
        verifier_out = VerifierOutput.model_validate_json(raw)
    except (ValidationError, ValueError) as exc:
        logger.warning("Verifier output could not be parsed; returning draft unchanged: %s", exc)
        return draft

    try:
        patched = apply_patches(draft, verifier_out.patches)
    except ValidationError as exc:
        logger.warning(
            "Verifier patches produced an invalid TriageOutput; returning draft unchanged: %s",
            exc,
        )
        return draft

    if verifier_out.verifier_notes:
        patched.model_metadata.verifier_notes = (
            list(patched.model_metadata.verifier_notes) + list(verifier_out.verifier_notes)
        )
    return patched
