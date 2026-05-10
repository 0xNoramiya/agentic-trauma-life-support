# Demo outputs — six cases on real Qwen2.5-VL-72B

One-page summary of the six demo cases run end-to-end against the live MI300X (drafter → verifier → renderer pipeline). Full per-case JSON in this directory; rendered SBAR handoffs are reproducible by feeding the JSON through `src/ats/render/handoff_en.py` or `handoff_id.py`.

> Setup: `Qwen/Qwen2.5-VL-72B-Instruct` BF16 on a single MI300X, vLLM 0.17.1 ROCm, AITER kernels, single-GPU (no tensor parallelism). Schema-constrained via OpenAI-canonical `response_format={"type": "json_schema", ...}`. Median end-to-end pipeline wall clock 46–60 s per case (`docs/BENCHMARKS.md`).

## Case-by-case

### case_01 — Tension pneumothorax (drama case, EN)

- **Vignette:** 30 M, motorbike vs car, ejected ~6 m. RR 32, SpO₂ 88, HR 124, BP 92/60, GCS 14. Decreased breath sounds left, JVD, tracheal deviation right.
- **Imaging findings (drafter):** tracheal deviation right (severe); decreased lung volume left (severe).
- **Red flag:** **Tension pneumothorax** → *"Insert large-bore chest tube on the left side now."*
- **Disposition:** urgent, transfer to trauma bay; CT chest/abdomen/pelvis; CBC + type & cross + coags.
- **Confidence:** high.
- **Verifier:** correctly removed an unsupported JVD-on-X-ray claim from the evidence chain (JVD is a clinical sign, not radiographic) — kept the tension PTX call intact. **Catches model hallucinating evidence to support a correct conclusion.**

### case_02 — Massive hemothorax + shock (EN)

- **Vignette:** 45 M, industrial fall, impaled briefly on rebar. RR 28, SpO₂ 92, HR 132, BP 78/42, GCS 14.
- **Imaging findings (drafter):** opacification of the right hemithorax, blunted costophrenic angle on the right.
- **Red flag:** *"Hypotension with tachycardia and blunted right costophrenic angle"* → chest tube on the right.
- **Verifier:** **flagged the laterality** — *"the chest X-ray shows significant opacification of the **left** hemithorax rather than the right."* The drafter had it on the wrong side; verifier patched.
- **Why this case matters:** demonstrates the verifier catching a real laterality error. In a clinical setting, a chest tube on the wrong side is a never-event.

### case_03 — Flail chest (EN)

- **Vignette:** 67 F, restrained driver in head-on MVC at ~80 km/h. Multiple lateral rib fractures suspected.
- **Imaging findings (drafter):** multiple left-sided rib fractures, paradoxical motion suggested.
- **Red flag:** *"Flail chest with paradoxical motion"* → high-flow O₂, consider positive-pressure ventilation.
- **Verifier:** *"The chest X-ray does not clearly show a flail segment with paradoxical motion. The concern level for breathing may be overestimated."* — **downgraded** the drafter's confidence.
- **Confidence (final):** moderate.
- **Why this case matters:** verifier catching the drafter overshooting based on plausible vignette + ambiguous image.

### case_04 — Pulmonary contusion (EN)

- **Vignette:** 22 M, crushed by scaffolding, brief LOC at scene. RR 24, SpO₂ 93 RA, HR 110, BP 118/72, GCS 14.
- **Imaging findings (drafter):** patchy bilateral airspace opacities consistent with pulmonary contusion.
- **Red flag:** *"Potential for respiratory failure due to bilateral pulmonary contusions"* → prepare for intubation if needed.
- **Disposition:** urgent, ICU admission with respiratory monitoring.
- **Verifier:** confirms bilateral contusion correlates with mild tachypnea + supplemental O₂ requirement.

### case_05 — Normal CXR + concerning vitals (THE CREDIBILITY CASE, EN)

- **Vignette:** 34 M, ejected from MVC at highway speed, prominent abdominal seatbelt sign, mild abdominal tenderness. Chest cleared clinically and radiographically.
- **Imaging findings (drafter):** chest unremarkable.
- **Red flag:** **Hypovolemic shock** → fluid resuscitation now.
- **Recommendation:** **escalate to abdominal imaging + FAST**, not chest intervention.
- **Why this case matters:** **the model does not invent a chest finding to justify the shock-level vitals.** A vision-language triage tool that hallucinates findings to match the clinical picture is *worse* than no tool. Case 05 is the demonstration that the drafter+verifier discipline holds when the right answer is "the chest is clean — look elsewhere."
- **This is the one case that, if it lands well in the demo video, sells the clinical credibility of the entire system.**

### case_06 — Pediatric trauma (Indonesian)

- **Vignette (Bahasa Indonesia):** Anak laki-laki 8 tahun, KLL motor vs mobil, terlempar ~3 m. RR 35, SpO₂ 91 RA, HR 130, TD 90/60, GCS 14. Suara napas menurun di paru kanan.
- **Imaging findings (drafter):** decreased breath sounds right, possible right hemothorax.
- **Red flag:** drafter recommended immediate right-sided chest tube. **Verifier overrode**: *"the chest X-ray shows no clear evidence of a significant right-sided hemothorax to justify immediate chest tube placement."*
- **Final language:** Indonesian — SBAR handoff (`render_id`) renders headers/labels in Bahasa Indonesia; enum values stay English so schema validates regardless of UI language.
- **Why this case matters:** multilingual pipeline + verifier catching an over-aggressive procedural recommendation in a pediatric patient.

## Headline observations

- **2 of 6 cases**, the drafter made a clinically meaningful error (case_02 laterality, case_03 over-call) — the verifier caught both.
- **1 of 6 cases (case_05)** is the explicit "do nothing wrong" test — drafter correctly declined to invent. This is the credibility story.
- **1 of 6 cases (case_06)** is multilingual — full Indonesian rendering, schema validates.
- **Median end-to-end wall clock 46–60 s** (drafter + verifier + renderer + RAG retrieval), all cases ≤ 60 s.
- All six cases assigned `priority: urgent`. The disposition urgency is appropriately high for the scenarios; the differentiation is in the *what to do next* path (chest tube vs. abdominal imaging vs. respiratory support vs. ICU admission), not in *how urgent.*

## Reproducibility

```bash
# Local mock-mode (returns the fixture; for CI / quickstart):
uv run python scripts/run_demo_cases.py --case case_01_tension_ptx

# Live MI300X (requires vLLM running on the droplet, .env pointed at it):
MOCK_MODE=false uv run python scripts/run_demo_cases.py --case case_05_normal_polytrauma
```

The case fixtures (vignettes + expected findings) live in `tests/fixtures/cases/{case_id}.json`. The chest X-ray images are not committed (licensing); see `docs/DEMO_CASES.md` for direct source URLs.
