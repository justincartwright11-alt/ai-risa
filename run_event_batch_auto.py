def log(msg, *args, verbose=False, always=False, file=None):
    if always or verbose:
        print(msg.format(*args), flush=True, file=file)
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime

# --- Helpers ---
def parse_args():
    parser = argparse.ArgumentParser(description="AI-RISA Batch Event Orchestrator")
    parser.add_argument('--events', nargs='*', help='List of event IDs')
    parser.add_argument('--schedule', help='Path to schedule JSON')
    parser.add_argument('--formats', nargs='*', default=['md', 'docx', 'pdf'], help='Formats to generate (md, docx, pdf)')
    parser.add_argument('--create-missing-stubs', action='store_true', help='Create missing stubs for dependencies')
    parser.add_argument('--main-event-only-stubs', action='store_true', help='Only create stubs for main event')
    parser.add_argument('--skip-existing', action='store_true', help='Skip formats if output already exists')
    parser.add_argument('--strict', action='store_true', help='Strict mode: abort on missing deps or failures')
    parser.add_argument('--dry-run', action='store_true', help='Dry run: validate and print actions, do not write or run')
    parser.add_argument('--summary-json', default='output/event_batch_run_summary.json', help='Write JSON summary to this path')
    parser.add_argument('--summary-csv', default='output/event_batch_run_summary.csv', help='Write CSV summary to this path')
    return parser.parse_args()

def slugify_name(name):
    return name.strip().lower().replace(' ', '_')

def is_tba_name(name):
    if not name: return True
    n = str(name).strip().lower()
    return n in {"tba", "tbd", "to be announced", "to be determined", "unknown", "opponent tba"}

def load_schedule(path, verbose=False):
    if not os.path.exists(path):
        log("[ERROR] Schedule file not found: {}", path, always=True, file=sys.stderr)
        sys.exit(2)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        log("[ERROR] Failed to read schedule file: {}", e, always=True, file=sys.stderr)
        sys.exit(2)
    events = data.get('events', [])
    if not events:
        log("[ERROR] Schedule file has no events: {}", path, always=True, file=sys.stderr)
        sys.exit(2)
    jobs = []
    for e in events:
        if isinstance(e, str):
            jobs.append({'event_id': e, 'formats': None, 'priority': None, 'source': 'schedule'})
        elif isinstance(e, dict):
            jobs.append({
                'event_id': e['event_id'],
                'formats': e.get('formats'),
                'priority': e.get('priority'),
                'source': 'schedule',
                **{k: v for k, v in e.items() if k not in {'event_id', 'formats', 'priority'}}
            })
    return data.get('schedule_name', ''), jobs

def normalize_event_jobs(args, verbose=False):
    jobs = []
    if args.schedule and args.events:
        log("[ERROR] Cannot use both --events and --schedule. Choose one.", always=True, file=sys.stderr)
        sys.exit(2)
    if args.schedule:
        sched_name, sched_jobs = load_schedule(args.schedule, verbose=verbose)
        seen = set()
        for job in sched_jobs:
            eid = job['event_id']
            fmts = job['formats'] or args.formats
            key = (eid, tuple(sorted(fmts)))
            if key in seen:
                continue
            seen.add(key)
            job['formats'] = fmts
            jobs.append(job)
        return sched_name, jobs
    if args.events:
        seen = set()
        for eid in args.events:
            key = (eid, tuple(sorted(args.formats)))
            if key in seen:
                continue
            seen.add(key)
            jobs.append({'event_id': eid, 'formats': args.formats, 'source': 'events_cli'})
    return '', jobs

def validate_event_file(event_id):
    event_path = f'C:/ai_risa_data/events/{event_id}.json'
    if not os.path.exists(event_path):
        # Try to detect metadata-only event from schedule
        return None, f"Event file missing: {event_path}", None
    try:
        with open(event_path, 'r', encoding='utf-8') as f:
            event = json.load(f)
    except Exception as e:
        return False, f"Event JSON parse error: {e}", None
    for k in ['event', 'date', 'venue', 'bouts']:
        if k not in event:
            return False, f"Missing key '{k}' in event file", None
    if not isinstance(event['bouts'], list) or not event['bouts']:
        return None, "'bouts' must be a non-empty list", event
    return True, "ok", event

