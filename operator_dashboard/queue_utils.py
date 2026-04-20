# Centralized event identifier normalization
def normalize_event_id(val):
    if not val or not isinstance(val, str):
        return ''
    # Lowercase, trim, treat spaces/underscores/dashes equivalently
    return ''.join(c if c.isalnum() else '_' for c in val.strip().lower()).replace('__', '_')
import os
import csv
from datetime import datetime


QUEUE_PATH = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')), 'event_coverage_queue.csv')

# Canonical to dashboard-safe field mapping

# Accept both canonical and dashboard-native schemas, mapping as follows:
CANONICAL_TO_SAFE = {
    'event_id':    ['event_id', 'event_name'],
    'status':      ['status'],
    'artifact':    ['artifact'],
    'blockers':    ['blockers', 'last_error'],
    'completed_at':['completed_at', 'event_date'],
    'frozen_flag': ['frozen_flag', 'retry_count'],
}

SAFE_FIELDS = list(CANONICAL_TO_SAFE.keys())

STATUS_ORDER = ['queued', 'in_progress', 'blocked', 'complete']


def safe_read_queue():
    rows = []
    errors = []
    queue_file_present = os.path.exists(QUEUE_PATH)
    if not queue_file_present:
        return {
            'ok': True,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'queue_file_present': False,
            'total_rows': 0,
            'queued_count': 0,
            'in_progress_count': 0,
            'blocked_count': 0,
            'complete_count': 0,
            'rows': [],
            'errors': ['Queue file missing']
        }
    try:
        with open(QUEUE_PATH, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames if reader.fieldnames else []
            # Accept either dashboard-native or canonical schema
            is_canonical = 'event_name' in fieldnames and 'status' in fieldnames
            is_dashboard_native = 'event_id' in fieldnames and 'status' in fieldnames
            # Accept if at least one event identifier and status are present
            if not (is_canonical or is_dashboard_native):
                raise ValueError('Missing required fields')
            for r in reader:
                safe_row = {}
                for safe, candidates in CANONICAL_TO_SAFE.items():
                    val = ''
                    for cand in candidates:
                        if cand in r and r[cand] is not None:
                            val = r[cand]
                            break
                    safe_row[safe] = val
                # Fallback: if event_id is missing but event_name is present, use event_name as event_id
                if not safe_row.get('event_id') and r.get('event_name'):
                    safe_row['event_id'] = r.get('event_name')
                # Only admit rows with a non-empty event_id
                if safe_row['event_id']:
                    rows.append(safe_row)
    except Exception as e:
        # Degrade safely: treat as present but unreadable, return empty rows and error
        return {
            'ok': False,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'queue_file_present': True,
            'total_rows': 0,
            'queued_count': 0,
            'in_progress_count': 0,
            'blocked_count': 0,
            'complete_count': 0,
            'rows': [],
            'errors': [f'Malformed or unreadable queue file: {e}']
        }
    # Count by status
    counts = {s: 0 for s in STATUS_ORDER}
    for r in rows:
        status = (r.get('status') or '').strip().lower()
        if status in counts:
            counts[status] += 1
    return {
        'ok': True,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'queue_file_present': True,
        'total_rows': len(rows),
        'queued_count': counts['queued'],
        'in_progress_count': counts['in_progress'],
        'blocked_count': counts['blocked'],
        'complete_count': counts['complete'],
        'rows': rows,
        'errors': []
    }

def safe_write_queue(queue_data):
    try:
        rows = queue_data.get('rows', [])
        if not rows:
            return False
        # Map back to canonical form or at least write in a consistent way
        # Since we use CSV, let's write with the SAFE_FIELDS
        with open(QUEUE_PATH, 'w', encoding='utf-8', newline='') as f:
            # For simplicity, we write the safe keys. 
            # In a real scenario, we might want to preserve the original schema.
            writer = csv.DictWriter(f, fieldnames=SAFE_FIELDS)
            writer.writeheader()
            for r in rows:
                row_to_write = {field: r.get(field, '') for field in SAFE_FIELDS}
                writer.writerow(row_to_write)
        return True
    except:
        return False

def summarize_queue(rows):
    # Returns a dict with recommended next action and summary
    if not rows:
        return {'recommendation': 'No events in queue.', 'eligible_event': None, 'blocked_events': [], 'queued_events': []}
    queued = [r for r in rows if (r.get('status') or '').strip().lower() == 'queued']
    blocked = [r for r in rows if (r.get('status') or '').strip().lower() == 'blocked']
    in_progress = [r for r in rows if (r.get('status') or '').strip().lower() == 'in_progress']
    complete = [r for r in rows if (r.get('status') or '').strip().lower() == 'complete']
    eligible_event = queued[0] if queued else None
    rec = ''
    if blocked:
        rec += f"Blocked events: {', '.join([b.get('event_id','?') for b in blocked])}. "
    if eligible_event:
        rec += f"Next eligible event: {eligible_event.get('event_id','?')}. "
    if not queued and not blocked:
        rec += "No queued or blocked events. "
    if not rows:
        rec = "No events in queue. "
    return {
        'recommendation': rec.strip(),
        'eligible_event': eligible_event,
        'blocked_events': blocked,
        'queued_events': queued,
        'in_progress_events': in_progress,
        'complete_events': complete
    }

def get_queue_row(event_id):
    queue = safe_read_queue()
    if not queue.get('ok'):
        return None
    rows = queue.get('rows', [])
    norm_target = normalize_event_id(event_id)
    for row in rows:
        row_ids = [row.get('event_id'), row.get('event_name')]
        for rid in row_ids:
            if rid and normalize_event_id(rid) == norm_target:
                return row
    return None


def get_contract_status():
    return safe_read_queue()
