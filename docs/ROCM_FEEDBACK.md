# ROCm + vLLM feedback — ATLS hackathon

A running list of issues, friction, and nice-to-haves from bringing up Qwen2.5-VL-7B and Qwen2.5-VL-72B on a single AMD MI300X via the DigitalOcean GPU Droplet (region ATL1) using the **vLLM 0.17.1 / ROCm 7.2.0 Quick Start image** and the `vllm/vllm-openai-rocm:v0.17.1` container. Each entry follows the same template so the AMD team can triage quickly.

## Format

For each finding:

- **Severity:** blocker / friction / nit
- **Title:** one-line summary
- **Description:** a paragraph
- **Repro steps:** numbered, copy-pasteable
- **Suggested fix:** one or two sentences
- **Logs / artifacts:** links or pasted excerpts

---

### 1. DigitalOcean ROCm Quick Start image silently grabs port 8000 with JupyterLab

- **Severity:** friction
- **Title:** DO Quick Start image starts a `rocm` JupyterLab container that occupies host port 8000, breaking the standard vLLM bring-up command.
- **Description:** The DigitalOcean GPU Droplet image labeled `vLLM 0.17.1 / ROCm 7.2.0 Quick Start` boots with a Docker container named `rocm` already running, exposing JupyterLab on `0.0.0.0:8000` (and `:8888`, `:30000`). The first time a user runs the canonical `vllm serve … --port 8000` command, vLLM crashes at startup with `OSError: [Errno 98] Address already in use`, and the bind error is buried in the API server traceback rather than surfaced as "the Quick Start helper is using this port." There's no banner at SSH login pointing this out either.
- **Repro steps:**
  1. Provision a single-MI300X GPU Droplet in ATL1 with the **vLLM 0.17.1 / ROCm 7.2.0 Quick Start** image.
  2. SSH in (or open the web console).
  3. `ss -tnlp | grep :8000` — observe `docker-proxy` on `:8000` from the `rocm` container.
  4. Try the canonical `docker run … vllm/vllm-openai-rocm:v0.17.1 <model> --port 8000 …` from the AMD bring-up docs.
  5. Container exits within ~5 s with `[Errno 98] Address already in use`.
- **Suggested fix:** Either (a) don't auto-start the JupyterLab container on the Quick Start image and instead document how to start it, or (b) add a `motd` / SSH login banner that says "JupyterLab is at https://<droplet>:8000 — stop it with `docker stop rocm && docker rm rocm` before you serve your own model on :8000," or (c) bind JupyterLab to `127.0.0.1:8000` instead of `0.0.0.0:8000` so it doesn't block external use of that port.
- **Logs / artifacts:**
  ```
  CONTAINER ID   IMAGE     COMMAND                  CREATED          STATUS          PORTS
  55014b9d458c   rocm      "/bin/sh -c 'jupyter…"   45 minutes ago   Up 45 minutes   0.0.0.0:8000->8000/tcp, 0.0.0.0:8888->8888/tcp, 0.0.0.0:30000->30000/tcp   rocm
  …
  (APIServer pid=1) OSError: [Errno 98] Address already in use
  ```

---

### 2. AITER first-run JIT compile makes /v1/models seem hung for 10+ minutes

- **Severity:** friction
- **Title:** With `VLLM_ROCM_USE_AITER=1`, the first model load JITs AITER kernels (rmsnorm, MoE, etc.) and the API server stays unreachable during this window with no progress signal in the logs.
- **Description:** vLLM's own progress messaging stops after `[default_loader.py] Loading weights took 6.02 seconds` and `[gpu_model_runner.py] Model loading took 15.81 GiB memory and 18.78 seconds`. The next visible line is `[aiter] start build [module_rmsnorm]`. From a developer's perspective, that line is then the last thing in the log for 10+ minutes while AITER compiles kernels under `/usr/local/lib/python3.12/dist-packages/aiter/jit/build/`. During that window `curl localhost:8000/v1/models` returns nothing (connection refused), so it's easy to assume the engine is dead. There's no `tqdm`-style or per-module-completion line, just the `start build` line per kernel.
- **Repro steps:**
  1. On a fresh MI300X droplet (no `~/.aiter/jit_cache` warmth), run:
     ```
     docker run -d --name vllm-7b \
       --device /dev/kfd --device /dev/dri --group-add video \
       --ipc host --network host --shm-size 16G \
       -v /root/.cache/huggingface:/root/.cache/huggingface \
       -e VLLM_ROCM_USE_AITER=1 \
       vllm/vllm-openai-rocm:v0.17.1 \
       Qwen/Qwen2.5-VL-7B-Instruct --max-model-len 8192 --port 8000 --api-key EMPTY
     ```
  2. `docker logs -f vllm-7b` — watch the `[aiter] start build [module_rmsnorm]` line appear and then stay there with no further log output for >10 minutes.
  3. `curl http://localhost:8000/v1/models` — connection refused throughout the JIT window.
