# Button 2 Visual Intelligence — WeasyPrint Geometry Extractor End-to-End Smoke Proof (v1)
# Slice: button2-visual-intelligence-weasyprint-geometry-extractor-smoke-v1
#
# Purpose: Evidence-only smoke proof that the WeasyPrint geometry extractor, geometry proof
# instrumentation, metadata bridge, compatibility adapter, and fail-closed certification
# behavior work together as a stable QA chain.
#
# Governance:
#   - No PDFs generated
#   - No files written
#   - No renderer layout changes
#   - No dashboard changes
#   - No report-generation behavior changes
#   - No automatic certification without operator approval

import pytest
from operator_dashboard.button2_visual_intelligence_weasyprint_geometry_extractor_preview_v1 import (
    extract_weasyprint_page_geometry,
)
from operator_dashboard.button2_visual_intelligence_overlap_offpage_proof_instrumentation_v1 import (
    run_geometry_proof,
)
from operator_dashboard.button2_visual_intelligence_renderer_contract_compatibility_layer_v1 import (
    map_report_context_to_visual_intelligence_contract,
)
from operator_dashboard.button2_visual_intelligence_renderer_contract_adapter_v1 import (
    adapt_renderer_output_to_contract,
)
from operator_dashboard.button2_dossier_handoff_report_context_preview import (
    build_button2_dossier_handoff_report_context_preview,
)


# ---------------------------------------------------------------------------
# Mock WeasyPrint document helpers (same pattern as extractor unit tests)
# ---------------------------------------------------------------------------

class _E:
    def __init__(self, tag): self.tag = tag

class _B:
    def __init__(self, tag=None, x=0.0, y=0.0, w=100.0, h=50.0, children=None):
        self.element = _E(tag) if tag else None
        self.position_x, self.position_y, self.width, self.height = x, y, w, h
        self.children = children or []

class _P:
    def __init__(self, pb): self._page_box = pb

class _D:
    def __init__(self, pages): self.pages = pages


def _doc(content_boxes, pw=595.0, ph=842.0):
    pb = _B(w=pw, h=ph, children=content_boxes)
    return _D([_P(pb)])


_CLEAN = [
    _B("div",  x=72, y=72,  w=200, h=100),
    _B("p",    x=72, y=180, w=200, h=100),
]
_OVERLAPPING = [
    _B("div",  x=72,  y=72,  w=300, h=200),
    _B("div",  x=200, y=150, w=200, h=200),  # overlaps first
]
_OVERFLOW = [
    _B("div",  x=72,  y=72,  w=200, h=100),
    _B("div",  x=72,  y=750, w=200, h=200),  # overflows bottom (y2=950 > 842-72=770)
]
_MARGINS = {"left": 72, "top": 72, "right": 72, "bottom": 72}


def _proof(mock_doc, margins=None, approval=False):
    geo = extract_weasyprint_page_geometry(mock_doc)
    return run_geometry_proof({
        **geo,
        **({"margins": margins} if margins else {}),
        "operator_approval": approval,
    })


# ---------------------------------------------------------------------------
# Smoke: extractor output feeds geometry proof instrumentation
# ---------------------------------------------------------------------------

def test_smoke_extractor_output_is_accepted_by_proof_instrumentation():
    geo = extract_weasyprint_page_geometry(_doc(_CLEAN))
    assert geo["extraction_status"] == "ok"
    assert isinstance(geo["blocks"], list) and len(geo["blocks"]) > 0
    proof = run_geometry_proof({**geo, "operator_approval": False})
    assert "overlap_proof" in proof
    assert "off_page_text_proof" in proof
    assert "visual_certification_status" in proof


# ---------------------------------------------------------------------------
# Smoke: clear geometry → clear proof
# ---------------------------------------------------------------------------

def test_smoke_clear_geometry_overlap_proof_clear():
    proof = _proof(_doc(_CLEAN), margins=_MARGINS)
    assert proof["overlap_proof"] == "clear"


def test_smoke_clear_geometry_off_page_proof_clear():
    proof = _proof(_doc(_CLEAN), margins=_MARGINS)
    assert proof["off_page_text_proof"] == "clear"


def test_smoke_clear_geometry_no_approval_not_certified():
    proof = _proof(_doc(_CLEAN), margins=_MARGINS, approval=False)
    assert proof["visual_certification_status"] == "not_certified"


def test_smoke_clear_geometry_with_approval_certified():
    proof = _proof(_doc(_CLEAN), margins=_MARGINS, approval=True)
    assert proof["visual_certification_status"] == "certified"


# ---------------------------------------------------------------------------
# Smoke: overlapping geometry → detected proof
# ---------------------------------------------------------------------------

def test_smoke_overlapping_geometry_overlap_detected():
    proof = _proof(_doc(_OVERLAPPING), margins=_MARGINS, approval=True)
    assert isinstance(proof["overlap_proof"], dict)
    assert proof["overlap_proof"]["status"] == "overlap_detected"
    assert len(proof["overlap_proof"]["violations"]) > 0


def test_smoke_overlapping_geometry_not_certified_despite_approval():
    proof = _proof(_doc(_OVERLAPPING), margins=_MARGINS, approval=True)
    assert proof["visual_certification_status"] == "not_certified"


# ---------------------------------------------------------------------------
# Smoke: off-page geometry → detected proof
# ---------------------------------------------------------------------------

