"""
Button 2 Customer PDF Phase 3 - Visual QA Rollup Proof Preview Tests v1

Focused evidence-only tests for visual QA rollup proof preview helper.
No file writes, no PDF generation, no renderer changes.

Reference: operator_dashboard/button2_customer_pdf_phase3_visual_qa_rollup_proof_preview_v1.py
"""

import sys
import os

pytest_plugins = []
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from button2_customer_pdf_phase3_visual_qa_rollup_proof_preview_v1 import (
    run_visual_qa_rollup_proof,
)


def _clear_hits():
    """Generate valid visual QA evidence for clear signal."""
    return [
        {
            "section_name": "overview",
            "check_id": "margin_001",
            "check_type": "margin",
            "component_name": "page_body",
            "value": 18,
            "status": "pass",
            "marker_id": "qa_margin_001",
        },
        {
            "section_name": "overview",
            "check_id": "padding_001",
            "check_type": "padding",
            "component_name": "content_box",
            "value": 16,
            "status": "pass",
            "marker_id": "qa_padding_001",
        },
        {
            "section_name": "overview",
            "check_id": "typography_001",
            "check_type": "typography",
            "component_name": "heading",
            "value": "consistent_font_sizes",
            "status": "pass",
            "marker_id": "qa_typo_001",
        },
        {
            "section_name": "overview",
            "check_id": "color_001",
            "check_type": "color",
            "component_name": "text",
            "value": "consistent_colors",
            "status": "pass",
            "marker_id": "qa_color_001",
        },
        {
            "section_name": "overview",
            "check_id": "alignment_001",
            "check_type": "alignment",
            "component_name": "content",
            "value": "left_aligned",
            "status": "pass",
            "marker_id": "qa_align_001",
        },
        {
            "section_name": "overview",
            "check_id": "spacing_001",
            "check_type": "spacing",
            "component_name": "sections",
            "value": "consistent_spacing",
            "status": "pass",
            "marker_id": "qa_spacing_001",
        },
        {
            "section_name": "overview",
            "check_id": "hierarchy_001",
            "check_type": "hierarchy",
            "component_name": "header_footer",
            "value": "hierarchical_order",
            "status": "pass",
            "marker_id": "qa_hierarchy_001",
        },
    ]


def test_valid_visual_qa_input_passes():
    """Valid visual QA evidence passes with clear signal."""
    hits = _clear_hits()
    result = run_visual_qa_rollup_proof(
        visual_qa_hits=hits,
        required_margin_ranges={"overview": [15, 20]},
        required_padding_ranges={"content_box": [12, 20]},
        required_typography_consistency_markers=["consistent_font_sizes"],
        required_color_consistency_markers=["consistent_colors"],
        required_alignment_markers=["left_aligned"],
        required_spacing_consistency_markers=["consistent_spacing"],
    )

    assert result["proof_status"] == "passed"
    assert result["rollup_signal"] == "clear"
    assert result["failure_reasons"] == []
    assert result["discovered_visual_qa_hit_count"] == 7


def test_invalid_margin_range_reports_detected():
    """Invalid margin (out of range) reports detected signal."""
    hits = _clear_hits()
    result = run_visual_qa_rollup_proof(
        visual_qa_hits=hits,
        required_margin_ranges={"overview": [20, 30]},
        required_padding_ranges={"content_box": [12, 20]},
        required_typography_consistency_markers=["consistent_font_sizes"],
        required_color_consistency_markers=["consistent_colors"],
        required_alignment_markers=["left_aligned"],
        required_spacing_consistency_markers=["consistent_spacing"],
    )

    assert result["proof_status"] == "failed_closed"
    assert result["rollup_signal"] == "detected"
    assert "out_of_range_margins" in result["failure_reasons"]
    assert len(result["out_of_range_margins"]) > 0


def test_invalid_padding_range_reports_detected():
    """Invalid padding (out of range) reports detected signal."""
    hits = _clear_hits()
    result = run_visual_qa_rollup_proof(
        visual_qa_hits=hits,
        required_margin_ranges={"overview": [15, 20]},
        required_padding_ranges={"content_box": [20, 30]},
        required_typography_consistency_markers=["consistent_font_sizes"],
        required_color_consistency_markers=["consistent_colors"],
        required_alignment_markers=["left_aligned"],
        required_spacing_consistency_markers=["consistent_spacing"],
    )

    assert result["proof_status"] == "failed_closed"
    assert result["rollup_signal"] == "detected"
    assert "out_of_range_padding" in result["failure_reasons"]
    assert len(result["out_of_range_padding"]) > 0


