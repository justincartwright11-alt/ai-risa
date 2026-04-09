# batch_export_reports.py
"""
Batch export runner for standardized report pipeline.
"""
import os
import json
from ai_risa_report_output_adapter import map_engine_output_to_report
from ai_risa_report_exporter import export_report
from report_delivery_config import make_report_filename, get_report_output_dir, get_manifest_filename
from package_report_outputs import zip_fixture_bundle
import hashlib

def sha256sum(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def write_readme(out_dir, manifest):
    readme_path = os.path.join(out_dir, "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(f"# Report Bundle: {manifest['fixture']}\n\n")
        f.write(f"**Version:** {manifest['version']}\n\n")
        f.write(f"**Export Timestamp:** {manifest['export_timestamp']}\n\n")
        f.write("## Artifact Inventory\n")
        for k, v in manifest['outputs'].items():
            f.write(f"- {k}: {v}\n")
        f.write(f"- manifest: {get_manifest_filename()}\n")
        f.write(f"- assets: {manifest['assets_folder']}\n")
        f.write("- checksums: checksums.txt\n\n")
        f.write("## How to Use\n")
        f.write("See manifest.json for artifact details. Use checksums.txt to verify integrity.\n")
        f.write("All filenames are deterministic and versioned.\n")
    return readme_path

def write_checksums(out_dir, manifest, zip_path):
    checksum_path = os.path.join(out_dir, "checksums.txt")
    files = [os.path.join(out_dir, v) for v in manifest['outputs'].values()]
    files.append(os.path.join(out_dir, get_manifest_filename()))
    files.append(zip_path)
    with open(checksum_path, "w", encoding="utf-8") as f:
        for file in files:
            if os.path.exists(file):
                f.write(f"{os.path.basename(file)}: {sha256sum(file)}\n")
    return checksum_path

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

        # Write manifest with explicit artifact inventory
        manifest = {
            "fixture": fixture_slug,
            "report_type": report_type,
            "version": report["packaging"].get("version", "unknown"),
            "export_timestamp": __import__("datetime").datetime.utcnow().isoformat(),
            "source_prediction_file": os.path.abspath(fixture_path),
            "outputs": {
                "json": json_name,
                "markdown": md_name,
                "pdf": pdf_name,
            },
            "assets_folder": os.path.join(out_dir, "assets"),
        }
        with open(os.path.join(out_dir, get_manifest_filename()), "w", encoding="utf-8") as mf:
            json.dump(manifest, mf, indent=2)
        print(f"Exported {fixture_slug} to {out_dir}")

        # Write README
        readme_path = write_readme(out_dir, manifest)
        print(f"README written to {readme_path}")

        # Zip bundle
        zip_fixture_bundle(fixture_slug)
        # Write checksums
        zip_path = os.path.join(os.path.dirname(out_dir), f"{fixture_slug}.zip")
        write_checksums(out_dir, manifest, zip_path)
        print(f"Checksums written to {os.path.join(out_dir, 'checksums.txt')}")

if __name__ == "__main__":
    batch_export()