def derive_bout_dependencies(fighter_a, fighter_b):
    slug_a = slugify_name(fighter_a)
    slug_b = slugify_name(fighter_b)
    deps = {
        'fighter_a': f'C:/ai_risa_data/fighters/{slug_a}.json',
        'fighter_b': f'C:/ai_risa_data/fighters/{slug_b}.json',
        'matchup': f'C:/ai_risa_data/matchups/{slug_a}_vs_{slug_b}.json',
        'prediction': f'C:/ai_risa_data/predictions/{slug_a}_vs_{slug_b}_prediction.json',
        'slugs': (slug_a, slug_b)
    }
    return deps

def create_stub_files(deps, fighter_a, fighter_b, create_all, dry_run, verbose=False):
    created = []
    # Fighter stubs
    for key, name in [('fighter_a', fighter_a), ('fighter_b', fighter_b)]:
        path = deps[key]
        if not os.path.exists(path):
            stub = {
                "name": name,
                "sport": "MMA",
                "division": "Unknown",
                "stance": "Orthodox",
                "style": "Unknown",
                "team": "",
                "notes": "Auto-generated stub for batch pipeline validation."
            }
            if not dry_run:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(stub, f, indent=2)
            log("[STUB] Created fighter stub: {}", path, verbose=verbose)
            created.append(path)
    # Matchup stub
    if not os.path.exists(deps['matchup']):
        stub = {
            "fighters": [fighter_a, fighter_b],
            "weight_class": "Unknown",
            "sport": "MMA"
        }
        if not dry_run:
            os.makedirs(os.path.dirname(deps['matchup']), exist_ok=True)
            with open(deps['matchup'], 'w', encoding='utf-8') as f:
                json.dump(stub, f, indent=2)
        log("[STUB] Created matchup stub: {}", deps['matchup'], verbose=verbose)
        created.append(deps['matchup'])
    # Prediction stub
    if not os.path.exists(deps['prediction']):
        stub = {
            "winner": fighter_a,
            "method": "Decision",
            "confidence": 0.55
        }
        if not dry_run:
            os.makedirs(os.path.dirname(deps['prediction']), exist_ok=True)
            with open(deps['prediction'], 'w', encoding='utf-8') as f:
                json.dump(stub, f, indent=2)
        log("[STUB] Created prediction stub: {}", deps['prediction'], verbose=verbose)
        created.append(deps['prediction'])
    return created

def run_format(event_id, fmt, dry_run, verbose=False):
    out_path = f'C:/ai_risa_data/reports/{event_id}_full_prim_report.{fmt if fmt != "md" else "md"}'
    cmd = [sys.executable, 'C:/ai_risa_data/run_full_auto_pipeline_final.py', '--mode', 'event', '--event', event_id, '--report', 'Full Prim Report', '--format', fmt]
    if dry_run:
        log("[RUN] (dry-run) Would run: {}", ' '.join(cmd), verbose=verbose)
        return 0, '', '', out_path, 0.0
    t0 = time.time()
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = proc.communicate()
    elapsed = time.time() - t0
    return proc.returncode, stdout, stderr, out_path, elapsed

def verify_output(path):
    return os.path.exists(path)

