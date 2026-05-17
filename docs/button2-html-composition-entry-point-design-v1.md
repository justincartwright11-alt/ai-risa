# Button 2 HTML Composition Entry Point — Design (v1)

**Slice:** `button2-html-composition-entry-point-design-v1`
**Date:** 2026-05-17
**Status:** LOCKED — design-only, no implementation changes

---

## Purpose

Design the missing HTML composition entry point that converts an approved
`report_context_preview` dict into a safe, complete HTML document suitable for
`render_button2_pdf()`.

**This module may compose HTML. It may not render PDFs, write files, export,
deliver, or bypass Gate 2 approval.**

---

## The Gap This Fills

The current Button 2 pipeline ends at `report_context_preview` (a structured
dict). The render gate `render_button2_pdf(html_content)` expects an HTML
string. Nothing between these two exists today. This module is that bridge.

```
report_context_preview (dict)
    → build_button2_report_html(report_context_preview)     ← THIS MODULE
        → { ok, html_content, ... }
            → render_button2_pdf(html_content)
                → { pdf_bytes, geometry_data }
```

---

## Input Contract

**Function signature:**
```python
build_button2_report_html(report_context_preview: dict) -> dict
```

**Required input fields** (all consumed from `report_context_preview`):

| Field | Type | Description |
|-------|------|-------------|
| `destination_marker` | str | Must equal `"button2_report_generation_preview"` |
| `report_context_kind` | str | Must equal `"dossier_handoff_report_context_preview"` |
| `handoff_summary_preview` | str | Pre-escaped text content for the report body |
| `source_context_kind` | str | Source label for traceability section |
| `source_ingest_mode` | str | Ingest mode label for metadata footer |
| `hierarchy_markers` | list | Ordered list of section block references |
| `source_traceability` | list | List of source citation dicts (`id`, `type`, `date`) |
| `overlap_proof` | str\|dict | Proof result — surfaced in QA metadata footer only |
| `off_page_text_proof` | str\|dict | Proof result — surfaced in QA metadata footer only |
| `visual_certification_status` | str | Certification label — surfaced in QA metadata footer only |

All string fields must be treated as untrusted and escaped before insertion
into HTML output. The `handoff_summary_preview` is already escaped by upstream
builders but must be double-checked.

---

## Output Contract

```python
{
    "ok": bool,                          # True on success
    "error": str | None,                 # Error code string on failure, else None
    "html_content": str | None,          # Full HTML document string, or None on failure
    "preview_only": True,                # Always True — no PDF or file produced
    "html_composition_performed": bool,  # True on success
    "pdf_generation_performed": False,   # Always False — this module never renders
    "file_write_performed": False,       # Always False — this module never writes
    "export_performed": False,           # Always False
    "delivery_performed": False,         # Always False
}
```

**On invalid input:**
```python
{
    "ok": False,
    "error": "<error_code>",
    "html_content": None,
    "preview_only": True,
    "html_composition_performed": False,
    "pdf_generation_performed": False,
    "file_write_performed": False,
    "export_performed": False,
    "delivery_performed": False,
}
```

---

## Validation Rules

Before composing HTML, the function must validate:

1. Input is a dict — else `"invalid_input_type"`
2. `destination_marker == "button2_report_generation_preview"` — else `"invalid_destination_marker"`
3. `report_context_kind == "dossier_handoff_report_context_preview"` — else `"invalid_report_context_kind"`
4. `handoff_summary_preview` is a non-empty string after strip — else `"missing_summary_content"`

All other fields have safe fallback values — validation failure should not occur on absent optional fields.

---

## HTML Template Design

### Approach: inline Python string template

**Rationale:** Jinja2 is not required. The `report_context_preview` is a flat
dict of pre-validated, escaped strings. An inline Python f-string template is
simpler, has no additional dependencies, and eliminates template injection risk.

All dynamic values are passed through `html.escape()` before insertion, even
if upstream builders have already escaped them. Double-escaping is not a
concern here because the upstream `_safe_text()` functions use `html.escape()`,
which is idempotent over already-escaped text for the characters used.

Wait — double-escaping IS a concern: if `handoff_summary_preview` already
contains `&amp;` and we re-escape it we get `&amp;amp;`. Correct approach:
accept that upstream builders already escape their outputs and do NOT
re-escape fields that flow through `_safe_text()`. Fields that are NOT
pre-escaped (e.g., dict keys, computed labels) must be escaped.

**Rule:** Fields that pass through `_safe_text()` in the upstream builder are
already escaped — read them as trusted escaped text. Fields extracted directly
from dicts (source IDs, type labels) must be escaped at composition time.

