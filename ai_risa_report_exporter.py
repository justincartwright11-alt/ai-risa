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
    else:
        raise ValueError(f"Unsupported format: {fmt}")