def main():
    args = parse_args()
    verbose = getattr(args, 'verbose', False)
    sched_name, jobs = normalize_event_jobs(args, verbose=verbose)
    summary = {
        'schedule_name': sched_name or 'Batch Run',
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'events': []
    }
    exit_code = 0
    batch_stats = {'total': 0, 'succeeded': 0, 'failed': 0, 'warnings': 0, 'skipped_existing': 0, 'skipped_metadata_only': 0}
    csv_rows = []
    for job in jobs:
        event_id = job['event_id']
        formats = job['formats']
        log("[LOAD] Event: {}", event_id, verbose=verbose)
        valid, msg, event = validate_event_file(event_id)
        event_status = 'success'
        if valid is None:
            # Metadata-only event (missing event file or empty bouts)
            log("[VALIDATE] {}: {} (metadata-only, skipped)", event_id, msg, verbose=verbose)
            event_summary = {
                'event_id': event_id,
                'title': '',
                'bouts_total': 0,
                'resolved_bouts': 0,
                'tba_bouts': 0,
                'stubs_created': [],
                'formats': {fmt: {'status': 'skipped_metadata_only', 'output_path': '', 'elapsed_seconds': 0, 'exit_code': 0} for fmt in formats},
                'validation_status': 'skipped_metadata_only',
                'event_status': 'skipped_metadata_only'
            }
            summary['events'].append(event_summary)
            for fmt in formats:
                csv_rows.append({
                    'schedule_name': sched_name or 'Batch Run',
                    'event_id': event_id,
                    'title': '',
                    'format': fmt,
                    'status': 'skipped_metadata_only',
                    'output_path': '',
                    'exit_code': 0,
                    'elapsed_seconds': 0,
                    'bouts_total': 0,
                    'resolved_bouts': 0,
                    'tba_bouts': 0,
                    'stubs_created_count': 0,
                    'event_status': 'skipped_metadata_only'
                })
            batch_stats['skipped_metadata_only'] += 1
            batch_stats['total'] += 1
            continue
        if not valid:
            log("[VALIDATE] {}: {}", event_id, msg, verbose=verbose)
            event_summary = {
                'event_id': event_id,
                'title': '',
                'bouts_total': 0,
                'resolved_bouts': 0,
                'tba_bouts': 0,
                'stubs_created': [],
                'formats': {fmt: {'status': 'failed', 'output_path': '', 'elapsed_seconds': 0, 'exit_code': 1} for fmt in formats},
                'validation_status': 'failed',
                'event_status': 'failed'
            }
            summary['events'].append(event_summary)
            for fmt in formats:
                csv_rows.append({
                    'schedule_name': sched_name or 'Batch Run',
                    'event_id': event_id,
                    'title': '',
                    'format': fmt,
                    'status': 'failed',
                    'output_path': '',
                    'exit_code': 1,
                    'elapsed_seconds': 0,
                    'bouts_total': 0,
                    'resolved_bouts': 0,
                    'tba_bouts': 0,
                    'stubs_created_count': 0,
                    'event_status': 'failed'
                })
            exit_code = 1
            batch_stats['failed'] += 1
            batch_stats['total'] += 1
            continue
        bouts = event['bouts']
        tba_bouts = 0
        resolved_bouts = 0
        stubs_created = []
        main_event_idx = next((i for i, b in enumerate(bouts) if b.get('main_event')), 0)
        for i, bout in enumerate(bouts):
            fighters = bout.get('fighters', [])
            if len(fighters) != 2 or not all(f and isinstance(f, str) for f in fighters):
                tba_bouts += 1
                continue
            if is_tba_name(fighters[0]) or is_tba_name(fighters[1]):
                tba_bouts += 1
                continue
            resolved_bouts += 1
            if args.create_missing_stubs and (not args.main_event_only_stubs or i == main_event_idx):
                deps = derive_bout_dependencies(fighters[0], fighters[1])
                created = create_stub_files(deps, fighters[0], fighters[1], not args.main_event_only_stubs, args.dry_run, verbose=verbose)
                stubs_created.extend(created)
        event_summary = {
            'event_id': event_id,
            'title': event.get('event', ''),
            'bouts_total': len(bouts),
            'resolved_bouts': resolved_bouts,
            'tba_bouts': tba_bouts,
            'stubs_created': stubs_created,
            'formats': {},
            'validation_status': 'success',
            'event_status': '',
        }
        event_failed = False
        event_warning = False
        for fmt in formats:
            out_path = f'C:/ai_risa_data/reports/{event_id}_full_prim_report.{fmt if fmt != "md" else "md"}'
            if args.skip_existing and verify_output(out_path):
                log("[RUN] {} {}: skipped_existing (already exists)", event_id, fmt, verbose=verbose)
                event_summary['formats'][fmt] = {
                    'status': 'skipped_existing',
                    'output_path': out_path,
                    'elapsed_seconds': 0,
                    'exit_code': 0
                }
                csv_rows.append({
                    'schedule_name': sched_name or 'Batch Run',
                    'event_id': event_id,
                    'title': event.get('event', ''),
                    'format': fmt,
                    'status': 'skipped_existing',
                    'output_path': out_path,
                    'exit_code': 0,
                    'elapsed_seconds': 0,
                    'bouts_total': len(bouts),
                    'resolved_bouts': resolved_bouts,
                    'tba_bouts': tba_bouts,
                    'stubs_created_count': len(stubs_created),
                    'event_status': 'skipped_existing'
                })
                batch_stats['skipped_existing'] += 1
                continue
            rc, stdout, stderr, out_path, elapsed = run_format(event_id, fmt, args.dry_run, verbose=verbose)
            if rc == 0 and verify_output(out_path):
                status = 'success' if not stderr.strip() else 'warning'
                if status == 'warning':
                    event_warning = True
                log("[RUN] {} {}: {} ({:.1f}s)", event_id, fmt, status.upper(), elapsed, verbose=verbose)
                event_summary['formats'][fmt] = {
                    'status': status,
                    'output_path': out_path,
                    'elapsed_seconds': round(elapsed, 2),
                    'exit_code': rc
                }
                csv_rows.append({
                    'schedule_name': sched_name or 'Batch Run',
                    'event_id': event_id,
                    'title': event.get('event', ''),
                    'format': fmt,
                    'status': status,
                    'output_path': out_path,
                    'exit_code': rc,
                    'elapsed_seconds': round(elapsed, 2),
                    'bouts_total': len(bouts),
                    'resolved_bouts': resolved_bouts,
                    'tba_bouts': tba_bouts,
                    'stubs_created_count': len(stubs_created),
                    'event_status': status
                })
                if status == 'success':
                    batch_stats['succeeded'] += 1
                else:
                    batch_stats['warnings'] += 1
            else:
                log("[RUN] {} {}: FAILED (rc={})", event_id, fmt, rc, always=True)
                event_summary['formats'][fmt] = {
                    'status': 'failed',
                    'output_path': out_path,
                    'elapsed_seconds': round(elapsed, 2),
                    'exit_code': rc
                }
                csv_rows.append({
                    'schedule_name': sched_name or 'Batch Run',
                    'event_id': event_id,
                    'title': event.get('event', ''),
                    'format': fmt,
                    'status': 'failed',
                    'output_path': out_path,
                    'exit_code': rc,
                    'elapsed_seconds': round(elapsed, 2),
                    'bouts_total': len(bouts),
                    'resolved_bouts': resolved_bouts,
                    'tba_bouts': tba_bouts,
                    'stubs_created_count': len(stubs_created),
                    'event_status': 'failed'
                })
                event_failed = True
                exit_code = 1
                batch_stats['failed'] += 1
        if event_failed:
            event_summary['event_status'] = 'failed'
        elif event_warning:
            event_summary['event_status'] = 'warning'
        else:
            event_summary['event_status'] = 'success'
        summary['events'].append(event_summary)
        batch_stats['total'] += 1
        # Console summary
        log("[SUMMARY] EVENT: {}", event_id, verbose=verbose, always=True)
        log("[SUMMARY] Title: {}", event.get('event', ''), verbose=verbose, always=True)
        log("[SUMMARY] Bouts: {} | Resolved: {} | TBA: {} | Stubs created: {}", len(bouts), resolved_bouts, tba_bouts, len(stubs_created), verbose=verbose, always=True)
        for fmt, fmtdata in event_summary['formats'].items():
            log("[SUMMARY] {}: {}", fmt, fmtdata['status'].upper(), verbose=verbose, always=True)
        log("", always=True)
    # Unified summary schema
    started_at = datetime.now().isoformat()
    finished_at = datetime.now().isoformat()
    status = "success"
    warnings = []
    errors = []
    artifacts = []
    # Add summary and CSV to artifacts
    if args.summary_json:
        artifacts.append(args.summary_json)
    if args.summary_csv:
        artifacts.append(args.summary_csv)
    # Optionally add generated report files if tracked in csv_rows
    for row in csv_rows:
        if row.get('output_path'):
            artifacts.append(row['output_path'])
    # Map counts
    counts = {
        'total_events': batch_stats['total'],
        'succeeded': batch_stats['succeeded'],
        'failed': batch_stats['failed'],
        'skipped_metadata_only': batch_stats['skipped_metadata_only'],
        'warnings': batch_stats['warnings'],
        'skipped_existing': batch_stats['skipped_existing'],
        'dry_run': int(getattr(args, 'dry_run', False)),
    }
    # Warnings: metadata-only, missing-bouts
    for row in csv_rows:
        if row['status'] == 'skipped_metadata_only':
            warnings.append({'event_id': row['event_id'], 'type': 'skipped_metadata_only'})
        if row['tba_bouts'] > 0:
            warnings.append({'event_id': row['event_id'], 'type': 'missing_bouts', 'count': row['tba_bouts']})
    # Errors: true runnable-event failures
    for row in csv_rows:
        if row['status'] == 'failed':
            errors.append({'event_id': row['event_id'], 'type': 'event_failed'})
    warning_type_counts = {}
    for warning in warnings:
        wtype = warning.get('type') or 'unspecified'
        warning_type_counts[wtype] = warning_type_counts.get(wtype, 0) + 1

    exclusions_rollup = {
        'skipped_metadata_only': counts.get('skipped_metadata_only', 0),
        'skipped_existing': counts.get('skipped_existing', 0),
        'missing_bouts_total': sum(int(w.get('count', 0) or 0) for w in warnings if w.get('type') == 'missing_bouts'),
    }

    if errors:
        interpretation_note = 'Batch run contains event-level failures. Review errors before using generated outputs.'
    elif warnings:
        interpretation_note = 'Batch run completed with non-fatal warnings. Some events were skipped or had coverage limits.'
    else:
        interpretation_note = 'Batch run completed without warnings. All scheduled events were analyzed as configured.'

    summary_payload = {
        "stage": "batch",
        "status": status if not errors else "error",
        "started_at": started_at,
        "finished_at": finished_at,
        "counts": counts,
        "warnings": warnings,
        "errors": errors,
        "artifacts": artifacts,
        "details": {
            "rows": csv_rows,
            "events": summary.get('events', []),
            "analysis_coverage": {
                "events_total": counts.get('total_events', 0),
                "events_analyzed": max(counts.get('total_events', 0) - counts.get('skipped_metadata_only', 0), 0),
                "events_skipped_metadata_only": counts.get('skipped_metadata_only', 0),
            },
            "skipped_items_exclusions": {
                "warning_type_counts": warning_type_counts,
                "reason_rollup": exclusions_rollup,
            },
            "operator_interpretation": {
                "note": interpretation_note,
                "warning_non_fatal": bool(warnings and not errors),
            },
        }
    }
    # Write unified summary JSON
    if args.summary_json:
        outdir = os.path.dirname(args.summary_json)
        if outdir:
            os.makedirs(outdir, exist_ok=True)
        with open(args.summary_json, 'w', encoding='utf-8') as f:
            json.dump(summary_payload, f, indent=2, ensure_ascii=False)
    # Write CSV summary (unchanged)
    if args.summary_csv:
        import csv
        outdir = os.path.dirname(args.summary_csv)
        if outdir:
            os.makedirs(outdir, exist_ok=True)
        fieldnames = ['schedule_name','event_id','title','format','status','output_path','exit_code','elapsed_seconds','bouts_total','resolved_bouts','tba_bouts','stubs_created_count','event_status']
        with open(args.summary_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in csv_rows:
                writer.writerow(row)
    # Batch summary
    log("[BATCH SUMMARY]", always=True)
    log("Total events: {}", batch_stats['total'], always=True)
    log("Succeeded: {}", batch_stats['succeeded'], always=True)
    log("Failed: {}", batch_stats['failed'], always=True)
    log("Warnings: {}", batch_stats['warnings'], always=True)
    log("Skipped existing: {}", batch_stats['skipped_existing'], always=True)
    log("Skipped metadata-only: {}", batch_stats['skipped_metadata_only'], always=True)
    # Only set exit_code=1 if there was a real failure (not just metadata-only skips)
    if batch_stats['failed'] == 0:
        exit_code = 0
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
