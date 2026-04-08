# ai_risa_report_renderer.py
"""
Consumes the adapter payload and builds a render-ready document model for output.
"""

def render_markdown(report_payload):
    lines = []
    # Metadata/packaging
    packaging = report_payload.get("packaging", {})
    lines.append(f"# {packaging.get('report_type', 'Fight Intelligence Report')}")
    lines.append(f"**Brand:** {packaging.get('brand_name', '')}")
    lines.append(f"**Theme:** {packaging.get('theme', '')}")
    lines.append(f"**Version:** {packaging.get('version', '')}\n")
    # Headline
    headline = report_payload.get("headline", {})
    lines.append(f"## Headline Prediction\n")
    lines.append(f"**Winner:** {headline.get('winner','')}  ")
    lines.append(f"**Confidence:** {headline.get('confidence_label','')}  ")
    lines.append(f"**Method:** {headline.get('method','')}  ")
    lines.append(f"**Round:** {headline.get('round','')}\n")
    # Sections
    for section in report_payload.get("sections", []):
        lines.append(f"### {section['title']}")
        content = section.get('content')
        if isinstance(content, dict):
            for k, v in content.items():
                lines.append(f"- **{k.replace('_',' ').title()}:** {v}")
        elif content is not None:
            lines.append(str(content))
        else:
            lines.append("_(No data)_")
        lines.append("")
    # Visual slots
    lines.append("## Visual Dashboard\n")
    for slot, slot_info in report_payload.get("visual_slots", {}).items():
        lines.append(f"**{slot_info['title']}:** {slot_info.get('fallback','No data')}")
    return "\n".join(lines)
