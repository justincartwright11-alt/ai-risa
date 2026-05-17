# Button 2 Visual Intelligence — WeasyPrint Geometry Extractor (Preview v1)
# Slice: button2-visual-intelligence-weasyprint-geometry-extractor-preview-v1
#
# Purpose: Extract page/block geometry metadata from a rendered WeasyPrint document
# for visual QA instrumentation. Does not import WeasyPrint — accepts any duck-typed
# rendered document object. Fails closed to "unavailable" on any missing/malformed structure.
#
# Governance:
#   - No layout changes
#   - No PDF writes
#   - No renderer changes
#   - No dashboard changes
#   - No customer export/delivery behavior
#   - preview_only=True always
#   - No automatic certification


# HTML element tags that represent content blocks worth measuring.
# Anonymous boxes, inline elements, and structural-only tags are excluded.
_CONTENT_TAGS = frozenset({
    "section", "article", "aside", "main", "header", "footer",
    "div", "p", "table", "thead", "tbody", "tr",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li", "blockquote", "pre", "figure",
})

# Minimum rendered size (points) to count as a visible block.
_MIN_SIZE_PT = 1.0


def _get_element_tag(box):
    """
    Return the lowercase HTML tag for a box, or None for anonymous/internal boxes.
    Strips XML namespace prefixes such as {http://www.w3.org/1999/xhtml}div → div.
    """
    try:
        element = box.element
        if element is None:
            return None
        tag = element.tag
        if not isinstance(tag, str):
            return None
        # Strip XML namespace: {ns}tag → tag
        if "{" in tag:
            tag = tag.split("}", 1)[-1]
        return tag.lower()
    except AttributeError:
        return None


def _walk_boxes(box, page_index, blocks, seq_counter):
    """
    Recursively walk a WeasyPrint box tree and collect content block geometry.
    Appends block dicts to `blocks`. `seq_counter` is a one-element list used as
    a mutable counter so sequential IDs are stable across recursive calls.
    Silently ignores boxes with missing/unexpected attributes.
    """
    try:
        tag = _get_element_tag(box)
        px = float(getattr(box, "position_x", 0) or 0)
        py = float(getattr(box, "position_y", 0) or 0)
        w = float(getattr(box, "width", 0) or 0)
        h = float(getattr(box, "height", 0) or 0)

        if tag and tag in _CONTENT_TAGS and w >= _MIN_SIZE_PT and h >= _MIN_SIZE_PT:
            block_id = f"{tag}-p{page_index}-{seq_counter[0]}"
            seq_counter[0] += 1
            blocks.append({
                "id": block_id,
                "bounds": [round(px, 4), round(py, 4), round(w, 4), round(h, 4)],
                "page_index": page_index,
            })

        for child in getattr(box, "children", []) or []:
            _walk_boxes(child, page_index, blocks, seq_counter)
    except Exception:
        # Fail gracefully — unexpected box structure must not crash QA pass
        pass


def extract_weasyprint_page_geometry(rendered_document):
    """
    Extract block geometry from a rendered WeasyPrint document (duck-typed).

    Accepts any object with:
        .pages  — iterable of page objects, each with a ._page_box attribute
        ._page_box  — root box with .width, .height, .children, and recursively
                      each child box with .element, .position_x, .position_y,
                      .width, .height, .children

    Returns a geometry_data dict:
        {
            "blocks":            list of {id, bounds: [x, y, w, h], page_index}
                                 or None if unavailable,
            "page_width":        float (points) or None,
            "page_height":       float (points) or None,
            "preview_only":      True (always),
            "extraction_status": "ok" | "no_content_blocks" | "unavailable",
        }

    The returned dict is compatible as input to run_geometry_proof().
    Fails closed: returns extraction_status="unavailable" for any missing/malformed input.
    Does not write files, generate PDFs, or change renderer layout.
    """
    _unavailable = {
        "blocks": None,
        "page_width": None,
        "page_height": None,
        "preview_only": True,
        "extraction_status": "unavailable",
    }

    try:
        pages = rendered_document.pages
    except AttributeError:
        return _unavailable

    if not isinstance(pages, (list, tuple)) or not pages:
        return _unavailable

    all_blocks = []
    page_width = None
    page_height = None

    for page_index, page in enumerate(pages):
        try:
            page_box = page._page_box
        except AttributeError:
            return _unavailable

        # Capture page dimensions from the first page
        if page_index == 0:
            try:
                page_width = float(page_box.width or 0)
                page_height = float(page_box.height or 0)
            except (AttributeError, TypeError, ValueError):
                return _unavailable

        seq_counter = [0]
        _walk_boxes(page_box, page_index, all_blocks, seq_counter)

    if page_width is None or page_height is None:
        return _unavailable

    return {
        "blocks": all_blocks,
        "page_width": page_width,
        "page_height": page_height,
        "preview_only": True,
        "extraction_status": "ok" if all_blocks else "no_content_blocks",
    }
