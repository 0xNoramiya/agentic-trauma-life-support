# Deploying the HF Space

This `space/` directory is **the HF Space repo content**. To deploy, you initialize a separate git repo here, add the HF Space as a remote, and push. The main `agentic-trauma-life-support` GitHub repo and the HF Space are two different git repos that happen to share content; the sync script keeps the vendored modules fresh.

## One-time setup

You must already have:
- An HF account with a write token (`hf_*`) — generate one at <https://huggingface.co/settings/tokens>.
- Membership in the `lablab-ai-amd-developer-hackathon` HF Org (you already joined this — confirmed in earlier session).

### Create the HF Space

You have two options. Pick one.

**Option A — via the HF web UI (recommended for first time):**
1. Go to <https://huggingface.co/new-space>
2. Owner: select `lablab-ai-amd-developer-hackathon` (the AMD Developer Hackathon org)
3. Space name: `agentic-trauma-life-support` (or shorter — `atls-demo` is fine)
4. License: `mit`
5. SDK: **Gradio**
6. Hardware: **CPU basic** (free tier). The Space calls Qwen2.5-VL-7B-Instruct via HF Inference API — CPU is enough for the UI.
7. Visibility: **Public**
8. Click "Create Space".

**Option B — via the `huggingface-cli`:**

```bash
pip install --user huggingface_hub
huggingface-cli login   # paste your write token
huggingface-cli repo create \
  --type space \
  --space_sdk gradio \
  agentic-trauma-life-support \
  --organization lablab-ai-amd-developer-hackathon
```

This gives you a remote at `https://huggingface.co/spaces/lablab-ai-amd-developer-hackathon/agentic-trauma-life-support`.

### Push this `space/` directory to the new HF Space

From the repo root:

```bash
cd space/

# Initialize a separate git repo for the Space (the parent project's main
# repo and the Space are separate repos)
git init -b main

# Add the HF Space as the origin
git remote add origin https://huggingface.co/spaces/lablab-ai-amd-developer-hackathon/agentic-trauma-life-support

# First push needs an HF write token. Paste it when prompted as the password
# (username can be anything; HF only checks the token).
git add .
git commit -m "Initial scaffold: Gradio UI + Qwen2.5-VL-7B via HF Inference API"
git push -u origin main
```

The Space will start building automatically. First build takes ~3 minutes.

When the Space is live: <https://huggingface.co/spaces/lablab-ai-amd-developer-hackathon/agentic-trauma-life-support>

Paste that URL into your lablab submission's "Application URL" field (`docs/SUBMISSION.md`).

## When the schema or prompts change in the main repo

```bash
cd space/
./sync_from_main.sh
git add ats/
git commit -m "sync: refresh vendored modules from main repo"
git push origin main
```

The Space rebuilds on push.

## Quota and rate limits

The free HF Inference API allows ~1k calls/month/account on most models. Each pipeline run does 1 (or 2 with verifier) calls. For a hackathon demo where judges click the Space a few dozen times, this is plenty.

If a user hits the rate limit, the app surfaces the error in the rendered Markdown and asks them to paste their own HF token in the password field — that re-routes the calls to their personal quota.

## Troubleshooting

**Build fails at startup:** check the Space's "Logs" tab in the HF web UI. Most often it's a Python version mismatch (HF Spaces default to Python 3.10; our requirements should work fine on 3.10+).

**`ModuleNotFoundError: No module named 'ats'`:** `app.py` adds the Space dir to `sys.path` before importing. If this fires anyway, confirm `ats/__init__.py` exists in the Space repo.

**`response_format` unsupported by the Inference Provider:** `app.py` falls back to a non-constrained call when the provider rejects `response_format`. If the model's output then doesn't match the schema, the app surfaces the raw output + validation errors so you can see what came back. Increasing `temperature` slightly (in the prompt or the Provider settings) helps.

**Vision input not supported:** if HF routes Qwen2.5-VL-7B to a provider that doesn't accept image_url chat content blocks, the call will fail. The fix is to set `HF_PROVIDER` env var on the Space to `together` or `fireworks` (both support vision in chat-completions).

## What this Space does NOT do

- It does not run vLLM. The Space is the **clickable demo**; the production hackathon serve is on a single MI300X via the main repo's `scripts/serve_vllm.sh prod`.
- It does not run RAG retrieval. The corpus FAISS index lives in the main repo. The Space's drafter prompt explicitly tells the model "no retrieved excerpts; do not invent citations."
- It does not run benchmarks. Real numbers come from `scripts/run_benchmarks.py` against the MI300X — see `docs/BENCHMARKS.md`.
