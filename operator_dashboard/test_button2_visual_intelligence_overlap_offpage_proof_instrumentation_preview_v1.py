# Button 2 Visual Intelligence — Overlap & Off-Page Proof Instrumentation Preview Tests (v1)
# Slice: button2-visual-intelligence-overlap-offpage-proof-instrumentation-preview-v1
#
# Governance:
#   - No PDFs generated
#   - No files written
#   - No renderer layout changes
#   - No dashboard changes
#   - No report-generation behavior changes
#   - No automatic certification

import pytest
from operator_dashboard.button2_visual_intelligence_overlap_offpage_proof_instrumentation_v1 import (
    compute_overlap_proof,
    compute_off_page_proof,
    compute_visual_certification_status,
    run_geometry_proof,
)
from operator_dashboard.button2_dossier_handoff_report_context_preview import (
    build_button2_dossier_handoff_report_context_preview,
)


# ---------------------------------------------------------------------------
# compute_overlap_proof
# ---------------------------------------------------------------------------

def test_overlap_proof_no_blocks_returns_unavailable():
    assert compute_overlap_proof([]) == "unavailable"


def test_overlap_proof_none_returns_unavailable():
    assert compute_overlap_proof(None) == "unavailable"


def test_overlap_proof_non_overlapping_returns_clear():
    blocks = [
        {"id": "block-1", "bounds": [0, 0, 100, 50], "page_index": 0},
        {"id": "block-2", "bounds": [0, 60, 100, 50], "page_index": 0},   # directly below, no overlap
        {"id": "block-3", "bounds": [110, 0, 100, 50], "page_index": 0},  # to the right, no overlap
    ]
    assert compute_overlap_proof(blocks) == "clear"


def test_overlap_proof_touching_edges_returns_clear():
    # Touching edges have zero intersection area — not an overlap
    blocks = [
        {"id": "block-1", "bounds": [0, 0, 100, 50], "page_index": 0},
        {"id": "block-2", "bounds": [100, 0, 100, 50], "page_index": 0},  # starts exactly where block-1 ends
    ]
    assert compute_overlap_proof(blocks) == "clear"


def test_overlap_proof_overlapping_returns_violation():
    blocks = [
        {"id": "block-1", "bounds": [0, 0, 100, 100], "page_index": 0},
        {"id": "block-2", "bounds": [50, 50, 100, 100], "page_index": 0},  # 50x50 overlap
    ]
    result = compute_overlap_proof(blocks)
    assert isinstance(result, dict)
    assert result["status"] == "overlap_detected"
    assert len(result["violations"]) == 1
    v = result["violations"][0]
    assert v["block_a"] == "block-1"
    assert v["block_b"] == "block-2"
    assert v["intersection_area"] == 2500.0
    assert v["page_index"] == 0


def test_overlap_proof_blocks_on_different_pages_no_cross_page_detection():
    # Blocks on different pages must not be compared against each other
    blocks = [
        {"id": "block-1", "bounds": [0, 0, 100, 100], "page_index": 0},
        {"id": "block-2", "bounds": [0, 0, 100, 100], "page_index": 1},  # same coords, different page
    ]
    assert compute_overlap_proof(blocks) == "clear"


def test_overlap_proof_malformed_block_returns_unavailable():
    assert compute_overlap_proof([{"id": "x"}]) == "unavailable"   # missing bounds
    assert compute_overlap_proof(["not a dict"]) == "unavailable"


# ---------------------------------------------------------------------------
# compute_off_page_proof
# ---------------------------------------------------------------------------

def test_off_page_proof_no_blocks_returns_unavailable():
    assert compute_off_page_proof([], 595, 842) == "unavailable"


def test_off_page_proof_invalid_dimensions_returns_unavailable():
    blocks = [{"id": "block-1", "bounds": [0, 0, 100, 50], "page_index": 0}]
    assert compute_off_page_proof(blocks, 0, 842) == "unavailable"
    assert compute_off_page_proof(blocks, 595, -1) == "unavailable"


def test_off_page_proof_block_within_page_returns_clear():
    blocks = [{"id": "block-1", "bounds": [72, 72, 451, 698], "page_index": 0}]
    # A4: 595x842, margins 72pt each side → usable area 451x698 starting at (72,72)
    result = compute_off_page_proof(blocks, 595, 842, {"left": 72, "top": 72, "right": 72, "bottom": 72})
    assert result == "clear"


