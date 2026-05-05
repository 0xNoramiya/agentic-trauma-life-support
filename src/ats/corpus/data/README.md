# Corpus data

This directory holds the trauma guideline corpus that the retriever indexes. **PDFs are not committed** — they are excluded by `.gitignore` (the patterns `*.pdf` and `src/ats/corpus/data/raw/`). You need to source the documents yourself before running `scripts/build_index.py`.

## Layout

```
src/ats/corpus/data/
- README.md                # this file
- manifest.json            # NOT committed — you create this; describes the PDFs
- raw/                     # NOT committed except for .gitkeep
  - .gitkeep
  - <your_source_pdfs>.pdf
- index.faiss              # produced by scripts/build_index.py (gitignored)
- meta.jsonl               # produced by scripts/build_index.py (gitignored)
```

## manifest.json format

`scripts/build_index.py` reads `src/ats/corpus/data/raw/manifest.json`, a JSON array of entries.

**A ready-to-use template lives at [`manifest.json.example`](manifest.json.example)** in this directory. It lists six chest-trauma-heavy sources (EAST PMG × 3, ACS TQIP × 2, WHO × 1) with the exact filenames + the direct PDF URLs we used during the hackathon (`_download_url` field). Reproduce the corpus with:

```bash
mkdir -p src/ats/corpus/data/raw
# Pull the 6 PDFs (only the URLs in _download_url; other fields are runtime metadata)
cd src/ats/corpus/data/raw
curl -L -o east_pmg_pulmonary_contusion_flail_chest.pdf 'https://www.east.org/Content/documents/practicemanagementguidelines/Management_of_pulmonary_contusion_and_flail_chest_.13.pdf'
curl -L -o east_pmg_hemothorax_occult_pneumothorax.pdf 'https://www.east.org/Content/documents/practicemanagementguidelines/Practice%20Management%20Guidelines%20for%20Management%20of%20Hemothorax%20and%20Occult%20Pneumothorax.pdf'
curl -L -o east_pmg_blunt_cardiac_injury.pdf 'https://www.east.org/Content/documents/practicemanagementguidelines/Screening_for_blunt_cardiac_injury___An_Eastern.5.pdf'
curl -L -o acs_tqip_chest_wall_injuries.pdf 'https://www.facs.org/media/qdgliayt/2025_tr_bestpracticesguidelines_chest-wall.pdf'
curl -L -o acs_tqip_massive_transfusion.pdf 'https://www.facs.org/media/zcjdtrd1/transfusion_guildelines.pdf'
curl -L -o who_trauma_care_checklist.pdf 'https://hlh.who.int/docs/librariesprovider4/hlh-documents/who-trauma-care-checklist.pdf'
cd -

# Copy the manifest. The build_index script ignores fields starting with _.
cp src/ats/corpus/data/manifest.json.example src/ats/corpus/data/raw/manifest.json
```

Total raw: ~17 MB. After ingest, the index is 281 chunks (PyMuPDF text extraction + tiktoken cl100k_base 500-token windows with 50-overlap). Schema for each entry:

```json
{
  "file": "east_pmg_pulmonary_contusion_flail_chest.pdf",
  "source": "EAST PMG",
  "section": "Pulmonary Contusion / Flail Chest",
  "url": "https://www.east.org/education-resources/practice-management-guidelines"
}
```

- `file` is relative to the directory the manifest lives in.
- `source` is the citation label; it shows up in the rendered handoff under the citation list.
- `section` is the human-readable section name; the chunker overwrites this per-chunk with the actual page number, but it is good metadata for the manifest.
- `url` is propagated into every chunk derived from that PDF.

## Suggested sources

Open or freely-licensed materials that we recommend pulling for the demo:

1. **ACS TQIP — Best Practices Guidelines.** The American College of Surgeons publishes Best Practices documents for thoracic trauma, geriatric trauma, mass casualty, etc. These are the gold standard for trauma quality care in the US system.
   <https://www.facs.org/quality-programs/trauma/quality/best-practices-guidelines/>

2. **EAST PMG — Eastern Association for the Surgery of Trauma, Practice Management Guidelines.** Free to read on the EAST site. Good coverage of pneumothorax, hemothorax, blunt chest trauma, rib fractures.
   <https://www.east.org/education-resources/practice-management-guidelines>

3. **WHO — Integrated Management for Emergency and Essential Surgical Care (IMEESC).** Free WHO resource oriented toward resource-limited settings. Important for our pitch about cost-accessible deployment.
   <https://www.who.int/teams/integrated-health-services/clinical-services-and-systems/surgical-care>

4. **StatPearls — trauma chapters.** Free on NCBI Bookshelf. Useful for general-knowledge background on specific findings (flail chest, pulmonary contusion, etc.). Some chapters are exportable as PDF.
   <https://www.ncbi.nlm.nih.gov/books/NBK430685/>

## Building the index

After you place PDFs and a `manifest.json` under `raw/`:

```bash
python scripts/build_index.py
```

This produces `index.faiss` and `meta.jsonl` in this directory. Both are gitignored.

The retriever (`src/ats/retrieval/retrieve.py`) loads them lazily at first call. If they are missing, retrieval returns an empty list and logs a warning — the rest of the pipeline still runs.
