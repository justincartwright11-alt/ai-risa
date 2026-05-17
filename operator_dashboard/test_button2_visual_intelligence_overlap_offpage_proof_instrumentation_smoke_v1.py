# Button 2 Visual Intelligence — Overlap/Off-Page Proof Instrumentation Smoke Proof (v1)
# Slice: button2-visual-intelligence-overlap-offpage-proof-instrumentation-smoke-v1
#
# Purpose: Evidence-only end-to-end smoke proof that geometry instrumentation, builder integration,
# metadata bridge, compatibility adapter, and fail-closed certification behavior work together
# as a stable QA chain.
#
# Governance:
#   - No PDFs generated
#   - No files written
#   - No renderer layout changes
#   - No dashboard changes
#   - No report-generation behavior changes
#   - No automatic certification without operator approval

import pytest
from operator_dashboard.button2_dossier_handoff_report_context_preview import (
    build_button2_dossier_handoff_report_context_preview,
)
from operator_dashboard.button2_visual_intelligence_renderer_contract_compatibility_layer_v1 import (
    map_report_context_to_visual_intelligence_contract,
)
from operator_dashboard.button2_visual_intelligence_renderer_contract_adapter_v1 import (
    adapt_renderer_output_to_contract,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CLEAN_BLOCKS = [
    {"id": "block-1", "bounds": [72, 72, 200, 100], "page_index": 0},
    {"id": "block-2", "bounds": [72, 180, 200, 100], "page_index": 0},
]

_OVERLAPPING_BLOCKS = [
    {"id": "block-1", "bounds": [72, 72, 200, 200], "page_index": 0},
    {"id": "block-2", "bounds": [150, 150, 200, 200], "page_index": 0},  # overlaps block-1
]

_OVERFLOW_BLOCKS = [
    {"id": "block-1", "bounds": [72, 72, 200, 100], "page_index": 0},
    {"id": "block-2", "bounds": [72, 750, 200, 200], "page_index": 0},   # overflows bottom at 842 with 72pt margin
]

_PAGE = {"page_width": 595, "page_height": 842, "margins": {"left": 72, "top": 72, "right": 72, "bottom": 72}}


def _make_ingest(geometry_data=None):
    ctx = {
        "button2_ingest_preview_context": {
            "destination_marker": "button2_report_generation_preview",
            "context_kind": "button1_dossier_handoff",
            "ingest_mode": "preview_only",
            "dossier_summary_preview": "Button1 Read-Only Dossier Handoff Preview\nFighter: Jon Jones",
        }
    }
    if geometry_data is not None:
        ctx["button2_ingest_preview_context"]["geometry_data"] = geometry_data
    return ctx


def _build(geometry_data=None):
    result = build_button2_dossier_handoff_report_context_preview(_make_ingest(geometry_data))
    assert result["ok"] is True
    return result["report_context_preview"]


# ---------------------------------------------------------------------------
# Smoke: geometry proof clear path works end-to-end
# ---------------------------------------------------------------------------

def test_smoke_clear_path_geometry_proof_reaches_report_context():
    rc = _build({**_PAGE, "blocks": _CLEAN_BLOCKS, "operator_approval": False})
    assert rc["overlap_proof"] == "clear"
    assert rc["off_page_text_proof"] == "clear"
    assert rc["visual_certification_status"] == "not_certified"   # no approval


def test_smoke_clear_path_with_approval_certifies():
    rc = _build({**_PAGE, "blocks": _CLEAN_BLOCKS, "operator_approval": True})
    assert rc["overlap_proof"] == "clear"
    assert rc["off_page_text_proof"] == "clear"
    assert rc["visual_certification_status"] == "certified"


# ---------------------------------------------------------------------------
# Smoke: geometry proof detected path works end-to-end
# ---------------------------------------------------------------------------

def test_smoke_overlap_detected_path_reaches_report_context():
    rc = _build({**_PAGE, "blocks": _OVERLAPPING_BLOCKS, "operator_approval": True})
    assert isinstance(rc["overlap_proof"], dict)
    assert rc["overlap_proof"]["status"] == "overlap_detected"
    assert rc["visual_certification_status"] == "not_certified"   # detected → no cert even with approval


def test_smoke_off_page_detected_path_reaches_report_context():
    rc = _build({**_PAGE, "blocks": _OVERFLOW_BLOCKS, "operator_approval": True})
    assert isinstance(rc["off_page_text_proof"], dict)
    assert rc["off_page_text_proof"]["status"] == "off_page_detected"
    assert rc["visual_certification_status"] == "not_certified"


# ---------------------------------------------------------------------------
# Smoke: malformed geometry fails closed
# ---------------------------------------------------------------------------

def test_smoke_none_geometry_fails_closed():
    rc = _build(None)
    assert rc["overlap_proof"] == "unavailable"
    assert rc["off_page_text_proof"] == "unavailable"
    assert rc["visual_certification_status"] == "not_certified"


def test_smoke_empty_blocks_fails_closed():
    rc = _build({**_PAGE, "blocks": [], "operator_approval": True})
    assert rc["overlap_proof"] == "unavailable"
    assert rc["off_page_text_proof"] == "unavailable"
    assert rc["visual_certification_status"] == "not_certified"


def test_smoke_malformed_blocks_fails_closed():
    rc = _build({**_PAGE, "blocks": [{"id": "x"}], "operator_approval": True})
    assert rc["overlap_proof"] == "unavailable"
    assert rc["visual_certification_status"] == "not_certified"


# ---------------------------------------------------------------------------
# Smoke: builder passes geometry_data into proof instrumentation
# ---------------------------------------------------------------------------

def test_smoke_builder_geometry_data_absent_keeps_unavailable():
    # Without geometry_data key, report-context must still default to unavailable
    rc = _build(None)
    assert rc["overlap_proof"] == "unavailable"
    assert rc["off_page_text_proof"] == "unavailable"


def test_smoke_builder_geometry_data_present_produces_real_proof():
    rc_no_geo = _build(None)
    rc_with_geo = _build({**_PAGE, "blocks": _CLEAN_BLOCKS, "operator_approval": False})
    # Only the geometry-powered context should have a real proof
    assert rc_no_geo["overlap_proof"] == "unavailable"
    assert rc_with_geo["overlap_proof"] == "clear"


# ---------------------------------------------------------------------------
# Smoke: metadata bridge receives proof results
# ---------------------------------------------------------------------------

def test_smoke_metadata_bridge_reads_clear_overlap_proof():
    rc = _build({**_PAGE, "blocks": _CLEAN_BLOCKS, "operator_approval": False})
    contract = map_report_context_to_visual_intelligence_contract(rc)
    # When overlap_proof=="clear", no_overlap must be True
    assert contract["no_overlap"] is True


def test_smoke_metadata_bridge_reads_clear_off_page_proof():
    rc = _build({**_PAGE, "blocks": _CLEAN_BLOCKS, "operator_approval": False})
    contract = map_report_context_to_visual_intelligence_contract(rc)
    assert contract["no_off_page_text"] is True


def test_smoke_metadata_bridge_reads_unavailable_overlap_as_false():
    rc = _build(None)
    contract = map_report_context_to_visual_intelligence_contract(rc)
    assert contract["no_overlap"] is False
    assert contract["no_off_page_text"] is False


def test_smoke_metadata_bridge_reads_detected_overlap_as_false():
    rc = _build({**_PAGE, "blocks": _OVERLAPPING_BLOCKS, "operator_approval": False})
    contract = map_report_context_to_visual_intelligence_contract(rc)
    assert contract["no_overlap"] is False


# ---------------------------------------------------------------------------
# Smoke: adapter rejects unavailable/detected proof
# ---------------------------------------------------------------------------

def test_smoke_adapter_rejects_unavailable_proof():
    rc = _build(None)
    contract = map_report_context_to_visual_intelligence_contract(rc)
    with pytest.raises(ValueError) as exc_info:
        adapt_renderer_output_to_contract(contract)
    assert "overlap" in str(exc_info.value).lower()


def test_smoke_adapter_rejects_detected_overlap():
    rc = _build({**_PAGE, "blocks": _OVERLAPPING_BLOCKS, "operator_approval": False})
    contract = map_report_context_to_visual_intelligence_contract(rc)
    with pytest.raises(ValueError):
        adapt_renderer_output_to_contract(contract)


def test_smoke_adapter_accepts_clear_proofs():
    rc = _build({**_PAGE, "blocks": _CLEAN_BLOCKS, "operator_approval": False})
    contract = map_report_context_to_visual_intelligence_contract(rc)
    # Both proofs clear → adapter must pass
    adapted = adapt_renderer_output_to_contract(contract)
    assert adapted["no_overlap"] is True
    assert adapted["no_off_page_text"] is True


# ---------------------------------------------------------------------------
# Smoke: certification requires clear proofs plus operator approval
# ---------------------------------------------------------------------------

def test_smoke_cert_requires_both_clear_and_approval():
    # clear + no approval → not_certified
    rc_no_approval = _build({**_PAGE, "blocks": _CLEAN_BLOCKS, "operator_approval": False})
    assert rc_no_approval["visual_certification_status"] == "not_certified"

    # clear + approval → certified
    rc_approved = _build({**_PAGE, "blocks": _CLEAN_BLOCKS, "operator_approval": True})
    assert rc_approved["visual_certification_status"] == "certified"


def test_smoke_cert_blocked_by_overlap_despite_approval():
    rc = _build({**_PAGE, "blocks": _OVERLAPPING_BLOCKS, "operator_approval": True})
    assert rc["visual_certification_status"] == "not_certified"


def test_smoke_cert_blocked_by_off_page_despite_approval():
    rc = _build({**_PAGE, "blocks": _OVERFLOW_BLOCKS, "operator_approval": True})
    assert rc["visual_certification_status"] == "not_certified"


def test_smoke_cert_blocked_by_unavailable_despite_approval():
    rc = _build(None)
    assert rc["visual_certification_status"] == "not_certified"


# ---------------------------------------------------------------------------
# Smoke: safety — no PDFs, no files, no dashboard/renderer changes
# ---------------------------------------------------------------------------

def test_smoke_no_pdf_generated_on_any_path():
    for geo in [None, {**_PAGE, "blocks": _CLEAN_BLOCKS, "operator_approval": True},
                {**_PAGE, "blocks": _OVERLAPPING_BLOCKS, "operator_approval": True}]:
        result = build_button2_dossier_handoff_report_context_preview(_make_ingest(geo))
        assert result["pdf_generation_performed"] is False
        assert result["file_write_performed"] is False


def test_smoke_preview_only_flag_always_set():
    for geo in [None, {**_PAGE, "blocks": _CLEAN_BLOCKS, "operator_approval": True}]:
        result = build_button2_dossier_handoff_report_context_preview(_make_ingest(geo))
        assert result["preview_only"] is True
        assert result["button2_generation_performed"] is False
        assert result["export_performed"] is False
        assert result["delivery_performed"] is False
