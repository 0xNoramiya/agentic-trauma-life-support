"""Runtime settings for ATLS, loaded from environment / .env."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CORPUS_DATA_DIR = REPO_ROOT / "src" / "ats" / "corpus" / "data"


class Settings(BaseSettings):
    """Application settings.

    All fields can be overridden via environment variables (case-insensitive)
    or a `.env` file at the repo root.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    vllm_base_url: str = Field(
        default="http://localhost:8000/v1",
        description="OpenAI-compatible base URL for the vLLM server.",
    )
    vllm_api_key: str = Field(
        default="EMPTY",
        description="API key for the vLLM server. vLLM accepts any non-empty string.",
    )
    model_name: str = Field(
        default="Qwen/Qwen2.5-VL-72B-Instruct",
        description="Model identifier to send to the vLLM server.",
    )
    embed_model: str = Field(
        default="BAAI/bge-m3",
        description="sentence-transformers model used for retrieval embeddings (1024-dim).",
    )
    default_lang: str = Field(
        default="en",
        description="Default UI language: 'en' or 'id'.",
    )
    mock_mode: bool = Field(
        default=True,
        description="If true, InferenceClient returns canned fixtures without contacting vLLM.",
    )
    corpus_index_path: Path = Field(
        default=CORPUS_DATA_DIR / "index.faiss",
        description="On-disk path to the FAISS index file.",
    )
    corpus_meta_path: Path = Field(
        default=CORPUS_DATA_DIR / "meta.jsonl",
        description="On-disk path to the JSONL metadata file paired with the FAISS index.",
    )


settings = Settings()
