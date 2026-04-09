# package_report_outputs.py
"""
Bundle each fixture's delivery folder as a zip archive for distribution.
"""
import os
import zipfile
from report_delivery_config import DELIVERY_ROOT, REPORT_VERSION

def zip_fixture_bundle(fixture_slug):
    out_dir = os.path.join(DELIVERY_ROOT, REPORT_VERSION, fixture_slug)
    zip_path = os.path.join(DELIVERY_ROOT, REPORT_VERSION, f"{fixture_slug}.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(out_dir):
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, out_dir)
                zf.write(abs_path, arcname=os.path.join(fixture_slug, rel_path))
    print(f"Bundled {fixture_slug} as {zip_path}")

def package_all_fixtures():
    fixture_dirs = [d for d in os.listdir(os.path.join(DELIVERY_ROOT, REPORT_VERSION)) if os.path.isdir(os.path.join(DELIVERY_ROOT, REPORT_VERSION, d))]
    for fixture_slug in fixture_dirs:
        zip_fixture_bundle(fixture_slug)

if __name__ == "__main__":
    package_all_fixtures()
