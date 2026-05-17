# Button 2 Report Generation Route — Render Gate Integration Design (v1)

**Slice:** `button2-report-generation-route-render-gate-integration-design-v1`
**Date:** 2026-05-17
**Status:** LOCKED — design-only, no implementation changes

---

## Purpose

Design how the `generate_report` route in `operator_dashboard/app.py` may eventually call `render_button2_pdf()` from the locked render gate, without:

- Bypassing the Gate 2 operator approval requirement
- Changing customer PDF output before composition is wired and approved
- Enabling visual QA or visual certification prematurely
- Writing files outside an explicit operator-approved path
- Expanding the current stub route in ways that reduce safety

This document must be locked before any implementation touches `app.py` or any report-generation route.

---

## Current State of `generate_report`

```python
@app.route("/api/operator/button2/generate-report", methods=["POST"])
def generate_report():
    data = request.get_json(silent=True) or {}
    approved = data.get("operator_approved", False)
    if not approved:
        return jsonify({
            "ok": False,
            "error": "operator_approval_required",
            "message": "PDF generation must be approved by operator."
        }), 403
    return jsonify({"ok": True, "message": "gate_passed_no_fight_selected"})
```

**What it does today:** enforces the approval gate, returns a stub pass. No render, no file write, no fight selection, no report composition.

**What it must do eventually:** accept operator approval + fight selection, build HTML from the composition pipeline, call `render_button2_pdf()`, write the PDF to a controlled output path, return the file path.

---

## Integration Design

### Gate 2 Approval — Locked, Non-Negotiable

The existing approval check must remain the first guard. It must not be weakened, bypassed, or made optional.

```python
approved = data.get("operator_approved", False)
if not approved:
    return 403
```

No render call is made without `approved == True`.

### Fight Selection — Required Input

Before any render can occur, a fight must be selected. The route must require a valid fight identifier in the request body. Without a selected fight, return an error (not a stub pass).

```python
fight_id = data.get("fight_id")
if not fight_id:
    return jsonify({"ok": False, "error": "fight_id_required"}), 400
```

### Report Composition — Existing Pipeline

HTML for the PDF must come from the existing report composition pipeline (the v29 composition engine, already locked). The route must not compose HTML inline — it must call into the composition pipeline and receive HTML content.

The composition call is:

```python
html_content = build_report_html(fight_id, ingest_context)
```

Where `build_report_html` is the composition pipeline entry point. This function must be identified and its output contract confirmed before the route integration is implemented.

### Render Gate Call

After approval, fight selection, and HTML composition, the route calls the render gate:

```python
render_result = render_button2_pdf(html_content)
pdf_bytes = render_result["pdf_bytes"]
geometry_data = render_result["geometry_data"]   # None unless BUTTON2_VISUAL_QA=1
```

The render gate is already proven safe:
- `write_pdf` always runs
- geometry extraction is guarded off by default
- extraction failures fail closed

### File Write — Controlled, Operator-Approved Path Only

The PDF file must only be written to the designated operator-controlled output directory. No user-supplied paths. No path traversal. Write must be logged.

```python
output_path = _resolve_output_path(fight_id)   # validated, safe
with open(output_path, "wb") as f:
    f.write(pdf_bytes)
```

`_resolve_output_path` must:
- Derive path solely from `fight_id` and a configured output root
- Reject any `fight_id` containing path separators or traversal sequences
- Return an absolute path inside the configured output root only

### QA Result — Preview Only, Not in Delivery Response

If `geometry_data` is not None (QA enabled), the proof chain results may be included in the API response for internal QA tooling. They must never appear in the customer-facing PDF or delivery payload.

```python
qa_summary = None
if geometry_data is not None:
    proof = run_geometry_proof(geometry_data)
    qa_summary = {
        "overlap_proof": proof["overlap_proof"],
        "off_page_text_proof": proof["off_page_text_proof"],
        "visual_certification_status": proof["visual_certification_status"],
    }
```

Visual certification status remains `not_certified` unless both proofs are `"clear"` AND a second explicit `visual_qa_operator_approval` flag is True. This is a separate approval from the PDF generation approval.

---

## Governance Rules for Implementation Slice

| Rule | Constraint |
|------|-----------|
| Gate 2 approval | Must remain first check; 403 if absent |
| Fight selection | Must be validated before render |
| HTML source | Must come from locked composition pipeline only |
| Render call | Must use `render_button2_pdf()` only — no direct `HTML(...).write_pdf()` |
| Output path | Must be derived server-side from `fight_id` + config root; no user path input |
| Visual QA | Side-channel only; `BUTTON2_VISUAL_QA` defaults False |
| Certification | Separate `visual_qa_operator_approval` required; never automatic |
| File write flag | Response must set `file_write_performed: True` when write occurs |
| PDF generation flag | Response must set `pdf_generation_performed: True` when PDF is produced |
| No partial renders | If any step fails after approval, no file is written |

---

## What This Design Does NOT Include

| Excluded | Reason |
|----------|--------|
| Fight selection UI | Out of scope for this design |
| Report composition pipeline wiring | Separate slice; composition entry point must be confirmed |
| Visual QA dashboard panel | Separate slice; QA results surface in API only |
| Automatic certification trigger | Not in scope; always requires operator approval |
| Output directory configuration | Separate config slice |

---

## Prerequisites Before Implementation

The following must be confirmed before the implementation slice begins:

1. **Composition entry point:** Identify the function that produces HTML for a given fight. Confirm its input contract and output type.
2. **Output root config:** Confirm the designated output directory exists or can be created safely.
3. **`fight_id` validation rules:** Confirm the canonical fight identifier format to build safe path derivation.

---

## Next Implementation Slice

```text
button2-report-generation-route-render-gate-integration-preview-v1
```

That slice must:
- Implement `_resolve_output_path(fight_id)` with path-traversal protection
- Wire `build_report_html(fight_id, ...)` → `render_button2_pdf()` → file write
- Update `generate_report` to call the render gate behind the existing Gate 2 approval check
- Add tests that confirm approval gate, fight selection guard, render call, file write, and QA result shape
- Not change the approval gate logic
- Not change any other route
