# AI-RISA Premium Report Factory — Button 2 Premium Report Content and Download Actions Repair: Design v1

**Date:** 2026-05-02  
**Slice Type:** Docs-only design  
**Scope:** Button 2 (Generate & Export) only

---

## Problem Statement

Button 2 now creates a real PDF file, but report content is not customer-ready. Current exports can include placeholder sections such as:

- prediction unavailable
- decision structure unavailable
- energy projection unavailable
- fatigue analysis unavailable
- mental condition unavailable
- collapse trigger unavailable
- deception unavailable
- round-by-round projection unavailable

Additionally, dashboard action links can render poorly as jammed text (`Open PDFOpen Reports Folder`) and are not operator-proof.

---

## Goal

Button 2 must only produce customer-ready premium PDFs, or clearly block customer generation when analysis data is missing. Dashboard file actions must be explicit, separate, and reliable.

---

## Design Requirements

### 1) Add `report_quality_status`

Introduce quality state with only these values:

- `customer_ready`
- `draft_only`
- `blocked_missing_analysis`

### 2) `customer_ready` eligibility gate

A report can be marked `customer_ready` only if all required content is present and meaningful:

- headline prediction exists
- executive summary has real content
- matchup snapshot contains both fighters
- decision structure content exists
- energy use content exists
- fatigue failure points content exists
- mental condition content exists
- collapse triggers content exists
- deception and unpredictability content exists
- round-by-round control shifts content exists
- scenario and method pathways content exists
- risk warnings content exists
- operator notes content exists
- no major section contains `unavailable` placeholder language

### 3) Missing analysis must block silent customer generation

If required analysis data is missing, Button 2 must not silently generate a customer PDF. Surface this message:

`Cannot generate customer PDF yet. Analysis data is missing for this matchup.`

### 4) Optional draft mode (explicitly labeled)

Draft generation may be supported, but must be unmistakably labeled:

`DRAFT ONLY — NOT CUSTOMER READY`

### 5) Button 2 result contract additions

Result payload displayed in dashboard must include:

- `report_quality_status`
- `generated_pdf_path`
- `generated_pdf_size_bytes`
- `customer_ready` (boolean)
- `missing_sections` (list)
- `export_error` (if any)

### 6) Replace unclear links with explicit actions

Replace ambiguous links with separate actions:

- `Download PDF`
- `Open Reports Folder`
- `Copy PDF Path`

### 7) Prevent jammed action text

UI must not render actions as merged text (`Open PDFOpen Reports Folder`). Each action must be discrete and visually separated.

### 8) Future-safe download fallback route

If local file opening remains unreliable in browser contexts, add a future Flask route in implementation phase:

- `GET /api/premium-report-factory/reports/download/<report_id>`

### 9) No Button 1 changes

### 10) No Button 3 changes

### 11) No result lookup changes

### 12) No learning or calibration changes

### 13) No billing changes

### 14) No uncontrolled writes

### 15) No Phase 4 expansion

---

## Proposed Design (Docs-Only)

### A) Quality gate model

Define a deterministic evaluator that inspects required report sections and returns:

- `report_quality_status`
- `customer_ready` boolean
- `missing_sections` list
- optional `quality_message`

Quality rules:

- If any required section missing or placeholder-only -> `blocked_missing_analysis` (customer export blocked)
- If draft mode requested and missing sections exist -> allow file generation as `draft_only`
- If all required sections present and no placeholders -> `customer_ready`

### B) Placeholder detection policy

Treat known placeholder phrases as non-customer-ready signals, including case-insensitive matches for:

- `unavailable`
- `not available`
- `pending`
- `tbd`
- empty/whitespace-only section text

This policy is design intent for implementation; phrase list can be centralized in one helper.

### C) Export behavior contract

- `customer_ready` path: allow customer PDF generation and mark `report_quality_status=customer_ready`
- missing analysis without draft: block customer generation with required message and `report_quality_status=blocked_missing_analysis`
- missing analysis with draft mode: allow export only as draft, mark `report_quality_status=draft_only`, and stamp report/header with `DRAFT ONLY — NOT CUSTOMER READY`

### D) Button 2 UI behavior

Results panel row should show:

- quality status badge (`customer_ready`, `draft_only`, `blocked_missing_analysis`)
- generated path and size
- `customer_ready` boolean
- missing sections summary
- export error where applicable

Actions column should always render separate controls:

- `Download PDF` button/link
- `Open Reports Folder` button/link
- `Copy PDF Path` button

### E) Backward compatibility

- Preserve existing path/size proof behavior already sealed in prior slice
- Preserve generated-status guard requiring valid non-zero `.pdf`
- Do not alter Button 1 or Button 3 flow contracts

---

## Validation Plan (Design)

1. Generate a report with missing analysis:
- confirm generation is blocked for customer mode, or explicitly marked `draft_only` in draft mode
- confirm block message: `Cannot generate customer PDF yet. Analysis data is missing for this matchup.`

2. Generate a report with complete analysis:
- confirm `report_quality_status=customer_ready`
- confirm `customer_ready=true`

3. Confirm customer-ready PDFs do not include placeholder `unavailable` text for major sections.

4. Confirm Button 2 displays three separate actions:
- `Download PDF`
- `Open Reports Folder`
- `Copy PDF Path`

5. Confirm generated path and size remain visible.

6. Confirm existing Button 1/2/3 tests remain green after implementation.

---

## Out of Scope

- Implementation code changes
- New production endpoints in this design lock
- Schema migrations or queue model expansion beyond quality fields
- Any behavior outside Button 2

---

## Design Verdict

Approved as a docs-only repair design slice for the next implementation gate.