def test_off_page_proof_block_overflows_right():
    # Block extends 10pt past right margin
    blocks = [{"id": "block-1", "bounds": [72, 72, 462, 100], "page_index": 0}]  # x2 = 534, right_bound = 523
    result = compute_off_page_proof(blocks, 595, 842, {"left": 72, "top": 72, "right": 72, "bottom": 72})
    assert isinstance(result, dict)
    assert result["status"] == "off_page_detected"
    assert result["violations"][0]["block_id"] == "block-1"
    assert result["violations"][0]["overflow_axis"] == "x"
    assert result["violations"][0]["overflow_px"] == 11.0   # 534 - 523 = 11


def test_off_page_proof_block_overflows_bottom():
    # Block extends 20pt past bottom margin
    blocks = [{"id": "block-1", "bounds": [72, 72, 100, 790], "page_index": 0}]  # y2 = 862, bottom_bound = 770
    result = compute_off_page_proof(blocks, 595, 842, {"left": 72, "top": 72, "right": 72, "bottom": 72})
    assert isinstance(result, dict)
    assert result["status"] == "off_page_detected"
    assert result["violations"][0]["overflow_axis"] == "y"
    assert result["violations"][0]["overflow_px"] == 92.0  # 862 - 770 = 92


def test_off_page_proof_block_starts_before_left_margin():
    blocks = [{"id": "block-1", "bounds": [20, 72, 100, 100], "page_index": 0}]  # x=20 < margin_left=72
    result = compute_off_page_proof(blocks, 595, 842, {"left": 72, "top": 72, "right": 72, "bottom": 72})
    assert result["status"] == "off_page_detected"
    assert result["violations"][0]["overflow_axis"] == "x"
    assert result["violations"][0]["overflow_px"] == 52.0  # 72 - 20 = 52


def test_off_page_proof_no_margins_uses_full_page():
    # Block fits within 595x842 with no margins
    blocks = [{"id": "block-1", "bounds": [0, 0, 595, 842], "page_index": 0}]
    assert compute_off_page_proof(blocks, 595, 842) == "clear"


def test_off_page_proof_block_1px_outside_returns_violation():
    blocks = [{"id": "block-1", "bounds": [0, 0, 596, 842], "page_index": 0}]  # 1pt overflow right
    result = compute_off_page_proof(blocks, 595, 842)
    assert result["status"] == "off_page_detected"
    assert result["violations"][0]["overflow_px"] == 1.0


# ---------------------------------------------------------------------------
# compute_visual_certification_status
# ---------------------------------------------------------------------------

def test_cert_status_both_clear_with_approval():
    assert compute_visual_certification_status("clear", "clear", True) == "certified"


def test_cert_status_both_clear_no_approval():
    assert compute_visual_certification_status("clear", "clear", False) == "not_certified"


def test_cert_status_overlap_unavailable():
    assert compute_visual_certification_status("unavailable", "clear", True) == "not_certified"


def test_cert_status_off_page_unavailable():
    assert compute_visual_certification_status("clear", "unavailable", True) == "not_certified"


def test_cert_status_overlap_detected():
    violation = {"status": "overlap_detected", "violations": []}
    assert compute_visual_certification_status(violation, "clear", True) == "not_certified"


# ---------------------------------------------------------------------------
# run_geometry_proof (integration)
# ---------------------------------------------------------------------------

def test_run_geometry_proof_none_input():
    result = run_geometry_proof(None)
    assert result["overlap_proof"] == "unavailable"
    assert result["off_page_text_proof"] == "unavailable"
    assert result["visual_certification_status"] == "not_certified"


def test_run_geometry_proof_empty_blocks():
    result = run_geometry_proof({"blocks": []})
    assert result["overlap_proof"] == "unavailable"
    assert result["off_page_text_proof"] == "unavailable"
    assert result["visual_certification_status"] == "not_certified"


def test_run_geometry_proof_clean_geometry_no_approval():
    geometry_data = {
        "blocks": [
            {"id": "block-1", "bounds": [72, 72, 200, 100], "page_index": 0},
            {"id": "block-2", "bounds": [72, 180, 200, 100], "page_index": 0},
        ],
        "page_width": 595,
        "page_height": 842,
        "margins": {"left": 72, "top": 72, "right": 72, "bottom": 72},
        "operator_approval": False,
    }
    result = run_geometry_proof(geometry_data)
    assert result["overlap_proof"] == "clear"
    assert result["off_page_text_proof"] == "clear"
    assert result["visual_certification_status"] == "not_certified"   # no approval


def test_run_geometry_proof_clean_geometry_with_approval():
    geometry_data = {
        "blocks": [
            {"id": "block-1", "bounds": [72, 72, 200, 100], "page_index": 0},
            {"id": "block-2", "bounds": [72, 180, 200, 100], "page_index": 0},
        ],
        "page_width": 595,
        "page_height": 842,
        "margins": {"left": 72, "top": 72, "right": 72, "bottom": 72},
        "operator_approval": True,
    }
    result = run_geometry_proof(geometry_data)
    assert result["overlap_proof"] == "clear"
    assert result["off_page_text_proof"] == "clear"
    assert result["visual_certification_status"] == "certified"


