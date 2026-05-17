# Button 2 Visual Intelligence — Render Gate Final Handoff (v1)

**Slice:** `button2-visual-intelligence-render-gate-final-handoff-v1`
**Date:** 2026-05-17
**Status:** LOCKED — docs-only, no implementation changes

---

## What This Handoff Freezes

The full Button 2 Visual QA infrastructure is now in place:

- Geometry extractor (duck-typed, WeasyPrint box-tree walk)
- Overlap and off-page proof instrumentation
- Metadata bridge (report-context → visual QA contract)
- Compatibility layer and adapter
- Guarded render call site with geometry side-channel

No customer PDF output has been generated. No renderer layout has changed. No dashboard has changed. No certification has been issued. All extraction is off by default.

---

## Locked Render Gate

**File:** `operator_dashboard/button2_pdf_render_gate_v1.py`

**Tag:** `button2-visual-intelligence-renderer-geometry-extractor-integration-preview-v1`

**Commit:** `22e4563`

### What the gate does

```
html_content
    → weasyprint.HTML(string=html_content).render()      [single render call]
        → [if BUTTON2_VISUAL_QA=1] extract_weasyprint_page_geometry(document)
            → geometry_data dict   (or None on exception — fail closed)
        → document.write_pdf()                            [unchanged write path]
    → { pdf_bytes, geometry_data }
```

### Guard rules (locked)

| Rule | Value |
|------|-------|
| `BUTTON2_VISUAL_QA` default | `"0"` — extraction disabled |
| Guard value to enable | `"1"` only |
| Extraction failure | `geometry_data = None` (fail closed) |
| `write_pdf` always called | Yes — regardless of QA state |
| `pdf_bytes` always in result | Yes — regardless of QA state |
| Customer delivery change | None |
| Dashboard change | None |

---

## Full QA Chain — Proven End-to-End

```
render_button2_pdf(html_content)
    → geometry_data
        → run_geometry_proof(geometry_data)
            → overlap_proof / off_page_text_proof / visual_certification_status
                → map_report_context_to_visual_intelligence_contract(report_context)
                    → adapt_renderer_output_to_contract(contract)
```

All links proven with mocks. No link requires WeasyPrint to be installed for testing. One integration test skips gracefully when WeasyPrint is absent.

---

## Validation Summary

| Slice | Commit | Tests |
|-------|--------|-------|
| `button2-visual-intelligence-weasyprint-geometry-extractor-preview-v1` | `3584c59` | 28 passed, 1 skipped |
| `button2-visual-intelligence-weasyprint-geometry-extractor-smoke-v1` | `0dab069` | 19 passed |
| `button2-visual-intelligence-overlap-offpage-proof-instrumentation-preview-v1` | `40023cc` | 31 passed |
| `button2-visual-intelligence-overlap-offpage-proof-instrumentation-smoke-v1` | `2d95171` | 22 passed |
| `button2-visual-intelligence-renderer-contract-metadata-adapter-integration-v1` | `b8f90c9` | 9 passed |
| `button2-visual-intelligence-renderer-contract-compatibility-smoke-v1` | (see tag) | 6 passed |
| `button2-visual-intelligence-renderer-contract-metadata-markers-preview-v1` | `1d5a0e1` | 2 passed |
| `button2-visual-intelligence-renderer-geometry-extractor-integration-preview-v1` | `22e4563` | 21 passed |
| **Total** | | **≥ 119 passed, 1 skipped** |

---

## What Has NOT Been Changed

| Scope | Status |
|-------|--------|
| `operator_dashboard/app.py` | Unchanged — `generate_report` is still a stub |
| Gate 2 approval flow | Unchanged — no PDF delivery route touched |
| Customer PDF output | Unchanged — no layout, content, or file changes |
| Dashboard UI | Unchanged |
| Report composition pipeline | Unchanged |
| Visual certification | `not_certified` always — operator approval not granted |
| Learning / calibration database | Unchanged |

---

## Discovery Finding (Locked)

The render call site did not exist in `app.py` or any operator dashboard module prior to this slice chain. The `generate_report` route returns `gate_passed_no_fight_selected` — no WeasyPrint call, no file write. The `button2_pdf_render_gate_v1.py` module is the **first and only** location in the codebase where a `HTML(...).render()` + `write_pdf()` call sequence exists.

This is the correct integration point for all future PDF delivery work.

---

## What Opens Next

```text
button2-report-generation-route-render-gate-integration-design-v1
```

Purpose: Design how the existing `generate_report` route may eventually call the render gate, subject to Gate 2 approval, without bypassing approval requirements, changing customer PDF output before it is ready, or enabling visual certification prematurely.

That design slice is docs-only and must be locked before any route integration is implemented.
