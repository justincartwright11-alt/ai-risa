# Button 2 Visual Intelligence Renderer Contract Compatibility Smoke Proof (v1)
# Purpose: Evidence-only smoke test that the compatibility layer, sample contract, adapter, and current report-context output work as a stable QA bridge.

import pytest
from operator_dashboard.button2_dossier_handoff_report_context_preview import build_button2_dossier_handoff_report_context_preview
from operator_dashboard.button2_visual_intelligence_renderer_contract_compatibility_layer_v1 import map_report_context_to_visual_intelligence_contract
from operator_dashboard.button2_visual_intelligence_renderer_contract_adapter_v1 import adapt_renderer_output_to_contract

def _make_minimal_ingest_context():
    return {
        "button2_ingest_preview_context": {
            "destination_marker": "button2_report_generation_preview",
            "context_kind": "button1_dossier_handoff",
            "ingest_mode": "preview_only",
            "dossier_summary_preview": "Button1 Read-Only Dossier Handoff Preview\nFighter: Jon Jones",
        }
    }

def test_smoke_current_report_context_maps_to_contract():
    result = build_button2_dossier_handoff_report_context_preview(_make_minimal_ingest_context())
    report_context = result["report_context_preview"]
    contract = map_report_context_to_visual_intelligence_contract(report_context)
    assert contract["page_marker"] == "button2_report_page"
    assert contract["hierarchy"][0]["block"] == "executive_summary"
    assert contract["visual_blocks"][0]["type"] == "summary"
    assert contract["source_trace_block"]["sources"][0]["type"] == "button1_dossier_handoff"
    assert contract["no_overlap"] is False
    assert contract["no_off_page_text"] is False

def test_smoke_compatibility_output_passes_adapter():
    result = build_button2_dossier_handoff_report_context_preview(_make_minimal_ingest_context())
    report_context = result["report_context_preview"]
    contract = map_report_context_to_visual_intelligence_contract(report_context)
    # Adapter should reject because no_overlap/no_off_page_text are not true
    try:
        adapt_renderer_output_to_contract(contract)
    except ValueError as e:
        err = str(e).lower()
        assert "overlap" in err
        assert "off-page" in err or "off_page" in err
    else:
        assert False, "Adapter did not fail closed as expected"

def test_smoke_malformed_report_context_fails_closed():
    with pytest.raises(ValueError, match="Missing required contract key: hierarchy"):
        map_report_context_to_visual_intelligence_contract({})

def test_smoke_missing_source_summary_reported():
    # Remove source_context_kind to simulate missing source summary
    result = build_button2_dossier_handoff_report_context_preview(_make_minimal_ingest_context())
    report_context = result["report_context_preview"].copy()
    report_context.pop("source_context_kind", None)
    contract = map_report_context_to_visual_intelligence_contract(report_context)
    assert contract["source_trace_block"]["sources"][0]["type"] == "unknown"

def test_smoke_overlap_off_page_signals_unavailable():
    result = build_button2_dossier_handoff_report_context_preview(_make_minimal_ingest_context())
    report_context = result["report_context_preview"]
    contract = map_report_context_to_visual_intelligence_contract(report_context)
    assert contract["no_overlap"] is False
    assert contract["no_off_page_text"] is False

def test_smoke_no_pdf_generated_or_file_written():
    result = build_button2_dossier_handoff_report_context_preview(_make_minimal_ingest_context())
    assert result["pdf_generation_performed"] is False
    assert result["file_write_performed"] is False
