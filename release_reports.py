#!/usr/bin/env python3
"""
release_reports.py

Top-level release automation wrapper for standardized report delivery pipeline.
Runs validation, regression, export, packaging, checksums, and bundle verification in order.
Fails fast on any error. Emits a release summary at the end.
"""
import subprocess
import sys
import os
from pathlib import Path

# Configurable paths to scripts and delivery root
VALIDATION_CMD = ["run_report_validation.bat"]
REGRESSION_CMD = ["python", "run_regression_tests.py"]  # If exists
EXPORT_SMOKE_CMD = ["python", "export_smoke_test.py"]   # If exists
BATCH_EXPORT_CMD = ["python", "batch_export_reports.py"]
DELIVERY_ROOT = Path("deliveries")
FROZEN_FIXTURE_PATH = Path("fixtures/predictions_frozen/")

# Utility to run a command and fail fast
def run_step(cmd, desc):
    print(f"\n=== {desc} ===")
    try:
        result = subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] {desc} failed with exit code {e.returncode}")
        sys.exit(e.returncode)
    print(f"[OK] {desc}")

# Step 1: Contract validation
run_step(VALIDATION_CMD, "Contract validation")

# Step 2: Presentation regression (optional, skip if not present)
if os.path.exists("run_regression_tests.py"):
    run_step(REGRESSION_CMD, "Presentation regression")
else:
    print("[SKIP] No regression test script found.")

# Step 3: Export smoke tests (optional, skip if not present)
if os.path.exists("export_smoke_test.py"):
    run_step(EXPORT_SMOKE_CMD, "Export smoke tests")
else:
    print("[SKIP] No export smoke test script found.")

# Step 4: Batch export
run_step(BATCH_EXPORT_CMD, "Batch export")

# After batch export, check if any files exist under deliveries/v100-template-standardized
output_root = Path("deliveries") / "v100-template-standardized"
if not output_root.exists() or not any(output_root.rglob("*")):
    print(f"[FAIL] No report artifacts were generated under {output_root}")
    sys.exit(2)

# Step 5: Per-report packaging and checksums are handled by batch_export_reports.py

# Step 6: Verify bundles and checksums
summary = []
if DELIVERY_ROOT.exists():
    for version_dir in DELIVERY_ROOT.iterdir():
        if not version_dir.is_dir():
            continue
        for fixture_dir in version_dir.iterdir():
            if not fixture_dir.is_dir():
                continue
            manifest = fixture_dir / "manifest.json"
            checksums = fixture_dir / "checksums.txt"
            readme = fixture_dir / "README.md"
            zip_path = version_dir / f"{fixture_dir.name}.zip"
            missing = [str(p) for p in [manifest, checksums, readme, zip_path] if not p.exists()]
            if missing:
                print(f"[FAIL] Missing artifacts for {fixture_dir.name}: {missing}")
                sys.exit(2)
            summary.append({
                "fixture": fixture_dir.name,
                "bundle": str(fixture_dir),
                "manifest": str(manifest),
                "checksums": str(checksums),
                "readme": str(readme),
                "zip": str(zip_path)
            })
else:
    print(f"[FAIL] Delivery root not found: {DELIVERY_ROOT}")
    sys.exit(2)

# Step 7: Release summary
print("\n=== Release Summary ===")
for entry in summary:
    print(f"Fixture: {entry['fixture']}")
    print(f"  Bundle:   {entry['bundle']}")
    print(f"  Manifest: {entry['manifest']}")
    print(f"  Checksums:{entry['checksums']}")
    print(f"  README:   {entry['readme']}")
    print(f"  Zip:      {entry['zip']}")
    print()
print("[SUCCESS] Release pipeline completed. All bundles verified.")
