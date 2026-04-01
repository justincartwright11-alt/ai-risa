# AI-RISA Full Prim Report Pipeline: Operator Notes

## Final Script: run_full_auto_pipeline_final.py

This script is the locked, production-ready pipeline for generating AI-RISA Full Prim Reports with premium content, chart embedding, and robust DOCX/PDF export.

---

## Accepted Command Syntax

Run from the workspace or C:/ai_risa_data directory:

```
python run_full_auto_pipeline_final.py --mode event --event <event_id> --report "Full Prim Report" --format <md|docx|pdf>
```

- `--mode event` (required)
- `--event <event_id>` (required, e.g. boxing_cardiff_2026_04_04)
- `--report "Full Prim Report"` (required)
- `--format md` (Markdown, canonical output)
- `--format docx` (DOCX, master export)
- `--format pdf` (PDF, secondary export)

You may run all three formats in sequence for full validation.

---

## Output Paths

- Markdown: `./output/<event_id>_Full_Prim_Report.md`
- DOCX:     `./output/<event_id>_Full_Prim_Report.docx`
- PDF:      `./output/<event_id>_Full_Prim_Report.pdf`

All outputs are written to the `output/` subdirectory relative to the script.

---

## Rollback Anchors

The following files are safe rollback points for each major pipeline stage:

- `run_full_auto_pipeline_recovered_baseline.py`   # Baseline: content engine, parser, routing
- `run_full_auto_pipeline_recovered_tablepolish.py` # Table polish: markdown tables, section headers
- `run_full_auto_pipeline_recovered_visuals.py`     # Visuals: chart helpers, chart insertion
- `run_full_auto_pipeline_recovered_embed.py`       # Exporter: markdown image parsing, DOCX/PDF embedding
- `run_full_auto_pipeline_final.py`                 # Final: locked, production candidate

To rollback, copy the desired file to `run_full_auto_pipeline_final.py` and re-run your export command.

---

## Notes

- Only true TBA bouts are routed to the watchlist/incomplete section.
- Lauren Price vs. Stephanie Pineiro Aquino is the canonical premium bout for validation.
- Markdown is the canonical report body; DOCX and PDF are derived exports.
- Chart images are generated and embedded in DOCX/PDF if referenced in markdown.
- No placeholders remain in the premium content pipeline.
- All scripts are Python 3.8+ compatible.

---

For further changes, always branch from the most recent stable rollback anchor.
