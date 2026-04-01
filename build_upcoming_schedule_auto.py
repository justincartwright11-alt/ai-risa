import argparse
import json
import os
import sys
import re
from datetime import datetime
from typing import List, Dict, Any

try:
    import yaml
except ImportError:
    yaml = None

def parse_args():
    parser = argparse.ArgumentParser(description="AI-RISA Event Discovery & Normalization Layer")
    parser.add_argument('--source', required=True, help='Source file (JSON or YAML)')
    parser.add_argument('--schedule-out', required=True, help='Output schedule JSON path')
    parser.add_argument('--events-dir', required=True, help='Directory for starter event JSONs')
    parser.add_argument('--summary-json', help='Discovery summary JSON output')
    parser.add_argument('--summary-csv', help='Discovery summary CSV output')
    parser.add_argument('--create-missing-stubs', action='store_true')
    parser.add_argument('--main-event-only-stubs', action='store_true')
    parser.add_argument('--launch-batch', action='store_true')
    parser.add_argument('--formats', nargs='*', default=['md', 'docx', 'pdf'])
    parser.add_argument('--strict', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--overwrite', action='store_true')
    parser.add_argument('--write-events', action='store_true', help='Write starter event JSONs')
    parser.add_argument('--write-schedule', action='store_true', help='Write schedule JSON')
    parser.add_argument('--batch-runner', default='C:/ai_risa_data/run_event_batch_auto.py')
    parser.add_argument('--fighters-dir', default='C:/ai_risa_data/fighters')
    parser.add_argument('--matchups-dir', default='C:/ai_risa_data/matchups')
    parser.add_argument('--predictions-dir', default='C:/ai_risa_data/predictions')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    return parser.parse_args()
def log(msg, *args, verbose=False, always=False, file=None):
    if always or verbose:
        print(msg.format(*args), flush=True, file=file)

def load_source_file(path, verbose=False):
    ext = os.path.splitext(path)[1].lower()
    with open(path, 'r', encoding='utf-8') as f:
        if ext in ['.yaml', '.yml']:
            if not yaml:
                log('[SOURCE] PyYAML not installed', verbose=verbose, always=True, file=sys.stderr)
                sys.exit(2)
            return yaml.safe_load(f)
        return json.load(f)

def slugify(text):
    text = re.sub(r'[^\w\s-]', '', text, flags=re.UNICODE)
    text = re.sub(r'\s+', '_', text.strip().lower())
    text = re.sub(r'_+', '_', text)
    return text.strip('_')

def strip_record_from_name(name):
    return re.sub(r'\s*\([^)]*\)', '', name).strip()

def build_event_id(event):
    promo = slugify(event.get('promotion', 'unknown'))
    name_raw = event.get('event_name', event.get('title', 'event'))
    name_slug = slugify(name_raw)
    # Remove redundant promotion prefix from event name slug
    if name_slug.startswith(promo + '_'):
        name_slug = name_slug[len(promo) + 1:]
    # Convert date to YYYY_MM_DD
    date = (event.get('date', 'unknown') or '').replace('-', '_')
    return f"{promo}_{name_slug}_{date}"

def normalize_event(raw_event):
    event = {}
    event['promotion'] = str(raw_event.get('promotion', '') or '').strip() or 'Unknown'
    event['event_name'] = str(raw_event.get('event_name', raw_event.get('title', '')) or '').strip() or 'Unknown'
    event['date'] = str(raw_event.get('date', '') or '').strip()
    event['city'] = str(raw_event.get('city', '') or '').strip()
    event['region'] = str(raw_event.get('region', '') or '').strip()
    event['country'] = str(raw_event.get('country', '') or '').strip()
    venue_val = raw_event.get('venue', raw_event.get('location', ''))
    event['venue'] = str(venue_val or '').strip()
    event['status'] = raw_event.get('status', 'scheduled')
    event['bouts'] = []
    event['main_event'] = None
    bouts = raw_event.get('bouts', [])
    for i, bout in enumerate(bouts):
        f1 = strip_record_from_name(bout.get('fighter_1', bout.get('red', '')))
        f2 = strip_record_from_name(bout.get('fighter_2', bout.get('blue', '')))
        is_main = bout.get('is_main_event', bout.get('main_event', False)) or (i == 0)
        bout_obj = {
            'bout_id': None,  # to be filled after event_id is known
            'card_segment': 'main' if is_main else 'undercard',
            'bout_order': i + 1,
            'fighter_1': f1,
            'fighter_2': f2,
            'fighter_1_id': None,
            'fighter_2_id': None,
            'matchup_id': None,
            'prediction_id': None,
            'is_main_event': is_main,
            'is_title_fight': bout.get('is_title_fight', False),
            'status': bout.get('status', 'scheduled')
        }
        event['bouts'].append(bout_obj)
        if is_main:
            event['main_event'] = bout_obj
    return event

def build_event_json(event, event_id, verbose=False):
    for i, bout in enumerate(event['bouts']):
        bout['bout_id'] = f"{event_id}_{'main' if bout['is_main_event'] else 'undercard'}_{str(bout['bout_order']).zfill(2)}"
    if not event['bouts']:
        log("[WARNING] Event '{}' has an empty bouts list. main_event_bout_id set to None.", event.get('event_name', event_id), verbose=verbose, always=True, file=sys.stderr)
        main_event_bout_id = None
    else:
        main_bout = next((b for b in event['bouts'] if b['is_main_event']), event['bouts'][0])
        main_event_bout_id = main_bout['bout_id']
    return {
        'event_id': event_id,
        'promotion': event['promotion'],
        'event_name': event['event_name'],
        'date': event['date'],
        'location': {
            'venue': event['venue'],
            'city': event['city'],
            'region': event['region'],
            'country': event['country']
        },
        'status': event['status'],
        'main_event_bout_id': main_event_bout_id,
        'bouts': event['bouts'],
        'source_meta': {
            'generated_by': 'build_upcoming_schedule_auto.py'
        }
    }

def build_schedule_json(events, schedule_name, formats):
    return {
        'schedule_name': schedule_name,
        'generated_at': datetime.now().isoformat(),
        'generated_by': 'build_upcoming_schedule_auto.py',
        'events': [
            {
                'event_id': e['event_id'],
                'event_json': e['event_json'],
                'formats': formats
            } for e in events
        ]
    }

def detect_dependency_gaps(event_json, base_dirs):
    gaps = []
    for bout in event_json['bouts']:
        f1 = bout['fighter_1']
        f2 = bout['fighter_2']
        if not f1 or not f2 or f1.lower() == 'tba' or f2.lower() == 'tba':
            gaps.append({'bout_id': bout['bout_id'], 'gap_type': 'tba', 'detail': 'TBA participant', 'severity': 'info'})
            continue
        slug1 = slugify(f1)
        slug2 = slugify(f2)
        fighter1_path = os.path.join(base_dirs['fighters'], f'{slug1}.json')
        fighter2_path = os.path.join(base_dirs['fighters'], f'{slug2}.json')
        matchup_path = os.path.join(base_dirs['matchups'], f'{slug1}_vs_{slug2}.json')
        prediction_path = os.path.join(base_dirs['predictions'], f'{slug1}_vs_{slug2}_prediction.json')
        if not os.path.exists(fighter1_path):
            gaps.append({'bout_id': bout['bout_id'], 'gap_type': 'missing_fighter_profile', 'detail': f'Missing {fighter1_path}', 'severity': 'warning'})
        if not os.path.exists(fighter2_path):
            gaps.append({'bout_id': bout['bout_id'], 'gap_type': 'missing_fighter_profile', 'detail': f'Missing {fighter2_path}', 'severity': 'warning'})
        if not os.path.exists(matchup_path):
            gaps.append({'bout_id': bout['bout_id'], 'gap_type': 'missing_matchup', 'detail': f'Missing {matchup_path}', 'severity': 'warning'})
        if not os.path.exists(prediction_path):
            gaps.append({'bout_id': bout['bout_id'], 'gap_type': 'missing_prediction', 'detail': f'Missing {prediction_path}', 'severity': 'warning'})
    return gaps

def write_json(path, data, dry_run=False, verbose=False):
    if dry_run:
        log('[WRITE] (dry-run) Would write: {}', path, verbose=verbose, always=True)
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    log('[WRITE] {}', path, verbose=verbose, always=True)

def write_summary_json(path, data, dry_run=False):
    write_json(path, data, dry_run)

def write_summary_csv(path, rows, dry_run=False, verbose=False):
    import csv
    if dry_run:
        log('[WRITE] (dry-run) Would write: {}', path, verbose=verbose, always=True)
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='') as f:
        if rows:
            fieldnames = list(rows[0].keys())
        else:
            fieldnames = [
                'event_id',
                'event_file',
                'event_file_status',
                'bouts_total',
                'tba_bouts',
                'missing_fighters_count',
                'missing_matchups_count',
                'missing_predictions_count',
                'main_event_runnable',
                'stubs_created_count',
                'status',
            ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    log('[WRITE] {}', path, verbose=verbose, always=True)

def maybe_create_main_event_stub(event_json, args):
    # Only create stubs if enabled
    if not args.create_missing_stubs:
        return []
    stubs = []
    main_bout = next((b for b in event_json['bouts'] if b['is_main_event']), None)
    if not main_bout:
        return []
    f1 = main_bout['fighter_1']
    f2 = main_bout['fighter_2']
    if not f1 or not f2 or f1.lower() == 'tba' or f2.lower() == 'tba':
        return []
    slug1 = slugify(f1)
    slug2 = slugify(f2)
    fighter1_path = os.path.join(args.fighters_dir, f'{slug1}.json')
    fighter2_path = os.path.join(args.fighters_dir, f'{slug2}.json')
    matchup_path = os.path.join(args.matchups_dir, f'{slug1}_vs_{slug2}.json')
    prediction_path = os.path.join(args.predictions_dir, f'{slug1}_vs_{slug2}_prediction.json')
    stub_template = {
        'fighter': {
            "name": None, "sport": "MMA", "division": "Unknown", "stance": "Orthodox", "style": "Unknown", "team": "", "notes": "Auto-generated stub from discovery layer."
        },
        'matchup': {
            "fighters": [f1, f2], "weight_class": "Unknown", "sport": "MMA"
        },
        'prediction': {
            "winner": f1, "method": "Decision", "confidence": 0.55
        }
    }
    for path, content in [
        (fighter1_path, {**stub_template['fighter'], 'name': f1}),
        (fighter2_path, {**stub_template['fighter'], 'name': f2}),
        (matchup_path, stub_template['matchup']),
        (prediction_path, stub_template['prediction'])
    ]:
        if not os.path.exists(path):
            write_json(path, content, args.dry_run)
            stubs.append(path)
    return stubs

def maybe_launch_batch_runner(schedule_path, args, verbose=False):
    if not args.launch_batch:
        return None
    import subprocess
    cmd = [sys.executable, args.batch_runner, '--schedule', schedule_path, '--formats'] + args.formats
    if args.strict:
        cmd.append('--strict')
    if args.create_missing_stubs:
        cmd.append('--create-missing-stubs')
    if args.main_event_only_stubs:
        cmd.append('--main-event-only-stubs')
    log('[BATCH] Launching: {}', " ".join(cmd), verbose=verbose, always=True)
    rc = subprocess.call(cmd)
    log('[BATCH] Exit code: {}', rc, verbose=verbose, always=True)
    return rc

def main():
    args = parse_args()
    verbose = args.verbose
    try:
        source_data = load_source_file(args.source, verbose=verbose)
    except Exception as e:
        log('[SOURCE] Failed to load source: {}', e, verbose=verbose, always=True, file=sys.stderr)
        sys.exit(2)
    if isinstance(source_data, dict) and 'events' in source_data:
        raw_events = source_data['events']
    elif isinstance(source_data, list):
        raw_events = source_data
    else:
        log('[SOURCE] Invalid source format', verbose=verbose, always=True, file=sys.stderr)
        sys.exit(2)
    normalized_events = []
    event_jsons = []
    summary_rows = []
    base_dirs = {'fighters': args.fighters_dir, 'matchups': args.matchups_dir, 'predictions': args.predictions_dir}
    for idx, raw_event in enumerate(raw_events):
        event = normalize_event(raw_event)
        event_id = build_event_id(event)
        event_json_path = os.path.join(args.events_dir, f'{event_id}.json')
        event_json = build_event_json(event, event_id, verbose=verbose)
        event_json['source_meta'].update({'origin_file': args.source, 'source_index': idx})
        gaps = detect_dependency_gaps(event_json, base_dirs)
        stubs_created = maybe_create_main_event_stub(event_json, args)
        event_file_status = 'written'
        if os.path.exists(event_json_path):
            event_file_status = 'existing_event_file'
            if args.strict:
                log('[EVENT] Existing event file in strict mode: {}', event_json_path, verbose=verbose, always=True, file=sys.stderr)
                sys.exit(2)
        if args.write_events and not args.dry_run:
            if not os.path.exists(event_json_path) or args.overwrite:
                write_json(event_json_path, event_json, args.dry_run, verbose=verbose)
        normalized_events.append({
            'event_id': event_id,
            'event_json': event_json_path
        })
        event_jsons.append(event_json)
        summary_rows.append({
            'event_id': event_id,
            'event_file': event_json_path,
            'event_file_status': event_file_status,
            'bouts_total': len(event_json['bouts']),
            'tba_bouts': sum(1 for b in event_json['bouts'] if not b['fighter_1'] or not b['fighter_2'] or b['fighter_1'].lower() == 'tba' or b['fighter_2'].lower() == 'tba'),
            'missing_fighters_count': sum(1 for g in gaps if g['gap_type'] == 'missing_fighter_profile'),
            'missing_matchups_count': sum(1 for g in gaps if g['gap_type'] == 'missing_matchup'),
            'missing_predictions_count': sum(1 for g in gaps if g['gap_type'] == 'missing_prediction'),
            'main_event_runnable': all(g['gap_type'] != 'tba' for g in gaps if g['bout_id'] == event_json['main_event_bout_id']),
            'stubs_created_count': len(stubs_created),
            'status': 'ready_with_gaps' if gaps else 'ready'
        })
        log('[EVENT] {} | {} | bouts: {} | tba: {} | missing: fighters={}, matchups={}, predictions={} | file: {} | main-event-runnable: {} | stubs: {}',
            event_id, event_json["event_name"], len(event_json["bouts"]), summary_rows[-1]["tba_bouts"], summary_rows[-1]["missing_fighters_count"], summary_rows[-1]["missing_matchups_count"], summary_rows[-1]["missing_predictions_count"], event_file_status, summary_rows[-1]["main_event_runnable"], len(stubs_created), verbose=verbose)
    schedule_name = os.path.splitext(os.path.basename(args.schedule_out))[0]
    schedule_json = build_schedule_json(normalized_events, schedule_name, args.formats)
    # Always write schedule if launching batch, regardless of --write-schedule
    if (args.write_schedule or args.launch_batch) and not args.dry_run:
        write_json(args.schedule_out, schedule_json, args.dry_run, verbose=verbose)
    # Unified summary schema
    started_at = datetime.now().isoformat()
    finished_at = None
    status = "success"
    warnings = []
    errors = []
    artifacts = []
    counts = {}
    # Collect artifact paths
    if args.write_schedule or args.launch_batch:
        artifacts.append(args.schedule_out)
    if args.summary_json:
        artifacts.append(args.summary_json)
    if args.summary_csv:
        artifacts.append(args.summary_csv)
    if args.write_events:
        for e in normalized_events:
            artifacts.append(e['event_json'])
    # Map counts
    counts['generated_events'] = len(normalized_events)
    counts['written_event_json'] = sum(1 for e in normalized_events if os.path.exists(e['event_json']))
    counts['written_schedule'] = int(os.path.exists(args.schedule_out))
    counts['missing_bouts'] = sum(1 for row in summary_rows if row['tba_bouts'] > 0)
    counts['dependency_gaps'] = sum(row['missing_fighters_count'] + row['missing_matchups_count'] + row['missing_predictions_count'] for row in summary_rows)
    # Warnings: metadata-only, missing-bouts, stub-creation
    for row in summary_rows:
        if row['tba_bouts'] > 0:
            warnings.append({'event_id': row['event_id'], 'type': 'missing_bouts', 'count': row['tba_bouts']})
        if row['stubs_created_count'] > 0:
            warnings.append({'event_id': row['event_id'], 'type': 'stubs_created', 'count': row['stubs_created_count']})
    # Errors: true failures (none in this pass, but placeholder)
    # Compose summary
    finished_at = datetime.now().isoformat()
    summary_payload = {
        "stage": "schedule",
        "status": status if not errors else "error",
        "started_at": started_at,
        "finished_at": finished_at,
        "counts": counts,
        "warnings": warnings,
        "errors": errors,
        "artifacts": artifacts,
        "details": {
            "rows": summary_rows,
            "events": normalized_events,
        }
    }
    if args.summary_json:
        write_summary_json(args.summary_json, summary_payload, args.dry_run)
    if args.summary_csv:
        write_summary_csv(args.summary_csv, summary_rows, args.dry_run, verbose=verbose)
    batch_exit_code = None
    if args.launch_batch:
        batch_exit_code = maybe_launch_batch_runner(args.schedule_out, args, verbose=verbose)
    if batch_exit_code is not None:
        log('[SUMMARY] Batch runner exit code: {}', batch_exit_code, verbose=verbose, always=True)
if __name__ == "__main__":
    main()
