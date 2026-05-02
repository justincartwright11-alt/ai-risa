# AI-RISA Premium Report Factory — Button 2 PDF File Path And Open Folder Repair Design Review v1

**Slice:** `ai-risa-premium-report-factory-button2-pdf-file-path-and-open-folder-repair-design-review-v1`
**Design commit:** `0804d93`
**Design tag:** `ai-risa-premium-report-factory-button2-pdf-file-path-and-open-folder-repair-design-v1`
**Review date:** 2026-05-02
**Reviewer:** Operator

---

## Purpose

This document is a formal design review of the Button 2 PDF file path and open folder repair design locked at `0804d93`. It confirms each design requirement is understood, scoped, and safe to implement. No implementation occurs in this slice.

---

## Review Checklist

### R1 — Generate & Export must return and display exact PDF file path

- **Design intent:** Button 2 must surface the exact resolved path to the generated customer PDF so the operator can reliably find the exported file.
- **Scope:** Button 2 backend generate/export response contract and Button 2 result panel in `operator_dashboard/templates/index.html`.
- **Risk:** Low. Additive result metadata and additive UI display.
- **Review verdict:** APPROVED. Acceptable to implement.

---

### R2 — Result row must show file size

- **Design intent:** Each generated PDF row must show actual file size from disk, in bytes or KB, so the operator can confirm the artifact is not empty.
- **Scope:** Button 2 backend response field plus Button 2 result row display.
- **Risk:** Low. Read-only filesystem stat.
- **Review verdict:** APPROVED. Acceptable to implement.

---

### R3 — UI must provide Open PDF and Open Reports Folder actions

- **Design intent:** The operator must be able to open the exact generated PDF and the folder containing it directly from Button 2.
- **Scope:** Button 2 result UI only. Requires safe open actions targeted at the surfaced path and containing folder.
- **Risk:** Low-medium. Implementation must use the real resolved path and avoid targeting placeholder artifacts.
- **Review verdict:** APPROVED. Acceptable to implement.

---

### R4 — Backend/result contract must expose export-proof fields

- **Design intent:** Button 2 response rows must include explicit proof fields:
  - `generated_pdf_exists`
  - `generated_pdf_path`
  - `generated_pdf_size_bytes`
  - `generated_pdf_openable`
  - `export_error`
- **Scope:** Button 2 backend generate/export result contract only.
- **Risk:** Low. Additive response fields. Existing consumers can continue reading prior fields.
- **Review verdict:** APPROVED. Acceptable to implement.

---

### R5 — `generated` requires valid PDF path, existence, and size > 0

- **Design intent:** A report must only be marked `generated` when the resolved artifact is a real `.pdf`, exists on disk, and has size greater than zero.
- **Scope:** Button 2 export completion and result-status assignment logic.
- **Risk:** Low-medium. Tightens success criteria and may expose currently masked failures, which is the intended repair.
- **Review verdict:** APPROVED. Acceptable to implement.

---

### R6 — Zero-byte files must be failed export

- **Design intent:** Zero-byte export artifacts are not usable PDFs and must be reported as failures.
- **Scope:** Button 2 export validation logic and result status messaging.
- **Risk:** None. This is a correctness guard.
- **Review verdict:** APPROVED. Acceptable to implement.

---

### R7 — Non-`.pdf` artifacts must not count as generated PDFs

- **Design intent:** Placeholder or sidecar files without a `.pdf` extension must not be treated as generated customer reports.
- **Scope:** Button 2 export artifact validation logic.
- **Risk:** None. This is a correctness guard.
- **Review verdict:** APPROVED. Acceptable to implement.

---

### R8 — Dashboard must display real output path even if under `reports/`

- **Design intent:** If export resolves to `reports/` instead of `ops/prf_reports/`, the Button 2 UI must show the real final path rather than an assumed output directory.
- **Scope:** Button 2 backend result population and Button 2 display logic.
- **Risk:** Low. This is a truthfulness requirement rather than a new feature.
- **Review verdict:** APPROVED. Acceptable to implement.

---

### R9 — Clear error when no valid PDF exists

- **Design intent:** If export does not produce a valid PDF, Button 2 must show: `PDF was not created. Check export error.`
- **Scope:** Button 2 result/error UI and backend `export_error` population.
- **Risk:** None. Clearer failure messaging only.
- **Review verdict:** APPROVED. Acceptable to implement.

---

### R10 — No Button 1 changes

- **Design intent:** This repair must not touch Button 1 behavior, contracts, or UI.
- **Scope:** All implementation diffs must exclude Button 1 surfaces.
- **Risk:** N/A (constraint).
- **Review verdict:** CONFIRMED. Must remain enforced in implementation.

---

### R11 — No Button 3 changes

- **Design intent:** This repair must not touch Button 3 behavior, contracts, or UI.
- **Scope:** All implementation diffs must exclude Button 3 surfaces.
- **Risk:** N/A (constraint).
- **Review verdict:** CONFIRMED. Must remain enforced in implementation.

---

### R12 — No Phase 4 expansion

- **Design intent:** The slice is a Button 2 export-proof repair only.
- **Scope:** No roadmap expansion or unrelated workflow additions.
- **Risk:** N/A (constraint).
- **Review verdict:** CONFIRMED.

---

### R13 — No billing

- **Design intent:** No billing or customer accounting logic is involved.
- **Scope:** Entire slice.
- **Risk:** N/A (constraint).
- **Review verdict:** CONFIRMED.

---

### R14 — No learning/calibration changes

- **Design intent:** No learning, calibration, or accuracy pipeline changes are involved.
- **Scope:** Entire slice.
- **Risk:** N/A (constraint).
- **Review verdict:** CONFIRMED.

---

### R15 — No uncontrolled writes

- **Design intent:** Export remains an explicit Button 2 operator-approved action only. No additional hidden writes may be introduced.
- **Scope:** Entire slice.
- **Risk:** N/A (constraint).
- **Review verdict:** CONFIRMED.

---

## Implementation scope summary

| File | Change |
|---|---|
| `operator_dashboard/templates/index.html` | Button 2 result UI: show path, size, open actions, and explicit export failure messaging |
| Button 2 backend export path | Populate export-proof fields, validate real PDF artifact before marking `generated` |

**Implementation note:** The success status must be derived from the actual final artifact on disk, not from an optimistic intermediate state or placeholder file.

---

## Design gaps — none identified

No ambiguities requiring redesign were found. The design is internally consistent and narrowly scoped to Button 2 export proof.

---

## Summary Verdict

All fifteen requirements reviewed. All approved or confirmed. No scope gaps. No design ambiguities requiring redesign.

**Design review outcome: PASS — safe to proceed to implementation slice.**

---

## Next slice

```text
ai-risa-premium-report-factory-button2-pdf-file-path-and-open-folder-repair-implementation-v1
```

Implementation must reference this review commit and must not exceed the approved Button 2 scope.
