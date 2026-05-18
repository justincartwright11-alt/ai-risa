"""
Button 2 Customer PDF Phase 3 - Source Traceability Proof Smoke Tests v1

Evidence-only smoke proof across clear, missing-source-class, missing-citation,
missing-footer, invalid-label, forbidden-source-class, malformed, and unavailable paths.

Reference: operator_dashboard/button2_customer_pdf_phase3_source_traceability_proof_preview_v1.py
"""

import sys
import os

pytest_plugins = []
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from button2_customer_pdf_phase3_source_traceability_proof_preview_v1 import (
    run_source_traceability_proof,
)


def _clear_hits():
    """Generate valid source traceability evidence for clear signal."""
    return [
        {
            "section_name": "overview",
            "source_index": 0,
            "source_type": "primary",
            "source_class": "official",
            "citation_count": 2,
            "verification_status": "verified",
            "marker_id": "src_001",
            "source_label": "Official Source",
            "source_confidence": "high",
            "source_footer_marker": True,
        },
        {
            "section_name": "fighter_a_analysis",
            "source_index": 1,
            "source_type": "secondary",
            "source_class": "corroborating",
            "citation_count": 1,
            "verification_status": "verified",
            "marker_id": "src_002",
            "source_label": "Secondary Source",
            "source_confidence": "medium",
            "source_footer_marker": True,
        },
    ]


def test_valid_source_traceability_input_passes():
    """Valid source traceability evidence passes with clear signal."""
    hits = _clear_hits()
    result = run_source_traceability_proof(
        source_traceability_hits=hits,
        required_source_classes=["official", "corroborating"],
        required_citations_per_section={"overview": 2, "fighter_a_analysis": 1},
        forbidden_source_classes=[],
        required_verification_statuses=["verified"],
    )

    assert result["proof_status"] == "passed"
    assert result["source_signal"] == "clear"
    assert result["failure_reasons"] == []


def test_missing_required_source_class_reports_detected():
    """Missing required source class reports detected signal."""
    hits = _clear_hits()
    result = run_source_traceability_proof(
        source_traceability_hits=hits,
        required_source_classes=["official", "corroborating", "missing_class"],
        required_citations_per_section={"overview": 2, "fighter_a_analysis": 1},
        forbidden_source_classes=[],
        required_verification_statuses=["verified"],
    )

    assert result["proof_status"] == "failed_closed"
    assert result["source_signal"] == "detected"
    assert "missing_required_source_classes" in result["failure_reasons"]


def test_missing_citation_marker_reports_detected():
    """Missing citation marker (insufficient count) reports detected signal."""
    hits = _clear_hits()
    result = run_source_traceability_proof(
        source_traceability_hits=hits,
        required_source_classes=["official", "corroborating"],
        required_citations_per_section={"overview": 5, "fighter_a_analysis": 1},
        forbidden_source_classes=[],
        required_verification_statuses=["verified"],
    )

    assert result["proof_status"] == "failed_closed"
    assert result["source_signal"] == "detected"
    assert "missing_required_citations" in result["failure_reasons"]


def test_missing_source_footer_marker_reports_detected():
    """Missing source footer marker reports detected signal."""
    hits = [
        {
            "section_name": "overview",
            "source_index": 0,
            "source_type": "primary",
            "source_class": "official",
            "citation_count": 2,
            "verification_status": "verified",
            "marker_id": "src_001",
            "source_label": "Official Source",
            "source_confidence": "high",
            "source_footer_marker": False,
        }
    ]
    result = run_source_traceability_proof(
        source_traceability_hits=hits,
        required_source_classes=["official"],
        required_citations_per_section={"overview": 2},
        forbidden_source_classes=[],
        required_verification_statuses=["verified"],
    )

    assert result["proof_status"] == "failed_closed"
    assert result["source_signal"] == "detected"
    assert "missing_source_footer_markers" in result["failure_reasons"]


