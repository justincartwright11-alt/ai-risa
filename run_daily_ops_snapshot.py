#!/usr/bin/env python3
"""
AI-RISA Daily Ops Snapshot
=========================
Produces a repeatable daily/event-closeout reporting snapshot without mutating any ledgers.
"""
import argparse
import subprocess
import shutil
import sys
from pathlib import Path
from datetime import datetime

# Defaults
DEFAULT_HEALTH_SCRIPT = r'C:\Users\jusin\ai_risa_data\run_ledger_health_summary.py'
DEFAULT_EXPORT_SCRIPT = r'C:\Users\jusin\ai_risa_data\run_export_reconciliation_csv.py'
DEFAULT_HEALTH_OUTPUT = r'C:\Users\jusin\ai_risa_data\ledger\ledger_health_snapshot.json'
DEFAULT_EXPORT_OUTPUT = r'C:\Users\jusin\ai_risa_data\exports\reconciliation_export.csv'
DEFAULT_REPORTS_ROOT = r'C:\Users\jusin\ai_risa_data\reports'


def print_header():
    now = datetime.now().isoformat(timespec='seconds')
    print("AI-RISA Daily Ops Snapshot\n==========================")
    print(f"Run timestamp: {now}\n")

def run_script(script, args=None):
    cmd = [sys.executable, script]
    if args:
        cmd += args
    subprocess.run(cmd, check=True)

def file_status(path):
    p = Path(path)
    if p.exists():
        size = p.stat().st_size
        return f"Exists ({size} bytes)"
    else:
        return "Missing"

def main():
    parser = argparse.ArgumentParser(description="Produce daily ops snapshot for AI-RISA.")
    parser.add_argument('--health-script', default=DEFAULT_HEALTH_SCRIPT)
    parser.add_argument('--export-script', default=DEFAULT_EXPORT_SCRIPT)
    parser.add_argument('--health-output-json', default=DEFAULT_HEALTH_OUTPUT)
    parser.add_argument('--export-output-csv', default=DEFAULT_EXPORT_OUTPUT)
    parser.add_argument('--reports-root', default=DEFAULT_REPORTS_ROOT)
    parser.add_argument('--no-archive', action='store_true', help='Do not archive outputs')
    args = parser.parse_args()

    print_header()
    success = True
    archive_dir = None

    try:
        # 1. Run health summary
        print(f"Running health summary: {args.health_script}")
        run_script(args.health_script, ['--output-json', args.health_output_json])
        print(f"  Output: {args.health_output_json} [{file_status(args.health_output_json)}]")

        # 2. Run reconciliation export
        print(f"Running reconciliation export: {args.export_script}")
        run_script(args.export_script)
        print(f"  Output: {args.export_output_csv} [{file_status(args.export_output_csv)}]")

        # 3. Export trend dashboard HTML
        trend_html_script = r'C:\ai_risa_data\run_export_trend_dashboard_html.py'
        print(f"Running trend dashboard HTML export: {trend_html_script}")
        run_script(trend_html_script)

        # 4. Package ops report
        packager_script = r'C:\ai_risa_data\run_package_ops_report.py'
        print(f"Running ops report packager: {packager_script}")
        run_script(packager_script)

        # 3. Archive copy
        if not args.no_archive:
            date_str = datetime.now().strftime('%Y-%m-%d')
            archive_dir = Path(args.reports_root) / date_str
            archive_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(args.health_output_json, archive_dir / 'ledger_health_snapshot.json')
            shutil.copy2(args.export_output_csv, archive_dir / 'reconciliation_export.csv')
            print(f"Archived to: {archive_dir}")
            print(f"  {archive_dir / 'ledger_health_snapshot.json'} [{file_status(archive_dir / 'ledger_health_snapshot.json')}]\n  {archive_dir / 'reconciliation_export.csv'} [{file_status(archive_dir / 'reconciliation_export.csv')}]")
        else:
            print("Archive step skipped (--no-archive)")

    except subprocess.CalledProcessError as e:
        print(f"ERROR: Subprocess failed: {e}")
        success = False
    except Exception as e:
        print(f"ERROR: {e}")
        success = False

    print("\nSummary:")
    print(f"  Health snapshot: {args.health_output_json} [{file_status(args.health_output_json)}]")
    print(f"  Reconciliation CSV: {args.export_output_csv} [{file_status(args.export_output_csv)}]")
    if archive_dir:
        print(f"  Archive folder: {archive_dir}")
    print(f"\nStatus: {'SUCCESS' if success else 'FAILURE'}")
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
