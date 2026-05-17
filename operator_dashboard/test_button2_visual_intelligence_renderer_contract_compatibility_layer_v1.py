# Test for Button 2 Visual Intelligence Renderer Contract Compatibility Layer (v1)
# Purpose: Validate mapping of current report-context preview into QA contract shape.

import pytest
from operator_dashboard.button2_dossier_handoff_report_context_preview import build_button2_dossier_handoff_report_context_preview
from operator_dashboard.button2_visual_intelligence_renderer_contract_compatibility_layer_v1 import map_report_context_to_visual_intelligence_contract

def _make_minimal_ingest_context():
    return {
        "button2_ingest_preview_context": {
            "destination_marker": "button2_report_generation_preview",
            "context_kind": "button1_dossier_handoff",
            "ingest_mode": "preview_only",
            "dossier_summary_preview": "Button1 Read-Only Dossier Handoff Preview\nFighter: Jon Jones",
        }
    }

def test_compatibility_layer_maps_page_marker():
    result = build_button2_dossier_handoff_report_context_preview(_make_minimal_ingest_context())
    report_context = result["report_context_preview"]
    contract = map_report_context_to_visual_intelligence_contract(report_context)
    assert contract["page_marker"] == "button2_report_page"

def test_compatibility_layer_maps_hierarchy():
    result = build_button2_dossier_handoff_report_context_preview(_make_minimal_ingest_context())
    report_context = result["report_context_preview"]
    contract = map_report_context_to_visual_intelligence_contract(report_context)
    assert contract["hierarchy"][0]["block"] == "executive_summary"

def test_compatibility_layer_maps_visual_blocks():
    result = build_button2_dossier_handoff_report_context_preview(_make_minimal_ingest_context())
    report_context = result["report_context_preview"]
    contract = map_report_context_to_visual_intelligence_contract(report_context)
    assert contract["visual_blocks"][0]["type"] == "summary"

def test_compatibility_layer_maps_source_trace_block():
    result = build_button2_dossier_handoff_report_context_preview(_make_minimal_ingest_context())
    report_context = result["report_context_preview"]
    contract = map_report_context_to_visual_intelligence_contract(report_context)
    assert contract["source_trace_block"]["sources"][0]["type"] == "button1_dossier_handoff"

def test_compatibility_layer_reports_overlap_off_page_unavailable():
    result = build_button2_dossier_handoff_report_context_preview(_make_minimal_ingest_context())
    report_context = result["report_context_preview"]
    contract = map_report_context_to_visual_intelligence_contract(report_context)
    assert contract["no_overlap"] is False
    assert contract["no_off_page_text"] is False

def test_compatibility_layer_fails_closed_on_malformed_context():
    # Should fail if both 'handoff_summary_preview' and 'report_context_kind' are missing
    with pytest.raises(ValueError, match="Missing required contract key: hierarchy"):
        map_report_context_to_visual_intelligence_contract({})
    # Should fail if only one is present (simulate missing both hierarchy and visual_blocks)
    with pytest.raises(ValueError, match="Missing required contract key: hierarchy"):
        map_report_context_to_visual_intelligence_contract({"foo": "bar"})
    # Should fail if 'handoff_summary_preview' is present but not 'report_context_kind' (visual_blocks present, hierarchy incomplete)
    with pytest.raises(ValueError, match="Missing required contract key: hierarchy"):
        map_report_context_to_visual_intelligence_contract({"handoff_summary_preview": "x"})
    # Should fail if 'report_context_kind' is present but not 'handoff_summary_preview' (hierarchy incomplete)
    with pytest.raises(ValueError, match="Missing required contract key: hierarchy"):
        map_report_context_to_visual_intelligence_contract({"report_context_kind": "dossier_handoff_report_context_preview"})

def test_compatibility_layer_no_pdf_generated_or_file_written():
    result = build_button2_dossier_handoff_report_context_preview(_make_minimal_ingest_context())
    assert result["pdf_generation_performed"] is False
    assert result["file_write_performed"] is False
