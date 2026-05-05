# Demo assets

Demo X-rays for `scripts/run_demo_cases.py` go here as `assets/{case_id}.jpg`.

These files are **not committed** — they are excluded by `.gitignore` (the patterns `assets/case_*.jpg`, `assets/case_*.jpeg`, `assets/case_*.png`). Two reasons:

1. Most case sources (Radiopaedia, NIH ChestX-ray14) have licensing terms that allow viewing and clinical use but not unattributed redistribution. Pulling them into a public repo and shipping them with the wheel is the wrong default.
2. They are not small.

## Sourcing the files

See [`docs/DEMO_CASES.md`](../docs/DEMO_CASES.md) for the source URL of each case. After downloading, save the image as `assets/{case_id}.jpg`. The demo script falls back to a grey placeholder image if the file is missing, which is fine for a mock-mode walkthrough but produces meaningless output against the real model.

The expected files are:

```
assets/case_01_tension_ptx.jpg
assets/case_02_massive_htx.jpg
assets/case_03_flail_chest.jpg
assets/case_04_pulm_contusion.jpg
assets/case_05_normal_polytrauma.jpg
assets/case_06_pediatric_id.jpg
```
