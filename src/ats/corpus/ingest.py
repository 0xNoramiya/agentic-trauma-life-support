"""PDF ingestion and chunking for the trauma guideline corpus.

We use PyMuPDF to extract text per page, then tiktoken (`cl100k_base`) to
size chunks. The encoding is OpenAI-flavored, but it works fine for sizing
chunks for an arbitrary downstream embedder.

Chunk size: ~500 tokens, 50-token overlap. Pages with fewer than 50
extractable tokens are skipped (cover pages, blank pages, image-only pages).

A reference-section filter drops chunks whose text density is dominated by
year-citation patterns ("J Trauma. 2009;67:14-21." style). The first pass
of corpus indexing pulled bibliography lines into retrieval and the model
"cited" them; better to discard these chunks than to surface them.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

import fitz  # PyMuPDF
import tiktoken

logger = logging.getLogger(__name__)

CHUNK_TOKENS = 500
CHUNK_OVERLAP = 50
MIN_PAGE_TOKENS = 50

# A chunk is treated as a reference section if it contains more than
# this many year mentions ("19xx" or "20xx") OR more than this many
# numbered-list entries that look like bibliography rows.
MAX_YEARS_PER_CHUNK = 4
MAX_NUMBERED_ENTRIES_PER_CHUNK = 4

_YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")
_NUMBERED_REF_RE = re.compile(r"^\s*\d+\.\s+\w", re.MULTILINE)

_ENCODING = None


def _looks_like_references(text: str) -> bool:
    """Heuristic: does this chunk look like a bibliography section?

    Triggers on either:
    - dense year mentions (>4 of "19xx"/"20xx" in a single ~500-token chunk), or
    - dense numbered list entries that start with "<num>. <Word>..." (>4 in chunk).

    Real prose body text usually contains 0-2 year mentions per chunk and
    no numbered-list entries; reference sections have one per line.
    """
    if len(_YEAR_RE.findall(text)) > MAX_YEARS_PER_CHUNK:
        return True
    if len(_NUMBERED_REF_RE.findall(text)) > MAX_NUMBERED_ENTRIES_PER_CHUNK:
        return True
    return False


def _get_encoding() -> tiktoken.Encoding:
    global _ENCODING
    if _ENCODING is None:
        _ENCODING = tiktoken.get_encoding("cl100k_base")
    return _ENCODING


def _chunk_text(text: str, page: int, source_name: str, url: str | None) -> list[dict]:
    """Split a single page's text into ~500-token chunks with 50-token overlap."""
    enc = _get_encoding()
    tokens = enc.encode(text)
    if len(tokens) < MIN_PAGE_TOKENS:
        return []

    chunks: list[dict] = []
    start = 0
    chunk_idx = 0
    while start < len(tokens):
        end = min(start + CHUNK_TOKENS, len(tokens))
        slice_tokens = tokens[start:end]
        chunk_text = enc.decode(slice_tokens).strip()
        if chunk_text and not _looks_like_references(chunk_text):
            chunks.append(
                {
                    "id": f"{source_name}-p{page}-c{chunk_idx}",
                    "text": chunk_text,
                    "source": source_name,
                    "section": f"page {page}",
                    "url": url,
                }
            )
            chunk_idx += 1
        if end >= len(tokens):
            break
        start = end - CHUNK_OVERLAP
    return chunks


def ingest_pdf(pdf_path: Path, source_name: str, url: str | None = None) -> list[dict]:
    """Ingest a single PDF into chunks.

    Returns a list of chunk dicts with id / text / source / section / url.
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    doc = fitz.open(str(pdf_path))
    out: list[dict] = []
    try:
        for page_num, page in enumerate(doc, start=1):
            text = page.get_text("text") or ""
            text = text.strip()
            if not text:
                continue
            page_chunks = _chunk_text(text, page_num, source_name, url)
            out.extend(page_chunks)
    finally:
        doc.close()
    logger.info("Ingested %d chunks from %s", len(out), pdf_path.name)
    return out


def ingest_directory(dir_path: Path) -> list[dict]:
    """Ingest every PDF listed in `manifest.json` inside `dir_path`.

    The manifest is a JSON array of entries:
        [
          {"file": "east_pmg_rib_fractures.pdf",
           "source": "EAST PMG",
           "section": "Rib Fractures",
           "url": "https://www.east.org/..."}
        ]

    The `section` field on the manifest is informational — actual chunk
    sections are page numbers. The manifest's `source` and `url` are
    propagated to every chunk from that file.
    """
    manifest_path = dir_path / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest.json not found in {dir_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    out: list[dict] = []
    for entry in manifest:
        pdf_path = dir_path / entry["file"]
        chunks = ingest_pdf(
            pdf_path,
            source_name=entry["source"],
            url=entry.get("url"),
        )
        out.extend(chunks)
    return out
