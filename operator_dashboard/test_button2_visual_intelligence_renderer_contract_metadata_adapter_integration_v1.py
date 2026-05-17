# Button 2 Visual Intelligence Renderer Contract — Metadata Adapter Integration Proof (v1)
# Slice: button2-visual-intelligence-renderer-contract-metadata-adapter-integration-v1
#
# Purpose: Prove the compatibility adapter reads real metadata marker fields from the report-context
# output (page_block_boundaries, hierarchy_markers, source_traceability, overlap_proof,
# off_page_text_proof, visual_certification_status) instead of inferring or faking them.
# Adapter still fails closed while overlap/off-page proof is unavailable. No certification.
#
# Governance:
#   - No PDFs generated
#   - No files written
#   - No renderer layout changes
#   - No dashboard changes
#   - No report-generation behavior changes

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


def _get_report_context():
    result = build_button2_dossier_handoff_report_context_preview(_make_minimal_ingest_context())
    assert result["ok"] is True
    return result["report_context_preview"]


def test_adapter_reads_page_block_boundaries_from_metadata():
    report_context = _get_report_context()
    # Verify real metadata field is present in report_context
    assert "page_block_boundaries" in report_context
    assert isinstance(report_context["page_block_boundaries"], list)
    assert len(report_context["page_block_boundaries"]) > 0
    # Verify adapter maps it into visual_blocks
    contract = map_report_context_to_visual_intelligence_contract(report_context)
    # visual_blocks should be identical to page_block_boundaries (read directly)
    assert contract["visual_blocks"] == report_context["page_block_boundaries"]
    assert contract["visual_blocks"][0]["type"] == "summary"


def test_adapter_reads_hierarchy_markers_from_metadata():
    report_context = _get_report_context()
    assert "hierarchy_markers" in report_context
    assert isinstance(report_context["hierarchy_markers"], list)
    assert len(report_context["hierarchy_markers"]) > 0
    contract = map_report_context_to_visual_intelligence_contract(report_context)
    # hierarchy should be identical to hierarchy_markers (read directly)
    assert contract["hierarchy"] == report_context["hierarchy_markers"]
    assert contract["hierarchy"][0]["block"] == "executive_summary"
    assert contract["hierarchy"][1]["block"] == "dossier_handoff_report_context_preview"


def test_adapter_reads_source_traceability_from_metadata():
    report_context = _get_report_context()
    assert "source_traceability" in report_context
    assert isinstance(report_context["source_traceability"], list)
    assert len(report_context["source_traceability"]) > 0
    contract = map_report_context_to_visual_intelligence_contract(report_context)
    # source_trace_block.sources should be the real source_traceability list
    assert contract["source_trace_block"]["sources"] == report_context["source_traceability"]
    assert contract["source_trace_block"]["sources"][0]["type"] == "button1_dossier_handoff"
    assert contract["source_trace_block"]["sources"][0]["id"] == "SRC-CTX"


def test_adapter_reads_overlap_proof_status_unavailable():
    report_context = _get_report_context()
    assert report_context["overlap_proof"] == "unavailable"
    contract = map_report_context_to_visual_intelligence_contract(report_context)
    # "unavailable" != "clear" → no_overlap must be False
    assert contract["no_overlap"] is False


def test_adapter_reads_off_page_text_proof_status_unavailable():
    report_context = _get_report_context()
    assert report_context["off_page_text_proof"] == "unavailable"
    contract = map_report_context_to_visual_intelligence_contract(report_context)
    # "unavailable" != "clear" → no_off_page_text must be False
    assert contract["no_off_page_text"] is False


def test_adapter_keeps_visual_certification_status_not_certified():
    report_context = _get_report_context()
    assert report_context["visual_certification_status"] == "not_certified"
    contract = map_report_context_to_visual_intelligence_contract(report_context)
    assert contract["visual_certification_status"] == "not_certified"


def test_adapter_still_rejects_unavailable_overlap_off_page_proof():
    """Adapter (adapt_renderer_output_to_contract) must still fail closed on no_overlap=False."""
    report_context = _get_report_context()
    contract = map_report_context_to_visual_intelligence_contract(report_context)
    # overlap/off-page still unavailable → adapter must raise
    with pytest.raises(ValueError) as exc_info:
        adapt_renderer_output_to_contract(contract)
    err = str(exc_info.value).lower()
    assert "overlap" in err


def test_no_pdf_generated_or_file_written():
    result = build_button2_dossier_handoff_report_context_preview(_make_minimal_ingest_context())
    assert result["pdf_generation_performed"] is False
    assert result["file_write_performed"] is False


def test_no_renderer_layout_or_dashboard_changes():
    """Preview-only flag must be set; generation must not be performed."""
    result = build_button2_dossier_handoff_report_context_preview(_make_minimal_ingest_context())
    assert result["preview_only"] is True
    assert result["button2_generation_performed"] is False
    assert result["export_performed"] is False
    assert result["delivery_performed"] is False
