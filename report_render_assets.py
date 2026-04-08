
# report_render_assets.py
"""
Theme and asset config for report rendering, including visual slot placeholder styling.
"""

THEMES = {
    "black_gold_analyst": {
        "primary": "#111",
        "accent": "#FFD700",
        "font": "Roboto, Arial, sans-serif",
        "title_size": 20,
        "heading_size": 16,
        "body_size": 12,
        "margin": 36,  # points
        "page_size": "A4",
        "header_text": "AI-RISA Combat Intelligence",
        "footer_text": "Confidential | Premium Fight Intelligence Brief",
        "placeholder_box": {
            "border_color": "#FFD700",
            "fill_color": "#222",
            "text_color": "#FFD700",
            "font_size": 10,
        },
    },
    # Add more themes as needed
}

# Visual slot placeholder style and config
VISUAL_PLACEHOLDER_STYLE = {
    "border": "1px dashed #FFD700",
    "padding": "8px",
    "background": "#222",
    "text_color": "#FFD700",
    "font_size": 10,
    "caption_style": "italic",
}

VISUAL_SLOT_CONFIG = {
    "radar": {
        "title": "Fighter Radar",
        "fallback_text": "Radar data unavailable for this fixture.",
        "asset_path": None,
        "caption": None,
    },
    "heat_map": {
        "title": "Round Heat Map",
        "fallback_text": "Heat map data unavailable for this fixture.",
        "asset_path": None,
        "caption": None,
    },
    "control_shift": {
        "title": "Control Shift Graph",
        "fallback_text": "Control-shift data unavailable for this fixture.",
        "asset_path": None,
        "caption": None,
    },
    "method_chart": {
        "title": "Method of Victory Chart",
        "fallback_text": "Method distribution data unavailable for this fixture.",
        "asset_path": None,
        "caption": None,
    },
}
