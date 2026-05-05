"""Drafter pipeline step: produce a `TriageOutput` from image + vitals + retrieved chunks."""

from __future__ import annotations

from pydantic import ValidationError

from ats.inference.client import InferenceClient, build_image_message
from ats.prompts.drafter import get_drafter_system
from ats.schema import TriageOutput

MAX_QUOTE_CHARS = 400


class DrafterValidationError(RuntimeError):
    """Raised when the model output cannot be validated as `TriageOutput` after retry."""

    def __init__(self, message: str, raw_output: str) -> None:
        super().__init__(message)
        self.raw_output = raw_output


def _format_retrieved(chunks: list[dict]) -> str:
    """Render retrieved chunks into a compact, citation-tagged block for the prompt."""
    if not chunks:
        return "(none — proceed using your training; do not invent citations.)"
    lines: list[str] = []
    for c in chunks:
        quote = (c.get("text") or "").strip().replace("\n", " ")
        if len(quote) > MAX_QUOTE_CHARS:
            quote = quote[: MAX_QUOTE_CHARS - 1].rstrip() + "…"
        lines.append(
            f"[{c['id']}] {c['source']} — {c['section']}: \"{quote}\""
        )
    return "\n".join(lines)


def _build_messages(
    image_b64: str,
    vitals_text: str,
    retrieved_chunks: list[dict],
    lang: str,
) -> list[dict]:
    """Build the chat-completion messages for the drafter call."""
    system = get_drafter_system("id" if lang == "id" else "en")
    retrieved_block = _format_retrieved(retrieved_chunks)

    user_content = [
        build_image_message(image_b64),
        {
            "type": "text",
            "text": (
                "Vitals and clinical vignette:\n"
                f"{vitals_text.strip()}\n\n"
                "Retrieved guideline excerpts:\n"
                f"{retrieved_block}\n\n"
                "Produce the TriageOutput JSON now."
            ),
        },
    ]

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_content},
    ]


def draft(
    client: InferenceClient,
    image_b64: str,
    vitals_text: str,
    retrieved_chunks: list[dict],
    lang: str,
    case_id: str,
) -> TriageOutput:
    """Run the drafter pass and return a validated `TriageOutput`.

    Retries once on validation failure with a follow-up message embedding
    the validation error. Raises `DrafterValidationError` after the retry.
    """
    messages = _build_messages(image_b64, vitals_text, retrieved_chunks, lang)
    raw = client.generate(messages, response_schema=TriageOutput)

    try:
        result = TriageOutput.model_validate_json(raw)
    except ValidationError as first_err:
        # Retry once with the error fed back to the model.
        retry_messages = messages + [
            {"role": "assistant", "content": raw},
            {
                "role": "user",
                "content": (
                    "The previous JSON failed schema validation with these errors:\n\n"
                    f"{first_err}\n\n"
                    "Return a corrected TriageOutput JSON that conforms to the schema. "
                    "JSON only, no commentary."
                ),
            },
        ]
        raw = client.generate(retry_messages, response_schema=TriageOutput)
        try:
            result = TriageOutput.model_validate_json(raw)
        except ValidationError as second_err:
            raise DrafterValidationError(
                f"Drafter output failed schema validation twice: {second_err}",
                raw_output=raw,
            ) from second_err

    # Pin the case_id from the caller, regardless of what the model wrote.
    result.case_id = case_id
    return result
