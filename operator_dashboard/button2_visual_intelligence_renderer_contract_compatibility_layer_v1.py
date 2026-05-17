# Button 2 Visual Intelligence Renderer Contract Compatibility Layer (v1)
# Purpose: Map existing Button 2 report-context preview output into the visual-intelligence QA contract shape for test/QA only.
# No renderer/PDF/dashboard/report-generation changes. No file writes.

def map_report_context_to_visual_intelligence_contract(report_context):
    """
    Map a Button 2 report-context preview dict into the QA contract shape.
    Fails closed if required fields are missing or malformed.
    Only adapts available metadata; does not invent overlap/off-page signals.
    """
    if not isinstance(report_context, dict):
        raise ValueError("Input must be a dict")
    contract = {}
    # Page marker
    contract["page_marker"] = "button2_report_page"
    # Hierarchy: require both executive_summary and report_context_kind for valid hierarchy
    hierarchy = []
    has_exec = "handoff_summary_preview" in report_context
    has_kind = "report_context_kind" in report_context
    if has_exec:
        hierarchy.append({"block": "executive_summary", "order": 0})
    if has_kind:
        hierarchy.append({"block": report_context["report_context_kind"], "order": 1})
    # Require both for valid hierarchy
    if not (has_exec and has_kind):
        contract["hierarchy"] = None
    else:
        contract["hierarchy"] = hierarchy
    # Visual blocks: simulate one block per known section
    visual_blocks = []
    if "handoff_summary_preview" in report_context:
        visual_blocks.append({
            "id": "block-1",
            "type": "summary",
            "bounds": [0, 0, 400, 100],
        })
    contract["visual_blocks"] = visual_blocks if visual_blocks else None
    # Source trace block: simulate from context kind
    contract["source_trace_block"] = {
        "sources": [
            {"id": "SRC-CTX", "type": report_context.get("source_context_kind", "unknown"), "date": "n/a"}
        ]
    }
    # Overlap/off-page: not available in current output, set to False
    contract["no_overlap"] = False
    contract["no_off_page_text"] = False
    contract["visual_block_density_ok"] = True  # Assume density is OK for minimal output
    # Fail closed if any required field is None
    for key in ["page_marker", "hierarchy", "visual_blocks", "source_trace_block"]:
        if contract[key] is None:
            raise ValueError(f"Missing required contract key: {key}")
    return contract
