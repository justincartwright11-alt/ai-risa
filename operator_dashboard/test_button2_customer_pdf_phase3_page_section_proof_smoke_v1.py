"""Smoke tests for Phase 3 page-section proof helper (v1)."""

import operator_dashboard.button2_customer_pdf_phase3_page_section_proof_preview_v1 as preview


def _required_sections():
    return ["cover", "summary", "source_traceability"]


def _allowed_pages():
    return {
        "cover": [0],
        "summary": [1],
        "source_traceability": {"min_page": 2, "max_page": 3},
    }


def _clear_hits():
    return [
        {"section_name": "cover", "page_index": 0, "marker_id": "cover-title"},
        {"section_name": "summary", "page_index": 1, "marker_id": "summary-head"},
        {"section_name": "source_traceability", "page_index": 2, "marker_id": "source-trace"},
    ]


def test_valid_page_section_input_passes():
    result = preview.run_page_section_proof(
        _clear_hits(),
        _required_sections(),
        _allowed_pages(),
        observed_page_count=4,
        expected_page_count=4,
    )

    assert result["proof_status"] == "passed"
    assert result["section_signal"] == "clear"
    assert result["failure_reasons"] == []


def test_missing_required_section_reports_detected():
    hits = [
        {"section_name": "cover", "page_index": 0},
        {"section_name": "summary", "page_index": 1},
    ]

    result = preview.run_page_section_proof(hits, _required_sections(), _allowed_pages())

    assert result["proof_status"] == "failed_closed"
    assert result["section_signal"] == "detected"
    assert "missing_required_sections" in result["failure_reasons"]
    assert "source_traceability" in result["missing_required_sections"]


def test_duplicate_section_marker_reports_detected_when_forbidden():
    hits = _clear_hits() + [{"section_name": "summary", "page_index": 1}]

    result = preview.run_page_section_proof(
        hits,
        _required_sections(),
        _allowed_pages(),
        forbid_duplicate_required_sections=True,
    )

    assert result["proof_status"] == "failed_closed"
    assert result["section_signal"] == "detected"
    assert "ambiguous_section_mapping" in result["failure_reasons"]
    assert "summary" in result["ambiguous_sections"]


def test_page_count_mismatch_reports_detected():
    result = preview.run_page_section_proof(
        _clear_hits(),
        _required_sections(),
        _allowed_pages(),
        observed_page_count=5,
        expected_page_count=4,
    )

    assert result["proof_status"] == "failed_closed"
    assert result["section_signal"] == "detected"
    assert "page_count_mismatch" in result["failure_reasons"]


def test_malformed_input_fails_closed_to_unavailable():
    malformed = [{"section_name": "cover", "page_index": "zero"}]
    result = preview.run_page_section_proof(malformed, _required_sections(), _allowed_pages())

    assert result["proof_status"] == "failed_closed"
    assert result["section_signal"] == "unavailable"
    assert "invalid_section_hit_shape" in result["failure_reasons"]


def test_unavailable_channel_fails_closed_to_unavailable():
    result = preview.run_page_section_proof(
        _clear_hits(),
        _required_sections(),
        _allowed_pages(),
        section_channel_available=False,
    )

    assert result["proof_status"] == "failed_closed"
    assert result["section_signal"] == "unavailable"
    assert "section_channel_unavailable" in result["failure_reasons"]


def test_no_pdf_generation_and_no_file_writes():
    result = preview.run_page_section_proof(_clear_hits(), _required_sections(), _allowed_pages())

    assert result["pdf_generation_performed"] is False
    assert result["file_write_performed"] is False


def test_no_renderer_dashboard_delivery_or_certification_changes():
    result = preview.run_page_section_proof(_clear_hits(), _required_sections(), _allowed_pages())

    assert result["renderer_behavior_changed"] is False
    assert result["dashboard_behavior_changed"] is False
    assert result["delivery_workflow_changed"] is False
    assert result["certification_automation_changed"] is False
