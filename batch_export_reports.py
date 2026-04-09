# batch_export_reports.py
"""
Batch export runner for standardized report pipeline.
"""
import os
import json
from ai_risa_report_output_adapter import map_engine_output_to_report
from ai_risa_report_exporter import export_report
from report_delivery_config import make_report_filename, get_report_output_dir, get_manifest_filename

# List of fixtures to export
FIXTURES = [
    "predictions/van_taira_baseline.json",
    "predictions/volkov_cortes_baseline.json",
    "predictions/volkov_cortes_sens2.json",
    "predictions/muhammad_bonfim_baseline.json",
    "predictions/muhammad_bonfim_sens2.json",
]

def batch_export():
    for fixture_path in FIXTURES:
        with open(fixture_path, "r", encoding="utf-8") as f:
            engine_output = json.load(f)
        report = map_engine_output_to_report(engine_output)
        fixture_slug = engine_output.get("prediction_id") or os.path.splitext(os.path.basename(fixture_path))[0]
        report_type = report["packaging"].get("report_type", "Report")
        out_dir = get_report_output_dir(fixture_slug)
        os.makedirs(out_dir, exist_ok=True)
        # Export JSON
        json_name = make_report_filename(fixture_slug, report_type, "json")
        export_report(report, os.path.join(out_dir, json_name), fmt="json")
        # Export Markdown
        md_name = make_report_filename(fixture_slug, report_type, "md")
        export_report(report, os.path.join(out_dir, md_name), fmt="md")
        # Export PDF
        pdf_name = make_report_filename(fixture_slug, report_type, "pdf")
        export_report(report, os.path.join(out_dir, pdf_name), fmt="pdf")
        # Write manifest
        manifest = {
            "fixture": fixture_slug,
            "report_type": report_type,
            "outputs": [json_name, md_name, pdf_name],
        }
        with open(os.path.join(out_dir, get_manifest_filename()), "w", encoding="utf-8") as mf:
            json.dump(manifest, mf, indent=2)
        print(f"Exported {fixture_slug} to {out_dir}")

if __name__ == "__main__":
    batch_export()