def test_run_geometry_proof_overlap_detected_blocks_no_cert():
    geometry_data = {
        "blocks": [
            {"id": "block-1", "bounds": [72, 72, 200, 200], "page_index": 0},
            {"id": "block-2", "bounds": [150, 150, 200, 200], "page_index": 0},  # overlaps block-1
        ],
        "page_width": 595,
        "page_height": 842,
        "operator_approval": True,  # approval is present but should still not certify
    }
    result = run_geometry_proof(geometry_data)
    assert isinstance(result["overlap_proof"], dict)
    assert result["overlap_proof"]["status"] == "overlap_detected"
    assert result["visual_certification_status"] == "not_certified"


def test_run_geometry_proof_no_dimensions_off_page_unavailable():
    # No page_width/page_height → off_page_text_proof must be unavailable
    geometry_data = {
        "blocks": [{"id": "block-1", "bounds": [72, 72, 200, 100], "page_index": 0}],
        "operator_approval": False,
    }
    result = run_geometry_proof(geometry_data)
    assert result["overlap_proof"] == "clear"
    assert result["off_page_text_proof"] == "unavailable"
    assert result["visual_certification_status"] == "not_certified"


# ---------------------------------------------------------------------------
# Builder integration: geometry_data in ingest context
# ---------------------------------------------------------------------------

def _make_ingest_context(geometry_data=None):
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


def test_builder_without_geometry_data_stays_unavailable():
    result = build_button2_dossier_handoff_report_context_preview(_make_ingest_context())
    rc = result["report_context_preview"]
    assert rc["overlap_proof"] == "unavailable"
    assert rc["off_page_text_proof"] == "unavailable"
    assert rc["visual_certification_status"] == "not_certified"


def test_builder_with_clean_geometry_no_approval_still_not_certified():
    geo = {
        "blocks": [
            {"id": "block-1", "bounds": [72, 72, 200, 100], "page_index": 0},
            {"id": "block-2", "bounds": [72, 180, 200, 100], "page_index": 0},
        ],
        "page_width": 595,
        "page_height": 842,
        "margins": {"left": 72, "top": 72, "right": 72, "bottom": 72},
        "operator_approval": False,
    }
    result = build_button2_dossier_handoff_report_context_preview(_make_ingest_context(geo))
    rc = result["report_context_preview"]
    assert rc["overlap_proof"] == "clear"
    assert rc["off_page_text_proof"] == "clear"
    assert rc["visual_certification_status"] == "not_certified"


def test_builder_with_clean_geometry_and_approval_certifies():
    geo = {
        "blocks": [
            {"id": "block-1", "bounds": [72, 72, 200, 100], "page_index": 0},
            {"id": "block-2", "bounds": [72, 180, 200, 100], "page_index": 0},
        ],
        "page_width": 595,
        "page_height": 842,
        "margins": {"left": 72, "top": 72, "right": 72, "bottom": 72},
        "operator_approval": True,
    }
    result = build_button2_dossier_handoff_report_context_preview(_make_ingest_context(geo))
    rc = result["report_context_preview"]
    assert rc["overlap_proof"] == "clear"
    assert rc["off_page_text_proof"] == "clear"
    assert rc["visual_certification_status"] == "certified"


def test_builder_with_overlapping_geometry_does_not_certify():
    geo = {
        "blocks": [
            {"id": "block-1", "bounds": [72, 72, 200, 200], "page_index": 0},
            {"id": "block-2", "bounds": [150, 150, 200, 200], "page_index": 0},
        ],
        "page_width": 595,
        "page_height": 842,
        "operator_approval": True,
    }
    result = build_button2_dossier_handoff_report_context_preview(_make_ingest_context(geo))
    rc = result["report_context_preview"]
    assert rc["overlap_proof"]["status"] == "overlap_detected"
    assert rc["visual_certification_status"] == "not_certified"


def test_builder_no_pdf_generated_regardless_of_geometry():
    geo = {
        "blocks": [{"id": "block-1", "bounds": [72, 72, 200, 100], "page_index": 0}],
        "page_width": 595,
        "page_height": 842,
        "operator_approval": True,
    }
    result = build_button2_dossier_handoff_report_context_preview(_make_ingest_context(geo))
    assert result["pdf_generation_performed"] is False
    assert result["file_write_performed"] is False
    assert result["preview_only"] is True
