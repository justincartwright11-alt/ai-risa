# Test for Button 2 Visual Intelligence Renderer Sample Contract (v1)
# Purpose: Validate the sample contract/fixture for future renderer tests.

from operator_dashboard.button2_visual_intelligence_renderer_sample_contract_v1 import BUTTON2_RENDERER_SAMPLE_CONTRACT

def test_sample_contract_page_marker():
    assert BUTTON2_RENDERER_SAMPLE_CONTRACT["page_marker"] == "button2_report_page"

def test_sample_contract_hierarchy():
    hierarchy = BUTTON2_RENDERER_SAMPLE_CONTRACT["hierarchy"]
    assert hierarchy[0]["block"] == "executive_summary"
    assert hierarchy[-1]["block"] == "risk_block"
    assert all(isinstance(b["order"], int) for b in hierarchy)

def test_sample_contract_visual_blocks():
    blocks = BUTTON2_RENDERER_SAMPLE_CONTRACT["visual_blocks"]
    assert len(blocks) == 4
    ids = [b["id"] for b in blocks]
    assert "block-1" in ids and "block-4" in ids
    assert all(isinstance(b["bounds"], list) and len(b["bounds"]) == 4 for b in blocks)

def test_sample_contract_source_trace_block():
    sources = BUTTON2_RENDERER_SAMPLE_CONTRACT["source_trace_block"]["sources"]
    assert any(s["type"] == "official" for s in sources)
    assert any(s["type"] == "analyst" for s in sources)

def test_sample_contract_no_overlap_and_density():
    assert BUTTON2_RENDERER_SAMPLE_CONTRACT["no_overlap"] is True
    assert BUTTON2_RENDERER_SAMPLE_CONTRACT["no_off_page_text"] is True
    assert BUTTON2_RENDERER_SAMPLE_CONTRACT["visual_block_density_ok"] is True
