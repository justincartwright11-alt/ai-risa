# Button 2 Visual Intelligence Renderer Sample Contract (v1)
# Purpose: Defines a minimal, testable contract/fixture for what a visually valid Button 2 report page must expose.
# This is a test-only artifact. No renderer/layout/PDF/dashboard changes.

BUTTON2_RENDERER_SAMPLE_CONTRACT = {
    "page_marker": "button2_report_page",
    "hierarchy": [
        {"block": "executive_summary", "order": 0},
        {"block": "evidence_panel", "order": 1},
        {"block": "scenario_block", "order": 2},
        {"block": "risk_block", "order": 3},
    ],
    "visual_blocks": [
        {"id": "block-1", "type": "summary", "bounds": [0, 0, 400, 100]},
        {"id": "block-2", "type": "evidence", "bounds": [0, 110, 400, 200]},
        {"id": "block-3", "type": "scenario", "bounds": [0, 220, 400, 120]},
        {"id": "block-4", "type": "risk", "bounds": [0, 350, 400, 100]},
    ],
    "source_trace_block": {
        "sources": [
            {"id": "SRC-001", "type": "official", "date": "2026-05-17"},
            {"id": "SRC-002", "type": "analyst", "date": "2026-05-16"}
        ]
    },
    "no_overlap": True,
    "no_off_page_text": True,
    "visual_block_density_ok": True,
}
