# AI-RISA Premium Report Factory — Button 2 Premium Report Content and Download Actions Repair: Post-Freeze Smoke v1

**Date:** 2026-05-02
**Scope:** Button 2 only (quality gating + download actions)
**Implementation under test:** `4325d1c` (`...-implementation-v1`)

---

## Smoke Objective

Prove the implementation behavior required by the locked design/design-review:

1. Missing-analysis matchup is `blocked_missing_analysis` or `draft_only`, never `customer_ready`.
2. Dashboard shows `report_quality_status`.
3. `Download PDF` action is separate and works.
4. `Open Reports Folder` and `Copy PDF Path` are separate actions.
5. UI does not render jammed action text like `Open PDFOpen Reports Folder`.

---

## Environment

- App URL: `http://127.0.0.1:5000/?v=button2-quality-smoke-v1`
- Server: Flask restarted on local port 5000 before smoke
- Queue record used: `prf_q_7b1e2a0d1275b54a` (Ares FC 39: Jbalia vs. Diatta)

---

## Run A — Draft Allowed (`allow_draft=true`)

### Steps

1. Open Button 2 section and load queue.
2. Keep `Allow draft output when analysis is missing` checked.
3. Select matchup `prf_q_7b1e2a0d1275b54a`.
4. Check generation approval.
5. Click `Generate & Export`.

### Observed Result

- Results table rendered with quality columns including `Quality Status`, `Customer Ready`, `Missing Sections`.
- Row values:
  - `report_quality_status = draft_only`
  - `customer_ready = false`
  - `missing_sections` populated (`headline_prediction`, `executive_summary`, `decision_structure`, etc.)
- Export proof fields visible:
  - `generated_pdf_path` shown
  - `generated_pdf_size_bytes` shown as `3242 bytes (3.2 KB)`
- Action controls shown as separate labels:
  - `Download PDF`
  - `Open Reports Folder`
  - `Copy PDF Path`
- Jammed action text check:
  - `Open PDFOpen Reports Folder` **not present**

### Download Action Verification

Download href in row:

`/api/premium-report-factory/reports/download/prf_r_491615b1eb697325?file_name=ai_risa_premium_report_ares_fc_39__jbalia_vs._diatta_prf_q_7b1e2a0d1275b54a_20260502.pdf`

Fetch validation:

- HTTP status: `200`
- Content-Type: `application/pdf`
- Response bytes: `3242`

Result: `Download PDF` works as a separate actionable control.

---

## Run B — Draft Disabled (`allow_draft=false`)

### Steps

1. Uncheck `Allow draft output when analysis is missing`.
2. Keep same selected matchup.
3. Check generation approval.
4. Click `Generate & Export`.

### Observed Result

- Status message:

`Generation failed: matchup_id=prf_q_7b1e2a0d1275b54a: Cannot generate customer PDF yet. Analysis data is missing for this matchup.`

- Results summary:
  - `Accepted: 0`
  - `Rejected: 1`
  - `No PDFs generated.`
- Rejection reason includes required block text:

`Cannot generate customer PDF yet. Analysis data is missing for this matchup.`

Result: missing-analysis customer generation is blocked when draft mode is disabled.

---

## Requirement Pass/Fail Matrix

| Requirement | Result |
|---|---|
| Missing-analysis is blocked or draft_only, not customer_ready | **PASS** (`draft_only` in Run A, blocked in Run B; `customer_ready=false`) |
| Dashboard shows `report_quality_status` | **PASS** |
| `Download PDF` is separate and works | **PASS** (HTTP 200, `application/pdf`, non-zero bytes) |
| `Open Reports Folder` and `Copy PDF Path` are separate | **PASS** |
| No jammed `Open PDFOpen Reports Folder` text | **PASS** |

---

## Scope Guard Confirmation

- No Button 1 changes in this slice.
- No Button 3 changes in this slice.
- No result lookup changes.
- No learning/calibration changes.
- No billing changes.
- No uncontrolled write paths introduced.

---

## Smoke Verdict

**PASS.** Button 2 quality-state gating and download-action rendering behave as required by the locked design.
