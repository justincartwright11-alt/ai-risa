# Button 2 Visual Intelligence — Renderer Geometry Metadata Source Design (v1)

**Slice:** `button2-visual-intelligence-renderer-geometry-metadata-source-design-v1`
**Date:** 2026-05-17
**Status:** LOCKED — design-only, no implementation changes

---

## Purpose

Design where real renderer geometry data should come from before any customer PDF layout is touched. The geometry instrumentation module (`button2_visual_intelligence_overlap_offpage_proof_instrumentation_v1.py`) is ready to receive block data. This document locks the decision on which renderer hook to use and what data shape it must produce.

---

## Current State

The instrumentation module accepts geometry data in this shape:

```python
geometry_data = {
    "blocks": [
        {"id": "block-1", "bounds": [x, y, w, h], "page_index": 0},
        ...
    ],
    "page_width": 595,      # points (A4)
    "page_height": 842,     # points (A4)
    "margins": {"left": 72, "top": 72, "right": 72, "bottom": 72},
    "operator_approval": False,
}
```

The builder wires this in when `geometry_data` is present in the ingest context. Today, no real renderer provides it — it must be injected from a real source.

---

## The Gap

The blocks currently stored in `page_block_boundaries` are **layout-inferred placeholders** (`[0, 0, 400, 100]`). Real overlap and off-page proof requires **computed positions from the actual render**.

---

## Candidate Geometry Sources

### Source A — WeasyPrint Box Tree (Recommended)

**How it works:**
After calling `document = html.render()` on a WeasyPrint HTML document, the rendered document exposes a `pages` list. Each page contains a box tree. Each box has computed position and size attributes: `position_x`, `position_y`, `width`, `height`.

**Access pattern (pseudocode):**
```python
document = weasyprint.HTML(string=html_content).render()
for page_index, page in enumerate(document.pages):
    for box in _walk_boxes(page._page_box):
        if box.element_tag and _is_content_block(box):
            blocks.append({
                "id": box.element_tag + "-" + str(id(box)),
                "bounds": [box.position_x, box.position_y, box.width, box.height],
                "page_index": page_index,
            })
```

**Pros:**
- Real computed geometry — exactly what appears in the PDF
- Zero visual impact — box tree is a read-only post-render artifact
- No additional rendering pass
- No external dependency beyond WeasyPrint (already in stack)

**Cons:**
- WeasyPrint box tree internals are not a public documented API; attribute names may shift between WeasyPrint versions
- Requires pinning WeasyPrint version or an abstraction layer that can adapt if attributes change

**Risk mitigation:**
- Wrap box extraction in a dedicated function (`extract_weasyprint_page_geometry`) that handles `AttributeError` gracefully and returns `"unavailable"` if the box structure is not as expected
- Add a version pin to `requirements.txt` / `pyproject.toml` alongside the implementation

---

### Source B — Post-Render PDF Geometry Extraction

**How it works:**
After rendering the PDF to an in-memory `BytesIO` buffer (not disk), parse it with `pdfminer.six` to extract character/word bounding boxes, then group them into logical blocks.

**Access pattern (pseudocode):**
```python
pdf_bytes = BytesIO()
document.write_pdf(pdf_bytes)
pdf_bytes.seek(0)
blocks = extract_blocks_from_pdf_bytes(pdf_bytes)
```

**Pros:**
- Fully decoupled from WeasyPrint internals
- Works with any PDF backend
- `pdfminer.six` has a stable public API

**Cons:**
- Requires a second parsing pass over every page
- Logical block grouping from character-level data requires a proximity/clustering heuristic
- Block IDs cannot be traced back to HTML element IDs without additional tagging

**Use as fallback if Source A proves brittle.**

---

### Source C — HTML Pre-Render Geometry via CSS Layout Query

**How it works:**
Before PDF rendering, render the HTML to a headless Playwright browser and query `getBoundingClientRect()` for all block-level elements. Map browser pixel coordinates to PDF points.

**Pros:**
- Uses real CSS layout
- Block IDs map directly to HTML element IDs

**Cons:**
- Adds Playwright as an infrastructure dependency
- Coordinate mapping (browser DPI → PDF points) requires calibration
- Slower than post-render extraction

**Status: Deferred.** Not justified at this stage.

---

## Decision

**Primary source: Source A (WeasyPrint Box Tree)**
**Fallback: Source B (pdfminer.six post-render)**

---

## Required Data Contract

Any geometry source implementation must produce blocks in this exact shape for the instrumentation module:

```python
[
    {
        "id": str,             # unique block identifier per page
        "bounds": [x, y, w, h],  # float, in PDF points
        "page_index": int,     # 0-based
    },
    ...
]
```

And must also supply:

```python
"page_width": float    # PDF page width in points
"page_height": float   # PDF page height in points
"margins": {           # optional; margins applied during layout
    "left": float,
    "top": float,
    "right": float,
    "bottom": float,
}
```

---

## Integration Point

The geometry source produces a `geometry_data` dict. This dict must be passed into the Button 2 report-context builder as:

```python
ingest_payload["button2_ingest_preview_context"]["geometry_data"] = geometry_data
```

The builder already reads this key and routes it through `run_geometry_proof()`.

No other code changes are required in the instrumentation module, the compatibility layer, or the adapter.

---

## What the Geometry Source Must NOT Do

| Constraint | Rule |
|------------|------|
| No layout changes | Must not alter positions, sizes, or styles of any element |
| No extra pages | Must not add or remove pages from the PDF |
| No file writes | Must not write the PDF to disk as part of geometry extraction |
| No customer delivery | Geometry extraction is a QA-only side-effect, not a deliverable |
| No blocking render | Must not prevent the main PDF render from completing normally |

---

## Box Filtering Rules (Source A)

Not every WeasyPrint box represents a content block. The geometry extractor must filter to:

- Boxes tagged with a content HTML element (`<section>`, `<div>`, `<p>`, `<table>`, `<h1>`–`<h6>`)
- Boxes with non-zero width and height
- Boxes that are not pure whitespace containers

Anonymous boxes, inline boxes, and margin boxes must be excluded to avoid false overlap detections.

---

## Block ID Convention

Block IDs must be stable and unique within a page:

```text
{element_tag}-p{page_index}-{sequential_index}
```

Example: `section-p0-3`, `div-p1-7`

Sequential index is assigned in document order during box tree traversal.

---

## Next Step (After This Design Is Locked)

Implement the WeasyPrint box tree geometry extractor as a narrow, preview-only module:

```text
operator_dashboard/button2_visual_intelligence_weasyprint_geometry_extractor_v1.py
```

That module must:
1. Accept a rendered WeasyPrint document object
2. Walk the box tree, filter to content blocks, assign IDs
3. Return a `geometry_data` dict in the shape defined above
4. Handle `AttributeError` gracefully → return `"unavailable"` sentinel
5. Not write any files, trigger any PDF delivery, or change any layout

Slice name: `button2-visual-intelligence-weasyprint-geometry-extractor-preview-v1`
