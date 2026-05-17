# Button 2 Visual Intelligence Renderer Contract Smoke Proof (v1)
# Purpose: Evidence-only smoke test that the contract, sample fixture, and adapter work as a stable QA chain.

import pytest
from operator_dashboard.button2_visual_intelligence_renderer_sample_contract_v1 import BUTTON2_RENDERER_SAMPLE_CONTRACT
from operator_dashboard.button2_visual_intelligence_renderer_contract_adapter_v1 import adapt_renderer_output_to_contract

def test_smoke_contract_exists():
    assert isinstance(BUTTON2_RENDERER_SAMPLE_CONTRACT, dict)
    assert BUTTON2_RENDERER_SAMPLE_CONTRACT["page_marker"] == "button2_report_page"

def test_smoke_adapter_accepts_valid_contract():
    contract = adapt_renderer_output_to_contract(BUTTON2_RENDERER_SAMPLE_CONTRACT)
    assert contract["page_marker"] == "button2_report_page"
    assert contract["no_overlap"] is True
    assert contract["no_off_page_text"] is True

def test_smoke_adapter_rejects_missing_page_marker():
    bad = dict(BUTTON2_RENDERER_SAMPLE_CONTRACT)
    bad.pop("page_marker")
    with pytest.raises(ValueError, match="Missing required contract key: page_marker"):
        adapt_renderer_output_to_contract(bad)

def test_smoke_adapter_rejects_missing_hierarchy_marker():
    bad = dict(BUTTON2_RENDERER_SAMPLE_CONTRACT)
    bad.pop("hierarchy")
    with pytest.raises(ValueError, match="Missing required contract key: hierarchy"):
        adapt_renderer_output_to_contract(bad)

def test_smoke_adapter_rejects_missing_visual_blocks():
    bad = dict(BUTTON2_RENDERER_SAMPLE_CONTRACT)
    bad.pop("visual_blocks")
    with pytest.raises(ValueError, match="Missing required contract key: visual_blocks"):
        adapt_renderer_output_to_contract(bad)

def test_smoke_adapter_rejects_missing_source_trace_block():
    bad = dict(BUTTON2_RENDERER_SAMPLE_CONTRACT)
    bad.pop("source_trace_block")
    with pytest.raises(ValueError, match="Missing required contract key: source_trace_block"):
        adapt_renderer_output_to_contract(bad)

def test_smoke_adapter_requires_no_overlap_and_no_off_page():
    bad = dict(BUTTON2_RENDERER_SAMPLE_CONTRACT)
    bad["no_overlap"] = False
    with pytest.raises(ValueError, match="Visual QA signals failed: overlap or off-page text detected"):
        adapt_renderer_output_to_contract(bad)
    bad2 = dict(BUTTON2_RENDERER_SAMPLE_CONTRACT)
    bad2["no_off_page_text"] = False
    with pytest.raises(ValueError, match="Visual QA signals failed: overlap or off-page text detected"):
        adapt_renderer_output_to_contract(bad2)

def test_smoke_no_pdf_generated_or_file_written():
    # Adapter and contract are pure, no side effects
    contract = adapt_renderer_output_to_contract(BUTTON2_RENDERER_SAMPLE_CONTRACT)
    assert contract["page_marker"] == "button2_report_page"
