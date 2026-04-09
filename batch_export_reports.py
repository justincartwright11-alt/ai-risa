# batch_export_reports.py
"""
Batch export runner for standardized report pipeline.
"""
import os
import json
import glob
from ai_risa_report_output_adapter import map_engine_output_to_report
from ai_risa_report_exporter import export_report
from report_delivery_config import make_report_filename, get_report_output_dir, get_manifest_filename, get_validated_output_path
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

# Deterministic fixture discovery from committed repo contents
FIXTURE_GLOBS = [
    "predictions/*_baseline.json",
    "predictions/*_sens2.json",
]

FIXTURES = sorted({
    path.replace("\\", "/")
    for pattern in FIXTURE_GLOBS
    for path in glob.glob(pattern)
})

def batch_export():
    def validate_fixtures(fixture_paths):
        required_fields = ["predicted_winner_id", "confidence", "method", "round"]
        if not fixture_paths:
            print("[FAIL] No fixtures found for export. Check input file paths and CI checkout.")
            raise SystemExit(2)
        valid_fixtures = []
        for fixture_path in fixture_paths:
            if not os.path.exists(fixture_path):
                print(f"[FAIL] Fixture input file missing: {fixture_path}")
                raise SystemExit(2)
            try:
                with open(fixture_path, "r", encoding="utf-8") as f:
                    engine_output = json.load(f)
            except Exception as e:
                print(f"[FAIL] Could not read or parse JSON: {fixture_path}\n  {e}")
                raise SystemExit(2)
            missing = [k for k in required_fields if k not in engine_output]
            if missing:
                print(f"[FAIL] Fixture missing required fields {missing}: {fixture_path}")
                raise SystemExit(2)
            valid_fixtures.append((fixture_path, engine_output))
        return valid_fixtures

    import sys
    smoke = "--smoke" in sys.argv
    print(f"[DIAG] batch_export_reports.py: Resolved {len(FIXTURES)} fixtures.")
    valid_fixtures = validate_fixtures(FIXTURES)
    if smoke:
        valid_fixtures = valid_fixtures[:1]
        if not valid_fixtures:
            print("[FAIL] No valid fixtures for smoke export.")
            raise SystemExit(2)
        print(f"[SMOKE] Exporting only: {valid_fixtures[0][0]}")
    for fixture_path, engine_output in valid_fixtures:
        report = map_engine_output_to_report(engine_output)
        fixture_slug = engine_output.get("prediction_id") or os.path.splitext(os.path.basename(fixture_path))[0]
        report_type = report["packaging"].get("report_type", "Report")
        out_dir = get_report_output_dir(fixture_slug)
        os.makedirs(out_dir, exist_ok=True)
        # Export JSON
        json_path = get_validated_output_path(fixture_slug, report_type, "json")
        export_report(report, json_path, fmt="json")
        # Export Markdown
        md_path = get_validated_output_path(fixture_slug, report_type, "md")
        export_report(report, md_path, fmt="md")
        # Export PDF
        pdf_path = get_validated_output_path(fixture_slug, report_type, "pdf")
        export_report(report, pdf_path, fmt="pdf")

        # Write manifest with explicit artifact inventory
        manifest = {
            "fixture": fixture_slug,
            "report_type": report_type,
            "version": report["packaging"].get("version", "unknown"),
            "export_timestamp": __import__("datetime").datetime.utcnow().isoformat(),
            "source_prediction_file": os.path.abspath(fixture_path),
            "outputs": {
                "json": os.path.basename(json_path),
                "markdown": os.path.basename(md_path),
                "pdf": os.path.basename(pdf_path),
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

        # Assert output dir contains files
        if not any(os.scandir(out_dir)):
            print(f"[FAIL] No files written to output dir: {out_dir}")
            raise SystemExit(2)

if __name__ == "__main__":
    batch_export()
