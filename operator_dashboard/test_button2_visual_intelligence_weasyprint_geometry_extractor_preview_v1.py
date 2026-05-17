# Button 2 Visual Intelligence — WeasyPrint Geometry Extractor Preview Tests (v1)
# Slice: button2-visual-intelligence-weasyprint-geometry-extractor-preview-v1
#
# Tests use mock objects that mimic WeasyPrint's duck-typed box tree structure.
# WeasyPrint integration test is skipped when weasyprint is not installed.
#
# Governance:
#   - No PDFs generated
#   - No files written
#   - No renderer layout changes
#   - No dashboard changes
#   - No automatic certification

import pytest
from operator_dashboard.button2_visual_intelligence_weasyprint_geometry_extractor_preview_v1 import (
    extract_weasyprint_page_geometry,
    _get_element_tag,
    _CONTENT_TAGS,
    _MIN_SIZE_PT,
)
from operator_dashboard.button2_visual_intelligence_overlap_offpage_proof_instrumentation_v1 import (
    run_geometry_proof,
)


# ---------------------------------------------------------------------------
# Mock WeasyPrint structure
# ---------------------------------------------------------------------------

class _MockElement:
    """Minimal mock of an lxml element with just a tag."""
    def __init__(self, tag):
        self.tag = tag


class _MockBox:
    """Minimal mock of a WeasyPrint box."""
    def __init__(self, tag=None, x=0.0, y=0.0, w=100.0, h=50.0, children=None):
        self.element = _MockElement(tag) if tag else None
        self.position_x = x
        self.position_y = y
        self.width = w
        self.height = h
        self.children = children or []


class _MockPage:
    """Minimal mock of a WeasyPrint Page."""
    def __init__(self, page_box):
        self._page_box = page_box


class _MockDocument:
    """Minimal mock of a WeasyPrint rendered document."""
    def __init__(self, pages):
        self.pages = pages


def _make_single_page_doc(content_boxes, page_w=595.0, page_h=842.0):
    """Helper: one page with given content boxes as children of the page box."""
    page_box = _MockBox(tag=None, x=0, y=0, w=page_w, h=page_h, children=content_boxes)
    return _MockDocument([_MockPage(page_box)])


# ---------------------------------------------------------------------------
# _get_element_tag helper
# ---------------------------------------------------------------------------

def test_get_element_tag_returns_tag():
    box = _MockBox("div")
    assert _get_element_tag(box) == "div"


def test_get_element_tag_strips_namespace():
    box = _MockBox("{http://www.w3.org/1999/xhtml}section")
    assert _get_element_tag(box) == "section"


def test_get_element_tag_anonymous_box_returns_none():
    box = _MockBox(tag=None)
    assert _get_element_tag(box) is None


def test_get_element_tag_no_element_attribute():
    class NoElement:
        pass
    assert _get_element_tag(NoElement()) is None


# ---------------------------------------------------------------------------
# Fail-closed: malformed / missing input
# ---------------------------------------------------------------------------

def test_extract_none_returns_unavailable():
    result = extract_weasyprint_page_geometry(None)
    assert result["extraction_status"] == "unavailable"
    assert result["blocks"] is None
    assert result["page_width"] is None
    assert result["page_height"] is None


def test_extract_missing_pages_attribute_returns_unavailable():
    class NoPagesDoc:
        pass
    result = extract_weasyprint_page_geometry(NoPagesDoc())
    assert result["extraction_status"] == "unavailable"


def test_extract_empty_pages_returns_unavailable():
    result = extract_weasyprint_page_geometry(_MockDocument([]))
    assert result["extraction_status"] == "unavailable"


def test_extract_page_missing_page_box_returns_unavailable():
    class PageWithoutPageBox:
        pass
    doc = _MockDocument([PageWithoutPageBox()])
    result = extract_weasyprint_page_geometry(doc)
    assert result["extraction_status"] == "unavailable"


def test_extract_page_box_missing_dimensions_returns_unavailable():
    class DimensionlessBox:
        children = []
    class PageWithDimensionlessBox:
        _page_box = DimensionlessBox()
    doc = _MockDocument([PageWithDimensionlessBox()])
    result = extract_weasyprint_page_geometry(doc)
    assert result["extraction_status"] == "unavailable"


# ---------------------------------------------------------------------------
# Core extraction: block id, bounds, page_index
# ---------------------------------------------------------------------------

