# AI-RISA Premium Report Factory — Button 2 PDF File Path and Open Folder Repair: Post-Freeze Smoke v1

**Date:** 2026-05-02
**Scope:** Button 2 (Generate & Export) — export proof UI + Windows-safe PDF filename

---

## Smoke Objective

Verify that after Button 2 generation:

1. The proof panel is visible and stays visible after queue reload.
2. The surfaced PDF path ends with `.pdf`.
3. The file exists on disk with size > 0.
4. `Open Reports Folder` link target matches the parent folder of the generated PDF.
5. Windows-invalid characters (colon from event name `Ares FC 39:`) are sanitized before the file is written.

---

## Defects Found During Smoke

### Defect 1 — Proof panel cleared on queue reload (UI)

**Symptom:** After generation, `runMainPrfGenerate` called `loadMainPrfQueue()` which unconditionally cleared `main-prf-generate-results` and `main-prf-generate-status`.

**Root cause:** `loadMainPrfQueue` always reset both panel elements regardless of caller context.

**Fix:** Added `options.preserveGenerateResults` guard to `loadMainPrfQueue`. `runMainPrfGenerate` now calls `loadMainPrfQueue({ preserveGenerateResults: true })`.

**File:** `operator_dashboard/templates/index.html`

---

### Defect 2 — Windows-invalid filename produces zero-byte NTFS alternate data stream (backend)

**Symptom:** `ops/prf_reports/` contained a zero-byte base file named `ai_risa_premium_report_ares_fc_39` (no extension) and no usable PDF. UI showed `3.2 KB` because it was reading the alternate data stream size, not the real file.

**Root cause:** `build_report_filename` in `prf_report_export.py` passed the raw event_id string `ares_fc_39: jbalia vs. diatta` directly into the filename. On Windows, the `:` is interpreted as an NTFS alternate data stream separator, so the OS silently split the write into a base path and a named stream.

**Fix:** Added `_sanitize_filename_component` to `prf_report_export.py`:
- Strips `\ / : * ? " < > |` (all Windows-invalid filename characters).
- Collapses whitespace to `_`.
- Strips leading/trailing ` . _`.
- Applied to both `event_id` and `matchup_id` before filename construction.

**File:** `operator_dashboard/prf_report_export.py`

---

## Regression Test Added

`test_prf_phase3_filename_sanitizes_windows_invalid_characters` in `operator_dashboard/test_app_backend.py`:

- Calls `build_report_filename('ares_fc_39: jbalia vs. diatta', 'prf_q_7b1e2a0d1275b54a')`.
- Asserts no `:`, `/`, or `\` in result.
- Asserts sanitized event slug `ares_fc_39__jbalia_vs._diatta` is present in the filename.
- Asserts filename ends with `.pdf`.

---

## Smoke Run Results

| Check | Result |
|---|---|
| Button 2 generate API response | `200 OK` |
| `generateStatus` text | `Export complete: 1 PDF(s) generated.` |
| Proof panel visible | `block` |
| Accepted count | 1 |
| Rejected count | 0 |
| PDF filename (no colon) | `ai_risa_premium_report_ares_fc_39__jbalia_vs._diatta_prf_q_7b1e2a0d1275b54a_20260502.pdf` |
| PDF path ends with `.pdf` | true |
| PDF exists on disk | true |
| PDF size on disk | 3242 bytes |
| Open PDF link target | `file:///C:/ai_risa_next_dashboard_polish/ops/prf_reports/ai_risa_premium_report_ares_fc_39__jbalia_vs._diatta_prf_q_7b1e2a0d1275b54a_20260502.pdf` |
| Open Reports Folder link target | `file:///C:/ai_risa_next_dashboard_polish/ops/prf_reports` |
| Reports folder on disk | `C:\ai_risa_next_dashboard_polish\ops\prf_reports` (matches) |
| Focused backend tests | 3 passed |
| Editor diagnostics (touched files) | 0 errors |

---

## Governance

- Automatic search/analysis allowed.
- Permanent writes required and received operator approval at each gate.

---

## Commit

`9dd026f` — Fix Button 2 PDF export path proof on Windows

**Tag:** `ai-risa-premium-report-factory-button2-pdf-file-path-and-open-folder-repair-implementation-v2`

---

## Smoke Verdict

**PASS.** Both defects resolved and regression-tested. Proof panel is stable. Real PDF artifact is written to `ops/prf_reports/` with a Windows-safe filename, non-zero size, and correct folder link.
