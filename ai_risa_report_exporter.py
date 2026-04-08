# ai_risa_report_exporter.py
"""
Exports the render-ready report to Markdown or JSON. PDF support can be added later.
"""
import json
from ai_risa_report_renderer import render_markdown

def export_report(report_payload, out_path, fmt="md"):
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
        # Visual slots
        story.append(Paragraph("Visual Dashboard", styles["CustomHeading"]))
        for slot, slot_info in report_payload.get("visual_slots", {}).items():
            story.append(Paragraph(f"{slot_info['title']}: {slot_info.get('fallback','No data')}", styles["CustomBody"]))
        # Footer (simple)
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(theme["footer_text"], styles["CustomBody"]))
        doc.build(story)
    else:
        raise ValueError(f"Unsupported format: {fmt}")
