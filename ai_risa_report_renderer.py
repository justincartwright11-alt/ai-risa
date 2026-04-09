# ai_risa_report_renderer.py
"""
Consumes the adapter payload and builds a render-ready document model for output.
"""


from report_render_assets import VISUAL_SLOT_CONFIG
import os
import json
from report_visual_asset_producer import get_fixture_id, get_manifest_path

def _resolve_visual_slot(slot_id, slot_payload=None):
    cfg = VISUAL_SLOT_CONFIG.get(slot_id, {})
    # Try to resolve asset from manifest (presentation-side only)
    slot_info = None
    try:
        # Use fixture id from payload
        fixture_id = get_fixture_id(slot_payload or {}) if slot_payload else None
        if not fixture_id:
            # Try to get from parent context (report_payload)
            import inspect
            frame = inspect.currentframe().f_back
            report_payload = frame.f_locals.get('report_payload')
            fixture_id = get_fixture_id(report_payload) if report_payload else None
        if fixture_id:
            manifest_path = get_manifest_path(fixture_id)
            if os.path.exists(manifest_path):
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
                slot_info = manifest.get(slot_id)
    except Exception:
        slot_info = None
    if slot_info and slot_info.get("asset_path"):
        return {
            "id": slot_id,
            "title": cfg.get("title", slot_id.title()),
            "status": "asset",
            "asset_path": slot_info["asset_path"],
            "fallback_text": cfg.get("fallback_text"),
            "caption": slot_info.get("caption"),
        }
    else:
        return {
            "id": slot_id,
            "title": cfg.get("title", slot_id.title()),
            "status": "placeholder",
            "asset_path": None,
            "fallback_text": cfg.get("fallback_text"),
            "caption": cfg.get("caption"),
        }

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
    # Visual slots (preserve order, always render placeholder or asset)
    lines.append("## Visual Dashboard\n")
    visual_slots = report_payload.get("visual_slots", {})
    for slot_id in VISUAL_SLOT_CONFIG:
        slot_payload = visual_slots.get(slot_id, {})
        slot = _resolve_visual_slot(slot_id, slot_payload)
        if slot["status"] == "asset":
            line = f"**{slot['title']}:** [See asset: {slot['asset_path']}]"
            if slot['caption']:
                line += f"  \n_Caption: {slot['caption']}_"
            lines.append(line)
        else:
            lines.append(f"**{slot['title']}:** {slot['fallback_text']}")
    return "\n".join(lines)
