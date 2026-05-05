# Demo cases

> Clinical vignettes authored / reviewed by an emergency physician for the ATLS hackathon demo set. Each case is paired with a `tests/fixtures/cases/{case_id}.json` fixture used by `scripts/run_demo_cases.py`. Source X-rays are not redistributed (licensing) — download them from the source URL listed and place them at `assets/{case_id}.jpg`.

There are six cases. Five English, one Indonesian. Case 05 is **the credibility case** — a deliberately normal chest film paired with concerning vitals; the model must not invent chest pathology and must escalate to abdominal imaging + FAST.

## Case 01 — Tension pneumothorax

- **case_id:** `case_01_tension_ptx`
- **mechanism:** motorbike vs car, ejected
- **source:** Radiopaedia tension pneumothorax (open teaching case): <https://radiopaedia.org/articles/tension-pneumothorax>
- **vitals:** RR 32, SpO2 88% RA, HR 124, BP 92/60, GCS 14, temp 36.4°C
- **expected_findings:**
  - left tension pneumothorax
  - tracheal deviation to the right
  - decreased left-sided lung volume
- **expected_priority:** immediate
- **language:** en
- **clinical_vignette:** 30M motorbike vs car, thrown approximately 6 meters. Decreased breath sounds on the left, JVD, tracheal deviation right.

## Case 02 — Massive hemothorax with shock

- **case_id:** `case_02_massive_htx`
- **mechanism:** fall 5m onto rebar
- **source:** Radiopaedia massive hemothorax (open teaching case): <https://radiopaedia.org/articles/haemothorax>
- **vitals:** RR 28, SpO2 92%, HR 132, BP 78/42, GCS 14, temp 36.1°C
- **expected_findings:**
  - massive right hemothorax
  - complete opacification of the right hemithorax
  - mediastinal shift away from the affected side
- **expected_priority:** immediate
- **language:** en
- **clinical_vignette:** 45M industrial fall, impaled briefly on rebar. Hypotensive, tachycardic, dull to percussion on the right. Class III hemorrhagic shock.

## Case 03 — Flail chest

- **case_id:** `case_03_flail_chest`
- **mechanism:** head-on motor vehicle collision, restrained driver
- **source:** Radiopaedia flail chest (open teaching case): <https://radiopaedia.org/articles/flail-chest>
- **vitals:** RR 26, SpO2 90% on NRB, HR 108, BP 138/82, GCS 15, temp 36.6°C
- **expected_findings:**
  - multiple right-sided segmental rib fractures
  - underlying pulmonary contusion
  - paradoxical chest wall motion on exam
- **expected_priority:** urgent
- **language:** en
- **clinical_vignette:** 67F restrained driver in head-on MVC at ~80 km/h. Splinting respirations, paradoxical motion of the right anterior chest wall. Pain control and ICU admission with close respiratory monitoring.

## Case 04 — Pulmonary contusion

- **case_id:** `case_04_pulm_contusion`
- **mechanism:** crushed by collapsing scaffolding, brief loss of consciousness
- **source:** Radiopaedia pulmonary contusion (open teaching case): <https://radiopaedia.org/articles/pulmonary-contusion>
- **vitals:** RR 24, SpO2 93% on 4L NC, HR 102, BP 124/76, GCS 14, temp 36.7°C
- **expected_findings:**
  - patchy non-segmental opacities, predominantly right
  - no pneumothorax
  - no rib fractures appreciated on this view
- **expected_priority:** urgent
- **language:** en
- **clinical_vignette:** 22M crushed by scaffolding, brief LOC at scene. On 4 L NC, mildly tachypneic, no obvious external chest deformity. Monitor for ARDS over the next 24-72 hours.

## Case 05 — Normal CXR with concerning vitals (THE CREDIBILITY CASE)

- **case_id:** `case_05_normal_polytrauma`
- **mechanism:** ejected from a motor vehicle, abdominal seatbelt sign
- **source:** NIH ChestX-ray14 — "No Finding" label: <https://nihcc.app.box.com/v/ChestXray-NIHCC>
- **vitals:** RR 22, SpO2 97%, HR 118, BP 102/64, GCS 15, temp 36.5°C
- **expected_findings:**
  - chest radiograph **unremarkable** (the model must say so explicitly)
  - no pneumothorax, no hemothorax, no widened mediastinum
  - tachycardia and relative hypotension despite a normal CXR
- **expected_priority:** urgent
- **language:** en
- **clinical_vignette:** 34M ejected from MVC at highway speed, prominent abdominal seatbelt sign, mild abdominal tenderness. Polytrauma evaluation in progress; chest cleared clinically and radiographically.

> **This is the credibility case.** A normal chest film with concerning vitals is one of the most important calls a triage system can make. The model must **not** invent chest pathology. The expected disposition is to recommend CT abdomen/pelvis + FAST and escalate to trauma surgery — not to fabricate a pneumothorax that isn't there. Demos should run this case explicitly to show that the system reports a clean chest when the chest is clean.

## Case 06 — Pediatric trauma (Bahasa Indonesia)

- **case_id:** `case_06_pediatric_id`
- **mechanism:** kecelakaan lalu lintas, motor vs mobil, terlempar 3 meter
- **source:** Radiopaedia pediatric pulmonary contusion (open teaching case): <https://radiopaedia.org/articles/pulmonary-contusion>
- **vitals:** RR 35, SpO2 91%, nadi 130, TD 90/60, GCS 14, suhu 36.8°C
- **expected_findings:**
  - kontusio paru kanan
  - tidak ada pneumotoraks
  - tidak ada fraktur iga yang jelas pada proyeksi ini
- **expected_priority:** urgent
- **language:** id
- **clinical_vignette:** Anak laki-laki 8 tahun, kecelakaan lalu lintas (motor vs mobil), terlempar 3 meter. Takipneu, retraksi ringan, suara napas menurun di hemithoraks kanan. Output keseluruhan harus dalam Bahasa Indonesia (kecuali nilai enum skema yang tetap dalam token Inggris).

## How to run

```bash
# English cases
python scripts/run_demo_cases.py --case case_01_tension_ptx
python scripts/run_demo_cases.py --case case_02_massive_htx
python scripts/run_demo_cases.py --case case_03_flail_chest
python scripts/run_demo_cases.py --case case_04_pulm_contusion
python scripts/run_demo_cases.py --case case_05_normal_polytrauma --show-citations

# Indonesian case
python scripts/run_demo_cases.py --case case_06_pediatric_id --lang id
```

Each invocation writes the JSON output to `docs/demo_outputs/{case_id}.json` and prints the rendered handoff to stdout.
