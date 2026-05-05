"""Inference client for the (remote) vLLM server.

Local development runs in mock mode by default — `generate(...)` returns
fixture data and the UI / pipeline / tests run end-to-end without a model.
When `mock_mode=False`, the client uses the OpenAI Python SDK pointed at
the vLLM server's OpenAI-compatible endpoint with the canonical OpenAI
`response_format={"type": "json_schema", ...}` form whenever a Pydantic
schema is provided. (We initially tried vLLM's older
`extra_body={"guided_json": ...}`; on v0.17.1 the model still wrapped its
output in a ```json fence and didn't strictly enforce required fields.
Switching to `response_format` produced clean schema-compliant JSON.)
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import httpx
from openai import OpenAI
from pydantic import BaseModel

from ats.config import Settings

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SAMPLE_CASE_PATH = REPO_ROOT / "tests" / "fixtures" / "sample_case.json"

# Defense-in-depth: even with response_format=json_schema, some models still
# wrap output in a markdown JSON fence. Strip if present.
_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*\n?(.*?)\n?\s*```\s*$", re.DOTALL)


def _strip_markdown_fence(s: str) -> str:
    m = _FENCE_RE.match(s)
    return m.group(1) if m else s


class InferenceClient:
    """Thin wrapper over the OpenAI SDK with a mock-mode short-circuit."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.base_url = settings.vllm_base_url
        self.model_name = settings.model_name
        self.mock_mode = settings.mock_mode
        self._client: OpenAI | None = None
        if not self.mock_mode:
            self._client = OpenAI(base_url=self.base_url, api_key=settings.vllm_api_key)

    @property
    def client(self) -> OpenAI:
        """Lazy-init OpenAI client. Raises if accessed in mock mode."""
        if self._client is None:
            raise RuntimeError(
                "InferenceClient is in mock mode. Set MOCK_MODE=false to use the live client."
            )
        return self._client

    def generate(
        self,
        messages: list[dict],
        response_schema: type[BaseModel] | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.2,
    ) -> str:
        """Send a chat-completion request and return the message content as a string.

        When `response_schema` is provided, the OpenAI-canonical
        `response_format={"type": "json_schema", "json_schema": {...}}` form
        is used so the server constrains decoding to the schema. Markdown
        ```json fences are stripped from the response just in case.
        """
        if self.mock_mode:
            return self._mock_generate(response_schema)

        kwargs: dict = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if response_schema is not None:
            kwargs["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": response_schema.__name__,
                    "schema": response_schema.model_json_schema(),
                    "strict": True,
                },
            }

        response = self.client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content
        return _strip_markdown_fence(content) if content is not None else ""

    def _mock_generate(self, response_schema: type[BaseModel] | None) -> str:
        """Return canned data shaped to the requested schema."""
        if response_schema is None:
            return "Mock response: no schema provided."

        name = response_schema.__name__

        if name == "TriageOutput":
            if not SAMPLE_CASE_PATH.exists():
                raise FileNotFoundError(
                    f"Mock fixture missing at {SAMPLE_CASE_PATH}. "
                    "tests/fixtures/sample_case.json is required for mock mode."
                )
            return SAMPLE_CASE_PATH.read_text(encoding="utf-8")

        if name == "VerifierOutput" or _has_verifier_shape(response_schema):
            return json.dumps({"verifier_notes": [], "patches": []})

        return "Mock response: unknown schema."

    def health_check(self) -> bool:
        """Return True if the vLLM server is reachable.

        In mock mode this always returns True.
        """
        if self.mock_mode:
            return True
        try:
            with httpx.Client(timeout=5.0) as http:
                resp = http.get(f"{self.base_url.rstrip('/')}/models")
            return resp.status_code == 200
        except (httpx.HTTPError, OSError):
            return False


def build_image_message(image_b64: str, mime: str = "image/jpeg") -> dict:
    """Build an OpenAI-style image_url content block from a base64 string."""
    return {
        "type": "image_url",
        "image_url": {"url": f"data:{mime};base64,{image_b64}"},
    }


def _has_verifier_shape(schema: type[BaseModel]) -> bool:
    """Heuristic check: a model with both `verifier_notes` and `patches` fields."""
    fields = getattr(schema, "model_fields", {})
    return "verifier_notes" in fields and "patches" in fields
