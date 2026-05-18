"""Smoke tests for Phase 3 geometry proof helper (v1)."""

import operator_dashboard.button2_customer_pdf_phase3_geometry_proof_preview_v1 as preview


def _bounds():
    return {0: {"width": 600, "height": 800}}


def _clear_blocks():
    return [
        {
            "region_name": "header",
            "page_index": 0,
            "x0": 20,
            "y0": 20,
            "x1": 580,
            "y1": 100,
            "region_kind": "text",
        },
        {
            "region_name": "body",
            "page_index": 0,
            "x0": 40,
            "y0": 130,
            "x1": 560,
            "y1": 700,
            "region_kind": "text",
        },
    ]


def test_clear_geometry_passes():
    result = preview.run_geometry_proof(
        _clear_blocks(),
        _bounds(),
        required_regions=["header", "body"],
        required_on_page_regions=["header", "body"],
        protected_non_overlap_pairs=[("header", "body")],
    )

    assert result["proof_status"] == "passed"
    assert result["geometry_signal"] == "clear"
    assert result["failure_reasons"] == []


def test_overlap_geometry_reports_detected():
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
            "y0": 80,
            "x1": 500,
            "y1": 220,
            "region_kind": "text",
        },
    ]

    result = preview.run_geometry_proof(
        blocks,
        _bounds(),
        protected_non_overlap_pairs=[("header", "watermark")],
    )

    assert result["proof_status"] == "failed_closed"
    assert result["geometry_signal"] == "detected"
    assert "protected_overlap_detected" in result["failure_reasons"]


def test_off_page_geometry_reports_detected():
    blocks = _clear_blocks() + [
        {
            "region_name": "source_traceability",
            "page_index": 0,
            "x0": 50,
            "y0": 760,
            "x1": 570,
            "y1": 830,
            "region_kind": "text",
        }
    ]

    result = preview.run_geometry_proof(
        blocks,
        _bounds(),
        required_on_page_regions=["source_traceability"],
    )

    assert result["proof_status"] == "failed_closed"
    assert result["geometry_signal"] == "detected"
    assert "off_page_required_regions" in result["failure_reasons"]
    assert "source_traceability" in result["off_page_required_regions"]


def test_malformed_geometry_fails_closed_to_unavailable():
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
    result = preview.run_geometry_proof(malformed, _bounds())

    assert result["proof_status"] == "failed_closed"
    assert result["geometry_signal"] == "unavailable"
    assert "invalid_region_geometry_shape" in result["failure_reasons"]


def test_missing_page_bounds_fails_closed_to_unavailable():
    result = preview.run_geometry_proof(_clear_blocks(), None)

    assert result["proof_status"] == "failed_closed"
    assert result["geometry_signal"] == "unavailable"
    assert "missing_page_bounds" in result["failure_reasons"]


def test_unavailable_channel_fails_closed_to_unavailable():
    result = preview.run_geometry_proof(
        _clear_blocks(),
        _bounds(),
        geometry_channel_available=False,
    )

    assert result["proof_status"] == "failed_closed"
    assert result["geometry_signal"] == "unavailable"
    assert "geometry_library_unavailable" in result["failure_reasons"]


def test_no_pdf_generation_and_no_file_writes():
    result = preview.run_geometry_proof(_clear_blocks(), _bounds())

    assert result["pdf_generation_performed"] is False
    assert result["file_write_performed"] is False


def test_no_renderer_dashboard_delivery_or_certification_changes():
    result = preview.run_geometry_proof(_clear_blocks(), _bounds())

    assert result["renderer_behavior_changed"] is False
    assert result["dashboard_behavior_changed"] is False
    assert result["delivery_workflow_changed"] is False
    assert result["certification_automation_changed"] is False
