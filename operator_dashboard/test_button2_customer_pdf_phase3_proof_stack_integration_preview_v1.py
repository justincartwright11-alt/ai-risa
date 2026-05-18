"""
Button 2 Customer PDF Phase 3 - Proof Stack Integration Preview Tests v1

Focused tests for proof-stack integration preview helper.
No file writes, no PDF generation, no renderer changes.

Reference: operator_dashboard/button2_customer_pdf_phase3_proof_stack_integration_preview_v1.py
"""

import sys
import os

pytest_plugins = []
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from button2_customer_pdf_phase3_proof_stack_integration_preview_v1 import (
    run_proof_stack_integration,
)


def _clear_channel_result(channel_name):
    """Generate valid proof channel result with clear signal."""
    signal_field = f"{channel_name}_signal"
    return {
        "proof_status": "passed",
        signal_field: "clear",
        "failure_reasons": [],
        "pdf_generation_performed": False,
        "file_write_performed": False,
        "renderer_behavior_changed": False,
        "dashboard_behavior_changed": False,
        "delivery_workflow_changed": False,
        "certification_automation_changed": False,
    }


def _clear_all_channels():
    """Generate all seven clear channel results."""
    return {
        "text_extraction": _clear_channel_result("text_extraction"),
        "geometry": _clear_channel_result("geometry"),
        "page_section": _clear_channel_result("page_section"),
        "typography_style": _clear_channel_result("typography_style"),
        "header_footer_watermark": _clear_channel_result("header_footer_watermark"),
        "source_traceability": _clear_channel_result("source_traceability"),
        "visual_qa_rollup": _clear_channel_result("visual_qa_rollup"),
    }


def test_all_clear_channels_produces_clear_stack_signal():
    """All clear channels produces clear stack signal."""
    channels = _clear_all_channels()
    result = run_proof_stack_integration(channels)

    assert result["proof_status"] == "passed"
    assert result["stack_signal"] == "clear"
    assert result["failure_reasons"] == []
    assert result["channel_signals"]["text_extraction"] == "clear"
    assert result["channel_signals"]["geometry"] == "clear"
    assert result["channel_signals"]["page_section"] == "clear"
    assert result["channel_signals"]["typography_style"] == "clear"
    assert result["channel_signals"]["header_footer_watermark"] == "clear"
    assert result["channel_signals"]["source_traceability"] == "clear"
    assert result["channel_signals"]["visual_qa_rollup"] == "clear"


def test_any_detected_channel_produces_detected_stack_signal():
    """Any detected channel produces detected stack signal."""
    channels = _clear_all_channels()
    channels["geometry"]["geometry_signal"] = "detected"
    channels["geometry"]["failure_reasons"] = ["geometry_issue"]

    result = run_proof_stack_integration(channels)

    assert result["proof_status"] == "failed_closed"
    assert result["stack_signal"] == "detected"
    assert "geometry_issue" in result["failure_reasons"]
    assert result["channel_signals"]["geometry"] == "detected"


def test_any_unavailable_channel_produces_unavailable_stack_signal():
    """Any unavailable channel produces unavailable stack signal."""
    channels = _clear_all_channels()
    channels["page_section"]["page_section_signal"] = "unavailable"
    channels["page_section"]["failure_reasons"] = ["page_section_unavailable"]

    result = run_proof_stack_integration(channels)

    assert result["proof_status"] == "failed_closed"
    assert result["stack_signal"] == "unavailable"
    assert "page_section_unavailable" in result["failure_reasons"]
    assert result["channel_signals"]["page_section"] == "unavailable"


def test_unavailable_takes_priority_over_detected():
    """Unavailable signal takes priority over detected signal."""
    channels = _clear_all_channels()
    channels["geometry"]["geometry_signal"] = "detected"
    channels["geometry"]["failure_reasons"] = ["geometry_issue"]
    channels["typography_style"]["typography_style_signal"] = "unavailable"
    channels["typography_style"]["failure_reasons"] = ["typography_unavailable"]

    result = run_proof_stack_integration(channels)

    assert result["proof_status"] == "failed_closed"
    assert result["stack_signal"] == "unavailable"
    assert "typography_unavailable" in result["failure_reasons"]
    assert "geometry_issue" in result["failure_reasons"]


