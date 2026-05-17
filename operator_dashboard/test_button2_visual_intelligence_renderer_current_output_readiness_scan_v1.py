# Button 2 Visual Intelligence Renderer Current Output Readiness Scan (v1)
# Purpose: Scan current Button 2 report output and attempt to adapt to the locked QA contract.
# No renderer/report-generation/dashboard changes. No file writes. No PDF output changes.

import pytest
from operator_dashboard.button2_dossier_handoff_report_context_preview import build_button2_dossier_handoff_report_context_preview
from operator_dashboard.button2_visual_intelligence_renderer_contract_adapter_v1 import adapt_renderer_output_to_contract

# Simulate a minimal valid ingest context for current output
def _make_minimal_ingest_context():
    return {
        "button2_ingest_preview_context": {
            "destination_marker": "button2_report_generation_preview",
            "context_kind": "button1_dossier_handoff",
            "ingest_mode": "preview_only",
            "dossier_summary_preview": "Button1 Read-Only Dossier Handoff Preview\nFighter: Jon Jones",
        }
    }

def test_scan_current_output_adaptability():
    # Build current output
    result = build_button2_dossier_handoff_report_context_preview(_make_minimal_ingest_context())
    assert result["ok"] is True
    report_context = result["report_context_preview"]
    # Try to adapt to contract (should fail closed, missing markers)
    with pytest.raises(ValueError) as exc:
        adapt_renderer_output_to_contract(report_context)
    assert "Missing required contract key" in str(exc.value)

def test_scan_reports_missing_page_marker():
    # Current output has no 'page_marker' field
    result = build_button2_dossier_handoff_report_context_preview(_make_minimal_ingest_context())
    report_context = result["report_context_preview"]
    assert "page_marker" not in report_context

def test_scan_reports_missing_hierarchy_marker():
    result = build_button2_dossier_handoff_report_context_preview(_make_minimal_ingest_context())
    report_context = result["report_context_preview"]
    assert "hierarchy" not in report_context

def test_scan_reports_missing_visual_blocks():
    result = build_button2_dossier_handoff_report_context_preview(_make_minimal_ingest_context())
    report_context = result["report_context_preview"]
    assert "visual_blocks" not in report_context

def test_scan_reports_missing_source_trace_block():
    result = build_button2_dossier_handoff_report_context_preview(_make_minimal_ingest_context())
    report_context = result["report_context_preview"]
    assert "source_trace_block" not in report_context

def test_scan_reports_no_overlap_signal_unavailable():
    result = build_button2_dossier_handoff_report_context_preview(_make_minimal_ingest_context())
    report_context = result["report_context_preview"]
    assert "no_overlap" not in report_context
    assert "no_off_page_text" not in report_context

def test_scan_does_not_generate_pdf_or_write_files():
    # No side effects, no PDF generation, no file writes
    result = build_button2_dossier_handoff_report_context_preview(_make_minimal_ingest_context())
    assert result["pdf_generation_performed"] is False
    assert result["file_write_performed"] is False
