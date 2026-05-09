# Deploying the HF Space

This `space/` directory is **the HF Space repo content**. The Space is a thin Gradio front-end; the model itself runs on **our own vLLM server on a single AMD MI300X** (DigitalOcean GPU droplet). The Space's `app.py` makes OpenAI-compatible chat-completions calls directly to that vLLM endpoint.

The main `agentic-trauma-life-support` GitHub repo and the HF Space are two different git repos that happen to share content; the sync script keeps the vendored modules fresh.

## Architecture

```
HF Space (CPU basic, free tier)            DO MI300X droplet
┌────────────────────────────────┐         ┌──────────────────────────────┐
│ space/app.py (Gradio UI)       │  HTTPS  │ vllm/vllm-openai-rocm:v0.17.1│
│  └─ OpenAI client              │ ──────> │  serving Qwen2.5-VL-72B BF16 │
│     base_url=$VLLM_BASE_URL    │  :8000  │  AITER kernels, single GPU,  │
│     api_key=$VLLM_API_KEY      │         │  no tensor parallelism       │
└────────────────────────────────┘         └──────────────────────────────┘
```

## One-time setup

You must already have:
- An HF account with a write token (`hf_*`) — generate one at <https://huggingface.co/settings/tokens>.
- Membership in the `lablab-ai-amd-developer-hackathon` HF Org (you joined this in the earlier session).
- The DO droplet running `scripts/serve_vllm.sh prod` with port 8000 reachable from the public internet (see "Droplet-side prep" below).

### Droplet-side prep (do this first)

The Space cannot reach the droplet over Tailscale — Tailscale tunnels are only between authorized peers. The Space needs the droplet's **public** IP or a public hostname.

1. **Open port 8000 to the public internet on the droplet.** From a fresh DO ROCm Quick Start image there is no firewall by default, but if you added one, allow inbound TCP 8000 from `0.0.0.0/0`.

2. **Pick an API key and pass it to vLLM.** The current `scripts/serve_vllm.sh` defaults to `--api-key EMPTY`. Edit the script (or set an env var) and substitute a real secret. The Space sends this same key as a `Bearer` token in the `Authorization` header — they must match.

   Example with a real key:
   ```bash
   # On the droplet, before launching prod:
   export VLLM_API_KEY="sk-atls-$(openssl rand -hex 16)"
   echo "$VLLM_API_KEY"   # copy this into the HF Space secret below
   # In serve_vllm.sh prod, replace `--api-key EMPTY` with --api-key "$VLLM_API_KEY"
   ```

3. **Launch vLLM.**
   ```bash
   docker stop rocm && docker rm rocm 2>/dev/null || true   # free port 8000
   ./scripts/serve_vllm.sh prod
   ```
   First-run AITER JIT compile takes ~22 min before `/v1/models` becomes ready. Subsequent starts hit the JIT cache and warm in ~2 min.

4. **Sanity-check from your laptop:**
   ```bash
   curl -H "Authorization: Bearer $VLLM_API_KEY" \
        http://<droplet-public-ip>:8000/v1/models
   ```
   You should get back a JSON envelope listing `Qwen/Qwen2.5-VL-72B-Instruct`.

### Create the HF Space

You have two options. Pick one.

**Option A — via the HF web UI (recommended for first time):**
1. Go to <https://huggingface.co/new-space>
2. Owner: select `lablab-ai-amd-developer-hackathon` (the AMD Developer Hackathon org)
3. Space name: `agentic-trauma-life-support` (or shorter — `atls-demo` is fine)
4. License: `mit`
5. SDK: **Gradio**
6. Hardware: **CPU basic** (free tier). The Space is just the UI; all model compute happens on the MI300X.
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

### Configure the Space's environment

In the Space's UI, go to **Settings → Variables and secrets** and add:

| Key             | Type    | Value                                                           |
|-----------------|---------|-----------------------------------------------------------------|
| `VLLM_BASE_URL` | Variable | `http://<droplet-public-ip>:8000/v1`                            |
| `VLLM_API_KEY`  | **Secret** | the same key you pass to `serve_vllm.sh prod` via `--api-key`   |
| `MODEL_ID`      | Variable | `Qwen/Qwen2.5-VL-72B-Instruct` *(default — only override if you serve a different model)* |
| `REQUEST_TIMEOUT` | Variable | `180` *(default — seconds; raise if 72B verifier passes time out)* |

> **Note:** Public HTTP (no TLS) is acceptable for a hackathon demo, but if you want HTTPS in front of vLLM, the easiest path is a Cloudflare Tunnel from the droplet — it gives you a `*.trycloudflare.com` URL with TLS, no firewall surgery. Then `VLLM_BASE_URL` becomes the cloudflared URL.

### Push this `space/` directory to the new HF Space

From the repo root:

```bash
cd space/

# Initialize a separate git repo for the Space (the parent project's main
# repo and the Space are separate repos).
git init -b main

# Add the HF Space as the origin
git remote add origin https://huggingface.co/spaces/lablab-ai-amd-developer-hackathon/agentic-trauma-life-support

# First push needs an HF write token. Paste it when prompted as the password
# (username can be anything; HF only checks the token).
git add .
git commit -m "Initial scaffold: Gradio UI calling our vLLM on MI300X"
git push -u origin main
```

The Space will start building automatically. First build takes ~3 minutes (CPU basic, no GPU).

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

## Demo windows / cost control

The MI300X droplet runs at ~$1.99/hr active and ~$0.05/hr idle. You can leave the Space deployed permanently (free tier) and only spin up the droplet during demo windows. When the droplet is off, `app.py` catches `APIConnectionError` and renders a friendly "backend unreachable" message instead of a 500 — the Space stays live, judges still get the explanation + the recorded demo video link.

## Troubleshooting

**Build fails at startup:** check the Space's "Logs" tab in the HF web UI. Most often it's a Python version mismatch (HF Spaces default to Python 3.10; our requirements work fine on 3.10+).

**`ModuleNotFoundError: No module named 'ats'`:** `app.py` adds the Space dir to `sys.path` before importing. If this fires anyway, confirm `ats/__init__.py` exists in the Space repo.

**`Configuration error: VLLM_BASE_URL is not configured`:** the Space's Settings → Variables and secrets is missing the `VLLM_BASE_URL` variable. Add it and the Space will pick it up on the next request (no rebuild needed for variable changes).

**`Backend unreachable` shown to the user:** the droplet is asleep, the public IP is wrong, or port 8000 isn't open. From a third-party host, run:
```bash
curl -m 5 -H "Authorization: Bearer <key>" http://<ip>:8000/v1/models
```
If that fails, the issue is droplet-side, not Space-side.

**`401 Unauthorized` from vLLM:** `VLLM_API_KEY` on the Space doesn't match `--api-key` on the server. Update one or the other so they agree.

**Schema validation failures on the rendered output:** vLLM v0.17.x supports `response_format={"type": "json_schema", ...}` natively, so guided decoding should hold. If you see schema errors, check the server logs — usually the model truncated the output (raise `max_tokens`) or the request hit `REQUEST_TIMEOUT` mid-token-stream.

## What this Space does NOT do

- It does not run vLLM. The Space is the **clickable demo**; the model runs on the MI300X.
- It does not run RAG retrieval. The corpus FAISS index lives in the main repo. The Space's drafter prompt explicitly tells the model "no retrieved excerpts; do not invent citations."
- It does not run benchmarks. Real numbers come from `scripts/run_benchmarks.py` against the MI300X — see `docs/BENCHMARKS.md`.
