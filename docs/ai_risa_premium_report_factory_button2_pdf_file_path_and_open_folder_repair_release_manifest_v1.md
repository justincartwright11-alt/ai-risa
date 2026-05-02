# AI-RISA Premium Report Factory — Button 2 PDF File Path and Open Folder Repair: Release Manifest v1

**Date:** 2026-05-02
**Scope:** Button 2 (Generate & Export) — export proof UI + Windows-safe PDF filename

---

## What Was Released

Button 2 of the AI-RISA Premium Report Factory now proves that a real, non-empty `.pdf` was exported before marking a report `generated`. The UI surfaces the exact file path, file size, and clickable actions to open the PDF and the reports folder.

A Windows-specific defect that caused event names containing `:` to produce zero-byte NTFS alternate data streams instead of usable PDFs was identified in smoke and fixed before this release was sealed.

---

## Shipped Behaviour

| Capability | State Before | State After |
|---|---|---|
| `generated` status requires real `.pdf` on disk | No — status set after any export attempt | Yes — requires file exists and `size > 0` |
| UI shows exact PDF file path | No | Yes |
| UI shows PDF file size | No | Yes |
| UI `Open PDF` action | No | Yes — `file://` link to exact path |
| UI `Open Reports Folder` action | No | Yes — `file://` link to parent folder |
| Proof panel survives queue reload | No — panel wiped after reload | Yes — `preserveGenerateResults` guard |
| Windows-safe PDF filename | No — raw event_id with `:` allowed | Yes — `_sanitize_filename_component` strips all Windows-reserved chars |
| Zero-byte artifact treated as failure | No | Yes — goes to `rejected_reports` |

---

## Changed Files

| File | Change Summary |
|---|---|
| `operator_dashboard/prf_report_export.py` | Added `_sanitize_filename_component`; applied to `event_id` and `matchup_id` in `build_report_filename` |
| `operator_dashboard/prf_report_builder.py` | Added `_validate_generated_pdf`; `generate_reports` adds proof fields; `list_generated_reports` computes file size proof |
| `operator_dashboard/templates/index.html` | Proof panel render (`_renderMainPrfGenerateResult`); `preserveGenerateResults` guard in `loadMainPrfQueue`; `_toFileUrl` and `_getFolderPath` helpers |
| `operator_dashboard/test_app_backend.py` | Three new focused tests for proof fields, zero-byte artifact rejection, and Windows filename sanitization |

---

## Commit Chain

| Commit | Tag | Gate |
|---|---|---|
| `0804d93` | `...-design-v1` | Design |
| `de3db90` | `...-design-review-v1` | Design review |
| `5a42b85` | `...-implementation-v1` | Implementation (initial) |
| `9dd026f` | `...-implementation-v2` | Implementation (Windows fix) |
| `1003ddb` | `...-post-freeze-smoke-v1` | Smoke |
| `a29c779` | `...-final-review-v1` | Final review |

---

## Not In Scope

- No result lookup, no accuracy comparison, no learning, no web discovery.
- No billing, no distribution, no auto-send.
- No global ledger write, no token mutations, no scoring rewrite.
- Button 1 and Button 3 behavior unchanged.
- No new Flask routes or config keys.

---

## Test Summary

Backend focused tests: **3 passed** (plus 8 prior Phase 3 tests passing throughout)
Editor diagnostics on touched files: **0 errors**
Live smoke: **PASS**

Smoke proof PDF archived at: `docs/smoke_proof_button2_ares_fc_39_jbalia_vs_diatta_20260502.pdf` (3242 bytes)

---

## Governance

- Automatic search/analysis allowed.
- Permanent writes required and received operator approval at each gate.
- Lock chain completed: design → design review → implementation → smoke → final review → release manifest.
