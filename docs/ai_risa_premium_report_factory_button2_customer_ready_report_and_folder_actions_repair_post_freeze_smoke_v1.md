# AI-RISA Premium Report Factory - Button 2 Customer-Ready Report and Folder Actions Repair: Post-Freeze Smoke v1

**Date:** 2026-05-02  
**Scope:** Button 2 only (customer-mode default + internal draft mode + folder/copy/download actions)  
**Implementation under test:** `6eadd2b` (`ai-risa-premium-report-factory-button2-customer-ready-report-and-folder-actions-repair-implementation-v1`)

---

## Smoke Objective

Prove required behavior from locked design/design-review is live on the dashboard:

1. Customer mode is default (draft unchecked by default).
2. Missing analysis blocks customer PDF generation.
3. Internal draft mode is explicit and produces draft-only output.
4. Draft PDF artifact is visibly labeled `DRAFT ONLY - NOT CUSTOMER READY`.
5. Actions remain separate: `Download PDF`, `Open Reports Folder`, `Copy PDF Path`.
6. `Copy PDF Path` confirms exact copied path.
7. `Open Reports Folder` works via backend endpoint (`POST /api/premium-report-factory/reports/open-folder`).

---

## Environment

- App URL: `http://127.0.0.1:5000/?v=button2-smoke-final`
- Server start command: `python -m operator_dashboard.app`
- Queue record used: `prf_q_7b1e2a0d1275b54a` (Ares FC 39: Jbalia vs. Diatta)

---

## Run A - Customer Mode Default (Draft Unchecked)

### Steps

1. Open Button 2 and confirm `Generate internal draft only - not customer ready` is unchecked by default.
2. Select matchup `prf_q_7b1e2a0d1275b54a`.
3. Check `I approve generating and exporting customer PDFs`.
4. Click `Generate & Export`.

### Observed Result

- HTTP failure status surfaced in UI (`400`) with required message:

`Cannot generate customer PDF yet. Analysis data is missing for this matchup.`

- Results panel shows:
  - `Accepted: 0`
  - `Rejected: 1`
  - `No PDFs generated.`

Result: customer generation is blocked by default when analysis is missing.

---

## Run B - Internal Draft Mode Enabled

### Steps

1. Check `Generate internal draft only - not customer ready`.
2. Keep same matchup selected and approval enabled.
3. Click `Generate & Export`.

### Observed Result

- Export completed with one report (`Accepted: 1`, `Rejected: 0`).
- Quality-state columns present and populated:
  - `Quality Status = draft_only`
  - `Customer Ready = false`
  - `Missing Sections` populated
- Actions rendered separately in one row:
  - `Download PDF`
  - `Open Reports Folder`
  - `Copy PDF Path`

Result: internal draft flow is explicit and isolated from customer-ready status.

---

## Action Verification

### Copy PDF Path

- Clicked `Copy PDF Path` in generated row.
- Status confirmation rendered exact path string:

`PDF path copied: C:\ai_risa_next_dashboard_polish\ops\prf_reports\ai_risa_premium_report_ares_fc_39__jbalia_vs._diatta_prf_q_7b1e2a0d1275b54a_20260502.pdf`

Result: copy confirmation is explicit and includes full copied path.

### Open Reports Folder

- Clicked `Open Reports Folder` in generated row.
- Status confirmation rendered:

`Opened reports folder: C:\ai_risa_next_dashboard_polish\ops\prf_reports`

Result: folder open uses backend endpoint and returns success message with opened path.

### Download PDF

- Download action remained a separate control and URL shape is endpoint-based:

`/api/premium-report-factory/reports/download/<report_id>?file_name=<pdf_name>`

Result: download action remains separate and contract-stable.

---

## Draft PDF Label Verification

Generated artifact text extraction using `pypdf` confirmed label string is embedded in output:

`DRAFT ONLY - NOT CUSTOMER READY`

Snippet observed from extracted text:

- `AI-RISA Premium Report`
- `Aboubakar Jbalia vs Cherif Diatta`
- `DRAFT ONLY - NOT CUSTOMER READY`

Result: draft-only PDF labeling is present in the exported artifact (not UI-only).

---

## Requirement Pass/Fail Matrix

| Requirement | Result |
|---|---|
| Customer mode default is active | **PASS** (draft option unchecked by default) |
| Missing analysis blocks customer PDF generation | **PASS** |
| Internal draft mode is explicit | **PASS** |
| Draft PDF artifact contains draft-only label | **PASS** |
| Download/Open Folder/Copy Path are separate actions | **PASS** |
| Copy confirmation includes exact path | **PASS** |
| Open-folder action works via backend endpoint | **PASS** |

---

## Scope Guard Confirmation

- No Button 1 changes in this smoke slice.
- No Button 3 changes in this smoke slice.
- No result lookup changes.
- No learning/calibration changes.
- No billing changes.
- No uncontrolled write paths introduced.

---

## Smoke Verdict

**PASS.** Button 2 customer-ready defaults, internal draft controls, draft PDF labeling, and folder/copy/download actions behave as required by the locked design.