#!/usr/bin/env python3
"""
AI-RISA Ops Report Packager
Bundles the latest operational outputs into a single dated zip for review/sharing.
"""
import argparse
import sys
from pathlib import Path
from datetime import datetime
import zipfile

# Defaults
HEALTH_SNAPSHOT = Path(r'C:\Users\jusin\ai_risa_data\ledger\ledger_health_snapshot.json')
RECONCILIATION_CSV = Path(r'C:\Users\jusin\ai_risa_data\exports\reconciliation_export.csv')
CALIBRATION_PATCH = Path(r'C:\Users\jusin\ai_risa_data\learning\calibration_patch_v1.json')
CLOSEOUT_SUMMARY = Path(r'C:\Users\jusin\ai_risa_data\closeout\event_closeout_summary.txt')  # optional
REPORTS_ROOT = Path(r'C:\Users\jusin\ai_risa_data\reports')


def main():
    parser = argparse.ArgumentParser(description="Bundle latest AI-RISA ops outputs into a dated zip report.")
    parser.add_argument('--date', default=datetime.now().strftime('%Y-%m-%d'), help='Date for report folder/zip (default: today)')
    args = parser.parse_args()

    date_str = args.date
    report_dir = REPORTS_ROOT / date_str
    zip_path = report_dir / f'ai_risa_ops_report_{date_str}.zip'
    report_dir.mkdir(parents=True, exist_ok=True)


    TREND_DASHBOARD_HTML = Path(r'C:\Users\jusin\ai_risa_data\reports\trend_dashboard_latest.html')
    files_to_include = [
        (HEALTH_SNAPSHOT, 'ledger_health_snapshot.json'),
        (RECONCILIATION_CSV, 'reconciliation_export.csv'),
        (CALIBRATION_PATCH, 'calibration_patch_v1.json'),
        (TREND_DASHBOARD_HTML, 'trend_dashboard_latest.html'),
    ]
    if CLOSEOUT_SUMMARY.exists():
        files_to_include.append((CLOSEOUT_SUMMARY, 'event_closeout_summary.txt'))

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for src, arcname in files_to_include:
            if src.exists():
                zf.write(src, arcname)
                print(f'Added: {src} as {arcname}')
            else:
                print(f'WARNING: {src} not found, skipping.')

    print(f'\nPackaged report: {zip_path}')
    if zip_path.exists():
        print(f'Size: {zip_path.stat().st_size} bytes')
        print('SUCCESS')
    else:
        print('FAILURE: Zip not created')
        sys.exit(1)

if __name__ == "__main__":
    main()
