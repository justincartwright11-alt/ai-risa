# ai_risa_report_exporter.py
"""
Exports the render-ready report to Markdown or JSON. PDF support can be added later.
"""
import json
from ai_risa_report_renderer import render_markdown


from ai_risa_report_renderer import render_markdown, _resolve_visual_slot
from report_render_assets import VISUAL_SLOT_CONFIG, AI_RISA_VISUAL_THEME
from report_visual_asset_producer import build_visual_manifest, get_fixture_id, get_manifest_path

# QA content scanning helpers — scan only human-facing values, never raw metadata keys.
_QA_EXCLUDED_EXACT_KEYS = frozenset({
    "fight_id", "source_path", "debug", "raw", "fixture", "internal",
})
_QA_EXCLUDED_KEY_SUFFIXES = ("_id",)
_QA_EXCLUDED_KEY_PREFIXES = ("debug_", "trace_", "internal_")


def _qa_content_text(content):
    """Return a flat string of human-facing text for QA token scanning.

    For dict content: recurse into values only for display-safe keys.
    Metadata keys (ending in _id, or in the excluded sets) are skipped so
    that internal field names like fighter_a_id never appear in the scan.
    For list/other content: stringify normally.
    """
    if content is None:
        return ""
    if isinstance(content, dict):
        parts = []
        for k, v in content.items():
            ks = str(k)
            if ks in _QA_EXCLUDED_EXACT_KEYS:
                continue
            if any(ks.endswith(suf) for suf in _QA_EXCLUDED_KEY_SUFFIXES):
                continue
            if any(ks.startswith(pre) for pre in _QA_EXCLUDED_KEY_PREFIXES):
                continue
            parts.append(_qa_content_text(v))
        return " ".join(parts)
    if isinstance(content, list):
        return " ".join(_qa_content_text(item) for item in content)
    return str(content)


