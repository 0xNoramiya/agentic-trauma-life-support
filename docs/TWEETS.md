# Build-in-Public tweet thread — pre-staged

Three tweet sets following playbook §9. **Read each one out loud before posting** — make sure it sounds like you, an emergency physician, not like marketing copy. Adjust freely. Tag @AIatAMD on X (and @AMDDeveloper / AMD Developer on LinkedIn) and @lablab on X (lablab.ai on LinkedIn).

The minimum-bar for the Build-in-Public extra prize is 2 social posts; 3 sets gives you margin and a thread on Day 5.

---

## Day 1 tweet (post after the 7B smoke test passes)

> Day 1 of the AMD Developer Hackathon.
>
> Building **Agentic Trauma Life Support (ATLS)**: a vision-language model running the ATLS primary survey on chest X-rays + dictated vitals.
>
> Single MI300X. Full BF16. No quantization, no NVLink.
>
> Smoke test green on Qwen2.5-VL-7B. Bringing up the 72B tomorrow.
>
> The 192GB HBM3 is what makes this single-GPU. H100 (80GB) and H200 (141GB) can't fit it.
>
> @AIatAMD @lablab #AMDDeveloperHackathon

**Attach:** screenshot of `rocm-smi --showproductname` and a snippet of the first vision response.

---

## Day 3 tweet (after RAG + verifier wired up)

> ATLS Day 3: Drafter → Verifier → Renderer pipeline live.
>
> Two model calls on the same MI300X-served Qwen2.5-VL-72B:
> 1. Drafter generates ATLS primary-survey JSON via vLLM guided JSON
> 2. Verifier re-examines image vs. draft and patches inconsistencies
>
> Caught a hallucinated pneumothorax laterality on the bad-case fixture. The pattern works.
>
> @AIatAMD @lablab

**Attach:** screenshot of the verifier_notes section catching the inconsistency.

---

## Day 5 thread (submission)

> 🧵 Submitted **Agentic Trauma Life Support** to the AMD Developer Hackathon.
>
> The pitch: a structured ATLS primary-survey assistant for global ER trauma triage, served on one accessible GPU.
>
> 1/

> 📦 What it is:
> - Chest X-ray + dictated vitals in (any language)
> - Structured ATLS primary-survey JSON + SBAR handoff out
> - Multilingual (English + Bahasa Indonesia)
> - Drafter/Verifier agentic pattern for clinical safety
>
> 2/

> 🖥 Why MI300X:
> Qwen2.5-VL-72B in BF16 = ~145 GB weights.
> - H100 (80 GB): can't fit
> - H200 (141 GB): can't fit
> - **MI300X (192 GB): fits with margin**
> - B200 (192 GB): fits but 3-5× the cost
>
> 3/

> 📊 Benchmarks on a single MI300X:
> - TTFT: [X] ms
> - Throughput: [Y] tok/sec
> - Peak VRAM: [Z] GB
> - Single-MI300X serves what 2× H100 + NVLink would, at ~half the per-hour cost.
>
> Full numbers + methodology: [link to docs/BENCHMARKS.md]
>
> 4/

> 📝 Engineering writeup:
> ~2,400 words on the bring-up — the cost-accessibility argument, the single-GPU-72B math, the Drafter/Verifier pattern, the 235B-AWQ spike (skipped, with rationale), and 5 numbered ROCm feedback items.
>
> [blog post link]
>
> 5/

> 🔧 Real ROCm friction caught + reported:
> 1. DO Quick Start image's hidden JupyterLab grabs port 8000
> 2. AITER first-run JIT silence for 10+ min during cold start
> 3. `--trust-remote-code` no-op on v0.17.1 (with confusing warning)
> 4. Image entrypoint inconsistency between rocm/vllm-dev:nightly and vllm/vllm-openai-rocm:vX.Y.Z
> 5. SE Asia ISP SSH MITM on port 22 to DO public IPs — Tailscale workaround
>
> AMD eng team — full details + repros: [link to docs/ROCM_FEEDBACK.md]
>
> 6/

> 🔗 Repo: <https://github.com/0xNoramiya/agentic-trauma-life-support>
> 🎮 Live demo (7B): [HF Space link]
> 🎬 Pitch video: [YouTube link]
> 🩺 Built by an emergency physician
>
> 7/

> @AIatAMD @lablab — thanks for the platform. ROCm has come a long way and the 192GB single-GPU class genuinely changes the deployment economics for global health applications.
>
> 8/8

---

## Optional bonus — a thread on the credibility case alone

This one is not required but if any tweet is going to land with non-AMD-audience clinicians, this is it. Post it after the Day 5 thread, or as a standalone reply.

> The hardest case for any vision-language triage tool is the one where the image is clean.
>
> A 34-year-old MVC ejection with abdominal seatbelt sign, BP 102/64, HR 118 is **shocky**.
>
> The temptation for a VLM is to invent a "small left effusion" or "mild contusion" to "explain" the vitals.
>
> The bleeding is below the diaphragm.
>
> If your triage assistant invents thoracic findings to match shock from a pelvic source, it's worse than no assistant.
>
> ATLS Day [N] — case 05 is the test case for this. The model has to say "imaging unremarkable, recommend FAST + CT abdomen/pelvis" and stop. It does. That's the whole pitch for clinical credibility.
>
> [demo screenshot of case 05 handoff]

---

## Posting checklist

- [ ] Day 1 tweet posted with @AIatAMD + @lablab tags + #AMDDeveloperHackathon
- [ ] Day 3 tweet posted (or the day the verifier landed if the schedule slipped)
- [ ] Day 5 submission thread posted (8 tweets)
- [ ] Cross-posted to LinkedIn with appropriate handles (AMD Developer, lablab.ai)
- [ ] Screenshot of the lablab submission confirmation included in the Day 5 thread
- [ ] Bonus: case 05 standalone tweet (high signal for clinician audience)
