# AI-RISA Premium Report Factory — Button 2 PDF File Path And Open Folder Repair Design v1

**Slice:** `ai-risa-premium-report-factory-button2-pdf-file-path-and-open-folder-repair-design-v1`
**Design date:** 2026-05-02
**Baseline commit:** `2a8902e`
**Baseline tag:** `ai-risa-premium-report-factory-button1-discovery-use-autofills-bouts-archive-lock-v1`
**Type:** docs-only design — no implementation in this slice

---

## Problem statement

Button 2 currently allows the operator to select a saved fight, approve Generate & Export, and observe a `generated` report status in the dashboard. However, the operator is not shown the actual usable PDF output path in the Button 2 results area.

Observed repository evidence shows:

- Actual `.pdf` files exist under `reports/`.
- `ops/prf_reports/` exists but contained zero-byte non-`.pdf` artifacts.
- The operator cannot reliably determine which file is the customer-ready PDF.

This means Button 2 export proof is not operator-safe enough. A `generated` status without a valid surfaced file path is insufficient.

---

## Design requirements

### R1 — Generate & Export must return and display exact PDF file path

After Button 2 Generate & Export completes for a selected saved fight, the backend response must include the exact resolved path to the generated PDF file, and the Button 2 results panel must display that path plainly.

The operator must not need to inspect the filesystem manually to find the report.

---

### R2 — Result row must show file size

For every successfully generated PDF, the Button 2 result row must display file size as either:

- raw bytes, or
- human-readable KB

The size must be based on the actual generated PDF file on disk.

---

### R3 — UI must provide Open PDF and Open Reports Folder actions

For each valid generated PDF surfaced in the Button 2 results panel, the UI must provide:

- **Open PDF** — opens the exact generated file
- **Open Reports Folder** — opens the directory that contains that generated file

These actions must target the real output location, even if the file is written under `reports/` rather than `ops/prf_reports/`.

---

### R4 — Backend/result contract must surface explicit export proof fields

The Button 2 backend/result contract must distinguish the following fields for every generated row:

```json
{
  "generated_pdf_exists": true,
  "generated_pdf_path": "C:/ai_risa_next_dashboard_polish/reports/ares_fc_39_2026_04_03_full_prim_report.pdf",
  "generated_pdf_size_bytes": 123456,
  "generated_pdf_openable": true,
  "export_error": ""
}
```

Required semantics:

- `generated_pdf_exists`: whether a valid PDF file exists on disk
- `generated_pdf_path`: exact resolved path to the generated PDF
- `generated_pdf_size_bytes`: actual file size in bytes
- `generated_pdf_openable`: true only when the resolved path points to a valid existing PDF file
- `export_error`: non-empty when export failed, or when a file artifact is invalid

---

### R5 — `generated` status requires a valid PDF file

A report may only be marked `generated` if all of the following are true:

- generated file path ends with `.pdf`
- file exists
- file size is greater than `0`

If any of those checks fail, the report must not be marked `generated`.

---

### R6 — Zero-byte files are failed exports

Any zero-byte export artifact must be treated as a failed export.

That artifact must not be counted as a usable generated report, even if it was created by the export process.

---

### R7 — Non-PDF artifacts are not generated PDFs

Any file that does not end in `.pdf` must not be counted as a generated PDF, even if it appears in a nominal export folder.

This explicitly excludes the zero-byte non-`.pdf` artifacts observed in `ops/prf_reports/`.

---

### R8 — Dashboard must display the real export path

If the export process writes the usable PDF to `reports/` instead of `ops/prf_reports/`, the Button 2 dashboard must display the real resolved file path.

The UI must reflect reality rather than an assumed output directory.

---

### R9 — Clear error when no valid PDF exists

If no valid PDF exists after Generate & Export completes, the Button 2 results panel must show:

> `PDF was not created. Check export error.`

This message must be paired with the surfaced `export_error` content when available.

---

### R10 — No Button 1 changes

This slice must not modify Button 1 behavior, contracts, or UI.

---

### R11 — No Button 3 changes

This slice must not modify Button 3 behavior, contracts, or UI.

---

### R12 — No Phase 4 expansion

No Phase 4 or adjacent roadmap work is in scope.

---

### R13 — No billing

No billing or customer accounting changes are in scope.

---

### R14 — No learning or calibration changes

No learning, calibration, or accuracy-pipeline changes are in scope.

---

### R15 — No uncontrolled writes

This slice must not introduce any uncontrolled writes.

Export remains an explicit Button 2 operator-approved action only.

---

## Design implications

### Backend implications

The Button 2 generate/export path must stop using status alone as proof of success. It must validate the real exported artifact and return a proof-oriented result contract.

The export result for each selected fight should be derived from the final resolved file on disk, not from an optimistic intermediate status.

If the export pipeline currently writes multiple artifacts or temporary placeholders, only the valid final `.pdf` file should drive `generated` status.

### Frontend implications

The Button 2 results area must evolve from status-only reporting to artifact-proof reporting.

For each row, the UI should display:

- matchup / event context
- generated status
- exact PDF path
- PDF size
- Open PDF action
- Open Reports Folder action
- clear export error message when no valid PDF exists

The current `generated` label alone is not sufficient.

---

## Validation plan

| Validation | Expected |
|---|---|
| Generate one saved fight PDF | Export flow completes with one result row |
| Returned path ends with `.pdf` | True |
| Returned file exists | True |
| Returned file size > 0 | True |
| UI displays path and size | Visible in Button 2 result row |
| Zero-byte export artifact | Not marked `generated` |
| Non-`.pdf` artifact | Not marked `generated` |
| Open Reports Folder action | Opens real folder containing surfaced PDF |
| Existing Button 1/2/3 tests | Remain green |

---

## Non-goals

The following are explicitly out of scope:

- Button 1 work of any kind
- Button 3 work of any kind
- endpoint expansion unrelated to Button 2 export proof
- billing logic
- learning/calibration logic
- Phase 4 or roadmap expansion
- cosmetic redesign outside the Button 2 result proof area

---

## Design summary

| Req | Description | Status |
|---|---|---|
| R1 | Display exact PDF file path | Designed |
| R2 | Display file size | Designed |
| R3 | Provide Open PDF and Open Reports Folder actions | Designed |
| R4 | Add explicit export proof fields to result contract | Designed |
| R5 | `generated` requires valid `.pdf`, existing file, size > 0 | Designed |
| R6 | Zero-byte files treated as failed export | Designed |
| R7 | Non-`.pdf` artifacts not counted as generated PDFs | Designed |
| R8 | UI shows real output path even if under `reports/` | Designed |
| R9 | Clear no-PDF error message | Designed |
| R10-R15 | Scope and governance constraints preserved | Confirmed |

---

## Next safe slice

```text
ai-risa-premium-report-factory-button2-pdf-file-path-and-open-folder-repair-design-review-v1
```

No implementation until design review is locked.