- **Suggested fix:** (a) Emit periodic progress messages from AITER's JIT loop (`[aiter] [3/12 modules built, 7 minutes elapsed]`), or (b) ship a precompiled AITER kernel cache in the `vllm/vllm-openai-rocm` image keyed by `(gfx942, vllm-version)`, or (c) provide a `vllm aiter-warmup` CLI command that the user can run once on droplet provisioning so subsequent serves come up in ~2 min instead of ~15 min.
- **Logs / artifacts:** Last log line for >10 minutes:
  ```
  (EngineCore_DP0 pid=141) [aiter] start build [module_rmsnorm] under /usr/local/lib/python3.12/dist-packages/aiter/jit/build/module_rmsnorm
  ```

---

### 3. `--trust-remote-code` is accepted but silently ignored on v0.17.1

- **Severity:** nit
- **Title:** Passing `--trust-remote-code` to `vllm/vllm-openai-rocm:v0.17.1` produces a confusing "no effect here" warning, even when serving Qwen2.5-VL which historically required it.
- **Description:** Following the pattern from `rocm/vllm-dev:nightly` docs, we passed `--trust-remote-code` to v0.17.1. vLLM logs:
  ```
  The argument `trust_remote_code` is to be used with Auto classes. It has no effect here and is ignored.
  ```
  printed twice. The model loaded fine without it (vLLM has its own `Qwen2_5_VLForConditionalGeneration` loader and doesn't go through HF Auto classes), but the warning misled us into thinking the model wasn't being trusted properly. Newer Qwen2.5-VL bring-up guides on the AMD ROCm site still include the flag in their copy-paste blocks, so this is a low-stakes but persistent friction across users following the docs.
- **Repro steps:**
  1. Run any `vllm serve Qwen/Qwen2.5-VL-* --trust-remote-code …` against `vllm/vllm-openai-rocm:v0.17.1`.
  2. Observe the duplicated "no effect here and is ignored" line in startup logs.
- **Suggested fix:** Either drop `--trust-remote-code` from the AMD ROCm Qwen2.5-VL bring-up examples (it's no-op on v0.17+), or have vLLM downgrade the message to a single `INFO` line. Also clarify in docs that v0.17+ has native loaders for the Qwen2.5-VL family so the flag isn't needed.
- **Logs / artifacts:** Inline above.

---

### 4. Bring-up command-shape inconsistency between `rocm/vllm-dev:nightly` and `vllm/vllm-openai-rocm:vX.Y.Z`

- **Severity:** nit
- **Title:** AMD's bring-up examples mostly use `rocm/vllm-dev:nightly` whose entrypoint differs from the version-pinned `vllm/vllm-openai-rocm` images that ship in DO Quick Start.
- **Description:** `rocm/vllm-dev:nightly` has no entrypoint and expects `vllm serve <model> --flag …` as the docker `CMD`. `vllm/vllm-openai-rocm:v0.17.1` (what's preloaded on the DO Quick Start droplet) has `[vllm serve]` as its entrypoint, so the command becomes `<model> --flag …` only. Newcomers who copy-paste from AMD's examples and `vllm serve <model>` to the version-pinned image hit a baffling argparse error:
  ```
  vllm: error: argument {chat,complete,bench,collect-env,run-batch,serve}: invalid choice: 'Qwen/...'
  ```
  …because `vllm serve` got dispatched as the model id. Easy to figure out from `docker inspect`, but unnecessary friction.
- **Repro steps:**
  1. Pull the DO Quick Start image (or `docker pull vllm/vllm-openai-rocm:v0.17.1`).
  2. Run `docker run … vllm/vllm-openai-rocm:v0.17.1 vllm serve Qwen/Qwen2.5-VL-7B-Instruct --port 8000 …`.
  3. Container exits with the argparse error above.
- **Suggested fix:** Align the entrypoints. Either drop `[vllm serve]` from the version-pinned image so all images take `vllm serve <model> …` (consistent with the nightly), or add `[vllm serve]` to `rocm/vllm-dev:nightly` so both take `<model> …`. Update AMD's Qwen2.5-VL ROCm bring-up doc to call out the entrypoint variant per image.
- **Logs / artifacts:**
  ```
  Entrypoint: [vllm serve]
  Cmd: []
  WorkingDir: /app
  ```
  …from `docker inspect vllm/vllm-openai-rocm:v0.17.1`.

---

### 5. SE Asia ISP SSH MITM breaks the documented bring-up flow without a tunnel

- **Severity:** friction (network, not strictly ROCm — but real for AMD's developer-program cohort)
- **Title:** Some Southeast Asian ISPs (observed: Indosat / Telkomsel / Telkom — Indonesia) transparently intercept SSH on port 22 to public DO IPs, presenting a different host key than the droplet's actual `/etc/ssh/ssh_host_ed25519_key.pub`. Standard publickey auth fails silently with no entry in the droplet's `/var/log/auth.log`.
- **Description:** From a developer in Indonesia (egress IP `140.213.10.17`, ISP path through `112.215.248.x` Telkom and `180.87.96.x`), `ssh root@<droplet-public-ip>` consistently presents a host-key SHA256 that does NOT match the droplet's actual `/etc/ssh/ssh_host_ed25519_key.pub` fingerprint. Auth fails with `Permission denied (publickey)` even though the local key is correct and `/root/.ssh/authorized_keys` on the droplet is correct. Sshd's auth log on the droplet shows zero entries from the developer's IP — confirming the SSH packets never reached sshd. Plain TCP to other ports on the same droplet either RSTs or times out, depending on the port. Switching SSH to a non-22 port (we tried `:2222`) didn't help — connection refused with no audit-log evidence on the droplet. The only path that worked was a Tailscale overlay (free tier; user runs `tailscale up --ssh` on the droplet, `tailscale up` on the laptop, then SSH targets the `100.x.y.z` tailnet IP).
- **Repro steps:**
  1. From an Indonesian ISP egress, provision a DO MI300X droplet with the standard ROCm Quick Start image and a single SSH key.
  2. From the laptop, `ssh-keyscan <droplet-public-ip>` and compare to `ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub` on the droplet — the ED25519 fingerprints will differ.
  3. `ssh root@<droplet-public-ip>` returns `Permission denied (publickey)` despite a correct setup.
  4. `journalctl -u ssh` on the droplet shows ZERO entries for the developer's source IP. Other source IPs (DO's DOTTY agent at `162.243.x.y`) log normally.
  5. Install Tailscale on both ends, join the same tailnet, `ssh root@<tailnet-ip>` — works first try.
- **Suggested fix:** AMD's Developer Program / DO GPU bring-up guides should include a "Networking from outside the US" section that calls this out specifically and prescribes Tailscale (or a comparable WireGuard tunnel) as a one-line workaround. Lots of AMD AI Developer Program signups are from APAC; this is going to keep biting people. Optional bonus: pre-bake `tailscale` into the ROCm Quick Start image so it's a one-command auth.
- **Logs / artifacts:**
  - From-laptop fingerprint: `SHA256:kUxls3NtkYiz56pXq4hJ3hMhkqHf0hMBCrr1gRWsQA8`
  - On-droplet fingerprint: `SHA256:24KlD7yQoqNbsKES1cgXhbkFrODDp3qwTRU/gV5SBo0`
  - traceroute terminates around `64.86.26.x` (Tata Communications) without ICMP returning from DO — typical for cross-Pacific routes, not the cause but useful context.

---

### 6. `--limit-mm-per-prompt` argument format changed silently between vLLM versions

- **Severity:** nit
- **Title:** AMD Qwen2.5-VL bring-up examples for ROCm pass `--limit-mm-per-prompt video=0`. On `vllm/vllm-openai-rocm:v0.17.1` this crashes argparse before the engine starts.
- **Description:** Earlier vLLM examples (and AMD's ROCm Qwen2.5-VL bring-up walkthroughs) use the shorthand `--limit-mm-per-prompt video=0` to disable video on a multimodal model. On v0.17.1 the argument's type is JSON-loaded, and the shorthand crashes:
  ```
  vllm serve: error: argument --limit-mm-per-prompt: Value video=0 cannot be converted to <function loads at 0x...>.
  ```
  The container exits in <5 seconds and the user has to chase the error to the `argparse` line in `vllm/entrypoints/cli/serve.py`. The fix is either to omit the flag (default is unrestricted, harmless for our workload) or to pass JSON: `--limit-mm-per-prompt '{"video": 0}'`.
- **Repro steps:**
  1. Run `docker run … vllm/vllm-openai-rocm:v0.17.1 Qwen/Qwen2.5-VL-7B-Instruct --port 8000 --api-key EMPTY --limit-mm-per-prompt video=0`.
  2. Container exits within seconds with the argparse error above.
- **Suggested fix:** Either keep accepting the `key=value` shorthand alongside JSON for backward compatibility (cheap), or — if the JSON migration is intentional — update AMD's published Qwen2.5-VL ROCm bring-up examples and the vLLM error message to suggest the JSON form (`--limit-mm-per-prompt '{"video": 0}'`).
- **Logs / artifacts:**
  ```
  [serve_vllm] mode=prod — Qwen2.5-VL-72B-Instruct (BF16, single MI300X)
  WARNING 05-05 10:33:08 [gpt_oss_triton_kernels_moe.py:56] Using legacy triton_kernels on ROCm
  …
  vllm serve: error: argument --limit-mm-per-prompt: Value video=0 cannot be converted to <function loads at 0x7881cbba2fc0>.
  ```

### 7. AITER JIT kernel build directory is inside the container; `docker run --rm` discards it

- **Severity:** medium
- **Title:** Re-running the same `vllm serve` command against the same model + same ROCm release re-spends 20+ minutes on AITER kernel JIT compilation, because the JIT build directory lives inside the container's writable layer at `/usr/local/lib/python3.12/dist-packages/aiter/jit/build/`. The standard `docker run --rm` lifecycle blows it away on every restart.
- **Description:** Cold-start cost on `vllm/vllm-openai-rocm:v0.17.1` for `Qwen/Qwen2.5-VL-72B-Instruct` on MI300X is ~22 minutes wall clock — ~94 s of weight load and ~20 minutes of AITER JIT (rmsnorm alone took 1188 s on a fresh container). On a second startup the same minute we expected a JIT cache hit and got the full cold compile again. We initially assumed the cache lived in `/root/.cache/aiter/` or `/root/.cache/torch/`; it doesn't. Strace and `find` showed the JIT artifacts get written to `/usr/local/lib/python3.12/dist-packages/aiter/jit/build/` *inside the container*. Without an explicit volume mount, `docker run --rm` deletes that path with the container.

  This is non-obvious because:
  - The official `serve_vllm` examples on AMD's docs all use `--rm` and do not mount any AITER cache directory.
  - There is no warning during JIT compile that says "this work will not persist."
  - A user who builds a snapshot of the host (we did, via DigitalOcean droplet snapshot) reasonably expects the AITER cache to come back with the snapshot — it doesn't, because it was never on the host.
- **Repro steps:**
  1. `docker run --rm vllm/vllm-openai-rocm:v0.17.1 Qwen/Qwen2.5-VL-72B-Instruct --port 8000 --api-key EMPTY --max-model-len 16384 --gpu-memory-utilization 0.95` — wait ~22 min for ready.
  2. `docker stop vllm-72b && docker rm vllm-72b`.
  3. Re-run the same command on the same droplet, same image, same model. Expect ~2-min warm start. Observe ~22-min cold start instead. The `[aiter] start build [module_rmsnorm]` line returns.
- **Suggested fix:** One of —
  - **Document loudly** that AITER's JIT cache lives in `/usr/local/lib/python3.12/dist-packages/aiter/jit/build/` (or wherever AITER stores it), and add a `-v /var/cache/aiter:/usr/local/lib/python3.12/dist-packages/aiter/jit/build` example to AMD's vLLM-on-MI300X bring-up guide. This buys ~20 minutes on every restart for free.
  - **Move the cache to a sane host-side default** — e.g., `/root/.cache/aiter/` or `$AITER_CACHE_DIR` — so it lives where users already think to mount caches. Most ROCm users already mount `~/.cache/huggingface`; a sibling default for AITER would be invisible-by-default the way it should be.
  - **Pre-bake** the AITER JIT cache into `vllm/vllm-openai-rocm:vX.Y.Z` for the most common (model, dtype, mi300x) combinations. The image is already 30+ GB; an extra few hundred MB of pre-compiled kernels would erase the worst recurring developer-experience tax in this stack.
- **Logs / artifacts:** Wall-clock difference between cold and warm AITER paths is the entire signal here — see `docs/BENCHMARKS.md` "Cold-start" section.

---

_Findings 1–7 captured 2026-05-05 to 2026-05-10 during Day 1 / Day 2 bring-up of Qwen2.5-VL-72B-Instruct on a single MI300X via DO ATL1 + vLLM 0.17.1. Finding #7 was discovered when we restored the droplet from a snapshot and observed a full cold AITER JIT recompile despite the host-side HF cache being intact._
