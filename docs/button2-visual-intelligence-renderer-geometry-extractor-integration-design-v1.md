# Button 2 Visual Intelligence — Renderer Geometry Extractor Integration Design (v1)

**Slice:** `button2-visual-intelligence-renderer-geometry-extractor-integration-design-v1`
**Date:** 2026-05-17
**Status:** LOCKED — design-only, no implementation changes

---

## Purpose

Design how the real Button 2 renderer will provide geometry data to the WeasyPrint geometry extractor and proof chain, without changing PDF layout or customer output behaviour. This document locks the integration strategy before any renderer code is touched.

---

## Current State

The full QA chain is proven end-to-end with mock geometry:

```
extract_weasyprint_page_geometry(rendered_doc)
    → geometry_data dict
        → run_geometry_proof(geometry_data)
            → overlap_proof / off_page_text_proof / visual_certification_status
                → map_report_context_to_visual_intelligence_contract(report_context)
                    → adapt_renderer_output_to_contract(contract)
```

The only missing link is: **who calls `extract_weasyprint_page_geometry` with a real rendered document, and when?**

---

## The Integration Gap

Button 2 currently renders PDFs via a function that calls WeasyPrint and writes the result to a file or buffer. That function does not expose the rendered document object — it either returns bytes directly or writes a file. The geometry extractor needs the rendered document object **before** it is written to bytes.

---

## Integration Strategy

### Rule: Do Not Change the Render Path for Customers

The existing Button 2 PDF render path must not change for customer-facing output. All geometry extraction is a **side-channel read** — it reads from an already-rendered document, does not alter layout, does not write files, and does not delay or replace customer output.

---

### Step 1 — Locate the Render Call Site

Find the function in the operator dashboard that calls WeasyPrint's `HTML(...).render()` or equivalent. This is the call site where the rendered document object is momentarily available before being written to bytes/file.

Target: `operator_dashboard/` — likely in `app.py` or a dedicated PDF export helper.

---

### Step 2 — Add a Non-Invasive Geometry Side-Channel

At the render call site, after `document = HTML(...).render()` and **before** `document.write_pdf(...)`, insert a single optional geometry extraction call:

```python
# Existing render call (DO NOT CHANGE):
document = weasyprint.HTML(string=html_content).render()

# --- Non-invasive geometry side-channel (QA only, preview-only) ---
if _visual_qa_enabled():
    _geometry_data = extract_weasyprint_page_geometry(document)
    # Store for QA metadata — does not affect PDF output
else:
    _geometry_data = None

# Existing write call (DO NOT CHANGE):
pdf_bytes = document.write_pdf()
```

The `_visual_qa_enabled()` guard ensures:
- Extraction only runs in QA/preview mode, never in customer delivery mode
- If the flag is False, extraction is skipped entirely with zero overhead
- The guard defaults to False until explicitly enabled

---

### Step 3 — Wire Geometry Data into Report Context

The extracted `_geometry_data` dict is passed as `geometry_data` into the Button 2 report-context builder:

```python
ingest_payload["button2_ingest_preview_context"]["geometry_data"] = _geometry_data
```

The builder already reads this key and routes it through `run_geometry_proof()`. No further builder changes are needed.

---

### Step 4 — Expose QA Results (Preview Only)

The proof results (`overlap_proof`, `off_page_text_proof`, `visual_certification_status`) are stored in the report-context preview dict. They are surfaced only:
- In preview/QA API responses
- In internal QA tooling
- Never in customer-facing PDF content or metadata

---

## Gating Rules

| Gate | Rule |
|------|------|
| Customer PDF output | Must not change. Geometry extraction is invisible to the customer. |
| Extraction enabled flag | Default False. Only set True in QA/preview render mode. |
| Certification gate | `visual_certification_status = "certified"` only if both proofs are `"clear"` and `operator_approval = True`. |
| Write path | `document.write_pdf()` call must not be modified or removed. |
| Error handling | If extraction raises any exception, catch and set `geometry_data = None` → proof stays `"unavailable"`. |

---

## Render Call Site Discovery

Before implementation, the render call site must be located. Candidate files:

- `operator_dashboard/app.py` — main Flask app, likely contains the PDF export route
- Any file matching `*export*`, `*render*`, `*pdf*` in `operator_dashboard/`

The implementer must:
1. Find the call to `weasyprint.HTML(...).render()` or `HTML(...).write_pdf()`
2. Confirm it is the single central render path (not duplicated)
3. Map how `html_content` is constructed and passed
4. Confirm the rendered document object is accessible before `write_pdf`

If `write_pdf` is called directly without a separate `render()` step (i.e., `HTML(...).write_pdf()` in one call), then the integration requires splitting it into:
```python
document = HTML(...).render()
pdf_bytes = document.write_pdf()
```
This split is layout-safe — `render()` + `write_pdf()` is exactly equivalent to the single-call form. It does not change output.

---

## What This Design Does NOT Include

| Excluded | Reason |
|----------|--------|
| Layout changes | Not in scope for this slice or the next |
| Dashboard UI changes | Visual QA is backend-only at this stage |
| Customer delivery changes | Extraction is invisible to customers |
| New PDF pages | Not added by extraction |
| Certification auto-trigger | Operator approval always required |
| New dependencies | WeasyPrint is already in stack; no new packages |

---

## Next Step (After This Design Is Locked)

1. Locate the render call site in `operator_dashboard/app.py` (or equivalent)
2. Confirm the single-call vs two-call render pattern
3. Implement the non-invasive geometry side-channel in a narrow slice:

```text
button2-visual-intelligence-renderer-geometry-extractor-integration-preview-v1
```

That slice must:
- Add `_visual_qa_enabled()` guard (default False)
- Split `HTML(...).write_pdf()` into `render()` + `write_pdf()` if needed (layout-neutral)
- Call `extract_weasyprint_page_geometry(document)` only when QA enabled
- Pass `_geometry_data` into the report-context builder
- Add a test that mock-patches the render call and confirms geometry flows to proof
- Not change any customer PDF output
