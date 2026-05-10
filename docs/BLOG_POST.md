# Serving Qwen2.5-VL-72B in full BF16 on a single MI300X for trauma decision support

Most trauma deaths happen where there isn't a trauma surgeon on call. The global standard for managing them — the American College of Surgeons' Advanced Trauma Life Support (ATLS) primary survey — is a structured, time-pressured walk through Airway → Breathing → Circulation → Disability → Exposure. It works because someone trained walks it. In the rural ER and the LMIC casualty department where most trauma actually arrives, that "someone trained" is increasingly often a junior clinician, a nurse on a phone link, or a referral chain that takes hours to reach the next decision-maker.

This is a story about whether we can put a clinically-credible structured triage assistant in front of those clinicians, on hardware they could actually deploy. The model is Qwen2.5-VL-72B-Instruct in full BF16 — no quantization, no CPU offload, no tensor parallelism. The hardware is a single AMD Instinct MI300X, sub-$2 per hour on AMD's developer cloud. The output is a structured ATLS primary survey JSON plus an SBAR-style handoff, in English or Bahasa Indonesia, with citations to ACS TQIP / EAST / WHO / StatPearls.

The pitch in one sentence: **Qwen2.5-VL-72B in BF16 is the largest open vision-language model that fits on the most cost-accessible 192GB-class GPU, and "most cost-accessible 192GB-class GPU" is exactly the constraint the global health use case has.**

## 1. Why we picked AMD

The cost-accessibility argument starts with the memory math. Qwen2.5-VL-72B-Instruct is roughly 145 GB of safetensors in BF16 (we measured 137 GB on disk after the HF download — close enough to the architectural calculation). Add a KV cache for `--max-model-len 16384` and `--max-num-seqs 4` and you're around 170-180 GB before headroom. The 192GB-class GPUs that can actually hold that workload, on a single device, are:

- **AMD Instinct MI300X** — 192 GB HBM3, ~$1.99/GPU/hr on AMD-partnered clouds (DigitalOcean, RunPod, others)
- **NVIDIA B200** — 192 GB HBM3e, $5-8/GPU/hr depending on the cloud
- **AMD Instinct MI325X / MI355X** — 256 GB / 288 GB HBM3e, but much harder to access right now
- **NVIDIA H200** — 141 GB. Doesn't fit.
- **NVIDIA H100** — 80 GB. Doesn't fit.

For the workload we care about, MI300X is the only option that combines "fits the model" with "the rural-ER cost story doesn't fall apart." A single H200 can't run this. Two H100s with NVLink can, but that's a 2× hardware cost, plus the operational complexity of tensor-parallel serving on hardware that costs you collective overhead on every forward pass. B200 fits but at 3-5× the per-hour rate, which makes the cost-accessibility framing harder to defend with a straight face.

That's the wedge AMD is selling. We took it at face value and built around it.

## 2. The use case in 60 seconds

The product is **Agentic Trauma Life Support (ATLS)** — the name is a deliberate double entendre with the ACS protocol of the same acronym. A clinician uploads a chest X-ray (or a phone photo of one), dictates or types vitals plus a brief vignette ("30-year-old male, motorbike vs car, ejected, helmeted. RR 32, sat 88 RA, BP 92/60, HR 124, GCS 14."), picks a language, and presses Generate. Output is a structured ATLS primary-survey object — every ABCDE assessment populated, imaging findings tagged with laterality and severity, citations into a retrieved guideline corpus, red flags called out, a disposition recommendation with urgency windows on every action — rendered as an SBAR handoff in English or Bahasa Indonesia.

The product positions itself as **decision support, not diagnosis**. Every output ships with a disclaimer to that effect. The point is not to replace the trauma physician — it's to give the on-call rural clinician the structured walk of the protocol with a citation trail back to ACS TQIP / EAST PMG / WHO / StatPearls, in the language they speak, in roughly the time it takes to read it.

## 3. The single-GPU 72B argument

It's worth being precise about why single-GPU matters. The 72B BF16 demo could in principle be run today on 2× H100 80GB with `--tensor-parallel-size 2` and NVLink. Two reasons that's the wrong shape for this product.

