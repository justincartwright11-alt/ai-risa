# AI-RISA Premium Report Factory — Button 2 Customer-Ready Report and Folder Actions Repair: Design v1

Date: 2026-05-02
Slice type: docs-only design
Scope: Button 2 only

## Problem

Button 2 now has working PDF download, but customer safety and operator reliability are still insufficient.

Observed state:
- Download PDF works.
- Open Reports Folder is not reliable enough.
- Copy PDF Path feedback is weak.
- Draft-only PDFs can still be generated with placeholder content like "prediction unavailable".
- Customer Ready can be false while a draft PDF still exists and can be opened.
- Missing Sections and analysis-missing error are present, but accidental weak-draft generation is still too easy.

## Goal

Make Button 2 customer-safe and idiot-proof by default while preserving explicit internal draft workflows.

## Design Requirements

1. Customer mode is default.
- In customer mode, if report_quality_status is not customer_ready, do not generate a customer PDF.

2. Draft output moved behind explicit secondary option.
- Label: Generate internal draft only — not customer ready.

3. Draft PDFs must be visibly marked.
- Required label/watermark: DRAFT ONLY — NOT CUSTOMER READY.

4. Draft PDFs must never be presented as customer exports.

5. Clear blocked state required in Button 2.
- Message: Cannot generate customer PDF yet. Analysis data is missing for this matchup.

6. Show missing sections before generation when possible.

7. Open Reports Folder must be reliable on Windows.
- Add local endpoint:
  POST /api/premium-report-factory/reports/open-folder
- Endpoint behavior: open local folder via OS shell and return success/failure payload.

8. Open PDF may continue to use the existing download endpoint.

9. Copy PDF Path must show explicit visible confirmation.
- Format:
  PDF path copied:
  C:\...\file.pdf

10. Result actions must remain separate.
- Download PDF
- Open Reports Folder
- Copy PDF Path

11. UI must never render jammed action text.

12. No Button 1 changes.
13. No Button 3 changes.
14. No result lookup changes.
15. No learning/calibration changes.
16. No billing changes.
17. No uncontrolled writes.

## Proposed Design

### A) Mode Model

Introduce explicit generation intent at Button 2 submit-time:
- customer_mode (default)
- internal_draft_mode (secondary explicit toggle)

Behavior:
- customer_mode:
  - require report_quality_status == customer_ready
  - otherwise block generation and surface missing sections + required blocked message
- internal_draft_mode:
  - allow generation when analysis is incomplete
  - mark report_quality_status = draft_only
  - stamp PDF with required draft-only label/watermark

### B) Pre-Generation Readiness Preview

Before final generation execution, return/compute readiness summary per selected matchup:
- customer_ready true/false
- report_quality_status
- missing_sections
- blocking message when applicable

Purpose:
- let operator see why generation is blocked before attempting customer export
- reduce accidental creation of weak drafts

### C) Draft Safety Rules

For any draft_only output:
- include DRAFT ONLY — NOT CUSTOMER READY label in report body (and preferred visible watermark in implementation)
- avoid customer-facing success language
- keep action area visually distinct from customer-ready success rows

### D) Folder Action Reliability

Use backend-assisted folder open action for Windows reliability:
- POST /api/premium-report-factory/reports/open-folder
- Request payload includes validated path or report identifier
- Backend resolves allowed folder target and executes OS open
- Response contract:
  - ok: true/false
  - opened_path
  - error (if failure)

### E) Copy Path Confirmation

After copy action succeeds, show non-ambiguous confirmation in Button 2 status area:
- PDF path copied:
- absolute path line beneath

If clipboard fails, show explicit failure fallback guidance.

### F) UI Rendering Rules

Action controls render as independent controls with spacing and no concatenation:
- Download PDF
- Open Reports Folder
- Copy PDF Path

Hard rule: no merged text rendering in table cells.

## Validation Plan

1. Customer mode with missing analysis blocks generation.
2. Draft mode with missing analysis generates draft_only output and visibly labels PDF as draft-only.
3. Open Reports Folder endpoint works on Windows and returns clear success/failure.
4. Copy PDF Path shows explicit copied-path confirmation.
5. Download PDF remains functional.
6. Existing Button 1/2/3 tests remain green.

## Out of Scope

- Any Button 1 behavior
- Any Button 3 behavior
- Result lookup or external data expansion
- Learning/calibration pipelines
- Billing/distribution expansion
- Non-Button-2 scope or Phase 4 expansion

## Design Verdict

Approved as docs-only design slice for the next design-review gate.
