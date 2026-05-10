#!/usr/bin/env bash
# build_slides.sh — render docs/SLIDES.md to docs/SLIDES.pdf via Marp.
#
# The slide deck is markdown (Marp flavor) with YAML frontmatter at the top.
# Each `---` separator starts a new slide. We invoke Marp through `npx` so
# you don't need a global install — first run will fetch the CLI from npm.
#
# Usage:
#   ./scripts/build_slides.sh        # writes docs/SLIDES.pdf
#   ./scripts/build_slides.sh html   # writes docs/SLIDES.html (for browser preview)
#
# Prereqs:
#   - Node.js 18+ on PATH (`node --version`)
#   - Internet on first run (npx fetches @marp-team/marp-cli)
#
# After the first run the marp-cli binary is cached in your npm cache and
# subsequent invocations are fast.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$REPO_ROOT/docs/SLIDES.md"
FORMAT="${1:-pdf}"

if [ ! -f "$SRC" ]; then
  echo "ERROR: $SRC not found. Run from the repo root or check the file path." >&2
  exit 1
fi

if ! command -v node >/dev/null 2>&1; then
  echo "ERROR: node is not on PATH. Install Node.js 18+ first." >&2
  exit 1
fi

case "$FORMAT" in
  pdf)
    OUT="$REPO_ROOT/docs/SLIDES.pdf"
    EXTRA=(--pdf --allow-local-files)
    ;;
  html)
    OUT="$REPO_ROOT/docs/SLIDES.html"
    EXTRA=(--html --allow-local-files)
    ;;
  *)
    echo "Unknown format: $FORMAT (expected: pdf | html)" >&2
    exit 64
    ;;
esac

echo "[build_slides] $SRC -> $OUT (format: $FORMAT)"
npx -y @marp-team/marp-cli@latest "${EXTRA[@]}" "$SRC" -o "$OUT"
echo "[build_slides] done: $OUT"
