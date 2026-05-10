# Build-in-Public — LinkedIn posts

Four technical updates chronicling the build of **Agentic Trauma Life Support (ATLS)** for the AMD Developer Hackathon. Each post is paired with a cover-image prompt you can paste into ChatGPT (any DALL-E / GPT image variant) — they share a clinical-editorial aesthetic so the four covers read as a series.

> **Voice check before posting:** read each one out loud. You're a practicing emergency physician building this — keep the tone confident, specific, and human. Adjust anything that sounds like marketing copy.

**Tag everywhere:** `lablab.ai` and `AMD Developer` — LinkedIn auto-suggests both as Pages once you start typing the @.

**Hashtag bundle (use ~5 per post):** `#AMDDeveloperHackathon #MI300X #ROCm #vLLM #AgenticAI #VisionLanguageModels #HealthcareAI #BuildInPublic #ATLS #TraumaCare`

---

## Post 1 — Bring-up & the single-MI300X argument

**Headline:** *Day 1 — Why Qwen2.5-VL-72B on one MI300X is the entire pitch.*

**Body:**

Started Day 1 of the AMD Developer Hackathon by getting **Qwen2.5-VL-72B-Instruct in BF16** running on a *single* AMD Instinct MI300X. No tensor parallelism. No quantization. No CPU offload. One GPU, one container, full precision.

Why this matters for the use case (trauma triage decision-support, deployable in resource-limited settings):

→ 72B BF16 weights are ~145 GB.
→ NVIDIA H100 has 80 GB. Doesn't fit.
→ NVIDIA H200 has 141 GB. Doesn't fit.
→ **AMD MI300X has 192 GB HBM3. Fits with margin.**
→ NVIDIA B200 also has 192 GB but lists at 3–5× the per-hour rate on every cloud I checked.

For the global-health, rural-ER deployment shape this product targets, the MI300X is the only sub-$2/hour GPU that fits 72B in BF16 on a single device. Two H100s with NVLink works, but that's 2× the hardware cost plus tensor-parallel operational complexity (NCCL versioning, partial-failure handling, longer cold starts).

The single-GPU shape isn't an optimization — it's the architectural argument.

Stack so far:

• `vllm/vllm-openai-rocm:v0.17.1` Docker image
• AITER kernels enabled (`VLLM_ROCM_USE_AITER=1`)
• `--gpu-memory-utilization 0.95` (sits comfortably ~78% utilized at idle)
• OpenAI-canonical `response_format={"type": "json_schema", ...}` for guided structured output

One real bring-up papercut for AMD: the AITER first-run JIT compile produces *no progress messages* for 10+ minutes after weights load. The last log line you see is `[aiter] start build [module_rmsnorm]`, and then you wait 1188 seconds wondering if the box hung. A `tqdm` line per kernel — or a precompiled AITER cache shipped in the official image — would turn a "is this dead?" experience into "okay, working."

Logging that one, plus 6 others, in a numbered ROCm feedback doc for AMD.

`#AMDDeveloperHackathon` `#MI300X` `#ROCm` `#vLLM` `#BuildInPublic` `lablab.ai` `AMD Developer`

**Cover image prompt (Post 1):**

