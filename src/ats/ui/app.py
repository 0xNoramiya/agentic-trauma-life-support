"""Gradio UI for ATLS triage.

Run with `python -m ats.ui.app`. Default port is 7860, bound to 127.0.0.1.

In mock mode (the default), the UI returns the bundled fixture for any input
so you can demo the layout / interactions without the MI300X. Set
`MOCK_MODE=false` in `.env` to point at the live vLLM server.
"""

from __future__ import annotations

import io
import json
import logging

import gradio as gr
from PIL import Image

from ats.config import settings
from ats.inference.client import InferenceClient
from ats.pipeline.run import run_triage

logger = logging.getLogger(__name__)

LANG_LABEL_TO_CODE = {
    "English": "en",
    "Bahasa Indonesia": "id",
}

DEFAULT_VITALS_EN = (
    "30M motorbike vs car, ejected. RR 32, SpO2 88% on room air, HR 124, BP 92/60, GCS 14."
    " Decreased breath sounds on the left, tracheal deviation to the right."
)


def _image_to_jpeg_bytes(img) -> bytes:
    """Convert a Gradio image input (PIL or numpy) to JPEG bytes."""
    if img is None:
        # Generate a small grey placeholder so the pipeline can still run in mock mode.
        placeholder = Image.new("L", (512, 512), color=128)
        buf = io.BytesIO()
        placeholder.save(buf, format="JPEG", quality=85)
        return buf.getvalue()
    if not isinstance(img, Image.Image):
        img = Image.fromarray(img)
    if img.mode != "RGB":
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def _make_handler(client: InferenceClient):
    def handle(image, vitals_text, lang_label, use_verifier, case_id):
        lang = LANG_LABEL_TO_CODE.get(lang_label, "en")
        case_id = (case_id or "demo").strip() or "demo"
        image_bytes = _image_to_jpeg_bytes(image)

        try:
            result = run_triage(
                client=client,
                image_bytes=image_bytes,
                vitals_text=vitals_text or "",
                lang=lang,
                case_id=case_id,
                use_verifier=bool(use_verifier),
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("run_triage failed")
            return (
                f"**Error during triage:** `{exc}`",
                "{}",
                "Retrieved chunks: 0 (error)",
            )

        return (
            result["handoff"],
            json.dumps(result["json"], indent=2, ensure_ascii=False),
            f"Retrieved chunks: {result['retrieved_count']}",
        )

    return handle


def _health_indicator(client: InferenceClient) -> str:
    ok = client.health_check()
    mode = "mock" if client.mock_mode else "live"
    if ok:
        return f"Server status: **OK** ({mode}, model={client.model_name})"
    return (
        f"Server status: **UNREACHABLE** ({mode} at {client.base_url}). "
        "Pipeline will surface drafter errors."
    )


def build_ui(client: InferenceClient | None = None) -> gr.Blocks:
    """Build and return the Gradio Blocks UI."""
    if client is None:
        client = InferenceClient(settings)

    with gr.Blocks(title="ATLS — Agentic Trauma Life Support") as demo:
        gr.Markdown("# Agentic Trauma Life Support (ATLS)")
        gr.Markdown("Decision support only. Not a diagnosis. Not for unsupervised clinical use.")
        gr.Markdown(_health_indicator(client))

        with gr.Row():
            with gr.Column(scale=1):
                image = gr.Image(label="Chest X-ray", type="pil")
                vitals = gr.Textbox(
                    label="Vitals and clinical vignette",
                    lines=6,
                    value=DEFAULT_VITALS_EN,
                )
                lang = gr.Radio(
                    label="Language",
                    choices=list(LANG_LABEL_TO_CODE.keys()),
                    value="English",
                )
                use_verifier = gr.Checkbox(label="Run verifier pass", value=True)
                case_id = gr.Textbox(label="Case ID", value="demo")
                submit = gr.Button("Generate ATLS handoff", variant="primary")

            with gr.Column(scale=2):
                handoff = gr.Markdown(label="SBAR handoff")
                with gr.Accordion("Raw TriageOutput JSON", open=False):
                    raw_json = gr.Code(label="JSON", language="json")
                retrieved_count = gr.Markdown()

        submit.click(
            _make_handler(client),
            inputs=[image, vitals, lang, use_verifier, case_id],
            outputs=[handoff, raw_json, retrieved_count],
        )

    return demo


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    demo = build_ui()
    demo.launch(server_name="127.0.0.1", server_port=7860)


if __name__ == "__main__":
    main()
