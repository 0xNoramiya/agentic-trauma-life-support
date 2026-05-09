"""HF Spaces app for Agentic Trauma Life Support.

Lightweight Gradio UI that calls our own vLLM server (running on a single
AMD MI300X) via the OpenAI-compatible chat-completions API and renders the
structured ATLS primary-survey output. The Space and the production
serving path use the *same* Qwen2.5-VL-72B BF16 model — the Space is just
the clickable front door.

The schema, prompts, and renderers are vendored under `ats/` from the
main repo (see `sync_from_main.sh`).

Configuration (all via HF Space `Settings → Variables and secrets`):
  - VLLM_BASE_URL  (required) e.g. http://<droplet-public-ip>:8000/v1
  - VLLM_API_KEY   (default: "EMPTY") must match `--api-key` on the server
  - MODEL_ID       (default: Qwen/Qwen2.5-VL-72B-Instruct)
  - REQUEST_TIMEOUT (default: 180 seconds — 72B first-token can be slow)
"""

from __future__ import annotations

import base64
import copy
import io
import json
import os
import re
import sys
from pathlib import Path

import gradio as gr
import openai
from openai import OpenAI
from PIL import Image
from pydantic import ValidationError

# Ensure the vendored `ats/` package is importable.
THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

from ats.prompts.drafter import get_drafter_system  # noqa: E402
from ats.prompts.verifier import VERIFIER_SYSTEM, get_verifier_prompt  # noqa: E402
from ats.render.handoff_en import render_en  # noqa: E402
from ats.render.handoff_id import render_id  # noqa: E402
from ats.schema import TriageOutput, VerifierOutput  # noqa: E402

VLLM_BASE_URL = os.environ.get("VLLM_BASE_URL", "").strip()
VLLM_API_KEY = os.environ.get("VLLM_API_KEY", "EMPTY").strip() or "EMPTY"
MODEL_ID = os.environ.get("MODEL_ID", "Qwen/Qwen2.5-VL-72B-Instruct").strip()
REQUEST_TIMEOUT = float(os.environ.get("REQUEST_TIMEOUT", "180"))

DISCLAIMER = (
    "**Decision support, not diagnosis.** Not for unsupervised clinical use. "
    "This Space talks to a single AMD MI300X serving Qwen2.5-VL-72B in BF16 "
    "(no model parallelism, no quantization). The MI300X is powered down "
    "outside live-demo windows to keep costs low; if the call below errors out, "
    "the box is asleep — see the engineering blog for the recorded run."
)

EXAMPLE_VIGNETTES = {
    "case_01_tension_ptx": (
        "30-year-old male, motorbike vs car, ejected. Decreased breath sounds on the right, "
        "tracheal deviation noted. RR 32, sat 88 RA, BP 92/60, HR 124, GCS 14."
    ),
    "case_05_normal_polytrauma": (
        "34-year-old male, MVC ejected from vehicle ~10 meters. Awake, complaining of "
        "abdominal pain. Visible seatbelt sign across abdomen. Chest exam unremarkable. "
        "RR 22, sat 97 RA, HR 118, BP 102/64, GCS 15."
    ),
    "case_06_pediatric_id": (
        "Anak laki-laki 8 tahun, KLL motor vs mobil, terlempar sekitar 3 meter, helm tidak "
        "digunakan. Compos mentis namun mengeluh nyeri dada kanan. Suara napas menurun di "
        "paru kanan. RR 35, SpO2 91% udara ruangan, nadi 130, TD 90/60, GCS 14."
    ),
}

