# Test for Button 2 Visual Intelligence Renderer Contract Adapter (v1)
# Purpose: Validate adapter mapping and fail-closed logic for QA contract shape.

import pytest
from operator_dashboard.button2_visual_intelligence_renderer_sample_contract_v1 import BUTTON2_RENDERER_SAMPLE_CONTRACT
from operator_dashboard.button2_visual_intelligence_renderer_contract_adapter_v1 import adapt_renderer_output_to_contract

def test_adapter_accepts_valid_sample_contract():
    contract = adapt_renderer_output_to_contract(BUTTON2_RENDERER_SAMPLE_CONTRACT)
    assert contract["page_marker"] == "button2_report_page"
    assert contract["no_overlap"] is True
    assert contract["no_off_page_text"] is True
    assert contract["visual_block_density_ok"] is True

def test_adapter_maps_hierarchy_and_blocks():
    contract = adapt_renderer_output_to_contract(BUTTON2_RENDERER_SAMPLE_CONTRACT)
    assert contract["hierarchy"][0]["block"] == "executive_summary"
    assert contract["visual_blocks"][0]["type"] == "summary"

def test_adapter_maps_source_trace_block():
    contract = adapt_renderer_output_to_contract(BUTTON2_RENDERER_SAMPLE_CONTRACT)
    sources = contract["source_trace_block"]["sources"]
    assert any(s["type"] == "official" for s in sources)
    assert any(s["type"] == "analyst" for s in sources)

def test_adapter_fails_closed_on_missing_marker():
    bad = dict(BUTTON2_RENDERER_SAMPLE_CONTRACT)
    bad.pop("page_marker")
    with pytest.raises(ValueError, match="Missing required contract key: page_marker"):
        adapt_renderer_output_to_contract(bad)

def test_adapter_fails_closed_on_bad_qa_signal():
    bad = dict(BUTTON2_RENDERER_SAMPLE_CONTRACT)
    bad["no_overlap"] = False
    with pytest.raises(ValueError, match="Visual QA signals failed: overlap or off-page text detected"):
        adapt_renderer_output_to_contract(bad)

def test_adapter_does_not_generate_pdf_or_write_files():
    # Adapter is pure function, no side effects
    contract = adapt_renderer_output_to_contract(BUTTON2_RENDERER_SAMPLE_CONTRACT)
    assert contract["page_marker"] == "button2_report_page"
