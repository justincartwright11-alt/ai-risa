"""Tests for Phase 3 typography/style proof preview module (v1)."""

import operator_dashboard.button2_customer_pdf_phase3_typography_style_proof_preview_v1 as preview


def _style_hits_clear():
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


def test_accepts_input_and_reports_clear_when_valid():
    result = preview.run_typography_style_proof(
        _style_hits_clear(),
        required_style_tokens=["font-family:IBM Plex Sans"],
        forbidden_style_tokens=["font-family:Comic Sans"],
        section_style_rules={
            "cover": ["font-family:IBM Plex Sans"],
            "summary": ["font-family:IBM Plex Sans"],
        },
        required_style_classes=["title", "body"],
        required_typography_markers=["cover-title", "summary-body"],
        allowed_font_weights=["400", "700"],
        font_size_range=[10, 28],
        line_height_range=[1.2, 1.8],
    )

    assert result["schema_version"] == "button2.phase3.typography_style_proof.v1"
    assert result["proof_channel"] == "typography_style"
    assert result["proof_status"] == "passed"
    assert result["style_signal"] == "clear"
    assert result["failure_reasons"] == []


def test_detects_missing_typography_markers():
    hits = _style_hits_clear()
    result = preview.run_typography_style_proof(
        hits,
        required_style_tokens=["font-family:IBM Plex Sans"],
        forbidden_style_tokens=[],
        section_style_rules={"cover": ["font-family:IBM Plex Sans"]},
        required_typography_markers=["cover-title", "missing-marker"],
    )

    assert result["proof_status"] == "failed_closed"
    assert result["style_signal"] == "detected"
    assert "missing_typography_markers" in result["failure_reasons"]
    assert "missing-marker" in result["missing_typography_markers"]


def test_detects_missing_required_style_tokens():
    result = preview.run_typography_style_proof(
        _style_hits_clear(),
        required_style_tokens=["font-family:IBM Plex Sans", "font-size:14"],
        forbidden_style_tokens=[],
        section_style_rules={"cover": ["font-family:IBM Plex Sans"]},
    )

    assert result["proof_status"] == "failed_closed"
    assert result["style_signal"] == "detected"
    assert "missing_required_style_tokens" in result["failure_reasons"]


def test_detects_invalid_style_values():
    hits = [
        {
            "section_name": "summary",
            "token": "font-family:IBM Plex Sans",
            "font_size": 8,
            "font_weight": 950,
            "line_height": 2.2,
        }
    ]
    result = preview.run_typography_style_proof(
        hits,
        required_style_tokens=["font-family:IBM Plex Sans"],
        forbidden_style_tokens=[],
        section_style_rules={"summary": ["font-family:IBM Plex Sans"]},
        allowed_font_weights=["400", "700"],
        font_size_range=[10, 28],
        line_height_range=[1.2, 1.8],
    )

    assert result["proof_status"] == "failed_closed"
    assert result["style_signal"] == "detected"
    assert "invalid_style_values" in result["failure_reasons"]
    assert result["invalid_style_values"]


def test_detects_forbidden_style_tokens():
    hits = _style_hits_clear() + [{"section_name": "cover", "token": "font-family:Comic Sans"}]
    result = preview.run_typography_style_proof(
        hits,
        required_style_tokens=["font-family:IBM Plex Sans"],
        forbidden_style_tokens=["font-family:Comic Sans"],
        section_style_rules={"cover": ["font-family:IBM Plex Sans"]},
    )

    assert result["proof_status"] == "failed_closed"
    assert result["style_signal"] == "detected"
    assert "forbidden_style_tokens_detected" in result["failure_reasons"]


def test_unavailable_when_channel_unavailable():
    result = preview.run_typography_style_proof(
        _style_hits_clear(),
        required_style_tokens=[],
        forbidden_style_tokens=[],
        section_style_rules={},
        style_channel_available=False,
    )

    assert result["proof_status"] == "failed_closed"
    assert result["style_signal"] == "unavailable"
    assert "style_channel_unavailable" in result["failure_reasons"]


def test_malformed_input_fails_closed():
    malformed = [{"section_name": "cover", "token": "font-family:IBM Plex Sans", "font_size": "big"}]
    result = preview.run_typography_style_proof(
        malformed,
        required_style_tokens=[],
        forbidden_style_tokens=[],
        section_style_rules={},
    )

    assert result["proof_status"] == "failed_closed"
    assert result["style_signal"] == "unavailable"
    assert "invalid_style_hit_shape" in result["failure_reasons"]


def test_no_pdf_generation_and_file_writes():
    result = preview.run_typography_style_proof(
        _style_hits_clear(),
        required_style_tokens=[],
        forbidden_style_tokens=[],
        section_style_rules={},
    )

    assert result["pdf_generation_performed"] is False
    assert result["file_write_performed"] is False


def test_no_renderer_dashboard_delivery_or_certification_changes():
    result = preview.run_typography_style_proof(
        _style_hits_clear(),
        required_style_tokens=[],
        forbidden_style_tokens=[],
        section_style_rules={},
    )

    assert result["renderer_behavior_changed"] is False
    assert result["dashboard_behavior_changed"] is False
    assert result["delivery_workflow_changed"] is False
    assert result["certification_automation_changed"] is False


def test_detects_ambiguous_style_mapping():
    hits = _style_hits_clear() + [
        {
            "section_name": "cover",
            "token": "font-family:IBM Plex Sans",
            "class_name": "title",
            "font_size": 24,
            "font_weight": 700,
            "line_height": 1.3,
        }
    ]
    result = preview.run_typography_style_proof(
        hits,
        required_style_tokens=["font-family:IBM Plex Sans"],
        forbidden_style_tokens=[],
        section_style_rules={"cover": ["font-family:IBM Plex Sans"]},
    )

    assert result["proof_status"] == "failed_closed"
    assert result["style_signal"] == "detected"
    assert "ambiguous_style_mapping" in result["failure_reasons"]