def test_extract_single_content_block_id_convention():
    doc = _make_single_page_doc([_MockBox("div", x=10, y=20, w=200, h=80)])
    result = extract_weasyprint_page_geometry(doc)
    assert result["extraction_status"] == "ok"
    assert len(result["blocks"]) == 1
    assert result["blocks"][0]["id"] == "div-p0-0"


def test_extract_block_bounds_correct():
    doc = _make_single_page_doc([_MockBox("p", x=72.5, y=100.0, w=451.0, h=60.0)])
    result = extract_weasyprint_page_geometry(doc)
    block = result["blocks"][0]
    assert block["bounds"] == [72.5, 100.0, 451.0, 60.0]


def test_extract_block_page_index():
    box_p0 = _MockBox("div", x=0, y=0, w=100, h=50)
    box_p1 = _MockBox("div", x=0, y=0, w=100, h=50)
    page0_box = _MockBox(tag=None, w=595, h=842, children=[box_p0])
    page1_box = _MockBox(tag=None, w=595, h=842, children=[box_p1])
    doc = _MockDocument([_MockPage(page0_box), _MockPage(page1_box)])
    result = extract_weasyprint_page_geometry(doc)
    assert len(result["blocks"]) == 2
    assert result["blocks"][0]["page_index"] == 0
    assert result["blocks"][1]["page_index"] == 1


def test_extract_sequential_ids_within_page():
    boxes = [
        _MockBox("div", x=0, y=0, w=100, h=50),
        _MockBox("p", x=0, y=60, w=100, h=30),
        _MockBox("section", x=0, y=100, w=100, h=40),
    ]
    result = extract_weasyprint_page_geometry(_make_single_page_doc(boxes))
    ids = [b["id"] for b in result["blocks"]]
    assert ids == ["div-p0-0", "p-p0-1", "section-p0-2"]


def test_extract_page_dimensions():
    doc = _make_single_page_doc([_MockBox("div", w=100, h=50)], page_w=595.0, page_h=842.0)
    result = extract_weasyprint_page_geometry(doc)
    assert result["page_width"] == 595.0
    assert result["page_height"] == 842.0


# ---------------------------------------------------------------------------
# Filtering: zero-size, anonymous, non-content tags
# ---------------------------------------------------------------------------

def test_extract_filters_zero_width_box():
    doc = _make_single_page_doc([_MockBox("div", w=0, h=50)])
    result = extract_weasyprint_page_geometry(doc)
    assert result["blocks"] == []
    assert result["extraction_status"] == "no_content_blocks"


def test_extract_filters_zero_height_box():
    doc = _make_single_page_doc([_MockBox("div", w=100, h=0)])
    result = extract_weasyprint_page_geometry(doc)
    assert result["blocks"] == []


def test_extract_filters_sub_minimum_size():
    # _MIN_SIZE_PT = 1.0 — a box of 0.5 x 0.5 must be excluded
    doc = _make_single_page_doc([_MockBox("div", w=_MIN_SIZE_PT - 0.5, h=_MIN_SIZE_PT - 0.5)])
    result = extract_weasyprint_page_geometry(doc)
    assert result["blocks"] == []


def test_extract_filters_anonymous_box():
    # Anonymous boxes have element=None
    doc = _make_single_page_doc([_MockBox(tag=None, w=200, h=100)])
    result = extract_weasyprint_page_geometry(doc)
    assert result["blocks"] == []


def test_extract_filters_non_content_tag_span():
    doc = _make_single_page_doc([_MockBox("span", w=100, h=20)])
    result = extract_weasyprint_page_geometry(doc)
    assert result["blocks"] == []


def test_extract_filters_non_content_tag_a():
    doc = _make_single_page_doc([_MockBox("a", w=100, h=20)])
    result = extract_weasyprint_page_geometry(doc)
    assert result["blocks"] == []


def test_extract_all_content_tags_accepted():
    # Each content tag must be extracted correctly
    for tag in sorted(_CONTENT_TAGS):
        doc = _make_single_page_doc([_MockBox(tag, w=100, h=50)])
        result = extract_weasyprint_page_geometry(doc)
        assert len(result["blocks"]) == 1, f"Tag '{tag}' was not extracted"
        assert result["blocks"][0]["id"].startswith(f"{tag}-")


# ---------------------------------------------------------------------------
# Recursive child traversal
# ---------------------------------------------------------------------------

def test_extract_recurses_into_children():
    child = _MockBox("p", x=10, y=10, w=100, h=30)
    parent = _MockBox("div", x=0, y=0, w=200, h=100, children=[child])
    result = extract_weasyprint_page_geometry(_make_single_page_doc([parent]))
    ids = [b["id"] for b in result["blocks"]]
    # Both parent div and child p should appear
    assert "div-p0-0" in ids
    assert "p-p0-1" in ids


