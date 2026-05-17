# Test for Button 2 Visual Intelligence Renderer Contract Metadata Markers Preview (v1)
# Purpose: Validate that preview-level visual QA metadata markers are present in report-context output, but status remains unavailable/not_certified.

from operator_dashboard.button2_dossier_handoff_report_context_preview import build_button2_dossier_handoff_report_context_preview

def _make_minimal_ingest_context():
    return {
        "button2_ingest_preview_context": {
            "destination_marker": "button2_report_generation_preview",
            "context_kind": "button1_dossier_handoff",
            "ingest_mode": "preview_only",
            "dossier_summary_preview": "Button1 Read-Only Dossier Handoff Preview\nFighter: Jon Jones",
        }
    }

def test_metadata_markers_present_and_unavailable():
    result = build_button2_dossier_handoff_report_context_preview(_make_minimal_ingest_context())
    report_context = result["report_context_preview"]
    # Check all required metadata markers
    assert "page_block_boundaries" in report_context
    assert "hierarchy_markers" in report_context
    assert "source_traceability" in report_context
    assert "overlap_proof" in report_context
    assert "off_page_text_proof" in report_context
    assert "visual_certification_status" in report_context
    # Status must remain unavailable/not_certified
    assert report_context["overlap_proof"] == "unavailable"
    assert report_context["off_page_text_proof"] == "unavailable"
    assert report_context["visual_certification_status"] == "not_certified"

def test_no_pdf_generated_or_file_written():
    result = build_button2_dossier_handoff_report_context_preview(_make_minimal_ingest_context())
    assert result["pdf_generation_performed"] is False
    assert result["file_write_performed"] is False
