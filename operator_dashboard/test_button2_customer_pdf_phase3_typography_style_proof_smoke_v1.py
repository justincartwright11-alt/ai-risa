"""Smoke tests for Phase 3 typography/style proof helper (v1)."""

import operator_dashboard.button2_customer_pdf_phase3_typography_style_proof_preview_v1 as preview


def _clear_hits():
    return [
        {
            "section_name": "cover",
            "token": "font-family:IBM Plex Sans",
            "class_name": "title",
            "marker_id": "cover-title",
            "font_size": 22,
            "font_weight": 700,
            "line_height": 1.35,
        },
        {
            "section_name": "summary",
            "token": "font-family:IBM Plex Sans",
            "class_name": "body",
            "marker_id": "summary-body",
            "font_size": 12,
            "font_weight": 400,
            "line_height": 1.5,
        },
    ]


def _run_base(hits, **kwargs):
    base_kwargs = {
        "required_style_tokens": ["font-family:IBM Plex Sans"],
        "forbidden_style_tokens": ["font-family:Comic Sans"],
        "section_style_rules": {
            "cover": ["font-family:IBM Plex Sans"],
            "summary": ["font-family:IBM Plex Sans"],
        },
        "required_style_classes": ["title", "body"],
        "required_typography_markers": ["cover-title", "summary-body"],
        "allowed_font_weights": ["400", "700"],
        "font_size_range": [10, 28],
        "line_height_range": [1.2, 1.8],
    }
    base_kwargs.update(kwargs)
    return preview.run_typography_style_proof(hits, **base_kwargs)


def test_valid_typography_style_input_passes():
    result = _run_base(_clear_hits())

    assert result["proof_status"] == "passed"
    assert result["style_signal"] == "clear"
    assert result["failure_reasons"] == []


def test_invalid_font_size_reports_detected():
    hits = _clear_hits()
    hits[0]["font_size"] = 8
    result = _run_base(hits)

    assert result["proof_status"] == "failed_closed"
    assert result["style_signal"] == "detected"
    assert "invalid_style_values" in result["failure_reasons"]


def test_invalid_font_weight_reports_detected():
    hits = _clear_hits()
    hits[1]["font_weight"] = 950
    result = _run_base(hits)

    assert result["proof_status"] == "failed_closed"
    assert result["style_signal"] == "detected"
    assert "invalid_style_values" in result["failure_reasons"]


def test_invalid_line_height_reports_detected():
    hits = _clear_hits()
    hits[1]["line_height"] = 2.2
    result = _run_base(hits)

    assert result["proof_status"] == "failed_closed"
    assert result["style_signal"] == "detected"
    assert "invalid_style_values" in result["failure_reasons"]


def test_missing_required_token_reports_detected():
    result = _run_base(
        _clear_hits(),
        required_style_tokens=["font-family:IBM Plex Sans", "font-size:14"],
    )

    assert result["proof_status"] == "failed_closed"
    assert result["style_signal"] == "detected"
    assert "missing_required_style_tokens" in result["failure_reasons"]


def test_missing_required_class_reports_detected():
    result = _run_base(
        _clear_hits(),
        required_style_classes=["title", "body", "footnote"],
    )

    assert result["proof_status"] == "failed_closed"
    assert result["style_signal"] == "detected"
    assert "missing_required_style_classes" in result["failure_reasons"]


def test_missing_typography_marker_reports_detected():
    result = _run_base(
        _clear_hits(),
        required_typography_markers=["cover-title", "summary-body", "missing-marker"],
    )

    assert result["proof_status"] == "failed_closed"
    assert result["style_signal"] == "detected"
    assert "missing_typography_markers" in result["failure_reasons"]


def test_malformed_input_fails_closed_to_unavailable():
    malformed = [{"section_name": "cover", "token": "font-family:IBM Plex Sans", "font_size": "big"}]
    result = _run_base(malformed)

    assert result["proof_status"] == "failed_closed"
    assert result["style_signal"] == "unavailable"
    assert "invalid_style_hit_shape" in result["failure_reasons"]


def test_unavailable_channel_fails_closed_to_unavailable():
    result = _run_base(_clear_hits(), style_channel_available=False)

    assert result["proof_status"] == "failed_closed"
    assert result["style_signal"] == "unavailable"
    assert "style_channel_unavailable" in result["failure_reasons"]


def test_no_pdf_generation_and_no_file_writes():
    result = _run_base(_clear_hits())

    assert result["pdf_generation_performed"] is False
    assert result["file_write_performed"] is False


def test_no_renderer_dashboard_delivery_or_certification_changes():
    result = _run_base(_clear_hits())

    assert result["renderer_behavior_changed"] is False
    assert result["dashboard_behavior_changed"] is False
    assert result["delivery_workflow_changed"] is False
    assert result["certification_automation_changed"] is False