# Strip ```json fences in case the model wraps output despite response_format.
_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*\n?(.*?)\n?\s*```\s*$", re.DOTALL)


def _strip_fence(s: str) -> str:
    m = _FENCE_RE.match(s.strip())
    return m.group(1) if m else s


def _image_to_data_url(img: Image.Image) -> str:
    """Encode a PIL image as a data: URL in JPEG."""
    if img.mode != "RGB":
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


def _build_drafter_messages(image_url: str, vitals_text: str, lang: str) -> list[dict]:
    system = get_drafter_system("id" if lang == "id" else "en")
    return [
        {"role": "system", "content": system},
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": image_url}},
                {
                    "type": "text",
                    "text": (
                        f"Vitals and clinical vignette:\n{vitals_text.strip()}\n\n"
                        "Retrieved guideline excerpts:\n"
                        "(none — proceed using your training; do not invent citations.)\n\n"
                        "Produce the TriageOutput JSON now."
                    ),
                },
            ],
        },
    ]


def _build_verifier_messages(image_url: str, draft: TriageOutput) -> list[dict]:
    return [
        {"role": "system", "content": VERIFIER_SYSTEM},
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": image_url}},
                {"type": "text", "text": get_verifier_prompt(draft)},
            ],
        },
    ]


def _make_client() -> OpenAI:
    if not VLLM_BASE_URL:
        raise RuntimeError(
            "VLLM_BASE_URL is not configured. Set it in the Space's "
            "Settings → Variables and secrets, e.g. "
            "http://<droplet-public-ip>:8000/v1"
        )
    return OpenAI(
        base_url=VLLM_BASE_URL,
        api_key=VLLM_API_KEY,
        timeout=REQUEST_TIMEOUT,
        max_retries=0,
    )


def _call_model(
    client: OpenAI,
    messages: list[dict],
    schema_cls: type,
    max_tokens: int = 2048,
) -> str:
    """Call vLLM chat-completions with OpenAI-canonical structured output.

    vLLM v0.17.x supports `response_format={"type": "json_schema", ...}`
    natively — same shape as OpenAI's structured output. We still strip
    markdown fences from the response as a belt-and-braces measure.
    """
    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": schema_cls.__name__,
            "schema": schema_cls.model_json_schema(),
            "strict": True,
        },
    }
    resp = client.chat.completions.create(
        model=MODEL_ID,
        messages=messages,
        max_tokens=max_tokens,
        temperature=0.2,
        response_format=response_format,
    )
    content = resp.choices[0].message.content or ""
    return _strip_fence(content)


def _apply_verifier_patches(draft: TriageOutput, patches: list) -> TriageOutput:
    """Apply patch list onto a deep copy of the draft. See main repo for the
    full path-walker; we keep a small inline version here."""
    patched = copy.deepcopy(draft)
    for p in patches:
        path = p.path if hasattr(p, "path") else p["path"]
        value = p.value if hasattr(p, "value") else p["value"]
        try:
            tokens: list = []
            for part in path.replace("[", ".").replace("]", "").split("."):
                if not part:
                    continue
                tokens.append(int(part) if part.isdigit() else part)
            target = patched
            for tok in tokens[:-1]:
                target = target[tok] if isinstance(tok, int) else getattr(target, tok)
            leaf = tokens[-1]
            if isinstance(leaf, int):
                target[leaf] = value
            else:
                setattr(target, leaf, value)
        except (AttributeError, IndexError, KeyError, ValueError):
            continue
    try:
        return TriageOutput.model_validate(patched.model_dump())
    except ValidationError:
        return draft


def _format_connection_error(exc: Exception) -> str:
    """Friendly markdown for the most common failure: droplet asleep."""
    return (
        "**Backend unreachable.** The MI300X droplet appears to be powered "
        "down (it's only on during demo windows to keep costs low). "
        "If you're a hackathon judge, reach out via the GitHub repo and "
        "we'll spin it up — the recorded video shows a full live run.\n\n"
        f"Underlying error:\n```\n{type(exc).__name__}: {exc}\n```"
    )


def run_pipeline(
    image: Image.Image | None,
    vitals: str,
    lang: str,
    use_verifier: bool,
    progress: gr.Progress | None = None,
) -> tuple[str, str]:
    """Returns (markdown handoff, JSON pretty-printed)."""
    if progress is None:
        progress = gr.Progress()
    if image is None:
        return "Please upload a chest X-ray first.", ""
    if not vitals.strip():
        return "Please type the vitals / clinical vignette.", ""

    try:
        client = _make_client()
    except RuntimeError as exc:
        return f"**Configuration error:** {exc}", ""

    image_url = _image_to_data_url(image)

    progress(0.0, desc=f"Drafting on {MODEL_ID}…")
    drafter_msgs = _build_drafter_messages(image_url, vitals, lang)
    try:
        raw_draft = _call_model(client, drafter_msgs, TriageOutput, max_tokens=2048)
    except (openai.APIConnectionError, openai.APITimeoutError) as exc:
        return _format_connection_error(exc), ""
    except openai.APIStatusError as exc:
        return f"**Drafter API error ({exc.status_code}):** `{exc.message}`", ""
    except Exception as exc:  # noqa: BLE001
        return f"**Drafter call failed:** `{exc}`", ""

    try:
        draft = TriageOutput.model_validate_json(raw_draft)
        draft.case_id = "live_demo"
    except ValidationError as exc:
        return (
            "**Drafter output didn't match the schema.** Raw output:\n\n"
            f"```json\n{raw_draft[:2000]}\n```\n\n"
            f"Validation errors:\n```\n{exc}\n```"
        ), raw_draft

    if use_verifier:
        progress(0.5, desc="Running verifier pass…")
        verifier_msgs = _build_verifier_messages(image_url, draft)
        try:
            raw_verifier = _call_model(client, verifier_msgs, VerifierOutput, max_tokens=1024)
            verifier_out = VerifierOutput.model_validate_json(raw_verifier)
            draft = _apply_verifier_patches(draft, verifier_out.patches)
            if verifier_out.verifier_notes:
                draft.model_metadata.verifier_notes = list(
                    draft.model_metadata.verifier_notes
                ) + list(verifier_out.verifier_notes)
        except (ValidationError, json.JSONDecodeError, Exception):  # noqa: BLE001
            # Verifier is best-effort; if it fails, surface the unverified draft.
            pass

    progress(1.0, desc="Rendering…")
    handoff = render_id(draft) if lang == "id" else render_en(draft)
    pretty_json = json.dumps(draft.model_dump(mode="json"), indent=2, ensure_ascii=False)
    return handoff, pretty_json


def _load_example(case_id: str) -> tuple[str, str]:
    vignette = EXAMPLE_VIGNETTES.get(case_id, "")
    lang = "id" if case_id.endswith("_id") else "en"
    return vignette, lang


def _backend_status_md() -> str:
    """One-line backend status shown in the UI."""
    if not VLLM_BASE_URL:
        return (
            "Backend: **not configured** — set `VLLM_BASE_URL` in Space "
            "Settings → Variables and secrets."
        )
    # Hide the host but show enough so the team can verify the right env is wired.
    redacted = re.sub(r"//[^/]+", "//<host>", VLLM_BASE_URL)
    return f"Backend: `{MODEL_ID}` via `{redacted}`"


def build_ui() -> gr.Blocks:
    with gr.Blocks(
        title="Agentic Trauma Life Support",
        theme=gr.themes.Soft(primary_hue="indigo"),
    ) as demo:
        gr.Markdown(
            "# Agentic Trauma Life Support\n\n"
            "Chest X-ray + dictated vitals → structured ATLS primary survey + "
            "SBAR handoff. Multilingual (English / Bahasa Indonesia). Drafter → "
            "Verifier → Renderer pipeline. Backed by **Qwen2.5-VL-72B in BF16 "
            "on a single AMD MI300X** — no tensor parallelism, no quantization.\n\n"
            + DISCLAIMER
            + "\n\n"
            + _backend_status_md()
        )

        with gr.Row():
            with gr.Column(scale=1):
                image = gr.Image(
                    type="pil",
                    label="Chest X-ray",
                    sources=["upload", "clipboard"],
                )
                vitals = gr.Textbox(
                    label="Vitals / clinical vignette",
                    lines=4,
                    placeholder=(
                        "Example: 30-year-old male, motorbike vs car, ejected. "
                        "Decreased breath sounds on the right, tracheal deviation. "
                        "RR 32, sat 88, BP 92/60, HR 124, GCS 14."
                    ),
                )
                lang = gr.Radio(
                    choices=[("English", "en"), ("Bahasa Indonesia", "id")],
                    value="en",
                    label="Language",
                )
                use_verifier = gr.Checkbox(
                    label="Run verifier pass (slower, catches hallucinated findings)",
                    value=False,
                )

                with gr.Accordion("Try a sample case", open=False):
                    gr.Markdown(
                        "Click any case to populate the vignette. You'll still need "
                        "to upload a chest X-ray (sample images are not redistributed "
                        "due to source licensing — see the main repo's "
                        "`docs/DEMO_CASES.md` for direct links to sources)."
                    )
                    with gr.Row():
                        ex_01 = gr.Button("case_01 — tension PTX (drama case)")
                        ex_05 = gr.Button("case_05 — normal CXR (credibility case)")
                        ex_06 = gr.Button("case_06 — pediatric ID (Indonesian)")
                    ex_01.click(
                        lambda: _load_example("case_01_tension_ptx"),
                        outputs=[vitals, lang],
                    )
                    ex_05.click(
                        lambda: _load_example("case_05_normal_polytrauma"),
                        outputs=[vitals, lang],
                    )
                    ex_06.click(
                        lambda: _load_example("case_06_pediatric_id"),
                        outputs=[vitals, lang],
                    )

                go_btn = gr.Button("Generate ATLS handoff", variant="primary")

            with gr.Column(scale=2):
                handoff_md = gr.Markdown(label="ATLS handoff (SBAR-style)")
                with gr.Accordion("Structured TriageOutput JSON", open=False):
                    json_view = gr.Code(language="json", label="JSON")

        go_btn.click(
            run_pipeline,
            inputs=[image, vitals, lang, use_verifier],
            outputs=[handoff_md, json_view],
        )

        gr.Markdown(
            "---\n\n"
            "**Repo:** [github.com/0xNoramiya/agentic-trauma-life-support]"
            "(https://github.com/0xNoramiya/agentic-trauma-life-support) · "
            "MIT licensed · Built by an emergency physician for the AMD Developer "
            "Hackathon, May 2026."
        )

    return demo


if __name__ == "__main__":
    build_ui().launch()