def test_missing_typography_consistency_marker_reports_detected():
    """Missing typography consistency marker reports detected signal."""
    hits = _clear_hits()
    result = run_visual_qa_rollup_proof(
        visual_qa_hits=hits,
        required_margin_ranges={"overview": [15, 20]},
        required_padding_ranges={"content_box": [12, 20]},
        required_typography_consistency_markers=[
            "consistent_font_sizes",
            "missing_typo_marker",
        ],
        required_color_consistency_markers=["consistent_colors"],
        required_alignment_markers=["left_aligned"],
        required_spacing_consistency_markers=["consistent_spacing"],
    )

    assert result["proof_status"] == "failed_closed"
    assert result["rollup_signal"] == "detected"
    assert "missing_typography_consistency_markers" in result["failure_reasons"]
    assert "missing_typo_marker" in result["missing_typography_consistency_markers"]


def test_missing_color_consistency_marker_reports_detected():
    """Missing color consistency marker reports detected signal."""
    hits = _clear_hits()
    result = run_visual_qa_rollup_proof(
        visual_qa_hits=hits,
        required_margin_ranges={"overview": [15, 20]},
        required_padding_ranges={"content_box": [12, 20]},
        required_typography_consistency_markers=["consistent_font_sizes"],
        required_color_consistency_markers=["consistent_colors", "missing_color_marker"],
        required_alignment_markers=["left_aligned"],
        required_spacing_consistency_markers=["consistent_spacing"],
    )

    assert result["proof_status"] == "failed_closed"
    assert result["rollup_signal"] == "detected"
    assert "missing_color_consistency_markers" in result["failure_reasons"]
    assert "missing_color_marker" in result["missing_color_consistency_markers"]


def test_missing_alignment_marker_reports_detected():
    """Missing alignment marker reports detected signal."""
    hits = _clear_hits()
    result = run_visual_qa_rollup_proof(
        visual_qa_hits=hits,
        required_margin_ranges={"overview": [15, 20]},
        required_padding_ranges={"content_box": [12, 20]},
        required_typography_consistency_markers=["consistent_font_sizes"],
        required_color_consistency_markers=["consistent_colors"],
        required_alignment_markers=["left_aligned", "missing_align_marker"],
        required_spacing_consistency_markers=["consistent_spacing"],
    )

    assert result["proof_status"] == "failed_closed"
    assert result["rollup_signal"] == "detected"
    assert "missing_alignment_markers" in result["failure_reasons"]
    assert "missing_align_marker" in result["missing_alignment_markers"]


def test_missing_spacing_consistency_marker_reports_detected():
    """Missing spacing consistency marker reports detected signal."""
    hits = _clear_hits()
    result = run_visual_qa_rollup_proof(
        visual_qa_hits=hits,
        required_margin_ranges={"overview": [15, 20]},
        required_padding_ranges={"content_box": [12, 20]},
        required_typography_consistency_markers=["consistent_font_sizes"],
        required_color_consistency_markers=["consistent_colors"],
        required_alignment_markers=["left_aligned"],
        required_spacing_consistency_markers=[
            "consistent_spacing",
            "missing_spacing_marker",
        ],
    )

    assert result["proof_status"] == "failed_closed"
    assert result["rollup_signal"] == "detected"
    assert "missing_spacing_consistency_markers" in result["failure_reasons"]
    assert "missing_spacing_marker" in result["missing_spacing_consistency_markers"]