### Document structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI-RISA Premium Report</title>
  <style>
    /* Minimal WeasyPrint-safe CSS — no external resources */
    body { font-family: sans-serif; font-size: 11pt; margin: 2cm; color: #111; }
    h1   { font-size: 16pt; margin-bottom: 0.5em; }
    h2   { font-size: 13pt; margin-top: 1.5em; margin-bottom: 0.3em; border-bottom: 1px solid #ccc; }
    pre  { font-size: 9pt; white-space: pre-wrap; word-break: break-word; }
    .meta-footer { font-size: 8pt; color: #888; margin-top: 2em; border-top: 1px solid #eee; padding-top: 0.5em; }
    .qa-row { margin: 0.2em 0; }
  </style>
</head>
<body>
  <h1>AI-RISA Premium Fight Report</h1>

  <h2>Report Summary</h2>
  <pre>{handoff_summary_preview}</pre>

  <h2>Source Traceability</h2>
  <ul>
    {source_traceability_items}
  </ul>

  <div class="meta-footer">
    <div class="qa-row">Source context: {source_context_kind}</div>
    <div class="qa-row">Ingest mode: {source_ingest_mode}</div>
    <div class="qa-row">Overlap proof: {overlap_proof_label}</div>
    <div class="qa-row">Off-page text proof: {off_page_text_proof_label}</div>
    <div class="qa-row">Visual certification: {visual_certification_status}</div>
  </div>
</body>
</html>
```

### CSS constraints

- No external stylesheets, fonts, or images — WeasyPrint must not make network requests
- No `@import url(...)` — inline only
- No absolute pixel units for page geometry — `cm`/`pt`/`em` only
- No JavaScript

### Proof field rendering in HTML

Proof fields (`overlap_proof`, `off_page_text_proof`, `visual_certification_status`)
appear in the `meta-footer` only. They are QA metadata — they must not appear
in the visible report body, headings, or summary. The meta-footer has font-size
8pt and color #888 to make it visually subordinate.

The proof field value may be a string (`"clear"`, `"unavailable"`, `"not_certified"`)
or a dict (e.g. `{"status": "overlap_detected", "violations": [...]}`). For HTML
rendering, convert to a safe label:
- string → escape and display as-is
- dict → display `proof["status"]` escaped, ignore violation detail in HTML output

---

## Safety Invariants

| Invariant | Implementation |
|-----------|----------------|
| No PDF rendered | Function returns `html_content` string only — no WeasyPrint calls |
| No file written | No `open()`, no `write()` |
| No delivery | No Flask response building, no HTTP calls |
| No Gate 2 bypass | No `operator_approved` flag; caller must have already passed Gate 2 |
| All dynamic values escaped | `html.escape()` on all non-pre-escaped inputs |
| No external resources | CSS is inline, no `url()` references |
| `preview_only: True` always | Hard-coded in output dict |
| `pdf_generation_performed: False` always | Hard-coded in output dict |
| `file_write_performed: False` always | Hard-coded in output dict |

---

## Module Location

```text
operator_dashboard/button2_html_composition_entry_point_v1.py
```

**Public API** (single exported function):

```python
def build_button2_report_html(report_context_preview: dict) -> dict:
    ...
```

No other public names. No class definitions needed.

---

## Test File

```text
operator_dashboard/test_button2_html_composition_entry_point_preview_v1.py
```

Minimum required test coverage:

| Test | Proof |
|------|-------|
| Valid input → `ok=True`, `html_content` is a non-empty string | Core path |
| `html_content` starts with `<!DOCTYPE html>` | Well-formed HTML |
| `handoff_summary_preview` text appears in `html_content` | Content routing |
| Missing `destination_marker` → `ok=False`, `"invalid_destination_marker"` | Validation |
| Wrong `destination_marker` → `ok=False`, `"invalid_destination_marker"` | Validation |
| Wrong `report_context_kind` → `ok=False`, `"invalid_report_context_kind"` | Validation |
| Missing summary content → `ok=False`, `"missing_summary_content"` | Validation |
| Non-dict input → `ok=False`, `"invalid_input_type"` | Validation |
| `pdf_generation_performed` always False | Safety invariant |
| `file_write_performed` always False | Safety invariant |
| `preview_only` always True | Safety invariant |
| `html_composition_performed` True on success, False on failure | Flag correctness |
| XSS probe in summary: `<script>` appears escaped in HTML | Escaping |
| `source_traceability` items appear in output | Content routing |
| Proof fields appear in meta-footer, not in main body headings | Proof placement |
| `overlap_proof` dict value rendered as label, not raw dict | Proof rendering |

---

## What Opens After This Design Is Locked

Implementation slice:
```text
button2-html-composition-entry-point-preview-v1
```

That slice builds `button2_html_composition_entry_point_v1.py` and its test file.
No changes to `app.py`, the render gate, or any other module are made in that slice.
