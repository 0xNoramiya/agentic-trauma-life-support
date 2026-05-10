"""Generate per-scene narration MP3s from a SCRIPT_*.md file via ElevenLabs TTS.

Reads scene blocks from a script markdown file (one ## Scene heading per scene),
extracts the narration text (a > blockquote), and writes one MP3 per scene with
narration to `video/audio/narration_<lang>_scene<N>.mp3`.

Usage:
  uv run python video/scripts/tts.py --script video/SCRIPT_EN.md --lang en
  uv run python video/scripts/tts.py --script video/SCRIPT_ID.md --lang id

Reads ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID from .env.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(REPO_ROOT / ".env")

API_KEY = os.environ.get("ELEVENLABS_API_KEY", "").strip()
VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM").strip()

# Scenes that have narration (skip 1 = silent, 4 = live demo audio).
NARRATED_SCENES = {2, 3, 5, 6, 7, 8}

# eleven_multilingual_v2 handles both EN and ID with the same voice.
MODEL_ID = "eleven_multilingual_v2"

# Clinical / calm voice settings: slightly more stable, slightly less expressive,
# enough similarity to keep voice identity consistent across scenes.
VOICE_SETTINGS = {
    "stability": 0.55,
    "similarity_boost": 0.75,
    "style": 0.15,
    "use_speaker_boost": True,
}

SCENE_RE = re.compile(r"^## Scene (\d+)", re.MULTILINE)


def parse_scenes(markdown: str) -> dict[int, str]:
    """Return {scene_number: narration_text} for scenes that have narration text.

    Strips DRAFT markers, _italic_ stage directions, and notes. Returns the
    spoken English (or Indonesian) text only.
    """
    scenes: dict[int, str] = {}
    parts = re.split(r"^## Scene (\d+)", markdown, flags=re.MULTILINE)
    # parts = [preamble, "1", "...body...", "2", "...body...", ...]
    for i in range(1, len(parts) - 1, 2):
        scene_num = int(parts[i])
        body = parts[i + 1]
        text = _extract_narration(body)
        if text:
            scenes[scene_num] = text
    return scenes


def _extract_narration(body: str) -> str:
    """Pull narration out of a scene body: the blockquote with the text to speak."""
    out: list[str] = []
    in_quote = False
    for raw_line in body.splitlines():
        line = raw_line.rstrip()
        if line.startswith(">"):
            in_quote = True
            inner = line.lstrip(">").strip()
            # Strip DRAFT markers if present (ID script).
            inner = re.sub(r"^_DRAFT — please review:_\s*", "", inner, flags=re.IGNORECASE)
            # Skip pure stage directions (lines that are entirely _italic_ or in [brackets]).
            if re.fullmatch(r"_[^_]+_", inner) or re.fullmatch(r"\[[^]]+\]", inner):
                continue
            # Drop any [bracketed] stage direction prefix.
            inner = re.sub(r"^\[[^]]+\]\s*", "", inner)
            # Strip markdown bold for cleaner TTS pacing.
            inner = re.sub(r"\*\*([^*]+)\*\*", r"\1", inner)
            inner = re.sub(r"_([^_]+)_", r"\1", inner)
            if inner:
                out.append(inner)
        elif in_quote and not line.strip():
            # Blank line inside the quote ends it.
            break
        elif not line.startswith(">") and in_quote:
            break
    return " ".join(out).strip()


def synth(text: str, out_path: Path) -> None:
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {
        "xi-api-key": API_KEY,
        "accept": "audio/mpeg",
        "content-type": "application/json",
    }
    payload = {
        "text": text,
        "model_id": MODEL_ID,
        "voice_settings": VOICE_SETTINGS,
    }
    with httpx.Client(timeout=120.0) as client:
        resp = client.post(url, headers=headers, json=payload)
        if resp.status_code != 200:
            raise RuntimeError(f"ElevenLabs API {resp.status_code}: {resp.text[:300]}")
        out_path.write_bytes(resp.content)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--script", type=Path, required=True)
    parser.add_argument("--lang", choices=("en", "id"), required=True)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=REPO_ROOT / "video" / "audio",
    )
    args = parser.parse_args()

    if not API_KEY:
        print("ELEVENLABS_API_KEY missing from .env", file=sys.stderr)
        return 2

    text = args.script.read_text(encoding="utf-8")
    scenes = parse_scenes(text)
    if not scenes:
        print("No narration scenes parsed.", file=sys.stderr)
        return 3

    args.out_dir.mkdir(parents=True, exist_ok=True)

    for scene_num in sorted(scenes):
        if scene_num not in NARRATED_SCENES:
            print(f"  scene {scene_num}: skipped (silent / live-demo)")
            continue
        narration = scenes[scene_num]
        out_path = args.out_dir / f"narration_{args.lang}_scene{scene_num:02d}.mp3"
        print(f"  scene {scene_num}: {len(narration):>4} chars → {out_path.name}")
        synth(narration, out_path)

    written = sum(1 for n in scenes if n in NARRATED_SCENES)
    print(f"\nDone. Wrote {written} files to {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