> Editorial magazine-cover composition on a warm off-white paper background (#F8F7F4). Centered: a single AMD MI300X data-center GPU rendered in clean technical line-illustration style, deep ink color (#1A1F2E), no logos, no glow effects, no flat-design playfulness. Above the GPU, in restrained serif type, the words "ONE GPU" in deep ink. Below the GPU, in small all-caps sans-serif, "192 GB HBM3 · QWEN2.5-VL-72B · BF16". To one side, a vertical hairline rule in muted sage green (#3A7A6E) with three short horizontal tick marks indicating memory thresholds: a small tick labeled "H100 80GB", a medium tick labeled "H200 141GB", and a tall tick labeled "MI300X 192GB" — the last one in sage green. Generous negative space. The aesthetic is a serious medical or engineering journal, not a SaaS landing page. No people, no stock-photo doctors, no glowing AI brain imagery. 16:9.

---

## Post 2 — The agentic pipeline (Drafter → Verifier → Renderer)

**Headline:** *Day 2 — Three agents on the same model, and why the second one matters most.*

**Body:**

Most "AI for medicine" demos are a single prompt, a single completion, a confident answer. That's the wrong shape for a tool that has to be safe.

ATLS uses a three-agent pipeline on the same Qwen2.5-VL-72B / MI300X / vLLM stack:

**1. Drafter** reads the chest X-ray + the vitals + the top-k retrieved guideline excerpts (FAISS over ACS TQIP / EAST PMG / WHO / StatPearls), and writes a strictly-typed `TriageOutput` JSON via vLLM's `response_format=json_schema`. No prose. No hand-waving. Every ABCDE assessment populated, every imaging finding tagged with laterality and severity, every recommended action with an urgency window.

**2. Verifier** is the same model in a different prompt. It re-sees the original X-ray and the drafter's JSON, and emits a small `VerifierOutput` of `{verifier_notes, patches}` — zero or more notes, zero or more `{path, value}` corrections to the draft. Patches are applied via a small in-file path-walker on a deep copy of the draft, then re-validated against the schema.

**3. Renderer** turns the validated JSON into an SBAR-style markdown handoff in English or Bahasa Indonesia. Schema enums stay English so the JSON validates regardless of UI language.

Why two model calls instead of one?

Yesterday's run on case_02 (massive hemothorax, blunt thoracic trauma) — the drafter generated a confident, well-structured ABCDE assessment recommending a chest tube *on the wrong side*. The radiograph showed left-sided opacification. The drafter said right.

The verifier caught it:

> "The chest X-ray shows significant opacification of the **left** hemithorax rather than the right, indicating a possible hemothorax on the left side. The draft's recommendation to insert a chest tube on the right side should be re-evaluated."

In a real ED, a chest tube on the wrong side is a never-event. The same model, talking to itself in a different voice, caught a clinically meaningful error in 13 seconds.

This is the bet: structured outputs + a cheap second pass on the same image > confident single-shot generation, *every time*, when the cost of being wrong is high.

Repo + the actual JSON outputs: github.com/0xNoramiya/agentic-trauma-life-support

`#AgenticAI` `#VisionLanguageModels` `#vLLM` `#HealthcareAI` `#BuildInPublic` `lablab.ai` `AMD Developer`

**Cover image prompt (Post 2):**

> Editorial composition, warm off-white paper canvas (#F8F7F4). Three labeled rectangles in a horizontal row, separated by thin sage-green arrows (#3A7A6E): the first labeled "Drafter" in deep-ink (#1A1F2E) serif, the second "Verifier" in deep-ink serif, the third "Renderer" in deep-ink serif. Each rectangle has a small italic "01", "02", "03" above the name in sage green. Underneath each box, one short line of body text in light sans-serif: "writes the JSON" / "re-checks the image" / "SBAR handoff". The middle box ("Verifier") has a single subtle terracotta-red asterisk (#B8463A) next to the number, suggesting it's the safety-critical step. Generous margins, no decoration, no people, no doctor stock-photo, no abstract neural-network swirls. The aesthetic is restrained editorial, like a textbook diagram in a serious medical journal. 16:9.

---

## Post 3 — The credibility test (case_05)

**Headline:** *Day 3 — The hardest test for a clinical vision model: an unremarkable X-ray.*

**Body:**

Here's the case that, if it lands, sells the entire system. If it doesn't, nothing else matters.

A 34-year-old man, ejected from a vehicle at highway speed, prominent abdominal seatbelt sign, mild abdominal tenderness. Vitals: HR 118, BP 102/64, RR 22, SpO₂ 97 % on room air. The chest X-ray is **completely unremarkable.**

Most vision-language models, given an X-ray plus shock-level vitals, will *invent something*. A subtle effusion. A small contusion. *Anything* to "explain" the clinical picture. That's narrative bias. In a real ED that's a misdirected workup, a delay to surgery, and the patient bleeds out from a splenic laceration nobody looked for.

We ran case_05 on the live MI300X. Median wall clock end-to-end: 57 seconds.

The Drafter said:

> *"Imaging unremarkable. No discrete findings on this view."*

And then escalated to the right place:

> *"Recommend FAST exam and CT abdomen / pelvis. Hemodynamic concern is consistent with intra-abdominal source given mechanism + seatbelt sign."*

The verifier confirmed the call and added a note:

> *"The chest X-ray appears unremarkable, but the patient has concerning vital signs and a mechanism suggesting intra-abdominal injury. The drafter correctly does not invent a chest pathology; the workup should target the abdomen."*

What this took, technically:

→ A drafter-prompt rule (the case-05 anti-invent rule) that explicitly tells the model "polytrauma + shock + clean chest = look below the diaphragm. Do not invent a chest finding."
→ Per-section `concern_level` discipline in the schema — the section that's wrong drives urgency, not always Breathing.
→ A verifier with explicit case-05-pattern recognition built into its prompt: a "mild" finding paired with shock vitals is flagged.

A vision-language triage tool that hallucinates chest pathology to match clinical context is *worse* than no tool. A tool that correctly says "the chest is clean — look elsewhere" is the entire pitch for clinical credibility.

Sample output: github.com/0xNoramiya/agentic-trauma-life-support/blob/main/docs/demo_outputs/case_05_normal_polytrauma.json

`#HealthcareAI` `#PatientSafety` `#TraumaCare` `#VisionLanguageModels` `#BuildInPublic` `lablab.ai` `AMD Developer`

**Cover image prompt (Post 3):**

> Editorial pull-quote layout on a warm off-white paper background (#F8F7F4). Centered, large display serif italic, deep ink (#1A1F2E): the words "Imaging unremarkable. Recommend FAST and CT abdomen." Just to the upper-left of the opening of the quote, a single oversized opening curly quotation mark (") rendered in muted terracotta red (#B8463A) — the only saturated color on the page. Below the quote, in small all-caps sans-serif at lower opacity: "CASE 05 · NORMAL CXR WITH HYPOTENSION · MODEL DECLINED TO INVENT". Generous margins. No imagery, no faces, no medical equipment, no abstract decoration. The composition reads like a quote pulled from a serious clinical journal — restraint and weight. 16:9.

---

## Post 4 — Live demo + real numbers + ROCm bring-up findings

**Headline:** *Day 4 — Live demo wired straight to the MI300X. The real numbers, the real workload.*

**Body:**

The HuggingFace Space for ATLS is now live, and it's pointed *directly* at our vLLM endpoint on the MI300X. Not a different model. Not an inference-API hop. The Space is a thin Gradio front-end that calls Qwen2.5-VL-72B-Instruct on the actual hardware described in the engineering writeup. **What you click is what we serve.**

Live demo: huggingface.co/spaces/lablab-ai-amd-developer-hackathon/atls

I also re-ran the benchmark suite with a real chest X-ray (case_01 tension pneumothorax) instead of the 1024×1024 grey placeholder I'd been using. The numbers shifted in interesting ways:

| Scenario (n=5, real CXR + ATLS prompt) | TTFT median | Throughput | Total wall |
|---|---:|---:|---:|
| Single image + 150-token prompt | 1981 ms | 19.9 tok/s | 15.4 s |
| Single image + 3 k-token retrieved-context | 1982 ms | 21.5 tok/s | 15.9 s |
| Concurrent batch of 4 | 2199 ms | 18.4 tok/s | 15.1 s |

**Peak VRAM under concurrent batch-of-4: 183.95 / 191.69 GiB (96 %)** — sits exactly at the `--gpu-memory-utilization 0.95` budget, exactly as advertised.

One number worth dwelling on: **real-CXR TTFT is 2.3× the same call with a flat-grey placeholder image** (1981 ms vs 862 ms). Same model, same path, but a uniform grey gives the vision tower nothing to encode and it short-circuits. I had been benchmarking against grey for two days and only caught it when the real X-ray went through. Worth a sanity-check item on anyone else's vision-language benchmark setup.

I also documented something AMD will care about: AITER's JIT kernel cache lives *inside* the container's writable layer at `/usr/local/lib/python3.12/dist-packages/aiter/jit/build/`. We measured **414 MB** of compiled kernels there. The standard `docker run --rm` lifecycle blows them away on every restart, costing ~20 minutes of cold-start AITER recompile *every single time*. We discovered it the hard way after restoring a droplet from a snapshot and watching a "warm" restart take the same 22 minutes as cold.

Mounting that directory as a host volume — or pre-baking the cache into `vllm/vllm-openai-rocm:vX.Y.Z` for common (model, dtype, gfx942) combinations — is the single highest-impact developer-experience change AMD could ship for ROCm-side vLLM. That's finding #7 in our numbered feedback doc; the other six are also up for AMD's review.

Repo + benchmarks + the seven-finding ROCm feedback doc: github.com/0xNoramiya/agentic-trauma-life-support

`#AMDDeveloperHackathon` `#MI300X` `#ROCm` `#vLLM` `#Benchmarks` `#BuildInPublic` `lablab.ai` `AMD Developer`

**Cover image prompt (Post 4):**

> Editorial composition on warm off-white paper (#F8F7F4). Three vertical bars in a row showing memory utilization: the first bar short and unfilled (light grey #D9D6D0), labeled "H100 80 GB" in small caps; the second medium and unfilled grey, labeled "H200 141 GB"; the third tall and filled in muted sage green (#3A7A6E), labeled "MI300X 192 GB" with a small italic checkmark above. Above the bars, in restrained display serif deep-ink (#1A1F2E): "TTFT 1981 ms". Below the bars, in small all-caps sans-serif: "PEAK VRAM 183.95 / 191.69 GiB · 96%". Optionally, a thin sage hairline at the bottom with the text "$1.99 / GPU-hour" in tabular numerals. No people, no graphs with axes, no busy decoration — just the bars, the numbers, and the typography. The composition reads as a single number-driven editorial figure, like the data spread of a financial-research note. 16:9.

---

## Optional Post 5 — Submission day (write after recording the demo video)

**Headline:** *Day 5 — Submitted. The pitch in one sentence.*

**Body:**

Submitted **Agentic Trauma Life Support (ATLS)** to the AMD Developer Hackathon today.

The pitch in one sentence:

> Qwen2.5-VL-72B in full BF16 is the largest open vision-language model that fits on the most cost-accessible 192 GB-class GPU, and "most cost-accessible 192 GB-class GPU" is exactly the constraint the global-health trauma-triage use case has.

What's in the submission:

→ Live demo on HuggingFace Spaces, served directly from a single MI300X
→ 27 passing tests covering schema, renderer, verifier, retrieval, end-to-end
→ A 2,400-word engineering blog post on the bring-up
→ A numbered ROCm feedback document with 7 real findings (port-8000 conflict, AITER JIT silence, AITER cache persistence, command-shape inconsistency, SE-Asia ISP MITM, argparse format change, the `--trust-remote-code` no-op)
→ Real benchmark numbers on the actual workload, with operational evidence committed (vLLM startup log, rocm-smi snapshots, AITER cache listing)
→ Six demo cases — one (case_05) explicitly designed to test the "do not invent" property of the verifier
→ Multilingual rendering (English + Bahasa Indonesia)
→ MIT licensed

What this hackathon convinced me of: the cost-accessibility argument for AMD's 192 GB GPUs is real and load-bearing for healthcare AI deployed outside academic medical centers. Sub-$2 per GPU-hour for a model that fits H200 cannot fit, on a stack (vLLM + ROCm + AITER) that's mature enough to ship — that's a different sentence than it would have been a year ago.

Thanks to AMD Developer for the MI300X access and lablab.ai for the hackathon. I'll keep building.

Live demo: huggingface.co/spaces/lablab-ai-amd-developer-hackathon/atls
Repo: github.com/0xNoramiya/agentic-trauma-life-support
Engineering writeup: docs/BLOG_POST.md inside the repo

`#AMDDeveloperHackathon` `#MI300X` `#ROCm` `#vLLM` `#HealthcareAI` `#BuildInPublic` `lablab.ai` `AMD Developer`

**Cover image prompt (Post 5):**

> Editorial closing-frame composition on warm off-white paper (#F8F7F4). Centered, large display serif deep-ink (#1A1F2E): the wordmark "ATLS" in tight letterspacing. Beneath the wordmark, a short horizontal hairline rule in muted sage green (#3A7A6E). Below the rule, three lines of small sans-serif text in deep ink, left-aligned and stacked: "github.com/0xNoramiya/agentic-trauma-life-support" / "huggingface.co/spaces/lablab-ai-amd-developer-hackathon/atls" / "MIT · Built by an emergency physician for the AMD Developer Hackathon · May 2026". No imagery. No people. No abstract decoration. Generous top margin. The composition is the closing slide of a serious editorial deck — restrained, confident, finished. 16:9.

---

## Posting cadence suggestion

Day-by-day, posted in the morning local time (peak LinkedIn engagement window for healthcare/tech mixed audiences):

| Day | Post | When to publish |
|---|---|---|
| 1 | Post 1 — Bring-up + single-MI300X argument | After 7B smoke test passes (you can post before the 72B numbers come in; the memory-math argument stands either way) |
| 2 | Post 2 — Drafter / Verifier / Renderer | After the first end-to-end run that produces a clean handoff |
| 3 | Post 3 — Credibility test (case_05) | After case_05 lands correctly on the live MI300X |
| 4 | Post 4 — Live demo + real benchmarks + ROCm feedback | After the HF Space deploys + you've captured the real-CXR numbers |
| 5 *(optional)* | Post 5 — Submission day | After lablab submission goes in |

If you only have time for four, **post 1, 2, 3, and 4** — they cover the technical arc without depending on the submission landing.

## What to avoid

- Don't lead with disclaimers ("not a medical device"). Put the technical claim first; the disclaimer goes in the repo and the in-app text where it belongs. LinkedIn isn't where you write the legal language.
- Don't use AI-cliché images: glowing brains, neural-network mesh overlays, a doctor in a futuristic hologram, etc. The cover-image prompts above explicitly avoid these.
- Don't overpromise. "Decision support" is the right framing; "AI doctor" is wrong.
- Don't tag people who didn't consent — only Pages (lablab.ai, AMD Developer). The two AMD employees you might be tempted to @-tag should @-engage you, not the other way around.
