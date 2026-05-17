# Button 2 Visual Intelligence Renderer Contract Adapter (v1)
# Purpose: Adapter to convert Button 2 renderer output into the locked sample contract shape for QA validation.
# No renderer/layout/PDF/dashboard changes. No file writes. No report-generation behavior change.

from operator_dashboard.button2_visual_intelligence_renderer_sample_contract_v1 import BUTTON2_RENDERER_SAMPLE_CONTRACT

REQUIRED_KEYS = [
    "page_marker",
    "hierarchy",
    "visual_blocks",
    "source_trace_block",
    "no_overlap",
    "no_off_page_text",
    "visual_block_density_ok",
]

def adapt_renderer_output_to_contract(renderer_output):
    """
    Convert renderer output dict to the locked contract shape for QA validation.
    Fails closed if required markers are missing or malformed.
    """
    contract = {}
    for key in REQUIRED_KEYS:
        if key not in renderer_output:
            raise ValueError(f"Missing required contract key: {key}")
        contract[key] = renderer_output[key]
    # Optionally, validate structure of each field (minimal for v1)
    if not isinstance(contract["hierarchy"], list) or not contract["hierarchy"]:
        raise ValueError("Hierarchy marker must be a non-empty list")
    if not isinstance(contract["visual_blocks"], list) or not contract["visual_blocks"]:
        raise ValueError("Visual blocks marker must be a non-empty list")
    if not isinstance(contract["source_trace_block"], dict):
        raise ValueError("Source trace block must be a dict")
    # Pass through QA signals
    if not contract["no_overlap"] or not contract["no_off_page_text"]:
        raise ValueError("Visual QA signals failed: overlap or off-page text detected")
    return contract
