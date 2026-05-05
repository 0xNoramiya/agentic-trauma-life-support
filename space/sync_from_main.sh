#!/usr/bin/env bash
# sync_from_main.sh — refresh vendored modules from the main repo's src/ats.
#
# The HF Space ships a self-contained `space/` directory: app.py + a vendored
# subset of the main `ats` package (schema, prompts, renderers; no FAISS/PyMuPDF
# since the Space uses the HF Inference API and skips local retrieval).
#
# Run this any time you change src/ats/{schema,prompts,render}/* on main.
# Then commit the resulting changes inside `space/` and push the Space repo.

set -euo pipefail

cd "$(dirname "$0")"
REPO_ROOT="$(git rev-parse --show-toplevel)"

cp "$REPO_ROOT/src/ats/schema.py"             ./ats/schema.py
cp "$REPO_ROOT/src/ats/prompts/__init__.py"   ./ats/prompts/__init__.py
cp "$REPO_ROOT/src/ats/prompts/drafter.py"    ./ats/prompts/drafter.py
cp "$REPO_ROOT/src/ats/prompts/verifier.py"   ./ats/prompts/verifier.py
cp "$REPO_ROOT/src/ats/render/__init__.py"    ./ats/render/__init__.py
cp "$REPO_ROOT/src/ats/render/handoff_en.py"  ./ats/render/handoff_en.py
cp "$REPO_ROOT/src/ats/render/handoff_id.py"  ./ats/render/handoff_id.py

echo "Vendored files refreshed:"
ls -1 ats/ ats/prompts/ ats/render/

echo
echo "Now: cd space/  &&  git add ats/  &&  git commit  &&  git push (to the HF Space remote)"
