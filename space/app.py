"""HF Spaces app for Agentic Trauma Life Support.

Lightweight Gradio UI that calls Qwen2.5-VL-7B-Instruct via
huggingface_hub.InferenceClient and renders the structured ATLS
primary-survey output. The full hackathon pitch — Qwen2.5-VL-72B in BF16
on a single AMD MI300X — is what produced the recorded demo video; this
Space is the clickable click-through demo for judges.

The schema, prompts, and renderers are vendored under `ats/` from the
main repo (see `sync_from_main.sh`).
"""

from __future__ import annotations

import base64
import io
import json
import os
import re
import sys
from pathlib import Path

import gradio as gr
from huggingface_hub import InferenceClient
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

MODEL_ID = "Qwen/Qwen2.5-VL-7B-Instruct"
PROVIDER = os.environ.get("HF_PROVIDER", "auto")  # let HF route to a working backend

DISCLAIMER = (
    "**Decision support, not diagnosis.** Not for unsupervised clinical use. "
    "This Space serves Qwen2.5-VL-7B; the production hackathon demo runs the 72B "
    "BF16 path on a single AMD MI300X. See the engineering blog for benchmarks."
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


def _build_drafter_messages(
    image_url: str, vitals_text: str, lang: str
) -> list[dict]:
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


def _call_model(
    client: InferenceClient,
    messages: list[dict],
    schema_cls: type,
    max_tokens: int = 2048,
) -> str:
    """Call HF Inference Provider chat-completion with response_format if available."""
    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": schema_cls.__name__,
            "schema": schema_cls.model_json_schema(),
            "strict": True,
        },
    }
    try:
        resp = client.chat_completion(
            messages=messages,
            model=MODEL_ID,
            max_tokens=max_tokens,
            temperature=0.2,
            response_format=response_format,
        )
    except TypeError:
        # Fall back if the provider's client signature doesn't accept response_format
        resp = client.chat_completion(
            messages=messages,
            model=MODEL_ID,
            max_tokens=max_tokens,
            temperature=0.2,
        )
    content = resp.choices[0].message.content or ""
    return _strip_fence(content)


def _apply_verifier_patches(draft: TriageOutput, patches: list) -> TriageOutput:
    """Apply patch list onto a deep copy of the draft. See main repo for the
    full path-walker; we keep a small inline version here."""
    import copy

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


def run_pipeline(
    image: Image.Image | None,
    vitals: str,
    lang: str,
    use_verifier: bool,
    hf_token: str | None,
    progress: gr.Progress | None = None,
) -> tuple[str, str]:
    """Returns (markdown handoff, JSON pretty-printed)."""
    if progress is None:
        progress = gr.Progress()
    if image is None:
        return "Please upload a chest X-ray first.", ""
    if not vitals.strip():
        return "Please type the vitals / clinical vignette.", ""

    token = (hf_token or os.environ.get("HF_TOKEN") or "").strip() or None
    client = InferenceClient(provider=PROVIDER, token=token)

    image_url = _image_to_data_url(image)

    progress(0.0, desc="Drafting…")
    drafter_msgs = _build_drafter_messages(image_url, vitals, lang)
    try:
        raw_draft = _call_model(client, drafter_msgs, TriageOutput, max_tokens=2048)
    except Exception as exc:  # noqa: BLE001
        return f"**Drafter call failed:** `{exc}`", ""

    try:
        draft = TriageOutput.model_validate_json(raw_draft)
        draft.case_id = "live_demo"
    except ValidationError as exc:
        return (
            f"**Drafter output didn't match the schema** (Qwen2.5-VL-7B can be "
            f"loose under guided JSON via the free Inference API). Raw output:\n\n"
            f"```json\n{raw_draft[:2000]}\n```\n\n"
            f"Validation errors:\n```\n{exc}\n```"
        ), raw_draft

    if use_verifier:
        progress(0.5, desc="Running verifier…")
        verifier_msgs = _build_verifier_messages(image_url, draft)
        try:
            raw_verifier = _call_model(client, verifier_msgs, VerifierOutput, max_tokens=1024)
            verifier_out = VerifierOutput.model_validate_json(raw_verifier)
            draft = _apply_verifier_patches(draft, verifier_out.patches)
            if verifier_out.verifier_notes:
                draft.model_metadata.verifier_notes = (
                    list(draft.model_metadata.verifier_notes)
                    + list(verifier_out.verifier_notes)
                )
        except (ValidationError, json.JSONDecodeError, Exception):  # noqa: BLE001
            # Verifier is best-effort; if it fails, we surface the unverified draft.
            pass

    progress(1.0, desc="Rendering…")
    handoff = render_id(draft) if lang == "id" else render_en(draft)
    pretty_json = json.dumps(draft.model_dump(mode="json"), indent=2, ensure_ascii=False)
    return handoff, pretty_json


def _load_example(case_id: str) -> tuple[str, str]:
    vignette = EXAMPLE_VIGNETTES.get(case_id, "")
    lang = "id" if case_id.endswith("_id") else "en"
    return vignette, lang


def build_ui() -> gr.Blocks:
    with gr.Blocks(
        title="Agentic Trauma Life Support",
        theme=gr.themes.Soft(primary_hue="indigo"),
    ) as demo:
        gr.Markdown(
            "# Agentic Trauma Life Support\n\n"
            "Chest X-ray + dictated vitals → structured ATLS primary survey + "
            "SBAR handoff. Multilingual (English / Bahasa Indonesia). Drafter → "
            "Verifier → Renderer pipeline. Backed by Qwen2.5-VL-7B-Instruct on "
            "this Space; the full demo runs Qwen2.5-VL-72B BF16 on a single "
            "AMD MI300X — see the engineering blog for that.\n\n" + DISCLAIMER
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
                hf_token = gr.Textbox(
                    label="HF token (optional — for higher rate limits)",
                    placeholder="hf_…",
                    type="password",
                    info=(
                        "Free tier works without a token at low volume. If you hit a "
                        "rate limit, paste your read token from "
                        "https://huggingface.co/settings/tokens."
                    ),
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
            inputs=[image, vitals, lang, use_verifier, hf_token],
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
