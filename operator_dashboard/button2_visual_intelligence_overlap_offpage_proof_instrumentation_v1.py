# Button 2 Visual Intelligence — Overlap & Off-Page Text Proof Instrumentation (v1)
# Slice: button2-visual-intelligence-overlap-offpage-proof-instrumentation-preview-v1
#
# Purpose: Preview-only instrumentation that inspects block geometry and reports
# overlap/off-page proof status without changing layout, generating PDFs, or certifying visuals.
#
# Governance:
#   - No layout changes
#   - No PDF writes
#   - No renderer changes
#   - No dashboard changes
#   - No automatic certification
#   - Fail closed: if geometry data absent/inconclusive → "unavailable"
#   - "certified" only if both proofs are "clear" AND operator_approval=True


def _intersection_area(bounds_a, bounds_b):
    """Return the intersection area of two [x, y, w, h] rectangles."""
    x1, y1, w1, h1 = bounds_a
    x2, y2, w2, h2 = bounds_b
    ix = max(0.0, min(x1 + w1, x2 + w2) - max(x1, x2))
    iy = max(0.0, min(y1 + h1, y2 + h2) - max(y1, y2))
    return ix * iy


def compute_overlap_proof(blocks):
    """
    Given a list of block dicts {id, bounds: [x, y, w, h], page_index},
    returns "clear", "unavailable", or a violation dict.
    Fails closed: returns "unavailable" on malformed input.
    """
    if not isinstance(blocks, list) or not blocks:
        return "unavailable"

    # Group blocks by page
    pages = {}
    for block in blocks:
        if not isinstance(block, dict):
            return "unavailable"
        if "bounds" not in block or len(block["bounds"]) != 4:
            return "unavailable"
        pi = block.get("page_index", 0)
        pages.setdefault(pi, []).append(block)

    violations = []
    for pi, page_blocks in pages.items():
        for i in range(len(page_blocks)):
            for j in range(i + 1, len(page_blocks)):
                a = page_blocks[i]
                b = page_blocks[j]
                area = _intersection_area(a["bounds"], b["bounds"])
                if area > 0:
                    violations.append({
                        "page_index": pi,
                        "block_a": a["id"],
                        "block_b": b["id"],
                        "intersection_area": round(area, 4),
                    })

    if violations:
        return {"status": "overlap_detected", "violations": violations}
    return "clear"


def compute_off_page_proof(blocks, page_width, page_height, margins=None):
    """
    Given blocks, page dimensions, and optional margins dict {top, bottom, left, right},
    returns "clear", "unavailable", or a violation dict.
    Fails closed: returns "unavailable" on malformed input.
    """
    if not isinstance(blocks, list) or not blocks:
        return "unavailable"
    if not isinstance(page_width, (int, float)) or page_width <= 0:
        return "unavailable"
    if not isinstance(page_height, (int, float)) or page_height <= 0:
        return "unavailable"

    if margins is None:
        margins = {}
    ml = margins.get("left", 0)
    mt = margins.get("top", 0)
    mr = margins.get("right", 0)
    mb = margins.get("bottom", 0)
    right_bound = page_width - mr
    bottom_bound = page_height - mb

    violations = []
    for block in blocks:
        if not isinstance(block, dict):
            return "unavailable"
        if "bounds" not in block or len(block["bounds"]) != 4:
            return "unavailable"
        bx, by, bw, bh = block["bounds"]
        bx2 = bx + bw
        by2 = by + bh
        pi = block.get("page_index", 0)
        bid = block.get("id", "unknown")

        if bx < ml:
            violations.append({"page_index": pi, "block_id": bid, "overflow_axis": "x", "overflow_px": round(ml - bx, 4)})
        elif bx2 > right_bound:
            violations.append({"page_index": pi, "block_id": bid, "overflow_axis": "x", "overflow_px": round(bx2 - right_bound, 4)})

        if by < mt:
            violations.append({"page_index": pi, "block_id": bid, "overflow_axis": "y", "overflow_px": round(mt - by, 4)})
        elif by2 > bottom_bound:
            violations.append({"page_index": pi, "block_id": bid, "overflow_axis": "y", "overflow_px": round(by2 - bottom_bound, 4)})

    if violations:
        return {"status": "off_page_detected", "violations": violations}
    return "clear"


def compute_visual_certification_status(overlap_proof, off_page_proof, operator_approval=False):
    """
    Returns "certified" only if both proofs are "clear" and operator_approval is True.
    Any other combination returns "not_certified".
    """
    if overlap_proof == "clear" and off_page_proof == "clear" and operator_approval is True:
        return "certified"
    return "not_certified"


def run_geometry_proof(geometry_data):
    """
    Entry point: accepts a geometry_data dict with:
        blocks         — list of {id, bounds: [x, y, w, h], page_index}
        page_width     — page width in points
        page_height    — page height in points
        margins        — optional dict {top, bottom, left, right}
        operator_approval — bool (default False)

    Returns a proof dict:
        {
            "overlap_proof": "clear" | "unavailable" | {status, violations},
            "off_page_text_proof": "clear" | "unavailable" | {status, violations},
            "visual_certification_status": "not_certified" | "certified",
        }

    Fails closed: missing or malformed input → all fields unavailable/not_certified.
    """
    _unavailable = {
        "overlap_proof": "unavailable",
        "off_page_text_proof": "unavailable",
        "visual_certification_status": "not_certified",
    }

    if not isinstance(geometry_data, dict):
        return _unavailable

    blocks = geometry_data.get("blocks") or []
    if not blocks:
        return _unavailable

    page_width = geometry_data.get("page_width")
    page_height = geometry_data.get("page_height")
    margins = geometry_data.get("margins")
    operator_approval = geometry_data.get("operator_approval", False)

    overlap_proof = compute_overlap_proof(blocks)

    if page_width is not None and page_height is not None:
        off_page_proof = compute_off_page_proof(blocks, page_width, page_height, margins)
    else:
        off_page_proof = "unavailable"

    cert_status = compute_visual_certification_status(overlap_proof, off_page_proof, operator_approval)

    return {
        "overlap_proof": overlap_proof,
        "off_page_text_proof": off_page_proof,
        "visual_certification_status": cert_status,
    }
