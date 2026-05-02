# AI-RISA Premium Report Factory — Button 2 PDF File Path and Open Folder Repair: Final Review v1

**Date:** 2026-05-02
**Scope:** Button 2 (Generate & Export) — export proof UI + Windows-safe PDF filename
**Reviewer gate:** Final review before release manifest and archive lock

---

## Slice Summary

This slice repairs two defects that prevented Button 2 from proving a real exported PDF:

1. **Proof panel cleared on queue reload** — the results panel was unconditionally wiped each time the queue refreshed after generation.
2. **Windows-invalid colon in event name** — event IDs containing `:` (e.g., `Ares FC 39:`) caused the PDF write to produce a zero-byte NTFS alternate data stream instead of a usable `.pdf` file.

Both defects were found during post-freeze smoke, fixed, regression-tested, and validated end-to-end before the smoke was locked.

---

## Commit Chain

| Commit | Tag | Description |
|---|---|---|
| `0804d93` | `...-design-v1` | Design doc |
| `de3db90` | `...-design-review-v1` | Design review lock |
| `5a42b85` | `...-implementation-v1` | Initial export proof UI and backend contract |
| `9dd026f` | `...-implementation-v2` | Windows filename sanitization + proof panel persistence |
| `1003ddb` | `...-post-freeze-smoke-v1` | Smoke doc lock |

---

## Files Changed

| File | Change |
|---|---|
| `operator_dashboard/prf_report_export.py` | Added `_sanitize_filename_component` and applied to both `event_id` and `matchup_id` in `build_report_filename` |
| `operator_dashboard/prf_report_builder.py` | Added `_validate_generated_pdf`; `generate_reports` now adds proof fields; zero-byte/non-PDF artifacts go to `rejected_reports` |
| `operator_dashboard/templates/index.html` | Added `preserveGenerateResults` guard to `loadMainPrfQueue`; `_renderMainPrfGenerateResult` renders path, size, Open PDF, Open Reports Folder |
| `operator_dashboard/test_app_backend.py` | Added `test_prf_phase3_generate_includes_pdf_proof_fields`, `test_prf_phase3_non_pdf_or_zero_byte_artifact_not_marked_generated`, `test_prf_phase3_filename_sanitizes_windows_invalid_characters` |

---

## Boundary Review

The following were explicitly **not** changed in this slice:

- No result lookup, no accuracy comparison, no learning, no web discovery.
- No billing, no distribution, no auto-send.
- No global ledger write, no token mutations, no scoring rewrite.
- `app.py` routes untouched.
- Button 1 and Button 3 behavior untouched.
- No new Flask routes or config keys.

---

## Correctness Review

### `_sanitize_filename_component`

- Strips all 8 Windows-reserved filename characters: `\ / : * ? " < > |`
- Collapses whitespace to `_`
- Strips leading/trailing ` . _`
- Falls back to `"unknown"` for empty input
- Applied to both `event_id` and `matchup_id` independently — neither can introduce a colon into the output path

### `_validate_generated_pdf`

- Requires non-empty path
- Requires `.pdf` extension (case-insensitive check via `.lower()`)
- Requires file exists on disk
- Requires `size > 0`
- Returns `(ok, path, size_bytes, error_msg)` — all four consumed in `generate_reports`

### `preserveGenerateResults` guard

- `loadMainPrfQueue(options = {})` only clears proof panels when `preserveGenerateResults` is falsy
- `runMainPrfGenerate` passes `{ preserveGenerateResults: true }` after a successful render
- Manual queue refresh (button click) continues to clear the panels, which is correct behaviour

---

## Test Coverage Review

| Test | Covers |
|---|---|
| `test_prf_phase3_generate_exports_pdf_file` | Real `.pdf` written to disk |
| `test_prf_phase3_generate_includes_pdf_proof_fields` | `generated_pdf_exists`, `generated_pdf_path`, `generated_pdf_size_bytes`, `generated_pdf_openable` present and valid |
| `test_prf_phase3_non_pdf_or_zero_byte_artifact_not_marked_generated` | Zero-byte artifact → rejected |
| `test_prf_phase3_failed_export_not_marked_generated` | Export failure → not marked generated |
| `test_prf_phase3_filename_sanitizes_windows_invalid_characters` | Colon and space in event_id → sanitized; no Windows-invalid characters in output |
| `test_prf_phase3_deterministic_filename` | Filename prefix `ai_risa_premium_report_` and `.pdf` suffix |

---

## Smoke Evidence

All checks confirmed in `post-freeze-smoke-v1` doc:

- API response: `200 OK`
- `generateStatus`: `Export complete: 1 PDF(s) generated.`
- Proof panel: `display: block`
- PDF filename: `ai_risa_premium_report_ares_fc_39__jbalia_vs._diatta_prf_q_7b1e2a0d1275b54a_20260502.pdf`
- PDF path ends with `.pdf`: true
- PDF exists on disk: true
- PDF size: 3242 bytes
- `Open PDF` link correct
- `Open Reports Folder` link matches actual parent folder
- Focused backend tests: 3 passed
- Editor diagnostics: 0 errors on touched files

Proof copy preserved at: `docs/smoke_proof_button2_ares_fc_39_jbalia_vs_diatta_20260502.pdf` (3242 bytes)

---

## Governance

- Automatic search/analysis allowed.
- Permanent writes required and received operator approval at each gate.
- No regressions against Button 1 or Button 3 slices.

---

## Final Review Verdict

**APPROVED.** The slice is narrow, well-bounded, fully tested, and smoke-proven. No forbidden side effects observed. Safe to proceed to release manifest.
