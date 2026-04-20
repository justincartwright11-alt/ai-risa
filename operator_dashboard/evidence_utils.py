import os
import operator_dashboard.safe_path_utils as safe_path_utils
from operator_dashboard.action_ledger_utils import safe_read_ledger
from operator_dashboard.queue_utils import QUEUE_PATH, CANONICAL_TO_SAFE
from datetime import datetime

APPROVED_RECORD_DIRS = ['artifacts', 'docs', 'outputs', 'results']
MAX_LEDGER_ENTRIES = 5

# Helper: Map queue row to evidence dict
def queue_row_to_evidence(row):
    evidence = {}
    if not row:
        # Degrade safely if row is None
        for safe_field in CANONICAL_TO_SAFE:
            evidence[safe_field] = ''
        evidence['artifact_exists'] = False
        evidence['artifact_safe'] = False
        return evidence
    for safe_field in CANONICAL_TO_SAFE:
        evidence[safe_field] = row.get(safe_field, '')
    # Artifact existence/safety
    artifact = evidence.get('artifact', '')
    safe, resolved = safe_path_utils.is_safe_artifact_path(artifact)
    evidence['artifact_exists'] = bool(safe and os.path.exists(resolved) if safe else False)
    evidence['artifact_safe'] = safe
    return evidence

# Helper: Get recent ledger entries for event_id
def get_recent_ledger_entries(event_id):
    try:
        ledger = safe_read_ledger()
        entries = [e for e in ledger if e.get('event_id', '').lower() == event_id.lower()]
        entries = sorted(entries, key=lambda e: e.get('timestamp', ''), reverse=True)
        return entries[:MAX_LEDGER_ENTRIES]
    except Exception:
        return []

# Helper: Resolve approved record links for event
def get_approved_record_links(event_id, artifact_path=None):
    links = []
    # Add artifact if safe
    if artifact_path:
        safe, resolved = safe_path_utils.is_safe_artifact_path(artifact_path)
        if safe and os.path.exists(resolved):
            links.append({'label': 'Artifact', 'path': resolved})
    # Add docs/outputs/results if present
    for d in APPROVED_RECORD_DIRS:
        base = os.path.join(os.path.dirname(QUEUE_PATH), d)
        if os.path.exists(base):
            for fname in os.listdir(base):
                if event_id.lower() in fname.lower():
                    fpath = os.path.join(base, fname)
                    safe, resolved = safe_path_utils.is_safe_artifact_path(os.path.relpath(fpath, os.path.dirname(__file__)))
                    if safe and os.path.exists(resolved):
                        links.append({'label': fname, 'path': resolved})
    return links

def register_event_evidence(event_id, evidence):
    # For now, let's just log it in the action ledger
    from operator_dashboard.action_ledger_utils import safe_write_action
    safe_write_action(event_id, 'REGISTER_EVIDENCE', f'Evidence registered: {evidence}')

def get_event_evidence(event_id):
    return aggregate_event_evidence(event_id)

def aggregate_event_evidence(event_id):
    from operator_dashboard.queue_utils import safe_read_queue, summarize_queue, normalize_event_id
    now = datetime.utcnow().isoformat() + 'Z'
    queue = safe_read_queue()
    rows = queue.get('rows', [])
    norm_target = normalize_event_id(event_id)
    event = None
    for r in rows:
        row_ids = [r.get('event_id'), r.get('event_name')]
        for rid in row_ids:
            if rid and normalize_event_id(rid) == norm_target:
                event = r
                break
        if event:
            break
    found = event is not None
    errors = []
    evidence = {
        'ok': True,  # Always True for safe miss contract
        'timestamp': now,
        'event_found': found,
        'event_id': event_id,
        'status': None,
        'blockers': None,
        'artifact': None,
        'artifact_exists': False,
        'artifact_safe': False,
        'completed_at': None,
        'frozen_flag': None,
        'recent_ledger_entries': [],
        'approved_record_links': [],
        'recommendation': '',
        'errors': []
    }
    if found:
        mapped = queue_row_to_evidence(event)
        for k in ['status','blockers','artifact','artifact_exists','artifact_safe','completed_at','frozen_flag']:
            evidence[k] = mapped.get(k)
        # Robust ledger handling: always return a list, empty on error or malformed
        try:
            entries = get_recent_ledger_entries(event_id)
            if not isinstance(entries, list):
                entries = []
            evidence['recent_ledger_entries'] = entries
        except Exception:
            evidence['recent_ledger_entries'] = []
        evidence['approved_record_links'] = get_approved_record_links(event_id, mapped.get('artifact'))
        evidence['recommendation'] = summarize_queue([event]).get('recommendation','')
        evidence['errors'] = []
        evidence['ok'] = True
    else:
        # Contract: miss returns ok=False, event_found=False, errors populated, all required fields present
        evidence['ok'] = False
        evidence['event_found'] = False
        evidence['event_id'] = event_id
        evidence['recent_ledger_entries'] = []
        evidence['errors'] = [f'Event {event_id} not found in queue']
        for k in ['status','blockers','artifact','artifact_exists','artifact_safe','completed_at','frozen_flag','approved_record_links','recommendation']:
            evidence[k] = None if k not in ['artifact_exists','artifact_safe'] else False
        evidence['approved_record_links'] = []
        evidence['recommendation'] = ''
    # Always ensure required fields are present and correct types
    if 'recent_ledger_entries' not in evidence or not isinstance(evidence['recent_ledger_entries'], list):
        evidence['recent_ledger_entries'] = []
    if 'errors' not in evidence or not isinstance(evidence['errors'], list):
        evidence['errors'] = []
    return evidence


def get_contract_status():
    return {'ok': True}
