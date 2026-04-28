# report_template_config.py
"""
Defines the master report template structure, section order, and visual slots.
"""


# Section definitions: id, title, order (Premium Single-Fight Report)
REPORT_SECTIONS = [
    {"id": "front_cover", "title": "Front Cover"},
    {"id": "executive_summary", "title": "Executive Summary"},
    {"id": "matchup_snapshot", "title": "Matchup Snapshot"},
    {"id": "decision_structure", "title": "Decision Structure"},
    {"id": "tactical_edges", "title": "Tactical Edges"},
    {"id": "energy_use", "title": "Energy Use"},
    {"id": "fatigue_failure_points", "title": "Fatigue Failure Points"},
    {"id": "mental_condition", "title": "Mental Condition"},
    {"id": "collapse_triggers", "title": "Collapse Triggers"},
    {"id": "deception_unpredictability", "title": "Deception and Unpredictability"},
    {"id": "fight_control", "title": "How the Fight Gets Controlled"},
    {"id": "fight_turns", "title": "How and Why the Fight Turns"},
    {"id": "scenario_tree", "title": "Scenario Tree"},
    {"id": "round_by_round_outlook", "title": "Round-by-Round Outlook"},
    {"id": "risk_factors", "title": "Risk Factors"},
    {"id": "what_could_flip", "title": "What Could Flip the Fight"},
    {"id": "corner_notes", "title": "Corner Notes"},
    {"id": "final_projection", "title": "Final Projection"},
    {"id": "confidence_explanation", "title": "Confidence Explanation"},
    {"id": "disclaimer", "title": "Disclaimer"},
]

# Visual slot definitions and fallbacks
VISUAL_SLOTS = {
    "radar": {
        "title": "Fighter Radar",
        "required": False,
        "fallback": "Radar data unavailable for this fixture.",
    },
    "heat_map": {
        "title": "Round Heat Map",
        "required": False,
        "fallback": "Heat map data unavailable for this fixture.",
    },
    "control_shift": {
        "title": "Control Shift Graph",
        "required": False,
        "fallback": "Control-shift data unavailable for this fixture.",
    },
    "method_chart": {
        "title": "Method of Victory Chart",
        "required": False,
        "fallback": "Method distribution data unavailable for this fixture.",
    },
}
