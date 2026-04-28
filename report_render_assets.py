
# report_render_assets.py
"""
Theme and asset config for report rendering, including visual slot placeholder styling.
"""

# === GLOBAL RASTER IMAGE SAFE-AREA SYSTEM ===
# Centralized inset/margin constants applied uniformly to all raster image panels.
PDF_IMAGE_BOX_PADDING_PT = 10       # ReportLab padding: image_box (inner frame)
PDF_IMAGE_WRAP_PADDING_PT = 10      # ReportLab padding: shadow_wrap (outer decorative frame)
PDF_RASTER_WRAPPER_INSET_PT = 10    # Keep outer raster panel border safely inside doc frame

# ===

# AI-RISA canonical visual identity palette.
# Used by ai_risa_report_exporter for color constants outside the per-theme THEMES dict.
AI_RISA_VISUAL_THEME = {
    "palette": {
        "black": "#020102",
        "graphite": "#271006",
        "panel": "#271006",
        "panel_alt": "#4F290D",
        "bronze": "#4F290D",
        "gold": "#BF8332",
        "gold_deep": "#7F521B",
        "gold_highlight": "#EDE2A6",
        "red": "#C61D06",
        "red_shadow": "#8E1408",
        "blue": "#2EA8FF",
        "blue_shadow": "#04204D",
        "text_primary": "#F3F3F3",
        "text_secondary": "#E6E8C6",
        "grid": "#4F290D",
    },
}

THEMES = {
    "black_gold_analyst": {
        "primary": AI_RISA_VISUAL_THEME["palette"]["black"],
        "accent": AI_RISA_VISUAL_THEME["palette"]["gold"],
        "danger_accent": AI_RISA_VISUAL_THEME["palette"]["red"],
        "data_accent": AI_RISA_VISUAL_THEME["palette"]["blue"],
        "text_primary": AI_RISA_VISUAL_THEME["palette"]["text_primary"],
        "text_secondary": AI_RISA_VISUAL_THEME["palette"]["text_secondary"],
        "panel_fill": AI_RISA_VISUAL_THEME["palette"]["panel"],
        "panel_fill_alt": AI_RISA_VISUAL_THEME["palette"]["panel_alt"],
        "grid_color": AI_RISA_VISUAL_THEME["palette"]["grid"],
        "watermark": AI_RISA_VISUAL_THEME["palette"]["gold"],
        "logo_path": "C:/ai_risa_data/brand_assets/ai_risa_logo_user_approved.png",
        "font": "Roboto, Arial, sans-serif",
        "title_size": 20,
        "heading_size": 16,
        "body_size": 12,
        "heading_case": "upper",
        "margin": 36,  # points
        "page_size": "A4",
        "header_text": "AI-RISA Combat Intelligence",
        "footer_text": "Confidential | Premium Fight Intelligence Brief",
        "placeholder_box": {
            "border_color": AI_RISA_VISUAL_THEME["palette"]["gold"],
            "fill_color": AI_RISA_VISUAL_THEME["palette"]["panel"],
            "text_color": AI_RISA_VISUAL_THEME["palette"]["gold"],
            "font_size": 10,
        },
        "texture": {
            "enabled": True,
            "line_step": 22,
            "alpha": 0.05,
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
