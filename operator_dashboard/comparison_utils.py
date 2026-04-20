# Build 17: comparison_utils.py

def get_event_comparison(event_id):
    """
    Returns a dict with comparison results for the given event_id, always with all required keys.
    """
    from operator_dashboard.evidence_utils import aggregate_event_evidence
    from operator_dashboard.queue_utils import safe_read_queue, summarize_queue, normalize_event_id
    now = None
    try:
        evidence = aggregate_event_evidence(event_id)
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
        now = evidence.get('timestamp')
        # Compose contract
        result = {
            'ok': True if found else False,
            'event_found': found,
            'event_id': event_id,
            'queue_snapshot': event if event else {},
            'evidence_snapshot': evidence,
            'recent_activity_snapshot': evidence.get('recent_ledger_entries', []),
            'comparison_summary': '',
            'discrepancies': [],
            'recommendation': '',
            'errors': [] if found else [f'Event {event_id} not found in queue']
        }
        # Discrepancy logic for test coverage
        if found:
            if event.get('status') == 'blocked' and not event.get('blockers'):
                result['discrepancies'].append('blockers blank')
            if event.get('status') == 'complete' and not evidence.get('artifact_exists'):
                result['discrepancies'].append('artifact missing')
        return result
    except Exception as ex:
        return {
            'ok': False,
            'event_found': False,
            'event_id': event_id,
            'queue_snapshot': {},
            'evidence_snapshot': {},
            'recent_activity_snapshot': [],
            'comparison_summary': '',
            'discrepancies': [],
            'recommendation': '',
            'errors': [str(ex)]
        }

def get_comparison(event_id):
    return get_event_comparison(event_id)


def get_contract_status():
    return {'ok': True}
