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

`scripts/build_index.py` reads `src/ats/corpus/data/raw/manifest.json`, a JSON array of entries:

```json
[
  {
    "file": "acs_tqip_best_practices_thoracic_trauma.pdf",
    "source": "ACS TQIP",
    "section": "Best Practices in Thoracic Trauma",
    "url": "https://www.facs.org/quality-programs/trauma/quality/best-practices-guidelines/"
  },
  {
    "file": "east_pmg_pneumothorax.pdf",
    "source": "EAST PMG",
    "section": "Pneumothorax",
    "url": "https://www.east.org/education-resources/practice-management-guidelines"
  }
]
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
