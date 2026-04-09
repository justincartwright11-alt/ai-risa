# report_template_config.py
"""
Defines the master report template structure, section order, and visual slots.
"""


# Section definitions: id, title, order
REPORT_SECTIONS = [
    {"id": "executive_summary", "title": "Executive Summary"},
    {"id": "prediction_core", "title": "Prediction Core"},
    {"id": "tactical_overview", "title": "Tactical Overview"},
    {"id": "risk_and_fallbacks", "title": "Risk and Fallbacks"},
    {"id": "visual_dashboard", "title": "Visual Dashboard"},
    {"id": "debug_appendix", "title": "Debug Appendix"},
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