def test_failure_reasons_aggregated_from_all_channels():
    """Failure reasons aggregated from all channels."""
    channels = _clear_all_channels()
    channels["text_extraction"]["text_extraction_signal"] = "detected"
    channels["text_extraction"]["failure_reasons"] = ["text_extraction_reason_1"]
    channels["source_traceability"]["source_traceability_signal"] = "detected"
    channels["source_traceability"]["failure_reasons"] = ["source_reason_1"]

    result = run_proof_stack_integration(channels)

    assert "text_extraction_reason_1" in result["failure_reasons"]
    assert "source_reason_1" in result["failure_reasons"]
    assert len(result["failure_reasons"]) == 2


def test_channel_signals_mapping_preserved():
    """Channel signals mapping preserved in result."""
    channels = _clear_all_channels()
    channels["geometry"]["geometry_signal"] = "detected"
    channels["page_section"]["page_section_signal"] = "unavailable"

    result = run_proof_stack_integration(channels)

    assert result["channel_signals"]["text_extraction"] == "clear"
    assert result["channel_signals"]["geometry"] == "detected"
    assert result["channel_signals"]["page_section"] == "unavailable"
    assert result["channel_signals"]["typography_style"] == "clear"


def test_channel_failure_reasons_mapping_preserved():
    """Channel failure reasons mapping preserved in result."""
    channels = _clear_all_channels()
    channels["geometry"]["geometry_signal"] = "detected"
    channels["geometry"]["failure_reasons"] = ["geometry_reason_1", "geometry_reason_2"]

    result = run_proof_stack_integration(channels)

    assert result["channel_failure_reasons"]["geometry"] == [
        "geometry_reason_1",
        "geometry_reason_2",
    ]
    assert result["channel_failure_reasons"]["text_extraction"] == []


def test_missing_required_channel_fails_closed_to_unavailable():
    """Missing required channel fails closed to unavailable signal."""
    channels = _clear_all_channels()
    del channels["geometry"]

    result = run_proof_stack_integration(channels)

    assert result["proof_status"] == "failed_closed"
    assert result["stack_signal"] == "unavailable"
    assert "invalid_channel_result_shape" in result["failure_reasons"]


def test_malformed_channel_result_fails_closed_to_unavailable():
    """Malformed channel result (not dict) fails closed to unavailable signal."""
    channels = _clear_all_channels()
    channels["geometry"] = "not a dict"

    result = run_proof_stack_integration(channels)

    assert result["proof_status"] == "failed_closed"
    assert result["stack_signal"] == "unavailable"
    assert "invalid_channel_result_shape" in result["failure_reasons"]


def test_missing_signal_field_fails_closed_to_unavailable():
    """Missing signal field in channel result fails closed to unavailable signal."""
    channels = _clear_all_channels()
    del channels["geometry"]["geometry_signal"]

    result = run_proof_stack_integration(channels)

    assert result["proof_status"] == "failed_closed"
    assert result["stack_signal"] == "unavailable"
    assert "invalid_channel_result_shape" in result["failure_reasons"]


def test_invalid_signal_value_fails_closed_to_unavailable():
    """Invalid signal value fails closed to unavailable signal."""
    channels = _clear_all_channels()
    channels["geometry"]["geometry_signal"] = "invalid_signal"

    result = run_proof_stack_integration(channels)

    assert result["proof_status"] == "failed_closed"
    assert result["stack_signal"] == "unavailable"
    assert "invalid_channel_result_shape" in result["failure_reasons"]


def test_unavailable_channel_fails_closed_to_unavailable():
    """Unavailable stack channel (stack_channel_available=False) fails closed to unavailable signal."""
    channels = _clear_all_channels()
    result = run_proof_stack_integration(channels, stack_channel_available=False)

    assert result["proof_status"] == "failed_closed"
    assert result["stack_signal"] == "unavailable"
    assert "stack_channel_unavailable" in result["failure_reasons"]


def test_no_pdf_generation_and_no_file_writes():
    """Proof helper reports no PDF generation and no file writes."""
    channels = _clear_all_channels()
    result = run_proof_stack_integration(channels)

    assert result["pdf_generation_performed"] is False
    assert result["file_write_performed"] is False


def test_no_renderer_dashboard_delivery_or_certification_changes():
    """Proof helper reports no renderer/dashboard/delivery/certification behavior changes."""
    channels = _clear_all_channels()
    result = run_proof_stack_integration(channels)

    assert result["renderer_behavior_changed"] is False
    assert result["dashboard_behavior_changed"] is False
    assert result["delivery_workflow_changed"] is False
    assert result["certification_automation_changed"] is False
