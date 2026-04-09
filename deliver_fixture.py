# deliver_fixture.py
"""
Single-command wrapper to validate, export, manifest, checksum, and package a single fixture.
"""
import os
import sys
import subprocess
import json
import hashlib
from ai_risa_report_output_adapter import map_engine_output_to_report
from ai_risa_report_exporter import export_report
from report_delivery_config import make_report_filename, get_report_output_dir, get_manifest_filename
from package_report_outputs import zip_fixture_bundle

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

def deliver_fixture(fixture_path):
    # 1. Validate pipeline
    result = subprocess.run(["run_report_validation.bat"], shell=True)
    if result.returncode != 0:
        print("Validation failed.")
        sys.exit(1)
    # 2. Export outputs
    with open(fixture_path, "r", encoding="utf-8") as f:
        engine_output = json.load(f)
    report = map_engine_output_to_report(engine_output)
    fixture_slug = engine_output.get("prediction_id") or os.path.splitext(os.path.basename(fixture_path))[0]
    report_type = report["packaging"].get("report_type", "Report")
    out_dir = get_report_output_dir(fixture_slug)
    os.makedirs(out_dir, exist_ok=True)
    json_name = make_report_filename(fixture_slug, report_type, "json")
    md_name = make_report_filename(fixture_slug, report_type, "md")
    pdf_name = make_report_filename(fixture_slug, report_type, "pdf")
    export_report(report, os.path.join(out_dir, json_name), fmt="json")
    export_report(report, os.path.join(out_dir, md_name), fmt="md")
    export_report(report, os.path.join(out_dir, pdf_name), fmt="pdf")
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
    # 3. Write README
    write_readme(out_dir, manifest)
    # 4. Zip bundle
    zip_fixture_bundle(fixture_slug)
    zip_path = os.path.join(os.path.dirname(out_dir), f"{fixture_slug}.zip")
    # 5. Write checksums
    write_checksums(out_dir, manifest, zip_path)
    print(f"Delivery complete for {fixture_slug} in {out_dir}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python deliver_fixture.py <fixture_path>")
        sys.exit(1)
    deliver_fixture(sys.argv[1])