def test_smoke_off_page_geometry_off_page_detected():
    proof = _proof(_doc(_OVERFLOW), margins=_MARGINS, approval=True)
    assert isinstance(proof["off_page_text_proof"], dict)
    assert proof["off_page_text_proof"]["status"] == "off_page_detected"


def test_smoke_off_page_geometry_not_certified_despite_approval():
    proof = _proof(_doc(_OVERFLOW), margins=_MARGINS, approval=True)
    assert proof["visual_certification_status"] == "not_certified"


# ---------------------------------------------------------------------------
# Smoke: malformed extractor input fails closed to unavailable
# ---------------------------------------------------------------------------

def test_smoke_none_doc_fails_closed():
    geo = extract_weasyprint_page_geometry(None)
    assert geo["extraction_status"] == "unavailable"
    proof = run_geometry_proof(geo)
    assert proof["overlap_proof"] == "unavailable"
    assert proof["off_page_text_proof"] == "unavailable"
    assert proof["visual_certification_status"] == "not_certified"


def test_smoke_empty_pages_fails_closed():
    geo = extract_weasyprint_page_geometry(_D([]))
    proof = run_geometry_proof({**geo, "operator_approval": True})
    assert proof["overlap_proof"] == "unavailable"
    assert proof["visual_certification_status"] == "not_certified"


def test_smoke_zero_size_blocks_all_filtered_fails_closed():
    # All blocks zero-size → no_content_blocks → proof unavailable
    zero_blocks = [_B("div", w=0, h=0), _B("p", w=0, h=0)]
    geo = extract_weasyprint_page_geometry(_doc(zero_blocks))
    assert geo["extraction_status"] == "no_content_blocks"
    proof = run_geometry_proof({**geo, "operator_approval": True})
    assert proof["overlap_proof"] == "unavailable"


# ---------------------------------------------------------------------------
# Smoke: metadata bridge reads extractor + proof results
# ---------------------------------------------------------------------------

def _rc_from_geo(mock_doc, margins=None, approval=False):
    geo = extract_weasyprint_page_geometry(mock_doc)
    ingest = {
        "button2_ingest_preview_context": {
            "destination_marker": "button2_report_generation_preview",
            "context_kind": "button1_dossier_handoff",
            "ingest_mode": "preview_only",
            "dossier_summary_preview": "Preview\nFighter: Test",
            "geometry_data": {**geo, **({"margins": margins} if margins else {}), "operator_approval": approval},
        }
    }
    result = build_button2_dossier_handoff_report_context_preview(ingest)
    assert result["ok"] is True
    return result["report_context_preview"]


def test_smoke_metadata_bridge_reads_clear_overlap_from_extractor():
    rc = _rc_from_geo(_doc(_CLEAN), margins=_MARGINS, approval=False)
    assert rc["overlap_proof"] == "clear"
    contract = map_report_context_to_visual_intelligence_contract(rc)
    assert contract["no_overlap"] is True


def test_smoke_metadata_bridge_reads_clear_off_page_from_extractor():
    rc = _rc_from_geo(_doc(_CLEAN), margins=_MARGINS, approval=False)
    assert rc["off_page_text_proof"] == "clear"
    contract = map_report_context_to_visual_intelligence_contract(rc)
    assert contract["no_off_page_text"] is True


def test_smoke_metadata_bridge_reads_detected_overlap_as_false():
    rc = _rc_from_geo(_doc(_OVERLAPPING), margins=_MARGINS, approval=False)
    contract = map_report_context_to_visual_intelligence_contract(rc)
    assert contract["no_overlap"] is False


# ---------------------------------------------------------------------------
# Smoke: adapter accepts only real clear proof
# ---------------------------------------------------------------------------

def test_smoke_adapter_accepts_clear_proof_from_extractor():
    rc = _rc_from_geo(_doc(_CLEAN), margins=_MARGINS, approval=False)
    contract = map_report_context_to_visual_intelligence_contract(rc)
    adapted = adapt_renderer_output_to_contract(contract)
    assert adapted["no_overlap"] is True
    assert adapted["no_off_page_text"] is True


def test_smoke_adapter_rejects_detected_overlap_from_extractor():
    rc = _rc_from_geo(_doc(_OVERLAPPING), margins=_MARGINS, approval=False)
    contract = map_report_context_to_visual_intelligence_contract(rc)
    with pytest.raises(ValueError):
        adapt_renderer_output_to_contract(contract)


def test_smoke_adapter_rejects_unavailable_proof_from_extractor():
    rc = _rc_from_geo(None, approval=False)
    contract = map_report_context_to_visual_intelligence_contract(rc)
    with pytest.raises(ValueError) as exc_info:
        adapt_renderer_output_to_contract(contract)
    assert "overlap" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# Smoke: safety — no PDFs, no files, no dashboard/renderer changes
# ---------------------------------------------------------------------------

def test_smoke_no_pdf_or_file_on_any_geometry_path():
    for mock_doc in [_doc(_CLEAN), _doc(_OVERLAPPING), None]:
        geo = extract_weasyprint_page_geometry(mock_doc)
        ingest = {
            "button2_ingest_preview_context": {
                "destination_marker": "button2_report_generation_preview",
                "context_kind": "button1_dossier_handoff",
                "ingest_mode": "preview_only",
                "dossier_summary_preview": "Preview",
                "geometry_data": {**geo, "operator_approval": True} if geo["blocks"] is not None else geo,
            }
        }
        result = build_button2_dossier_handoff_report_context_preview(ingest)
        assert result["pdf_generation_performed"] is False
        assert result["file_write_performed"] is False
        assert result["preview_only"] is True
