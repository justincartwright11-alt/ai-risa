def get_recent_operator_actions(limit=5):
    # Build 19: Return recent operator actions for control summary
    entries = safe_read_ledger()
    # Only operator-visible actions (filter if needed)
    for e in entries:
        e['description'] = f"[{e.get('normalized_event','')}] {e.get('action','')} {e.get('user_message','')}"
    entries_sorted = sorted(entries, key=lambda x: x.get('timestamp',''), reverse=True)
    return entries_sorted[:limit]
# Build 17: action_ledger_utils.py
import os
import json
from datetime import datetime
import uuid

LEDGER_PATH = os.path.join(os.path.dirname(__file__), 'action_ledger.jsonl')
MAX_READ = 500

# Ledger entry fields:
# timestamp, correlation_id, action, normalized_event, user_message, outcome_status, response, error, details_summary

ALLOWED_OUTCOMES = {'started', 'succeeded', 'failed', 'clarification'}

def safe_read_ledger():
    entries = []
    try:
        if not os.path.exists(LEDGER_PATH):
            return []
        with open(LEDGER_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if isinstance(entry, dict):
                        entries.append(entry)
                except Exception:
                    continue
        return entries[-MAX_READ:]
    except Exception:
        return []

def append_ledger_entry(entry):
    try:
        with open(LEDGER_PATH, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    except Exception:
        pass

def make_entry(action, normalized_event, user_message, outcome_status, response, error=None, details_summary=None, correlation_id=None):
    return {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'correlation_id': correlation_id or str(uuid.uuid4()),
        'action': action or '',
        'normalized_event': normalized_event,
        'user_message': user_message or '',
        'outcome_status': outcome_status if outcome_status in ALLOWED_OUTCOMES else 'failed',
        'response': response or '',
        'error': error,
        'details_summary': details_summary or ''
    }

def aggregate_event_ledger(event_id):
    # Read all ledger entries for this event
    entries = [e for e in safe_read_ledger() if e.get('normalized_event') == event_id]
    return {
        'ok': True,
        'event_id': event_id,
        'ledger_entries': entries,
        'errors': []
    }

def get_recent_event_entries(event_id, max_count=10):
    entries = [e for e in safe_read_ledger() if (
        e.get('normalized_event') == event_id or e.get('event_id') == event_id
    )]
    return entries[-max_count:]

def get_ledger_object(event_id):
    entries = [e for e in safe_read_ledger() if e.get('normalized_event') == event_id]
    return {
        'event_id': event_id,
        'entries': entries,
        'last_updated': entries[-1]['timestamp'] if entries else None
    }

def summarize_ledger():
    entries = safe_read_ledger()
    return {
        'count': len(entries),
        'last_entry': entries[-1] if entries else None
    }

def get_recent_operator_actions(limit=10):
    entries = safe_read_ledger()
    return {
        'ok': True,
        'actions': entries[-limit:],
        'count': len(entries)
    }


def get_contract_status():
    return {'ok': True}
