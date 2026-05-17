# Button 2 Visual Intelligence — Overlap & Off-Page Text Proof Instrumentation Design (v1)

**Slice:** `button2-visual-intelligence-overlap-offpage-proof-instrumentation-design-v1`
**Date:** 2026-05-17
**Status:** LOCKED — design-only, no implementation changes

---

## Purpose

Design how real overlap and off-page text proof can be produced for Button 2 PDF report pages, without changing the visual layout of any rendered output. This design must be locked before any instrumentation code is written.

---

## Background

The current QA bridge exposes two markers that remain unavailable:

```python
"overlap_proof": "unavailable"
"off_page_text_proof": "unavailable"
```

These markers block visual certification (`visual_certification_status = "not_certified"`). The adapter correctly fails closed because no real proof exists.

To unblock certification, the system must be able to produce proof that:
1. No two content blocks overlap on a page
2. No text content falls outside the printable page boundary

This proof must be produced **without changing any rendered output**.

---

## Constraints

| Constraint | Rule |
|------------|------|
| No layout changes | Instrumentation must not move, resize, or reflow any content |
| No new PDF pages | Must not add blank or debug pages to output |
| No visual artifacts | Must not embed visible markers, borders, or debug overlays in delivered PDFs |
| Preview-only path | Proof may be computed on the same render pipeline but stored separately |
| Fail closed | If instrumentation is absent or inconclusive, proof remains `"unavailable"` |
| No fake proof | `"clear"` may only be set when real geometry data is available and verified |

---

## Proof Targets

### 1. Overlap Proof

**Definition:** No two rendered content blocks share any pixel area on the same page.

**What constitutes a block:**
- Section header
- Body text block
- Stat/data table
- Image or chart placeholder
- Footer / header bar
- Page number element

**What "clear" means:**
```text
overlap_proof = "clear"
```
→ For every page, the bounding rectangles of all rendered blocks have zero intersection area.

**What "overlap_detected" means:**
```text
overlap_proof = "overlap_detected"
```
→ One or more block pairs intersect. Includes the page index and block IDs.

---

### 2. Off-Page Text Proof

**Definition:** No rendered text or content block extends beyond the printable page boundary (after margins are applied).

**What "clear" means:**
```text
off_page_text_proof = "clear"
```
→ All block bounding boxes fall entirely within `[margin_left, margin_top, page_width - margin_right, page_height - margin_bottom]`.

**What "off_page_detected" means:**
```text
off_page_text_proof = "off_page_detected"
```
→ One or more blocks extend beyond the page boundary. Includes the page index, block ID, and overflow dimension.

---

## Instrumentation Options

### Option A — WeasyPrint Post-Render Box Tree Inspection

WeasyPrint exposes an internal document layout tree after rendering. After calling `document.render()`, the resulting page objects contain box trees with computed positions and sizes.

**Approach:**
1. Call `document.render()` as normal (no layout change)
2. Walk the box tree per page
3. Extract `(x, y, width, height)` for each box
4. Compute intersections and boundary checks
5. Store results in the metadata proof dict
6. Do not affect the final PDF write

**Pros:** No layout change; uses real computed geometry; zero visual impact.
**Cons:** WeasyPrint internals are not a public API; may require pinning to a specific WeasyPrint version.

---

### Option B — Post-Render PDF Geometry Extraction (pdfminer / pypdf)

After the PDF is written to a bytes buffer (not disk), parse it with `pdfminer.six` or `pypdf` to extract text element positions from the page stream.

**Approach:**
1. Render PDF to an in-memory `BytesIO` buffer
2. Parse the buffer with `pdfminer` to extract character/word bounding boxes per page
3. Group into logical blocks by proximity
4. Compute overlaps and page-boundary checks
5. Store results in the metadata proof dict
6. Discard the buffer; the proof is only stored in metadata

**Pros:** Fully decoupled from renderer internals; works with any PDF backend.
**Cons:** Adds a parse pass over every page; block grouping heuristic may not perfectly match rendered blocks.

---

### Option C — HTML Pre-Render Geometry (CSS Layout Snapshot)

Before PDF rendering, use a headless browser (e.g., Playwright) or a CSS geometry pass to compute block positions from the HTML template.

**Approach:**
1. Render the HTML template to a headless browser
2. Query `getBoundingClientRect()` for all block elements
3. Map browser coordinates to expected PDF page coordinates
4. Compute overlaps and boundary checks
5. Store results in the metadata proof dict

**Pros:** Uses real HTML layout; no dependency on WeasyPrint internals.
**Cons:** Requires a headless browser in the render pipeline; coordinate mapping may require calibration.

---

## Recommended Approach

**Option A (WeasyPrint Box Tree) for overlap proof** — most accurate for the actual rendered geometry, zero visual impact, and already in the render pipeline.

**Option B (PDF Geometry Extraction) as fallback** — use if WeasyPrint internals prove unstable between versions. Can run as an independent post-render pass.

Option C is deferred — headless browser adds infrastructure complexity not justified at this stage.

---

## Proof Data Shape

The proof output stored in `report_context_preview` must follow this shape:

```python
# When proof is available and clean:
"overlap_proof": "clear"
"off_page_text_proof": "clear"

# When proof detects a problem:
"overlap_proof": {
    "status": "overlap_detected",
    "violations": [
        {
            "page_index": 0,
            "block_a": "block-1",
            "block_b": "block-3",
            "intersection_area": 120.0   # px²
        }
    ]
}

"off_page_text_proof": {
    "status": "off_page_detected",
    "violations": [
        {
            "page_index": 0,
            "block_id": "block-5",
            "overflow_axis": "y",
            "overflow_px": 14.2
        }
    ]
}

# When instrumentation is absent or inconclusive:
"overlap_proof": "unavailable"
"off_page_text_proof": "unavailable"
```

---

## Visual Certification Gate

Visual certification may only advance from `"not_certified"` to `"certified"` when **all** of the following are true:

1. `overlap_proof == "clear"`
2. `off_page_text_proof == "clear"`
3. All required metadata marker fields are present
4. Operator explicitly approves the certification step

The adapter (`adapt_renderer_output_to_contract`) must reject any contract where `no_overlap` or `no_off_page_text` is not `True`.

---

## What This Design Does NOT Include

- Any layout, spacing, font, or style change to any PDF page
- Any new visible element in delivered PDFs
- Any operator dashboard UI change
- Any change to report generation behavior
- Any operator approval bypass

---

## Next Step (After This Design Is Locked)

Implement a narrow, preview-only instrumentation module that:

1. Accepts a rendered WeasyPrint document object (or a PDF bytes buffer)
2. Extracts block geometry per page
3. Returns an overlap/off-page proof dict in the shape defined above
4. Does not write any files or trigger any PDF delivery

Slice name: `button2-visual-intelligence-overlap-offpage-proof-instrumentation-preview-v1`
