"""Smoke tests for Phase 3 header/footer/watermark proof helper (v1)."""

import operator_dashboard.button2_customer_pdf_phase3_header_footer_watermark_proof_preview_v1 as preview


def _clear_hits():
    return [
        {"page_index": 0, "area_type": "header", "token": "report-title", "marker_id": "header-title"},
        {"page_index": 0, "area_type": "header", "token": "page-number", "marker_id": "header-page-1"},
        {"page_index": 0, "area_type": "footer", "token": "status-label", "marker_id": "footer-status"},
        {"page_index": 0, "area_type": "footer", "token": "source-footer", "marker_id": "footer-source"},
        {"page_index": 0, "area_type": "watermark", "token": "confidential-watermark", "marker_id": "watermark-confidential"},
        {"page_index": 1, "area_type": "header", "token": "report-title", "marker_id": "header-title"},
        {"page_index": 1, "area_type": "header", "token": "page-number", "marker_id": "header-page-2"},
        {"page_index": 1, "area_type": "footer", "token": "status-label", "marker_id": "footer-status"},
        {"page_index": 1, "area_type": "footer", "token": "qa-footer", "marker_id": "footer-qa"},
    ]


def test_valid_header_footer_watermark_input_passes():
    result = preview.run_header_footer_watermark_proof(
        _clear_hits(),
        required_header_tokens=["report-title", "page-number"],
        required_footer_tokens=["status-label", "source-footer"],
        required_watermark_tokens=["confidential-watermark"],
        forbidden_watermark_tokens=["draft-watermark"],
        required_page_coverage=[0, 1],
    )

    assert result["proof_status"] == "passed"
    assert result["hfw_signal"] == "clear"
    assert result["failure_reasons"] == []


def test_missing_required_header_marker_reports_detected():
    result = preview.run_header_footer_watermark_proof(
        _clear_hits(),
        required_header_tokens=["report-title", "page-number", "missing-header-token"],
        required_footer_tokens=["status-label", "source-footer"],
        required_watermark_tokens=["confidential-watermark"],
        forbidden_watermark_tokens=[],
        required_page_coverage=[0, 1],
    )

    assert result["proof_status"] == "failed_closed"
    assert result["hfw_signal"] == "detected"
    assert "missing_required_header_tokens" in result["failure_reasons"]


def test_missing_required_footer_marker_reports_detected():
    result = preview.run_header_footer_watermark_proof(
        _clear_hits(),
        required_header_tokens=["report-title", "page-number"],
        required_footer_tokens=["status-label", "source-footer", "missing-footer-token"],
        required_watermark_tokens=["confidential-watermark"],
        forbidden_watermark_tokens=[],
        required_page_coverage=[0, 1],
    )

    assert result["proof_status"] == "failed_closed"
    assert result["hfw_signal"] == "detected"
    assert "missing_required_footer_tokens" in result["failure_reasons"]


def test_missing_required_watermark_marker_reports_detected():
    result = preview.run_header_footer_watermark_proof(
        _clear_hits(),
        required_header_tokens=["report-title", "page-number"],
        required_footer_tokens=["status-label", "source-footer"],
        required_watermark_tokens=["confidential-watermark", "missing-watermark-token"],
        forbidden_watermark_tokens=[],
        required_page_coverage=[0, 1],
    )

    assert result["proof_status"] == "failed_closed"
    assert result["hfw_signal"] == "detected"
    assert "missing_required_watermark_tokens" in result["failure_reasons"]


def test_forbidden_watermark_token_reports_detected():
    hits = _clear_hits() + [
        {"page_index": 0, "area_type": "watermark", "token": "draft-watermark"}
    ]
    result = preview.run_header_footer_watermark_proof(
        hits,
        required_header_tokens=["report-title", "page-number"],
        required_footer_tokens=["status-label", "source-footer"],
        required_watermark_tokens=["confidential-watermark"],
        forbidden_watermark_tokens=["draft-watermark"],
        required_page_coverage=[0, 1],
    )

    assert result["proof_status"] == "failed_closed"
    assert result["hfw_signal"] == "detected"
    assert "forbidden_watermark_tokens_detected" in result["failure_reasons"]


def test_malformed_input_fails_closed_to_unavailable():
    malformed = [{"page_index": "zero", "area_type": "header", "token": "report-title"}]
    result = preview.run_header_footer_watermark_proof(
        malformed,
        required_header_tokens=[],
        required_footer_tokens=[],
        required_watermark_tokens=[],
        forbidden_watermark_tokens=[],
        required_page_coverage=[],
    )

    assert result["proof_status"] == "failed_closed"
    assert result["hfw_signal"] == "unavailable"
    assert "invalid_hfw_hit_shape" in result["failure_reasons"]


def test_unavailable_channel_fails_closed_to_unavailable():
    result = preview.run_header_footer_watermark_proof(
        _clear_hits(),
        required_header_tokens=[],
        required_footer_tokens=[],
        required_watermark_tokens=[],
        forbidden_watermark_tokens=[],
        required_page_coverage=[],
        hfw_channel_available=False,
    )

    assert result["proof_status"] == "failed_closed"
    assert result["hfw_signal"] == "unavailable"
    assert "hfw_channel_unavailable" in result["failure_reasons"]


def test_no_pdf_generation_and_no_file_writes():
    result = preview.run_header_footer_watermark_proof(
        _clear_hits(),
        required_header_tokens=[],
        required_footer_tokens=[],
        required_watermark_tokens=[],
        forbidden_watermark_tokens=[],
        required_page_coverage=[],
    )

    assert result["pdf_generation_performed"] is False
    assert result["file_write_performed"] is False


def test_no_renderer_dashboard_delivery_or_certification_changes():
    result = preview.run_header_footer_watermark_proof(
        _clear_hits(),
        required_header_tokens=[],
        required_footer_tokens=[],
        required_watermark_tokens=[],
        forbidden_watermark_tokens=[],
        required_page_coverage=[],
    )

    assert result["renderer_behavior_changed"] is False
    assert result["dashboard_behavior_changed"] is False
    assert result["delivery_workflow_changed"] is False
    assert result["certification_automation_changed"] is False
