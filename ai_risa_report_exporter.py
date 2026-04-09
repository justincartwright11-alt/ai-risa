# ai_risa_report_exporter.py
"""
Exports the render-ready report to Markdown or JSON. PDF support can be added later.
"""
import json
from ai_risa_report_renderer import render_markdown


from ai_risa_report_renderer import render_markdown, _resolve_visual_slot
from report_render_assets import VISUAL_SLOT_CONFIG
from report_visual_asset_producer import build_visual_manifest, get_fixture_id, get_manifest_path

def export_report(report_payload, out_path, fmt="md"):
    # Build or update the visual manifest and assets for this report
    build_visual_manifest(report_payload)
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
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
            from reportlab.lib.units import inch
            from report_render_assets import THEMES
        except ImportError:
            raise RuntimeError("PDF export requires reportlab. Please install it in your environment.")

        theme = THEMES.get(report_payload.get("packaging", {}).get("theme", "black_gold_analyst"), THEMES["black_gold_analyst"])
        doc = SimpleDocTemplate(out_path, pagesize=A4, leftMargin=theme["margin"], rightMargin=theme["margin"], topMargin=theme["margin"], bottomMargin=theme["margin"])
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="CustomTitle", fontSize=theme["title_size"], leading=theme["title_size"]+2, alignment=1, spaceAfter=12))
        styles.add(ParagraphStyle(name="CustomHeading", fontSize=theme["heading_size"], leading=theme["heading_size"]+2, spaceAfter=8, spaceBefore=8))
        styles.add(ParagraphStyle(name="CustomBody", fontSize=theme["body_size"], leading=theme["body_size"]+2, spaceAfter=4))

        story = []
        # Title
        packaging = report_payload.get("packaging", {})
        story.append(Paragraph(packaging.get("report_type", "Fight Intelligence Report"), styles["CustomTitle"]))
        story.append(Paragraph(f"Brand: {packaging.get('brand_name','')}", styles["CustomBody"]))
        story.append(Paragraph(f"Theme: {packaging.get('theme','')}", styles["CustomBody"]))
        story.append(Paragraph(f"Version: {packaging.get('version','')}", styles["CustomBody"]))
        story.append(Spacer(1, 0.2*inch))
        # Headline
        headline = report_payload.get("headline", {})
        story.append(Paragraph("Headline Prediction", styles["CustomHeading"]))
        story.append(Paragraph(f"Winner: {headline.get('winner','')}", styles["CustomBody"]))
        story.append(Paragraph(f"Confidence: {headline.get('confidence_label','')}", styles["CustomBody"]))
        story.append(Paragraph(f"Method: {headline.get('method','')}", styles["CustomBody"]))
        story.append(Paragraph(f"Round: {headline.get('round','')}", styles["CustomBody"]))
        story.append(Spacer(1, 0.15*inch))
        # Sections
        for section in report_payload.get("sections", []):
            story.append(Paragraph(section["title"], styles["CustomHeading"]))
            content = section.get('content')
            if isinstance(content, dict):
                for k, v in content.items():
                    story.append(Paragraph(f"{k.replace('_',' ').title()}: {v}", styles["CustomBody"]))
            elif content is not None:
                story.append(Paragraph(str(content), styles["CustomBody"]))
            else:
                story.append(Paragraph("(No data)", styles["CustomBody"]))
            story.append(Spacer(1, 0.1*inch))
        # Visual slots (preserve order, always render placeholder or asset)
        story.append(Paragraph("Visual Dashboard", styles["CustomHeading"]))
        visual_slots = report_payload.get("visual_slots", {})
        for slot_id in VISUAL_SLOT_CONFIG:
            slot_payload = visual_slots.get(slot_id, {})
            slot = _resolve_visual_slot(slot_id, slot_payload)
            if slot["status"] == "asset":
                para = f"{slot['title']}: [See asset: {slot['asset_path']}]"
                if slot['caption']:
                    para += f"<br/><i>Caption: {slot['caption']}</i>"
                story.append(Paragraph(para, styles["CustomBody"]))
            else:
                story.append(Paragraph(f"{slot['title']}: {slot['fallback_text']}", styles["CustomBody"]))
        # Footer (simple)
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(theme["footer_text"], styles["CustomBody"]))
        doc.build(story)
    else:
        raise ValueError(f"Unsupported format: {fmt}")