def test_visual_hierarchy_failure_reports_detected():
    """Visual hierarchy failure (status=fail) reports detected signal."""
    hits = [
        {
            "section_name": "overview",
            "check_id": "hierarchy_001",
            "check_type": "hierarchy",
            "component_name": "header_footer",
            "value": "hierarchical_order",
            "status": "fail",
            "marker_id": "qa_hierarchy_001",
        }
    ]
    result = run_visual_qa_rollup_proof(
        visual_qa_hits=hits,
        required_margin_ranges={},
        required_padding_ranges={},
        required_typography_consistency_markers=[],
        required_color_consistency_markers=[],
        required_alignment_markers=[],
        required_spacing_consistency_markers=[],
    )

    assert result["proof_status"] == "failed_closed"
    assert result["rollup_signal"] == "detected"
    assert "visual_hierarchy_validation_failed" in result["failure_reasons"]
    assert len(result["visual_hierarchy_failures"]) > 0


def test_malformed_input_hits_not_list_fails_closed_to_unavailable():
    """Malformed hits input (not list) fails closed to unavailable signal."""
    result = run_visual_qa_rollup_proof(
        visual_qa_hits="not a list",
        required_margin_ranges={},
        required_padding_ranges={},
        required_typography_consistency_markers=[],
        required_color_consistency_markers=[],
        required_alignment_markers=[],
        required_spacing_consistency_markers=[],
    )

    assert result["proof_status"] == "failed_closed"
    assert result["rollup_signal"] == "unavailable"
    assert "invalid_visual_qa_hit_shape" in result["failure_reasons"]


def test_malformed_input_hit_missing_required_field_fails_closed_to_unavailable():
    """Malformed hit (missing required field) fails closed to unavailable signal."""
    hits = [
        {
            "section_name": "overview",
            "check_id": "margin_001",
            # missing check_type, component_name, value, status
        }
    ]
    result = run_visual_qa_rollup_proof(
        visual_qa_hits=hits,
        required_margin_ranges={},
        required_padding_ranges={},
        required_typography_consistency_markers=[],
        required_color_consistency_markers=[],
        required_alignment_markers=[],
        required_spacing_consistency_markers=[],
    )

    assert result["proof_status"] == "failed_closed"
    assert result["rollup_signal"] == "unavailable"
    assert "invalid_visual_qa_hit_shape" in result["failure_reasons"]


def test_unavailable_channel_fails_closed_to_unavailable():
    """Unavailable channel (visual_qa_channel_available=False) fails closed to unavailable signal."""
    hits = _clear_hits()
    result = run_visual_qa_rollup_proof(
        visual_qa_hits=hits,
        required_margin_ranges={"overview": [15, 20]},
        required_padding_ranges={"content_box": [12, 20]},
        required_typography_consistency_markers=["consistent_font_sizes"],
        required_color_consistency_markers=["consistent_colors"],
        required_alignment_markers=["left_aligned"],
        required_spacing_consistency_markers=["consistent_spacing"],
        visual_qa_channel_available=False,
    )

    assert result["proof_status"] == "failed_closed"
    assert result["rollup_signal"] == "unavailable"
    assert "visual_qa_channel_unavailable" in result["failure_reasons"]


def test_no_pdf_generation_and_no_file_writes():
    """Proof helper reports no PDF generation and no file writes."""
    hits = _clear_hits()
    result = run_visual_qa_rollup_proof(
        visual_qa_hits=hits,
        required_margin_ranges={"overview": [15, 20]},
        required_padding_ranges={"content_box": [12, 20]},
        required_typography_consistency_markers=["consistent_font_sizes"],
        required_color_consistency_markers=["consistent_colors"],
        required_alignment_markers=["left_aligned"],
        required_spacing_consistency_markers=["consistent_spacing"],
    )

    assert result["pdf_generation_performed"] is False
    assert result["file_write_performed"] is False


def test_no_renderer_dashboard_delivery_or_certification_changes():
    """Proof helper reports no renderer/dashboard/delivery/certification behavior changes."""
    hits = _clear_hits()
    result = run_visual_qa_rollup_proof(
        visual_qa_hits=hits,
        required_margin_ranges={"overview": [15, 20]},
        required_padding_ranges={"content_box": [12, 20]},
        required_typography_consistency_markers=["consistent_font_sizes"],
        required_color_consistency_markers=["consistent_colors"],
        required_alignment_markers=["left_aligned"],
        required_spacing_consistency_markers=["consistent_spacing"],
    )

    assert result["renderer_behavior_changed"] is False
    assert result["dashboard_behavior_changed"] is False
    assert result["delivery_workflow_changed"] is False
    assert result["certification_automation_changed"] is False