def export_report(report_payload, out_path=None, fmt="pdf"):
    # QA validation step
    def _qa_check(payload):
        errors = []
        forbidden_tokens = ["fighter_", "unknown", "n/a", "token mention", "not available", "template text", "(No data)"]
        required_sections = [
            "front_cover", "executive_summary", "matchup_snapshot", "decision_structure", "tactical_edges", "energy_use", "fatigue_failure_points", "mental_condition", "collapse_triggers", "deception_unpredictability", "fight_control", "fight_turns", "scenario_tree", "round_by_round_outlook", "risk_factors", "what_could_flip", "corner_notes", "final_projection", "confidence_explanation", "disclaimer"
        ]
        section_map = {s["id"]: s for s in payload.get("sections", []) if s.get("id")}
        # Get fighter names from front cover for cross-check
        fc = section_map.get("front_cover", {}).get("content", {})
        expected_fighters = []
        if fc:
            fighters_str = fc.get("fighters", "")
            if " vs " in fighters_str:
                expected_fighters = [x.strip().lower() for x in fighters_str.split(" vs ")]
        for sec in required_sections:
            s = section_map.get(sec)
            content = _qa_content_text(s.get("content")) if s else ""
            # Blank/missing
            if not s or not s.get("content") or content.strip() in ("", "None", "(No data)"):
                errors.append(f"Section '{sec}' is blank or missing.")
            # Forbidden tokens/content
            for token in forbidden_tokens:
                if token in content.lower():
                    errors.append(f"Section '{sec}' contains forbidden content: '{token}'.")
            # Truncated section labels (e.g., 'decision_struc', 'executive_summa')
            if len(s.get("title", "")) < 8:
                errors.append(f"Section '{sec}' has truncated or invalid title: '{s.get('title','')}'.")
            # Wrong fighter names (should match front cover)
            if expected_fighters:
                for ef in expected_fighters:
                    if ef and ef not in content.lower() and sec in ["executive_summary", "matchup_snapshot"]:
                        errors.append(f"Section '{sec}' missing expected fighter name: '{ef}'.")
        # Check for missing core fields
        for k in ["fight_id", "fighters", "event_date", "sport", "promotion"]:
            if not fc or not fc.get(k):
                errors.append(f"Front cover missing field: {k}")
        # Confidence explanation and disclaimer
        if not section_map.get("confidence_explanation"):
            errors.append("Missing confidence explanation section.")
        if not section_map.get("disclaimer"):
            errors.append("Missing disclaimer section.")
        return errors

    # Build or update the visual manifest and assets for this report
    build_visual_manifest(report_payload)

    # QA check before export
    qa_errors = _qa_check(report_payload)
    if qa_errors:
        print("QA validation failed: " + "; ".join(qa_errors))
        raise RuntimeError("Sale-readiness QA failed. Export blocked. Errors: " + "; ".join(qa_errors))

    # Output directory and filename
    import os
    output_dir = os.path.join(os.path.dirname(__file__), "reports")
    os.makedirs(output_dir, exist_ok=True)
    fight_id = None
    for s in report_payload.get("sections", []):
        if s["id"] == "front_cover":
            fight_id = s["content"].get("fight_id")
            break
    if not fight_id:
        fight_id = report_payload.get("packaging", {}).get("report_id") or "unknown_fight"

    # Standardize fight_slug for filename
    import re
    fight_slug = str(fight_id).lower().replace(" ", "_").replace("-", "_")
    if fight_slug.endswith("_premium"):
        fight_slug = fight_slug[:-8]
    # Strip trailing date patterns (e.g. _2025_01_01 or _2025) that may be appended to fight_id
    fight_slug = re.sub(r'_\d{4}(?:_\d{2}_\d{2})?$', '', fight_slug)
    filename = f"{fight_slug}_premium_v2.pdf"

    # Use explicit out_path if provided, else use standardized default
    out_path = out_path if out_path else os.path.join(output_dir, filename)

    if fmt == "md":
        md = render_markdown(report_payload)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(md)
    elif fmt == "json":
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report_payload, f, indent=2)
    elif fmt == "pdf":
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.utils import ImageReader
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import (
                SimpleDocTemplate,
                Paragraph,
                Spacer,
                Image,
                Table,
                TableStyle,
                KeepTogether,
                CondPageBreak,
                PageBreak,
            )
            from reportlab.lib.units import inch
            from report_render_assets import THEMES
        except ImportError:
            raise RuntimeError("PDF export requires reportlab. Please install it in your environment.")

        packaging = report_payload.get("packaging", {})
        brand_name = packaging.get("brand_name") or "AI-RISA"
        theme_name = packaging.get("theme") or "black_gold_analyst"
        version = packaging.get("version") or "RC1"

        theme = THEMES.get(theme_name, THEMES["black_gold_analyst"])
        primary_color = colors.HexColor(theme.get("primary", "#020102"))
        accent_color = colors.HexColor(theme.get("accent", "#BF8332"))
        danger_color = colors.HexColor(theme.get("danger_accent", "#C61D06"))
        data_color = colors.HexColor(theme.get("data_accent", "#2EA8FF"))
        text_primary = colors.HexColor(theme.get("text_primary", "#F3F3F3"))
        text_secondary = colors.HexColor(theme.get("text_secondary", "#E6E8C6"))
        panel_fill = colors.HexColor(theme.get("panel_fill", "#271006"))
        panel_fill_alt = colors.HexColor(theme.get("panel_fill_alt", "#4F290D"))
        gold_highlight = colors.HexColor(AI_RISA_VISUAL_THEME["palette"].get("gold_highlight", "#EDE2A6"))
        gold_deep = colors.HexColor(AI_RISA_VISUAL_THEME["palette"].get("gold_deep", "#7F521B"))
        red_shadow = colors.HexColor(AI_RISA_VISUAL_THEME["palette"].get("red_shadow", "#8E1408"))
        blue_shadow = colors.HexColor(AI_RISA_VISUAL_THEME["palette"].get("blue_shadow", "#04204D"))
        black_base = colors.HexColor(AI_RISA_VISUAL_THEME["palette"].get("black", "#020102"))
        watermark_color = colors.HexColor(theme.get("watermark", "#BF8332"))
        grid_color = colors.HexColor(theme.get("grid_color", AI_RISA_VISUAL_THEME["palette"]["grid"]))
        logo_path = theme.get("logo_path")

        if not logo_path or not os.path.exists(logo_path):
            raise RuntimeError(
                "Approved logo file is required and was not found at "
                f"{logo_path!r}. Place exact user-approved artwork there and rerun."
            )

        approved_logo = ImageReader(logo_path)

        doc = SimpleDocTemplate(out_path, pagesize=A4, leftMargin=theme["margin"], rightMargin=theme["margin"], topMargin=theme["margin"], bottomMargin=theme["margin"])
        try:
            from report_render_assets import PDF_IMAGE_BOX_PADDING_PT, PDF_IMAGE_WRAP_PADDING_PT, PDF_RASTER_WRAPPER_INSET_PT
        except ImportError:
            PDF_IMAGE_BOX_PADDING_PT = 10
            PDF_IMAGE_WRAP_PADDING_PT = 10
            PDF_RASTER_WRAPPER_INSET_PT = 10

        # Shared raster panel width-fit solver: keep all framed PNG wrappers fully inside the document frame.
        raster_wrapper_width = max(3.5 * inch, doc.width - (2 * PDF_RASTER_WRAPPER_INSET_PT))
        raster_image_box_width = max(
            3.0 * inch,
            raster_wrapper_width - (2 * PDF_IMAGE_WRAP_PADDING_PT) - 2,
        )
        raster_image_max_width = max(
            2.4 * inch,
            raster_image_box_width - (2 * PDF_IMAGE_BOX_PADDING_PT) - 2,
        )
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="CustomTitle", fontSize=theme["title_size"], leading=theme["title_size"]+2, alignment=1, spaceAfter=12, textColor=accent_color, fontName="Helvetica-Bold"))
        styles.add(ParagraphStyle(name="CustomHeading", fontSize=theme["heading_size"], leading=theme["heading_size"]+2, spaceAfter=8, spaceBefore=8, keepWithNext=True, textColor=accent_color, fontName="Helvetica-Bold"))
        styles.add(ParagraphStyle(name="CustomBody", fontSize=theme["body_size"], leading=theme["body_size"]+2, spaceAfter=4, textColor=text_primary))
        styles.add(ParagraphStyle(name="CustomCaption", fontSize=10, leading=12, alignment=1, textColor=text_secondary, italic=True, spaceAfter=6))
        styles.add(ParagraphStyle(name="CoverTitle", fontSize=34, leading=40, alignment=1, textColor=accent_color, spaceAfter=6))
        styles.add(ParagraphStyle(name="CoverSubTitle", fontSize=16, leading=20, alignment=1, textColor=text_primary, spaceAfter=14))
        styles.add(ParagraphStyle(name="CoverMeta", fontSize=12, leading=16, alignment=1, textColor=text_secondary, spaceAfter=3))
        styles.add(ParagraphStyle(name="CoverBand", fontSize=12, leading=16, alignment=1, textColor=text_primary, spaceAfter=0))

        def _build_heading_divider():
            """Minimal premium divider for open narrative layout."""
            divider = Table([[""]], colWidths=[6.64 * inch], rowHeights=[0.06 * inch])
            divider.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), panel_fill),
                ("LINEABOVE", (0, 0), (-1, 0), 0.65, gold_highlight),
                ("LINEBELOW", (0, 0), (-1, 0), 0.35, accent_color),
                ("LINEBEFORE", (0, 0), (0, 0), 1.0, danger_color),
                ("LINEAFTER", (-1, 0), (-1, 0), 1.0, data_color),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            return divider

        fight_id_for_page = get_fixture_id(report_payload)
        def _draw_page_chrome(canvas, _doc):
            canvas.saveState()
            width, height = A4
            canvas.setFillColor(primary_color)
            canvas.rect(0, 0, width, height, fill=1, stroke=0)

            # Subtle tactical texture grid (non-flat cinematic background).
            texture = theme.get("texture", {})
            if texture.get("enabled", True):
                step = int(texture.get("line_step", 22))
                alpha = float(texture.get("alpha", 0.05))
                canvas.setStrokeColor(grid_color)
                canvas.setLineWidth(0.25)
                canvas.setStrokeAlpha(alpha)
                for x in range(0, int(width), step):
                    canvas.line(x, 0, x, height)
                for y in range(0, int(height), step):
                    canvas.line(0, y, width, y)
                canvas.setStrokeAlpha(1)

            canvas.setStrokeColor(accent_color)
            canvas.setLineWidth(0.8)
            canvas.line(theme["margin"], height - 26, width - theme["margin"], height - 26)
            canvas.line(theme["margin"], 24, width - theme["margin"], 24)

            # Gloss sweep for dimensional metallic page feel.
            canvas.setFillColor(colors.Color(gold_highlight.red, gold_highlight.green, gold_highlight.blue, alpha=0.09))
            canvas.saveState()
            canvas.translate(width * 0.56, height * 0.96)
            canvas.rotate(-18)
            canvas.rect(-210, -10, 420, 28, fill=1, stroke=0)
            canvas.restoreState()

            # Beveled perimeter and subtle blue glow edge.
            canvas.setStrokeColor(accent_color)
            canvas.setLineWidth(1.1)
            canvas.rect(8, 8, width - 16, height - 16, fill=0, stroke=1)
            canvas.setStrokeColor(data_color)
            canvas.setStrokeAlpha(0.25)
            canvas.setLineWidth(0.6)
            canvas.rect(11, 11, width - 22, height - 22, fill=0, stroke=1)
            canvas.setStrokeAlpha(1)

            # Corner bracket accents for HUD-like frame depth.
            canvas.setStrokeColor(accent_color)
            canvas.setLineWidth(1.0)
            l = 18
            canvas.line(14, height - 14, 14 + l, height - 14)
            canvas.line(14, height - 14, 14, height - 14 - l)
            canvas.line(width - 14, height - 14, width - 14 - l, height - 14)
            canvas.line(width - 14, height - 14, width - 14, height - 14 - l)
            canvas.line(14, 14, 14 + l, 14)
            canvas.line(14, 14, 14, 14 + l)
            canvas.line(width - 14, 14, width - 14 - l, 14)
            canvas.line(width - 14, 14, width - 14, 14 + l)

            # Header logo treatment (small approved brand mark).
            canvas.drawImage(
                approved_logo,
                theme["margin"],
                height - 24,
                width=66,
                height=18,
                preserveAspectRatio=True,
                mask='auto',
            )

            canvas.setFillColor(accent_color)
            canvas.setFont("Helvetica-Bold", 8)
            canvas.drawString(theme["margin"] + 72, height - 20, f"{brand_name} Combat Intelligence")
            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(text_secondary)
            canvas.drawRightString(width - theme["margin"], 14, f"Page {canvas.getPageNumber()}")

            # Footer logo treatment (micro mark, low visual weight).
            canvas.drawImage(
                approved_logo,
                theme["margin"],
                8,
                width=28,
                height=10,
                preserveAspectRatio=True,
                mask='auto',
            )

            # subtle watermark using approved logo art.
            canvas.saveState()
            canvas.translate(width * 0.5, height * 0.5)
            canvas.rotate(33)
            canvas.setFillAlpha(0.06)
            canvas.drawImage(
                approved_logo,
                -170,
                -65,
                width=340,
                height=130,
                preserveAspectRatio=True,
                mask='auto',
            )
            canvas.restoreState()

            canvas.restoreState()

        story = []
        # Cover block
        front_cover = next((s.get("content") for s in report_payload.get("sections", []) if s.get("id") == "front_cover" and isinstance(s.get("content"), dict)), {})
        headline = report_payload.get("headline", {})
        cover_flow = []
        if logo_path and os.path.exists(logo_path):
            cover_logo = Image(logo_path)
            cover_logo._restrictSize(4.2 * inch, 1.6 * inch)
            cover_flow.append(cover_logo)
            cover_flow.append(Spacer(1, 0.12 * inch))

        cover_flow.append(Paragraph("AI-RISA", styles["CoverTitle"]))
        cover_flow.append(Paragraph("Combat Intelligence", styles["CoverSubTitle"]))
        cover_flow.append(Spacer(1, 0.08 * inch))
        cover_flow.append(Paragraph(front_cover.get("fighters", "Fight Intelligence Brief"), styles["CustomTitle"]))
        cover_flow.append(Paragraph(f"Event Date: {front_cover.get('event_date', 'Date TBD')}", styles["CoverMeta"]))
        cover_flow.append(Paragraph(f"Promotion: {front_cover.get('promotion', 'Unknown')}", styles["CoverMeta"]))
        cover_flow.append(Spacer(1, 0.18 * inch))

        band_text = (
            f"Headline Projection  |  {headline.get('winner','TBD')}  |  "
            f"{headline.get('method','TBD')}  |  {headline.get('round','TBD')}  |  "
            f"{headline.get('confidence_label','') or 'Confidence TBD'}"
        )
        band_table = Table([[Paragraph(band_text, styles["CoverBand"]) ]], colWidths=[6.62 * inch])
        band_table.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.9, danger_color),
            ("BACKGROUND", (0, 0), (-1, -1), red_shadow),
            ("TEXTCOLOR", (0, 0), (-1, -1), text_primary),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        cover_flow.append(band_table)
        cover_flow.append(Spacer(1, 0.12 * inch))
        story.append(KeepTogether(cover_flow))
        story.append(Spacer(1, 0.25 * inch))

        # Headline
        headline = report_payload.get("headline", {})
        headline_block = [
            Paragraph("Headline Prediction", styles["CustomHeading"]),
            _build_heading_divider(),
            Spacer(1, 0.05 * inch),
            Paragraph(f"Winner: {headline.get('winner','')}", styles["CustomBody"]),
            Paragraph(f"Confidence: {headline.get('confidence_label','')}", styles["CustomBody"]),
            Paragraph(f"Method: {headline.get('method','')}", styles["CustomBody"]),
            Paragraph(f"Round: {headline.get('round','')}", styles["CustomBody"]),
        ]
        story.append(KeepTogether(headline_block))
        story.append(Spacer(1, 0.18*inch))

        # --- Combat Intelligence Dashboard page (Page 2) ---
        try:
            from ai_risa_combat_dashboard_adapter import build_combat_dashboard_view_model

            dash = build_combat_dashboard_view_model(report_payload)
            panels = dash.get("panels") or {}
            fa_name = dash.get("fighter_a_name") or "Fighter A"
            fb_name = dash.get("fighter_b_name") or "Fighter B"

            styles.add(ParagraphStyle(
                name="DashTitle",
                fontSize=16, leading=20, alignment=1, spaceAfter=4,
                textColor=accent_color, fontName="Helvetica-Bold",
            ))
            styles.add(ParagraphStyle(
                name="DashSubtitle",
                fontSize=9, leading=12, alignment=1, spaceAfter=8,
                textColor=text_secondary,
            ))
            styles.add(ParagraphStyle(
                name="DashPanelHead",
                fontSize=9, leading=11, spaceAfter=3, spaceBefore=3,
                textColor=gold_highlight, fontName="Helvetica-Bold",
            ))
            styles.add(ParagraphStyle(
                name="DashPanelBody",
                fontSize=8, leading=10, spaceAfter=2,
                textColor=text_primary,
            ))
            styles.add(ParagraphStyle(
                name="DashFighterLabel",
                fontSize=8, leading=10, spaceAfter=1,
                textColor=text_secondary, fontName="Helvetica-Bold",
            ))

            def _panel_box(contents, border_color=None):
                """Wrap a list of flowables in a styled panel cell."""
                inner = Table([[c] for c in contents], colWidths=[2.88 * inch])
                inner.setStyle(TableStyle([
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]))
                bc = border_color or accent_color
                outer = Table([[inner]], colWidths=[3.0 * inch])
                outer.setStyle(TableStyle([
                    ("BOX", (0, 0), (-1, -1), 0.8, bc),
                    ("BACKGROUND", (0, 0), (-1, -1), panel_fill),
                    ("LINEABOVE", (0, 0), (-1, 0), 1.2, bc),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]))
                return outer

            def _wide_panel_box(contents, width_in=6.62, border_color=None):
                bc = border_color or accent_color
                outer = Table([[c] for c in contents], colWidths=[width_in * inch])
                outer.setStyle(TableStyle([
                    ("BOX", (0, 0), (-1, -1), 0.8, bc),
                    ("BACKGROUND", (0, 0), (-1, -1), panel_fill),
                    ("LINEABOVE", (0, 0), (-1, 0), 1.2, bc),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]))
                return outer

            story.append(PageBreak())

            # Dashboard title banner
            story.append(Paragraph(dash.get("dashboard_title", "AI-RISA Combat Intelligence Dashboard"), styles["DashTitle"]))
            story.append(Paragraph(dash.get("dashboard_subtitle", "Advanced Intelligence — Ring Intelligence Systems Architecture"), styles["DashSubtitle"]))
            story.append(_build_heading_divider())
            story.append(Spacer(1, 0.08 * inch))

            # Row 1: Headline Prediction (wide) | Fighter Architecture (right half)
            hp = panels.get("headline_prediction") or {}
            hp_lines = [
                Paragraph("HEADLINE PREDICTION", styles["DashPanelHead"]),
                Paragraph(f"Winner:  {hp.get('predicted_winner', 'Not available')}", styles["DashPanelBody"]),
                Paragraph(f"Confidence:  {hp.get('confidence', 'Not available')}", styles["DashPanelBody"]),
                Paragraph(f"Method:  {hp.get('method', 'Not available')}", styles["DashPanelBody"]),
                Paragraph(f"Round:  {hp.get('round', 'Not available')}", styles["DashPanelBody"]),
                Paragraph(f"Signal Gap:  {hp.get('signal_gap', 'Not available')}", styles["DashPanelBody"]),
            ]

            fa_arch = (panels.get("fighter_architecture") or {}).get("fighter_a") or {}
            fb_arch = (panels.get("fighter_architecture") or {}).get("fighter_b") or {}
            arch_labels = [
                ("Decision Structure", "decision_structure"),
                ("Energy Use", "energy_use"),
                ("Fatigue Resistance", "fatigue_resistance"),
                ("Mental Condition", "mental_condition"),
                ("Collapse Risk", "collapse_risk"),
                ("Deception & Unpredictability", "deception_unpredictability"),
            ]
            arch_lines = [Paragraph("FIGHTER ARCHITECTURE", styles["DashPanelHead"])]
            arch_data = [["Metric", fa_name[:12], fb_name[:12]]]
            for label, key in arch_labels:
                arch_data.append([label, fa_arch.get(key, "N/A"), fb_arch.get(key, "N/A")])
            arch_table = Table(arch_data, colWidths=[1.32 * inch, 0.72 * inch, 0.72 * inch])
            arch_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), panel_fill_alt),
                ("TEXTCOLOR", (0, 0), (-1, 0), gold_highlight),
                ("TEXTCOLOR", (0, 1), (-1, -1), text_primary),
                ("TEXTCOLOR", (1, 1), (1, -1), danger_color),
                ("TEXTCOLOR", (2, 1), (2, -1), data_color),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("GRID", (0, 0), (-1, -1), 0.35, grid_color),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]))
            arch_lines.append(arch_table)

            row1 = Table(
                [[_panel_box(hp_lines, border_color=danger_color), _panel_box(arch_lines)]],
                colWidths=[3.18 * inch, 3.18 * inch],
            )
            row1.setStyle(TableStyle([
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            story.append(row1)
            story.append(Spacer(1, 0.07 * inch))

            # Row 2: Round Control Shifts (wide)
            rcs = panels.get("round_control_shifts") or {}
            rcs_lines = [Paragraph("ROUND-BY-ROUND CONTROL SHIFTS", styles["DashPanelHead"])]
            if rcs.get("available"):
                rcs_fa = rcs.get("fighter_a") or {}
                rcs_fb = rcs.get("fighter_b") or {}
                rcs_rounds = rcs.get("rounds") or []
                rcs_lines.append(Paragraph(
                    f"Early:  {fa_name[:10]} {rcs_fa.get('early_control','—')}  vs  {fb_name[:10]} {rcs_fb.get('early_control','—')}",
                    styles["DashPanelBody"],
                ))
                rcs_lines.append(Paragraph(
                    f"Mid:    {fa_name[:10]} {rcs_fa.get('mid_control','—')}  vs  {fb_name[:10]} {rcs_fb.get('mid_control','—')}",
                    styles["DashPanelBody"],
                ))
                rcs_lines.append(Paragraph(
                    f"Late:   {fa_name[:10]} {rcs_fa.get('late_control','—')}  vs  {fb_name[:10]} {rcs_fb.get('late_control','—')}",
                    styles["DashPanelBody"],
                ))
                if rcs_fa.get("values") and rcs_rounds:
                    pairs = list(zip(rcs_rounds, rcs_fa.get("values", []), rcs_fb.get("values", [])))
                    row_data = [["Round", fa_name[:10], fb_name[:10]]] + [[r, a, b] for r, a, b in pairs]
                    rcs_table = Table(row_data, colWidths=[0.55 * inch] * 3)
                    rcs_table.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), panel_fill_alt),
                        ("TEXTCOLOR", (0, 0), (-1, 0), gold_highlight),
                        ("TEXTCOLOR", (1, 1), (1, -1), danger_color),
                        ("TEXTCOLOR", (2, 1), (2, -1), data_color),
                        ("TEXTCOLOR", (0, 1), (0, -1), text_secondary),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 7),
                        ("GRID", (0, 0), (-1, -1), 0.3, grid_color),
                        ("LEFTPADDING", (0, 0), (-1, -1), 3),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                        ("TOPPADDING", (0, 0), (-1, -1), 2),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                    ]))
                    rcs_lines.append(rcs_table)
            else:
                rcs_lines.append(Paragraph("Not available", styles["DashPanelBody"]))
            story.append(_wide_panel_box(rcs_lines))
            story.append(Spacer(1, 0.07 * inch))

            # Row 3: Energy + Fatigue | Collapse Triggers
            ef = panels.get("energy_fatigue") or {}
            ef_lines = [
                Paragraph("ENERGY USE + FATIGUE FAILURE WINDOW", styles["DashPanelHead"]),
                Paragraph(f"Danger Window: {ef.get('danger_window', 'Not available')}", styles["DashPanelBody"]),
            ]
            ef_summary = ef.get("energy_use_summary") or "Not available"
            ef_fatigue = ef.get("fatigue_failure_summary") or "Not available"
            if ef_summary and ef_summary != "Not available":
                # Show first paragraph only for concise panel
                ef_short = ef_summary.split("\n\n")[0][:220].strip()
                ef_lines.append(Paragraph(ef_short.replace("\n", " "), styles["DashPanelBody"]))
            else:
                ef_lines.append(Paragraph("Energy use data not available.", styles["DashPanelBody"]))
            if ef_fatigue and ef_fatigue != "Not available":
                ef_fatigue_short = ef_fatigue.split("\n\n")[0][:200].strip()
                ef_lines.append(Paragraph(ef_fatigue_short.replace("\n", " "), styles["DashPanelBody"]))

            ct = panels.get("collapse_triggers") or []
            ct_lines = [Paragraph("COLLAPSE TRIGGERS", styles["DashPanelHead"])]
            if ct:
                for trigger in ct[:5]:
                    ct_lines.append(Paragraph(f"• {trigger[:100]}", styles["DashPanelBody"]))
            else:
                ct_lines.append(Paragraph("Not available", styles["DashPanelBody"]))

            row3 = Table(
                [[_panel_box(ef_lines), _panel_box(ct_lines, border_color=danger_color)]],
                colWidths=[3.18 * inch, 3.18 * inch],
            )
            row3.setStyle(TableStyle([
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            story.append(row3)
            story.append(Spacer(1, 0.07 * inch))

            # Row 4: Scenario Tree | Method Pathways
            st = panels.get("scenario_tree") or {}
            st_lines = [Paragraph("SCENARIO TREE", styles["DashPanelHead"])]
            for path_key in ("path_a", "path_b", "path_c"):
                path = st.get(path_key) or {}
                label = path.get("label", path_key.upper())
                desc = (path.get("description") or "Not available")[:120]
                st_lines.append(Paragraph(f"<b>{label[:28]}</b>", styles["DashPanelBody"]))
                st_lines.append(Paragraph(desc, styles["DashPanelBody"]))

            mp = panels.get("method_pathways") or {}
            mp_lines = [Paragraph("METHOD PATHWAYS", styles["DashPanelHead"])]
            mp_lines.append(Paragraph(f"Predicted: {mp.get('predicted_method', 'Not available')}", styles["DashPanelBody"]))
            pathways = mp.get("pathways") or []
            if pathways:
                pw_data = [["Method", "Probability"]] + [[p.get("method", "—"), p.get("probability", "—")] for p in pathways]
                pw_table = Table(pw_data, colWidths=[1.6 * inch, 1.0 * inch])
                pw_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), panel_fill_alt),
                    ("TEXTCOLOR", (0, 0), (-1, 0), gold_highlight),
                    ("TEXTCOLOR", (0, 1), (-1, -1), text_primary),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 7),
                    ("GRID", (0, 0), (-1, -1), 0.3, grid_color),
                    ("LEFTPADDING", (0, 0), (-1, -1), 3),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]))
                mp_lines.append(pw_table)
            else:
                mp_lines.append(Paragraph("Not available", styles["DashPanelBody"]))

            row4 = Table(
                [[_panel_box(st_lines), _panel_box(mp_lines, border_color=data_color)]],
                colWidths=[3.18 * inch, 3.18 * inch],
            )
            row4.setStyle(TableStyle([
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            story.append(row4)
            story.append(Spacer(1, 0.07 * inch))

        except Exception as _dash_exc:
            # Dashboard page must never crash the report — degrade gracefully
            story.append(Paragraph(
                f"[Combat Intelligence Dashboard unavailable: {_dash_exc}]",
                styles["CustomCaption"],
            ))

        # --- End Combat Intelligence Dashboard page ---

        # Sections
        for section in report_payload.get("sections", []):
            if section.get("id") == "front_cover":
                continue
            story.append(CondPageBreak(1.35 * inch))
            heading_text = str(section["title"] or "")
            if theme.get("heading_case") == "upper":
                heading_text = heading_text.upper()
            section_heading = Paragraph(heading_text, styles["CustomHeading"])
            section_divider = _build_heading_divider()
            content = section.get('content')
            content_flow = []
            if isinstance(content, dict):
                for k, v in content.items():
                    content_flow.append(Paragraph(f"{k.replace('_',' ').title()}: {v}", styles["CustomBody"]))
            elif content is not None:
                blocks = [b.strip() for b in str(content).split("\n\n") if b.strip()]
                if not blocks:
                    blocks = [str(content)]
                for block in blocks:
                    content_flow.append(Paragraph(block.replace("\n", "<br/>"), styles["CustomBody"]))
            else:
                content_flow.append(Paragraph("(No data)", styles["CustomBody"]))

            if content_flow:
                story.append(KeepTogether([section_heading, section_divider, Spacer(1, 0.045 * inch), content_flow[0]]))
                story.extend(content_flow[1:])
            else:
                story.append(section_heading)
            story.append(Spacer(1, 0.12*inch))
        # Visual slots (preserve order, always render placeholder or asset)
        story.append(CondPageBreak(2.2 * inch))
        visual_slots = report_payload.get("visual_slots", {})
        visual_cards = []
        for slot_id in VISUAL_SLOT_CONFIG:
            slot_payload = visual_slots.get(slot_id, {})
            slot = _resolve_visual_slot(slot_id, slot_payload)
            visual_title = str(slot["title"] or "")
            if theme.get("heading_case") == "upper":
                visual_title = visual_title.upper()
            visual_block = [Paragraph(visual_title, styles["CustomHeading"])]
            if slot["status"] == "asset":
                image = Image(slot["asset_path"])
                image._restrictSize(raster_image_max_width, 4.35 * inch)
                image_box = Table([[image]], colWidths=[raster_image_box_width], hAlign="LEFT")
                image_box.setStyle(TableStyle([
                    ("BOX", (0, 0), (-1, -1), 1.0, accent_color),
                    ("INNERGRID", (0, 0), (-1, -1), 0.35, data_color),
                    ("BACKGROUND", (0, 0), (-1, -1), panel_fill),
                    ("LEFTPADDING", (0, 0), (-1, -1), PDF_IMAGE_BOX_PADDING_PT),
                    ("RIGHTPADDING", (0, 0), (-1, -1), PDF_IMAGE_BOX_PADDING_PT),
                    ("TOPPADDING", (0, 0), (-1, -1), PDF_IMAGE_BOX_PADDING_PT),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), PDF_IMAGE_BOX_PADDING_PT),
                ]))
                shadow_wrap = Table([[image_box]], colWidths=[raster_wrapper_width], hAlign="LEFT")
                shadow_wrap.setStyle(TableStyle([
                    ("BOX", (0, 0), (-1, -1), 1.4, accent_color),
                    ("INNERGRID", (0, 0), (-1, -1), 0.45, data_color),
                    ("BACKGROUND", (0, 0), (-1, -1), panel_fill_alt),
                    ("LINEBEFORE", (0, 0), (0, 0), 1.2, danger_color),
                    ("LINEAFTER", (-1, 0), (-1, 0), 1.2, data_color),
                    ("LEFTPADDING", (0, 0), (-1, -1), PDF_IMAGE_WRAP_PADDING_PT),
                    ("RIGHTPADDING", (0, 0), (-1, -1), PDF_IMAGE_WRAP_PADDING_PT),
                    ("TOPPADDING", (0, 0), (-1, -1), PDF_IMAGE_WRAP_PADDING_PT),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), PDF_IMAGE_WRAP_PADDING_PT),
                ]))
                visual_block.append(shadow_wrap)
                if slot['caption']:
                    visual_block.append(Paragraph(slot['caption'], styles["CustomCaption"]))
            else:
                visual_block.append(Paragraph(slot['fallback_text'], styles["CustomBody"]))
            visual_block.append(Spacer(1, 0.12 * inch))
            visual_cards.append(KeepTogether(visual_block))

        dashboard_heading = Paragraph("Visual Dashboard", styles["CustomHeading"])
        if visual_cards:
            # Keep dashboard heading attached to the first visual card.
            story.append(CondPageBreak(5.1 * inch))
            story.append(KeepTogether([dashboard_heading, visual_cards[0]]))
            story.extend(visual_cards[1:])
        else:
            story.append(dashboard_heading)

        comparison_asset_path = None
        try:
            fight_id_for_manifest = get_fixture_id(report_payload)
            manifest_path = get_manifest_path(fight_id_for_manifest)
            if os.path.exists(manifest_path):
                with open(manifest_path, "r", encoding="utf-8") as mf:
                    visual_manifest = json.load(mf)
                comparison_asset = (visual_manifest or {}).get("premium_metric_comparison") or {}
                comparison_asset_path = comparison_asset.get("asset_path")
        except Exception:
            comparison_asset_path = None

        comparison_table = report_payload.get("comparison_table") or {}
        headers = comparison_table.get("headers") or []
        rows = comparison_table.get("rows") or []
        if comparison_asset_path and os.path.exists(comparison_asset_path):
            story.append(PageBreak())
            table_heading = str(comparison_table.get("title", "Premium Metric Comparison"))
            if theme.get("heading_case") == "upper":
                table_heading = table_heading.upper()
            story.append(Paragraph(table_heading, styles["CustomHeading"]))
            comparison_wrapper_width = max(3.2 * inch, raster_wrapper_width - 8)
            comparison_image_max_width = max(2.6 * inch, comparison_wrapper_width - 10)
            comparison_image = Image(comparison_asset_path)
            comparison_image._restrictSize(comparison_image_max_width, 5.05 * inch)
            comparison_image_box = Table([[comparison_image]], colWidths=[comparison_wrapper_width], hAlign="LEFT")
            comparison_image_box.setStyle(TableStyle([
                ("BOX", (0, 0), (-1, -1), 1.2, accent_color),
                ("INNERGRID", (0, 0), (-1, -1), 0.45, data_color),
                ("BACKGROUND", (0, 0), (-1, -1), panel_fill_alt),
                ("LINEBEFORE", (0, 0), (0, 0), 1.2, danger_color),
                ("LINEAFTER", (-1, 0), (-1, 0), 1.2, data_color),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(comparison_image_box)
            story.append(Spacer(1, 0.08 * inch))
        elif headers and rows:
            # Force comparison block onto a fresh page to fully isolate it from any preceding text.
            story.append(PageBreak())
            table_heading = str(comparison_table.get("title", "Comparison Table"))
            if theme.get("heading_case") == "upper":
                table_heading = table_heading.upper()
            table_title = Paragraph(table_heading, styles["CustomHeading"])
            table_data = [headers] + rows
            metric_table = Table(table_data, repeatRows=1, colWidths=[1.72 * inch, 2.47 * inch, 2.47 * inch], hAlign="LEFT")
            table_theme = theme.get("table_theme", {})
            metric_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (1, 0), colors.HexColor(table_theme.get("header_bg", "#4F290D"))),
                ("BACKGROUND", (0, 0), (0, 0), red_shadow),
                ("BACKGROUND", (-1, 0), (-1, 0), blue_shadow),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor(table_theme.get("header_text", "#E6BF67"))),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 12),
                ("FONTSIZE", (0, 1), (-1, -1), 11),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor(table_theme.get("row_a", "#020102"))),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                    colors.HexColor(table_theme.get("row_a", "#020102")),
                    colors.HexColor(table_theme.get("row_b", "#271006")),
                ]),
                ("GRID", (0, 0), (-1, -1), 0.55, colors.HexColor(table_theme.get("grid", "#1B73C2"))),
                ("LINEABOVE", (0, 0), (-1, 0), 0.55, gold_highlight),
                ("LINEBELOW", (0, 0), (-1, 0), 0.45, gold_deep),
                ("LINEBEFORE", (0, 1), (0, -1), 0.7, danger_color),
                ("LINEAFTER", (-1, 1), (-1, -1), 0.7, data_color),
                ("LINEABOVE", (0, 1), (-1, 1), 0.45, accent_color),
                ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor(table_theme.get("text", "#F3F3F3"))),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("ALIGN", (0, 0), (0, -1), "LEFT"),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]))
            # framed_table must be wide enough to contain metric_table (6.66 in) plus its own padding (6+6 pt).
            # 6.66 in = 479.52 pt; 479.52 + 12 = 491.52 pt = 6.827 in → use 6.83 in.
            framed_table = Table([[metric_table]], colWidths=[6.83 * inch])
            framed_table.setStyle(TableStyle([
                ("BOX", (0, 0), (-1, -1), 1.1, accent_color),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, data_color),
                ("BACKGROUND", (0, 0), (-1, -1), black_base),
                ("LINEBEFORE", (0, 0), (0, 0), 1.2, danger_color),
                ("LINEAFTER", (-1, 0), (-1, 0), 1.2, data_color),
                ("LINEABOVE", (0, 0), (-1, 0), 0.5, gold_highlight),
                ("LINEBELOW", (0, 0), (-1, 0), 0.45, gold_deep),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            # beveled_table must be wide enough to contain framed_table (6.83 in) plus its own padding (4+4 pt).
            # 6.83 in = 491.76 pt; 491.76 + 8 = 499.76 pt = 6.941 in → use 6.94 in.
            beveled_table = Table([[framed_table]], colWidths=[6.94 * inch])
            beveled_table.setStyle(TableStyle([
                ("BOX", (0, 0), (-1, -1), 1.35, accent_color),
                ("BACKGROUND", (0, 0), (-1, -1), panel_fill_alt),
                ("LINEABOVE", (0, 0), (-1, 0), 0.65, gold_highlight),
                ("LINEBELOW", (0, 0), (-1, 0), 0.55, gold_deep),
                ("LINEBEFORE", (0, 0), (0, 0), 1.3, danger_color),
                ("LINEAFTER", (-1, 0), (-1, 0), 1.3, data_color),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            title_band = Table([[table_title]], colWidths=[6.94 * inch], hAlign="LEFT")
            title_band.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), black_base),
                ("BOX", (0, 0), (-1, -1), 1.0, accent_color),
                ("LINEABOVE", (0, 0), (-1, 0), 0.55, gold_highlight),
                ("LINEBELOW", (0, 0), (-1, 0), 0.45, gold_deep),
                ("LINEBEFORE", (0, 0), (0, 0), 1.1, danger_color),
                ("LINEAFTER", (-1, 0), (-1, 0), 1.1, data_color),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(KeepTogether([title_band, beveled_table]))
            story.append(Spacer(1, 0.05 * inch))
            accent_row = Table([["Threat Signal", "Data Signal"]], colWidths=[3.325 * inch, 3.325 * inch], hAlign="LEFT")
            accent_row.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, 0), danger_color),
                ("BACKGROUND", (1, 0), (1, 0), data_color),
                ("BOX", (0, 0), (-1, -1), 0.9, accent_color),
                ("LINEABOVE", (0, 0), (-1, 0), 0.45, gold_highlight),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            accent_row_wrap = Table([[accent_row]], colWidths=[6.65 * inch])
            accent_row_wrap.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), black_base),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            story.append(accent_row_wrap)
        # Footer (simple)
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(theme["footer_text"], styles["CustomCaption"]))
        try:
            doc.build(story, onFirstPage=_draw_page_chrome, onLaterPages=_draw_page_chrome)
        except Exception as e:
            raise RuntimeError(f"Malformed PDF: {e}")
    else:
        raise ValueError(f"Unsupported format: {fmt}")
    return out_path
