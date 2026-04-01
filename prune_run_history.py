#!/usr/bin/env python3
"""
AI-RISA Run History Retention Policy.

Prunes old timestamped run folders based on:
  - Maximum age in days (default: 30)
  - Maximum run count (default: 100)

Safety rules:
  - Never delete the newest successful run
  - Only prune after a new successful run is completed
  - Log all deletions
  - Update run index after deletion
  - Preserve run history integrity
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path


def load_index(index_file):
    """Load run history index from JSON file."""
    if not os.path.exists(index_file):
        return []
    
    try:
        with open(index_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return []
            data = json.loads(content)
            
            # Ensure we always return a list
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return [data]
            else:
                return []
    except (json.JSONDecodeError, IOError) as e:
        print(f"ERROR: Failed to load index: {e}", file=sys.stderr)
        return []


def save_index(index_file, records):
    """Save run history index to JSON file."""
    try:
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
        return True
    except IOError as e:
        print(f"ERROR: Failed to save index: {e}", file=sys.stderr)
        return False


def parse_timestamp(timestamp_str):
    """Parse timestamp string (YYYY-MM-DD_HHMMSS format)."""
    try:
        return datetime.strptime(timestamp_str, '%Y-%m-%d_%H%M%S')
    except ValueError:
        return None


def apply_retention_policy(runs_dir, max_age_days, max_runs, dry_run=False):
    """
    Apply retention policy to run history.
    
    Args:
        runs_dir: Directory containing timestamped run folders
        max_age_days: Delete runs older than this many days
        max_runs: Keep at most this many runs
        dry_run: If True, don't actually delete anything
    
    Returns:
        dict with retention results
    """
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'dry_run': dry_run,
        'runs_dir': runs_dir,
        'max_age_days': max_age_days,
        'max_runs': max_runs,
        'total_runs_before': 0,
        'total_runs_after': 0,
        'deleted_by_age': [],
        'deleted_by_count': [],
        'deleted_count': 0,
        'errors': []
    }
    
    if not os.path.isdir(runs_dir):
        results['errors'].append(f"Runs directory does not exist: {runs_dir}")
        return results
    
    # Load index
    index_file = os.path.join(runs_dir, 'run_history_index.json')
    records = load_index(index_file)
    results['total_runs_before'] = len(records)
    
    if len(records) == 0:
        results['total_runs_after'] = 0
        results['errors'].append("No runs in index (empty or missing)")
        return results
    
    # Sort by timestamp (newest first)
    records_sorted = sorted(
        records,
        key=lambda r: parse_timestamp(r.get('timestamp', '')) or datetime.min,
        reverse=True
    )
    
    # Find newest successful run (never delete this one)
    newest_successful = None
    for record in records_sorted:
        if record.get('status') == 'success':
            newest_successful = record
            break
    
    if not newest_successful:
        results['errors'].append("No successful runs found (refusing to delete all runs)")
        return results
    
    now = datetime.now()
    cutoff_date = now - timedelta(days=max_age_days)
    
    to_delete = []
    
    # First pass: apply age policy
    for record in records_sorted:
        timestamp = parse_timestamp(record.get('timestamp', ''))
        if not timestamp:
            results['errors'].append(f"Invalid timestamp in record: {record.get('timestamp')}")
            continue
        
        # Never delete the newest successful run
        if record is newest_successful:
            continue
        
        # Delete if older than max_age_days
        if timestamp < cutoff_date:
            to_delete.append({
                'record': record,
                'reason': 'age',
                'timestamp': timestamp
            })
    
    # Second pass: apply count policy (limit to max_runs, preserving newest)
    # Keep: newest_successful + newest (max_runs - 1) others
    
    # After age-based deletion, check total count
    remaining_count = len(records) - len(to_delete)
    
    if remaining_count > max_runs:
        # Need to delete more to meet count limit
        # Sort remaining runs by age (oldest first)
        remaining = [r for r in records_sorted if r not in [d['record'] for d in to_delete]]
        excess_count = remaining_count - max_runs
        
        # Try to delete oldest runs, but never delete newest successful
        for record in reversed(remaining):  # oldest first
            if excess_count <= 0:
                break
            
            # Never delete the newest successful run
            if record is newest_successful:
                continue
            
            # Check if already marked for deletion by age
            if record not in [d['record'] for d in to_delete]:
                to_delete.append({
                    'record': record,
                    'reason': 'count',
                    'timestamp': parse_timestamp(record.get('timestamp', '')) or datetime.min
                })
                excess_count -= 1
    
    # Perform deletions
    for deletion in to_delete:
        record = deletion['record']
        run_path = record.get('run_path')
        reason = deletion['reason']
        timestamp = record.get('timestamp', '?')
        
        if not run_path or not os.path.exists(run_path):
            results['errors'].append(f"Run path not found: {run_path}")
            continue
        
        try:
            if reason == 'age':
                results['deleted_by_age'].append(timestamp)
            else:
                results['deleted_by_count'].append(timestamp)
            
            if not dry_run:
                shutil.rmtree(run_path, ignore_errors=True)
                print(f"  Deleted [{reason}]: {timestamp} ({run_path})")
            else:
                print(f"  Would delete [{reason}]: {timestamp} ({run_path})")
            
            results['deleted_count'] += 1
        
        except Exception as e:
            results['errors'].append(f"Failed to delete {run_path}: {e}")
    
    # Update index (remove deleted records)
    if not dry_run and to_delete:
        deleted_paths = {d['record'].get('run_path') for d in to_delete}
        records = [r for r in records if r.get('run_path') not in deleted_paths]
        
        if save_index(index_file, records):
            print(f"  Updated run index ({len(records)} runs remaining)")
        else:
            results['errors'].append("Failed to update run index")
    
    results['total_runs_after'] = len(records) if not dry_run else len(records_sorted) - len(to_delete)
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description='AI-RISA run history retention policy enforcement',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check what would be deleted (dry-run)
  python prune_run_history.py --dry-run
  
  # Apply retention policy with defaults (30 days, 100 max runs)
  python prune_run_history.py
  
  # Keep only last 14 days and 50 runs
  python prune_run_history.py --max-age 14 --max-runs 50
  
  # Verbose output
  python prune_run_history.py --verbose
        """
    )
    
    parser.add_argument(
        '--runs-dir',
        default='C:\\ai_risa_data\\runs',
        help='Run history directory (default: C:\\ai_risa_data\\runs)'
    )
    
    parser.add_argument(
        '--max-age',
        type=int,
        default=30,
        help='Delete runs older than this many days (default: 30)'
    )
    
    parser.add_argument(
        '--max-runs',
        type=int,
        default=100,
        help='Keep at most this many runs (default: 100)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be deleted without actually deleting'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.max_age < 0:
        print("ERROR: --max-age must be non-negative", file=sys.stderr)
        return 1
    
    if args.max_runs < 1:
        print("ERROR: --max-runs must be at least 1", file=sys.stderr)
        return 1
    
    # Run retention policy
    mode = "DRY RUN" if args.dry_run else "LIVE"
    print(f"\n=== AI-RISA Run History Retention [{mode}] ===")
    print(f"Runs directory: {args.runs_dir}")
    print(f"Max age: {args.max_age} days")
    print(f"Max runs: {args.max_runs}")
    print()
    
    results = apply_retention_policy(
        args.runs_dir,
        args.max_age,
        args.max_runs,
        dry_run=args.dry_run
    )
    
    # Report results
    print(f"\nResults:")
    print(f"  Runs before: {results['total_runs_before']}")
    print(f"  Runs after: {results['total_runs_after']}")
    print(f"  Deleted: {results['deleted_count']}")
    
    if results['deleted_by_age']:
        print(f"\n  By age ({len(results['deleted_by_age'])} runs):")
        for ts in results['deleted_by_age'][:5]:
            print(f"    - {ts}")
        if len(results['deleted_by_age']) > 5:
            print(f"    ... and {len(results['deleted_by_age']) - 5} more")
    
    if results['deleted_by_count']:
        print(f"\n  By count limit ({len(results['deleted_by_count'])} runs):")
        for ts in results['deleted_by_count'][:5]:
            print(f"    - {ts}")
        if len(results['deleted_by_count']) > 5:
            print(f"    ... and {len(results['deleted_by_count']) - 5} more")
    
    if results['errors']:
        print(f"\n  Errors ({len(results['errors'])} total):")
        for err in results['errors'][:5]:
            print(f"    - {err}")
        if len(results['errors']) > 5:
            print(f"    ... and {len(results['errors']) - 5} more")
    
    # Verbose output
    if args.verbose:
        print(f"\nFull results:")
        print(json.dumps(results, indent=2))
    
    print()
    
    if args.dry_run:
        print("Note: This was a dry-run. No changes were made.")
        return 0
    else:
        if results['errors']:
            print("WARNING: Some errors occurred during retention policy application.", file=sys.stderr)
            return 1
        else:
            print("Retention policy applied successfully.")
            return 0


if __name__ == '__main__':
    sys.exit(main())