**One — the cost story.** A 2× H100 box on a public cloud is roughly $4-5/hr, not $2. Spread over enough requests that probably amortizes, but the framing for the use case is "deployable in resource-limited settings." Two GPUs is twice the GPUs. That breaks the framing.

**Two — operational simplicity.** Tensor-parallel serving works, but it adds an entire class of concerns: NCCL versioning, NVLink topology, partial failure across the collective, longer cold starts because `vllm serve` has to pin and warm all peer GPUs before the first token. We ran into a non-trivial number of bring-up frictions on a single MI300X (see section 8) — and not one of them was about NCCL or peer-to-peer, because there are no peers. For a five-day single-developer hackathon, "the unit of deployment is one GPU" is a meaningful simplification.

The MI300X's 192 GB HBM3 is what makes the simplification possible. On the same hardware we can serve 72B at `--max-model-len 16384` `--max-num-seqs 4` with `--gpu-memory-utilization 0.95` and still have headroom for the multimodal vision encoder. None of those numbers are aggressive — they are the comfortable middle of the curve.

## 4. Bring-up: ROCm + vLLM + Qwen2.5-VL-72B

The canonical command lives in `scripts/serve_vllm.sh prod` and reduces to:

```bash
docker run -d --name vllm-72b \
  --device /dev/kfd --device /dev/dri --group-add video \
  --ipc host --network host --shm-size 16G \
  -v /root/.cache/huggingface:/root/.cache/huggingface \
  -e VLLM_ROCM_USE_AITER=1 \
  -e VLLM_ROCM_USE_AITER_MHA=1 \
  -e SAFETENSORS_FAST_GPU=1 \
  -e MIOPEN_FIND_MODE=FAST \
  -e HF_TOKEN="$(cat ~/.cache/huggingface/token)" \
  vllm/vllm-openai-rocm:v0.17.1 \
    Qwen/Qwen2.5-VL-72B-Instruct \
    --max-model-len 16384 --max-num-seqs 4 \
    --gpu-memory-utilization 0.95 \
    --limit-mm-per-prompt video=0 \
    --port 8000 --api-key EMPTY
```

A few notes on what's in there.

**The image.** `vllm/vllm-openai-rocm:v0.17.1` ships preloaded on DigitalOcean's ROCm Quick Start image, version-pinned, and has `[vllm serve]` as its Docker entrypoint — so command-line args are positional/flag args to `vllm serve` directly. Slightly different from `rocm/vllm-dev:nightly` which most ROCm Qwen2.5-VL bring-up examples use. We've documented the inconsistency in `docs/ROCM_FEEDBACK.md` finding #4 — it's the kind of thing where `docker inspect` solves it in a minute, but only after you spend ten minutes wondering why argparse thinks your model name is a subcommand.

**The env toggles.** `VLLM_ROCM_USE_AITER=1` enables AMD's AITER kernels (the fastest path on MI300X). `VLLM_ROCM_USE_AITER_MHA=1` switches multi-head attention onto the same path. `SAFETENSORS_FAST_GPU=1` does direct safetensors → GPU loads, which cuts cold-start materially. `MIOPEN_FIND_MODE=FAST` skips the exhaustive autotune that MIOPEN does on first run.

**The flags.** `--limit-mm-per-prompt video=0` keeps the multimodal slot reserved for images only — we never feed video. `--gpu-memory-utilization 0.95` is comfortable on 192 GB; we never had to back it off. `--max-num-seqs 4` is conservative for a hackathon demo where p95 latency matters more than throughput.

**Things we used to think were necessary, and aren't.** `--trust-remote-code` is silently ignored on v0.17.1 ("argument is to be used with Auto classes; has no effect here") — vLLM has its own native `Qwen2_5_VLForConditionalGeneration` loader. The flag is harmless but produces a startup warning that we read as concerning the first time. Dropped it from the production command. (Finding #3 in ROCM_FEEDBACK.)

## 5. Numbers

Representative single-MI300X numbers from `scripts/run_benchmarks.py`, n=5 per scenario, streaming chat-completion against the live vLLM server over Tailscale (laptop in Indonesia → DO ATL1 droplet):

