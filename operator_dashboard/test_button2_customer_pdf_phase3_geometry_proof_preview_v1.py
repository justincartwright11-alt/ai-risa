"""Tests for Phase 3 geometry proof preview module (v1)."""

import operator_dashboard.button2_customer_pdf_phase3_geometry_proof_preview_v1 as preview


def _base_bounds():
    return {0: {"width": 600, "height": 800}}


def _base_blocks():
    return [
        {
            "region_name": "header",
            "page_index": 0,
            "x0": 20,
            "y0": 20,
            "x1": 580,
            "y1": 90,
            "region_kind": "text",
        },
        {
            "region_name": "body",
            "page_index": 0,
            "x0": 40,
            "y0": 120,
            "x1": 560,
            "y1": 700,
            "region_kind": "text",
        },
    ]


def test_contract_shape_and_channel():
    result = preview.run_geometry_proof(_base_blocks(), _base_bounds())
    assert result["schema_version"] == "button2.phase3.geometry_proof.v1"
    assert result["proof_channel"] == "geometry"


def test_clear_signal_when_geometry_is_valid():
    result = preview.run_geometry_proof(
        _base_blocks(),
        _base_bounds(),
        required_regions=["header", "body"],
        required_on_page_regions=["header", "body"],
        protected_non_overlap_pairs=[("header", "body")],
    )
    assert result["proof_status"] == "passed"
    assert result["geometry_signal"] == "clear"
    assert result["failure_reasons"] == []


def test_detected_signal_for_missing_required_region():
    result = preview.run_geometry_proof(
        _base_blocks(),
        _base_bounds(),
        required_regions=["header", "body", "footer"],
    )
    assert result["proof_status"] == "failed_closed"
    assert result["geometry_signal"] == "detected"
    assert "missing_required_regions" in result["failure_reasons"]
    assert "footer" in result["missing_required_regions"]


def test_detected_signal_for_off_page_text():
    blocks = _base_blocks() + [
        {
            "region_name": "source_traceability",
            "page_index": 0,
            "x0": 30,
            "y0": 760,
            "x1": 580,
            "y1": 840,
            "region_kind": "text",
        }
    ]
    result = preview.run_geometry_proof(
        blocks,
        _base_bounds(),
        required_on_page_regions=["source_traceability"],
    )
    assert result["proof_status"] == "failed_closed"
    assert result["geometry_signal"] == "detected"
    assert "off_page_required_regions" in result["failure_reasons"]
    assert "source_traceability" in result["off_page_required_regions"]


def test_detected_signal_for_protected_overlap():
    blocks = [
        {
            "region_name": "header",
            "page_index": 0,
            "x0": 20,
            "y0": 20,
            "x1": 580,
            "y1": 120,
            "region_kind": "text",
        },
        {
            "region_name": "watermark",
            "page_index": 0,
            "x0": 100,
            "y0": 60,
            "x1": 500,
            "y1": 220,
            "region_kind": "text",
        },
    ]
    result = preview.run_geometry_proof(
        blocks,
        _base_bounds(),
        protected_non_overlap_pairs=[("header", "watermark")],
    )
    assert result["proof_status"] == "failed_closed"
    assert result["geometry_signal"] == "detected"
    assert "protected_overlap_detected" in result["failure_reasons"]
    assert result["protected_overlap_pairs_detected"]


def test_unavailable_signal_when_geometry_channel_unavailable():
    result = preview.run_geometry_proof(
        _base_blocks(),
        _base_bounds(),
        geometry_channel_available=False,
    )
    assert result["proof_status"] == "failed_closed"
    assert result["geometry_signal"] == "unavailable"
    assert "geometry_library_unavailable" in result["failure_reasons"]


def test_malformed_geometry_fails_closed():
    malformed = [
        {
            "region_name": "header",
            "page_index": 0,
            "x0": 20,
            "y0": 20,
            "x1": 10,
            "y1": 90,
        }
    ]
    result = preview.run_geometry_proof(malformed, _base_bounds())
    assert result["proof_status"] == "failed_closed"
    assert result["geometry_signal"] == "unavailable"
    assert "invalid_region_geometry_shape" in result["failure_reasons"]


def test_missing_page_bounds_fails_closed():
    result = preview.run_geometry_proof(_base_blocks(), None)
    assert result["proof_status"] == "failed_closed"
    assert result["geometry_signal"] == "unavailable"
    assert "missing_page_bounds" in result["failure_reasons"]


def test_no_pdf_or_file_writes():
    result = preview.run_geometry_proof(_base_blocks(), _base_bounds())
    assert result["pdf_generation_performed"] is False
    assert result["file_write_performed"] is False


def test_no_renderer_dashboard_delivery_or_certification_changes():
    result = preview.run_geometry_proof(_base_blocks(), _base_bounds())
    assert result["renderer_behavior_changed"] is False
    assert result["dashboard_behavior_changed"] is False
    assert result["delivery_workflow_changed"] is False
    assert result["certification_automation_changed"] is False