def test_extract_anonymous_parent_with_content_children():
    # An anonymous page-box child wrapping content — children should still be found
    content = _MockBox("section", x=72, y=72, w=451, h=200)
    anon_wrapper = _MockBox(tag=None, x=0, y=0, w=595, h=842, children=[content])
    page_box = _MockBox(tag=None, x=0, y=0, w=595, h=842, children=[anon_wrapper])
    doc = _MockDocument([_MockPage(page_box)])
    result = extract_weasyprint_page_geometry(doc)
    assert len(result["blocks"]) == 1
    assert result["blocks"][0]["id"] == "section-p0-0"


# ---------------------------------------------------------------------------
# preview_only flag
# ---------------------------------------------------------------------------

def test_extract_preview_only_always_true():
    result_ok = extract_weasyprint_page_geometry(_make_single_page_doc([_MockBox("div", w=100, h=50)]))
    result_unavail = extract_weasyprint_page_geometry(None)
    assert result_ok["preview_only"] is True
    assert result_unavail["preview_only"] is True


# ---------------------------------------------------------------------------
# Output feeds run_geometry_proof (end-to-end compatibility)
# ---------------------------------------------------------------------------

def test_extractor_output_feeds_geometry_proof_clear():
    # Non-overlapping blocks inside page → clear proofs
    boxes = [
        _MockBox("div", x=72, y=72, w=200, h=100),
        _MockBox("div", x=72, y=180, w=200, h=100),
    ]
    geo = extract_weasyprint_page_geometry(_make_single_page_doc(boxes, page_w=595, page_h=842))
    assert geo["extraction_status"] == "ok"

    proof = run_geometry_proof({
        **geo,
        "margins": {"left": 72, "top": 72, "right": 72, "bottom": 72},
        "operator_approval": False,
    })
    assert proof["overlap_proof"] == "clear"
    assert proof["off_page_text_proof"] == "clear"
    assert proof["visual_certification_status"] == "not_certified"   # no approval


def test_extractor_output_feeds_geometry_proof_with_approval_certifies():
    boxes = [
        _MockBox("div", x=72, y=72, w=200, h=100),
        _MockBox("p",   x=72, y=180, w=200, h=100),
    ]
    geo = extract_weasyprint_page_geometry(_make_single_page_doc(boxes, page_w=595, page_h=842))
    proof = run_geometry_proof({
        **geo,
        "margins": {"left": 72, "top": 72, "right": 72, "bottom": 72},
        "operator_approval": True,
    })
    assert proof["visual_certification_status"] == "certified"


def test_extractor_unavailable_output_keeps_proof_unavailable():
    geo = extract_weasyprint_page_geometry(None)
    proof = run_geometry_proof(geo)
    assert proof["overlap_proof"] == "unavailable"
    assert proof["off_page_text_proof"] == "unavailable"
    assert proof["visual_certification_status"] == "not_certified"


def test_extractor_overlap_detected_blocks_proof_detected():
    boxes = [
        _MockBox("div", x=72, y=72, w=300, h=200),
        _MockBox("div", x=200, y=150, w=200, h=200),  # overlaps first
    ]
    geo = extract_weasyprint_page_geometry(_make_single_page_doc(boxes))
    proof = run_geometry_proof({**geo, "operator_approval": True})
    assert proof["overlap_proof"]["status"] == "overlap_detected"
    assert proof["visual_certification_status"] == "not_certified"


# ---------------------------------------------------------------------------
# WeasyPrint real integration (skipped if not installed)
# ---------------------------------------------------------------------------

def test_weasyprint_real_render_integration():
    weasyprint = pytest.importorskip("weasyprint")
    html = """<!DOCTYPE html>
<html><body>
<div style="width:400px;height:100px;position:absolute;top:72pt;left:72pt">Block A</div>
<p style="width:400px;height:60px;position:absolute;top:180pt;left:72pt">Block B</p>
</body></html>"""
    doc = weasyprint.HTML(string=html).render()
    result = extract_weasyprint_page_geometry(doc)
    assert result["preview_only"] is True
    assert result["page_width"] is not None and result["page_width"] > 0
    assert result["page_height"] is not None and result["page_height"] > 0
    assert isinstance(result["blocks"], list)
    # At minimum, some blocks must be extracted
    ids = [b["id"] for b in result["blocks"]]
    assert any("-p0-" in i for i in ids), f"No page-0 blocks found: {ids}"