- **TTFT (single image, short ~150-token vitals):** **862 ms median, 1506 ms p95**
- **TTFT (single image, ~3k-token retrieved context):** **864 ms median, 1018 ms p95** — interestingly the same; image encoding through the vision tower is the dominant prompt-prefill cost, not the text portion
- **Sustained throughput:** **23.1 tok/sec median (short), 23.7 tok/sec (long context)** — consistent regardless of input size
- **Total per-call wall clock (drafter pass, ~220-token output):** 9.6 s median, 10.1 s p95
- **End-to-end pipeline (drafter + verifier on the six demo cases):** 46–60 s, **median ~55 s**
- **Cold start to API ready:** ~22 minutes on first run after droplet boot — almost all of which is AITER kernel JIT compilation (the rmsnorm kernel alone took 1188 s on a fresh MI300X). The hidden silence during this window is captured as `docs/ROCM_FEEDBACK.md` finding #2.
- **Peak VRAM under `--max-num-seqs 4`:** ~150–185 GiB / 192 GiB depending on KV-cache fill — comfortably under the 0.95 utilization budget.

Full per-scenario table with p50/p95 in [`docs/BENCHMARKS.md`](BENCHMARKS.md).

The cost-comparison table that goes with these numbers:

|                 | Single MI300X | 2× H100 (NVLink) | Single H200 | Single B200 |
|-----------------|---------------|-------------------|-------------|-------------|
| Fits 72B BF16   | yes (~75% util) | yes (TP=2)       | no          | yes         |
| $ / hour (cloud) | ~$1.99       | ~$4-5            | n/a         | ~$5-8       |
| Cold start      | ~12 min       | ~10-15 min (TP)  | n/a         | ~10 min     |
| Operational complexity | single-GPU | TP + NCCL    | n/a         | single-GPU  |

## 6. Drafter / Verifier and clinical safety

The pipeline is two model calls to the same vLLM server, with the same image embedded both times.

**Drafter** takes the chest X-ray, the dictated vitals, and the top-k chunks retrieved from the guideline corpus, and produces a strictly-shaped `TriageOutput` JSON via vLLM's guided JSON decoding (`extra_body={"guided_json": TriageOutput.model_json_schema()}`). The schema is non-trivial: nested ABCDE assessments, imaging findings tagged with laterality and severity, recommended actions with urgency windows, red flags with concrete evidence, citations with verbatim quotes. The drafter system prompt walks through the protocol explicitly and includes one-shot in-context example for tension pneumothorax to anchor format.

**Verifier** is the same model in a different prompt. It re-sees the original X-ray and the drafter's JSON and emits a small `VerifierOutput` of `{verifier_notes, patches}` — zero or more notes, zero or more `{path, value}` corrections to the draft. Patches are applied via a small in-file path-walker (`primary_survey.B_breathing.imaging_findings[0].laterality`-style paths) on a deep copy of the draft, then the result is re-validated against the schema.

The point of the verifier is to catch a specific class of clinical-safety failures. The two patterns that motivated it:

- **A finding with `laterality: "n/a"` for a side-having pathology.** "Pneumothorax with laterality n/a" is a red flag for hallucinated content — pneumothoraces always have a side. The verifier patches them to a chosen side based on the image, or removes the finding.
- **The case-05 pattern: a "mild" chest finding that exists primarily to justify shock-level vitals.** This is the failure mode we worry about most for clinical credibility. A patient with abdominal seatbelt sign, BP 102/64, HR 118 looks shocky — and a vision-language model with too much narrative bias can cheerfully invent a "small left-sided pleural effusion" or "mild contusion" to "explain" the vitals. **The shock is from a non-thoracic source.** The drafter prompt is explicit about this ("polytrauma + shock + clean chest is the classical presentation of intra-abdominal or pelvic hemorrhage; the bleeding is below the diaphragm, not above it"), and the verifier prompt has the same pattern called out by name as something to flag and patch out.

We have an explicit demo case for this. Case 05 (`docs/DEMO_CASES.md`) is a 34-year-old MVC ejection with a normal chest X-ray and BP 102/64 / HR 118. The model has to say "imaging unremarkable, recommend FAST + CT abdomen/pelvis" — not invent a pathology to match the vitals. **If only one case lands well in the demo video, this is the one.** A vision-language triage tool that hallucinates findings to match the clinical picture is worse than no tool. A tool that correctly says "the chest is clean — look elsewhere" is the entire pitch for clinical credibility.