def test_invalid_source_label_reports_detected():
    """Invalid source label (empty string) reports detected signal."""
    hits = [
        {
            "section_name": "overview",
            "source_index": 0,
            "source_type": "primary",
            "source_class": "official",
            "citation_count": 2,
            "verification_status": "verified",
            "marker_id": "src_001",
            "source_label": "",
            "source_confidence": "high",
            "source_footer_marker": True,
        }
    ]
    result = run_source_traceability_proof(
        source_traceability_hits=hits,
        required_source_classes=["official"],
        required_citations_per_section={"overview": 2},
        forbidden_source_classes=[],
        required_verification_statuses=["verified"],
    )

    assert result["proof_status"] == "failed_closed"
    assert result["source_signal"] == "detected"
    assert "invalid_source_label_shape" in result["failure_reasons"]


def test_invalid_source_confidence_label_reports_detected():
    """Invalid source confidence (empty string) reports detected signal."""
    hits = [
        {
            "section_name": "overview",
            "source_index": 0,
            "source_type": "primary",
            "source_class": "official",
            "citation_count": 2,
            "verification_status": "verified",
            "marker_id": "src_001",
            "source_label": "Official Source",
            "source_confidence": "",
            "source_footer_marker": True,
        }
    ]
    result = run_source_traceability_proof(
        source_traceability_hits=hits,
        required_source_classes=["official"],
        required_citations_per_section={"overview": 2},
        forbidden_source_classes=[],
        required_verification_statuses=["verified"],
    )

    assert result["proof_status"] == "failed_closed"
    assert result["source_signal"] == "detected"
    assert "invalid_source_confidence_shape" in result["failure_reasons"]


def test_forbidden_source_class_reports_detected():
    """Forbidden source class reports detected signal."""
    hits = _clear_hits()
    result = run_source_traceability_proof(
        source_traceability_hits=hits,
        required_source_classes=["official", "corroborating"],
        required_citations_per_section={"overview": 2, "fighter_a_analysis": 1},
        forbidden_source_classes=["corroborating"],
        required_verification_statuses=["verified"],
    )

    assert result["proof_status"] == "failed_closed"
    assert result["source_signal"] == "detected"
    assert "forbidden_source_classes_detected" in result["failure_reasons"]


def test_malformed_input_fails_closed_to_unavailable():
    """Malformed input (hits not list) fails closed to unavailable signal."""
    result = run_source_traceability_proof(
        source_traceability_hits="not a list",
        required_source_classes=["official"],
        required_citations_per_section={"overview": 2},
        forbidden_source_classes=[],
        required_verification_statuses=["verified"],
    )

    assert result["proof_status"] == "failed_closed"
    assert result["source_signal"] == "unavailable"
    assert "invalid_source_hit_shape" in result["failure_reasons"]


def test_unavailable_channel_fails_closed_to_unavailable():
    """Unavailable channel (source_channel_available=False) fails closed to unavailable signal."""
    hits = _clear_hits()
    result = run_source_traceability_proof(
        source_traceability_hits=hits,
        required_source_classes=["official", "corroborating"],
        required_citations_per_section={"overview": 2, "fighter_a_analysis": 1},
        forbidden_source_classes=[],
        required_verification_statuses=["verified"],
        source_channel_available=False,
    )

    assert result["proof_status"] == "failed_closed"
    assert result["source_signal"] == "unavailable"
    assert "source_channel_unavailable" in result["failure_reasons"]


def test_no_pdf_generation_and_no_file_writes():
    """Proof helper reports no PDF generation and no file writes."""
    hits = _clear_hits()
    result = run_source_traceability_proof(
        source_traceability_hits=hits,
        required_source_classes=["official", "corroborating"],
        required_citations_per_section={"overview": 2, "fighter_a_analysis": 1},
        forbidden_source_classes=[],
        required_verification_statuses=["verified"],
    )

    assert result["pdf_generation_performed"] is False
    assert result["file_write_performed"] is False


def test_no_renderer_dashboard_delivery_or_certification_changes():
    """Proof helper reports no renderer/dashboard/delivery/certification behavior changes."""
    hits = _clear_hits()
    result = run_source_traceability_proof(
        source_traceability_hits=hits,
        required_source_classes=["official", "corroborating"],
        required_citations_per_section={"overview": 2, "fighter_a_analysis": 1},
        forbidden_source_classes=[],
        required_verification_statuses=["verified"],
    )

    assert result["renderer_behavior_changed"] is False
    assert result["dashboard_behavior_changed"] is False
    assert result["delivery_workflow_changed"] is False
    assert result["certification_automation_changed"] is False
