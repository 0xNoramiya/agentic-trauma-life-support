# lablab.ai submission — copy/paste fields

Field-by-field draft for the lablab.ai submission. **Paste-and-tweak on Day 5; do not submit verbatim without re-reading.** All `<placeholder>` items need to be filled in immediately before submission.

---

## Project Title

**Agentic Trauma Life Support (ATLS)**

---

## Short Description (1–2 sentences)

The agentic AI realization of the ATLS primary survey on chest X-ray plus dictated vitals — multilingual, citation-backed, served by Qwen2.5-VL-72B in full BF16 on a single AMD Instinct MI300X. Decision support for trauma triage in resource-limited settings.

---

## Long Description (~500 words)

**Trauma is the leading cause of death age 1–44 worldwide.** The global standard for managing it — Advanced Trauma Life Support (ATLS) from the American College of Surgeons — is a structured, time-pressured walk through Airway → Breathing → Circulation → Disability → Exposure. ATLS works because someone trained walks it. In rural ERs and resource-limited settings, that someone trained is often a junior clinician on a phone link, or a referral chain that takes hours.

**Agentic Trauma Life Support (ATLS)** is the agentic AI realization of the ACS protocol of the same name (the double entendre is intentional). A clinician uploads a chest X-ray, dictates vitals plus a brief vignette, picks a language, and presses Generate. The output is a structured ATLS primary-survey JSON — every ABCDE assessment populated, imaging findings tagged with laterality and severity, citations into a retrieved guideline corpus (ACS TQIP / EAST PMG / WHO / StatPearls), red flags called out, a disposition with urgency windows on every action — rendered as an SBAR-style handoff in English or Bahasa Indonesia.

**The agentic pipeline is Drafter → Verifier → Renderer.** The Drafter generates the structured JSON via vLLM's guided JSON decoding against a strict Pydantic schema. The Verifier — the same model in a clinical-safety-reviewer prompt — re-examines the image against the draft and emits patches plus notes for inconsistencies, including the most important one: the model inventing a "mild" chest finding to justify shock-level vitals when the bleeding source is actually intra-abdominal. We have a dedicated demo case for that hallucination pattern (case_05), and the model has to get it right.

**The single-MI300X argument is the load-bearing technical claim.** Qwen2.5-VL-72B-Instruct in BF16 is ~145 GB of weights. H100 (80 GB) and H200 (141 GB) cannot fit it. MI300X (192 GB HBM3) fits with margin and serves the workload at sub-$2 per hour — the only option that combines "fits the model" with the cost story the global-health use case requires. The B200 fits but at 3–5× the per-hour cost. We benchmark TTFT, throughput, and peak VRAM on a single MI300X and ship the numbers in the engineering blog post.

**Build-in-Public artifacts** ship alongside the demo: a 2,400-word engineering blog post on the bring-up (`docs/BLOG_POST.md`), a numbered ROCm feedback document with five real findings from Day 1 (`docs/ROCM_FEEDBACK.md`), a writeup of the Day 1 235B-AWQ spike (skipped, with rationale, in `docs/SPIKE_235B_AWQ.md`), a multilingual demo with both English and Indonesian outputs, and 23 passing tests covering the schema, renderers, verifier patch logic, drafter validation retry, and end-to-end mock-mode pipeline.

**Built by a practicing emergency physician.** MIT licensed. Decision support only — not a diagnosis, not for unsupervised clinical use.

---

## Technology Tags

- vLLM
- ROCm
- Qwen2.5-VL
- AMD MI300X
- Hugging Face
- Gradio
- FAISS
- Pydantic
- Python
- Vision-Language Models
- Healthcare / Medical AI

---

## Category Tags

- Vision and Multimodal (Track 3)
- AI Agents
- Healthcare
- Decision Support
- Trauma / Emergency Medicine

---

## Cover Image

**What to use:** a 1200×630 PNG composite of (a) the rendered handoff from case 01 (tension pneumothorax) on the right, with the highlights called out (B critical, red flag, immediate priority, citations), and (b) the project name + tagline on the left. No stock photography, no flat-design illustrations.

**Generate it from:** a clean run of `case_01_tension_ptx` in the Gradio UI, screenshotted from the rendered Markdown view, then composed in any image editor.

---

## Video Presentation

**YouTube unlisted URL:** _<paste after recording per `docs/DEMO_SCRIPT.md`>_

3 minutes max. Script and shot list in `docs/DEMO_SCRIPT.md`.

---

## Slide Presentation

**PDF or Google Slides link:** _<paste PDF link>_

Source markdown in `docs/SLIDES.md`. Export to PDF before submitting.

---

## Public GitHub Repository URL

<https://github.com/0xNoramiya/agentic-trauma-life-support>

---

## Demo Application Platform

Hugging Face Spaces (under the AMD Developer Hackathon HF Organization)

---

## Application URL

_<paste HF Space URL after deploy>_

---

## Engineering Blog Post (optional but encouraged)

`docs/BLOG_POST.md` in the repo. Cross-post to Medium / dev.to before submission for the Build-in-Public extra prize.

---

## Build-in-Public extras (separate prize)

- [ ] Minimum 2 social posts tagging @AIatAMD and @lablab on X (templates in playbook §9)
- [x] Open-source repo (MIT)
- [x] Technical walkthrough (the engineering blog post)
- [x] Meaningful ROCm / Developer Cloud feedback (`docs/ROCM_FEEDBACK.md` — five numbered findings)

---

## Pre-submit checklist

- [ ] Re-read every field above; replace every `<placeholder>` and `_pending_` line with real content
- [ ] Verify the HF Space loads and runs case 01 end-to-end before pasting the URL
- [ ] Verify the YouTube video runtime is ≤ 3:00
- [ ] Verify the GitHub repo is public, has the MIT license, and the README's "Demo" section links resolve
- [ ] Engineering blog post live (Medium/dev.to/GH Pages — at least one)
- [ ] Take a screenshot of the lablab submission confirmation. Tweet it.