## 7. The 235B-AWQ spike

We considered taking a Day 1 swing at running Qwen3-VL-235B in AWQ on the single MI300X — a flashier headline ("a 235B vision MoE on one accessible GPU") and a meaningful test of the AMD AWQ path. We didn't ship it.

The full writeup is in [`docs/SPIKE_235B_AWQ.md`](SPIKE_235B_AWQ.md). The short version: Day 1's bring-up budget was partly consumed by a network-side issue (more on that in section 8), and the realistic remaining spike window was below the playbook's hard cap of 4 hours for a clean go/no-go on a 235B model. The risk-adjusted return on a fresh 235B-AWQ landing in that window was negative — a stalled spike would have eaten the morning of Day 2 in error-mode rather than driving the 72B path forward, and the 72B BF16 single-MI300X claim is the load-bearing pitch on its own. Skipped. The writeup of the consideration is itself an artifact.

If the rest of the hackathon runs ahead of schedule, the spike comes back as a follow-on. `scripts/serve_vllm.sh spike` is intentionally left as a stub for that case.

## 8. What we'd want from AMD next

The full friction list is in [`docs/ROCM_FEEDBACK.md`](ROCM_FEEDBACK.md), with severity, repro steps, and suggested fixes for each. The five items captured during Day 1 bring-up:

1. **The DigitalOcean ROCm Quick Start image silently grabs port 8000 with a JupyterLab container.** The first time you run `vllm serve … --port 8000`, vLLM crashes with `OSError: [Errno 98] Address already in use` and you have to chase it down to a Docker container called `rocm` that nobody told you was there. Friction. Either bind JupyterLab to localhost, or add a login banner.

2. **AITER first-run JIT compile produces no progress messages for 10+ minutes.** The last log line you see after weights load is `[aiter] start build [module_rmsnorm]`, and then you wait. Friction. A `tqdm` line per kernel — or better, ship a precompiled AITER cache in the official image keyed by `(gfx942, vllm-version)` — would turn a "is this dead?" experience into a "okay, working" one.

3. **`--trust-remote-code` is accepted but silently ignored on v0.17.1.** The startup logs say `argument is to be used with Auto classes; has no effect here`, which misleads users following older bring-up examples. Nit. Fix the docs or the warning.

4. **`rocm/vllm-dev:nightly` and `vllm/vllm-openai-rocm:vX.Y.Z` take different command shapes** — one needs `vllm serve <model> …`, the other has `[vllm serve]` as the entrypoint and takes `<model> …` directly. Nit. Pick one.

5. **The most consequential one for the AMD AI Developer Program APAC cohort: SE Asia ISP SSH MITM.** We're in Indonesia. The developer's laptop ↔ DO public IP path is transparently intercepted by the ISP on port 22 — host-key fingerprint mismatch, `Permission denied (publickey)` with zero entries in the droplet's `/var/log/auth.log`, packets never reach sshd. Other ports get RST'd or filtered too. The fix is an overlay network — we used Tailscale, which works on the free tier in five minutes. We landed on it and moved on, but a non-trivial fraction of the AMD AI Developer Program cohort signs up from APAC and is going to bounce off this. A single page in the cloud-bring-up docs ("if you're outside the US and SSH to the public IP is acting weird, install Tailscale") would solve it.

None of these are showstoppers. Together they cost us roughly two hours of Day 1.

## 9. Repo and demo

- Repo: <https://github.com/0xNoramiya/agentic-trauma-life-support>
- **Live demo (72B on the actual MI300X):** <https://huggingface.co/spaces/lablab-ai-amd-developer-hackathon/atls> — the Space is a thin Gradio front-end that calls our vLLM endpoint directly, so a click there hits the same model weights, the same AITER kernels, the same `response_format=json_schema` path described above. The MI300X droplet is powered down outside live-demo windows; if a click returns "Backend unreachable," the box is asleep — see the recorded demo video for the full live run.
- Demo video: _pending recording_
- Built by an emergency physician for the AMD Developer Hackathon, May 2026.
- License: MIT.
