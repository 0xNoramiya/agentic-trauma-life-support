# Day 2 quickstart

Exact commands to resume work after the Day 1 droplet shutdown. Walk top-to-bottom.

---

## 0. Verify droplet billing state (do this first)

Open <https://cloud.digitalocean.com/droplets>. Find `atls-dev-mi300x`.

- **If state is "Off"** → you're on idle billing (~$0.05/hr). 
- **If state is "Active" or "Stopped" but the OS is halted** → click **Power Off** in the dashboard to switch to inactive billing rate. Per DO policy, OS-level shutdown alone does not transition the billing state.

Don't proceed to step 1 until this is settled.

---

## 1. Power on

In the DO dashboard, click **Power On** on the droplet. Takes ~1 minute.

Tailscale will auto-reconnect once the OS boots (the daemon is a systemd service and the auth state is persisted). On your laptop, verify with:

```bash
tailscale status | grep atls-droplet
```

Should show `atls-droplet` as `active` (not `offline, last seen N min ago`). If still offline 2+ min after the dashboard says "Active", check the DO console (web shell) — Tailscale may have failed to start.

---

## 2. SSH and verify state

```bash
ssh atls-droplet
```

Once in, run the wakeup script we left:

```bash
bash /root/atls-wakeup.sh
```

This prints date, tailnet IP, disk free, GPU summary, cached models, container status. **Expected:** `Qwen2.5-VL-72B-Instruct` and `Qwen2.5-VL-7B-Instruct` both listed under "Models cached", no containers running, GPU idle.

---

## 3. Push the latest serve_vllm.sh from your laptop to the droplet

The serve script lives in this repo at `scripts/serve_vllm.sh`. Push it up:

```bash
# from your laptop, in this repo
scp scripts/serve_vllm.sh atls-droplet:/root/serve_vllm.sh
ssh atls-droplet "chmod +x /root/serve_vllm.sh"
```

(You can also re-push it any time you tweak the script locally.)

---

## 4. Start the 72B server

```bash
ssh atls-droplet "/root/serve_vllm.sh prod"
```

This runs in the **foreground** — leave the SSH session open. You'll see weights loading (the 72B is already cached, no HF download), then AITER kernel JIT compile.

**The first run after the droplet boots takes ~10-15 minutes** before `/v1/models` becomes reachable. You'll see `[aiter] start build [module_*]` lines; that's the JIT compile. There's no progress bar (per `docs/ROCM_FEEDBACK.md` finding #2). Wait it out. The next time you start the server (without rebooting), AITER hits its JIT cache and warms in ~2 min.

If you want it backgrounded instead, add `-d` to the docker invocation in the script and watch logs with `docker logs -f vllm-72b`.

---

## 5. Verify the API is up

In a second SSH session:

```bash
ssh atls-droplet "curl -s http://localhost:8000/v1/models -H 'Authorization: Bearer EMPTY'"
```

Should return a `{"object": "list", "data": [{"id": "Qwen/Qwen2.5-VL-72B-Instruct", ...}]}` payload.

Quick vision smoke test (synthetic image, just to confirm the pipeline):

```bash
ssh atls-droplet "DEBIAN_FRONTEND=noninteractive apt-get install -y python3-pil 2>/dev/null
python3 -c '
from PIL import Image, ImageDraw
import base64, io, json
img = Image.new(\"L\", (336, 336), 30)
draw = ImageDraw.Draw(img); draw.ellipse([60, 60, 280, 280], fill=80)
buf = io.BytesIO(); img.save(buf, \"JPEG\", quality=85); b64 = base64.b64encode(buf.getvalue()).decode()
req = {\"model\":\"Qwen/Qwen2.5-VL-72B-Instruct\",\"messages\":[{\"role\":\"user\",\"content\":[
  {\"type\":\"image_url\",\"image_url\":{\"url\":f\"data:image/jpeg;base64,{b64}\"}},
  {\"type\":\"text\",\"text\":\"Describe this image in 1 sentence.\"}]}],\"max_tokens\":80,\"temperature\":0.2}
open(\"/tmp/req.json\",\"w\").write(json.dumps(req))
'
curl -s -o /tmp/resp.json -w 'http=%{http_code} time=%{time_total}s\n' \
  http://localhost:8000/v1/chat/completions \
  -H 'Authorization: Bearer EMPTY' -H 'Content-Type: application/json' \
  --data @/tmp/req.json
python3 -c 'import json; r=json.load(open(\"/tmp/resp.json\")); print(r[\"choices\"][0][\"message\"][\"content\"]); print(r[\"usage\"])'"
```

Expect HTTP 200 and a sane response. (Output content will be bogus on the synthetic image — we just want plumbing.)

---

## 6. Point the local UI at the droplet

On your laptop, edit `.env`:

```
VLLM_BASE_URL=http://100.116.60.54:8000/v1
VLLM_API_KEY=EMPTY
MODEL_NAME=Qwen/Qwen2.5-VL-72B-Instruct
EMBED_MODEL=BAAI/bge-m3
DEFAULT_LANG=en
MOCK_MODE=false
```

(Use `tailscale ip -4 atls-droplet` if the IP has changed; usually it doesn't.)

Then:

```bash
uv run python -m ats.ui.app
```

Browser to <http://127.0.0.1:7860>. Upload a real chest X-ray (case 01 first), paste the vignette, hit Generate. End-to-end latency on first request: ~30-60s for the 72B vision call (warm vision encoder, fresh prompt). Subsequent requests faster.

---

## 7. Run case 01 from the CLI as a sanity check

```bash
uv run python scripts/run_demo_cases.py --case case_01_tension_ptx
```

Output goes to `docs/demo_outputs/case_01_tension_ptx.json` plus stdout for the rendered handoff. Verify B critical, tension physiology red flag, immediate priority, needle decompression with a citation.

---

## 8. End-of-Day-2 checkpoint

When you stop for the day:

```bash
ssh atls-droplet "docker stop vllm-72b && docker rm vllm-72b"
# then in DO dashboard: Power Off the droplet
```

This drops you back to idle billing.

---

## Common gotchas

- **`/v1/models` returns 404 / connection refused for >15 min after `serve_vllm.sh prod` started.** AITER is still compiling. Check `docker logs vllm-72b --tail 5` — if you see `[aiter] start build [module_*]` lines, just wait.
- **Out of memory at startup.** Drop `--max-model-len` from 16384 → 12288 → 8192. Drop `--max-num-seqs` from 4 → 2 → 1. See `docs/ROCM_FEEDBACK.md` and the Risk Register in the playbook for the full fallback ladder.
- **Local UI shows "Connection refused" when calling vLLM at the tailnet IP.** Confirm the droplet is on the tailnet: `tailscale status | grep atls-droplet` should be `active` not `offline`. If `offline`, the droplet hasn't finished booting + Tailscale auth — wait another minute.
- **You forgot to Power Off and the droplet ran all night.** No big deal — your $100 AMD credit covers the GPU portion; the personal-billed CPU/storage piece is pennies. Fix the habit, move on.
