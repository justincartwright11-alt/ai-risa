from operator_dashboard.action_ledger_utils import get_recent_event_entries
# Build 18: Portfolio requires aggregate_event_timeline
def register_event_timeline(event_id, timeline):
    from operator_dashboard.action_ledger_utils import safe_write_action
    # safe_write_action(event_id, 'REGISTER_TIMELINE', f'Timeline registered: {timeline}')
    pass

def get_event_timeline(event_id):
        entries = get_recent_event_entries(event_id, max_count=5)
        timeline = []
        for e in entries:
            if isinstance(e, dict):
                timeline.append({
                        'timestamp': e.get('timestamp'),
                        'action': e.get('action'),
                        'user_message': e.get('user_message'),
                        'outcome_status': e.get('outcome_status'),
                        'response': e.get('response'),
                })
        return {
                'ok': True,
                'event_found': bool(entries),
                'event_id': event_id,
                'timeline': timeline,
                'recent_ledger_entries': entries,
                'recommendation': 'Review timeline for recent actions.' if entries else 'No timeline entries found.',
                'errors': [] if entries else [f'No timeline found for {event_id}']
        }


def aggregate_event_timeline(event_id):
    res = get_event_timeline(event_id)
    ts = 0
    if res.get('timeline'):
        try:
            # Handle both string and numeric timestamps
            timestamps = []
            for e in res['timeline']:
                t = e.get('timestamp')
                if t:
                    try:
                        timestamps.append(int(t))
                    except (ValueError, TypeError):
                        pass
            ts = max(timestamps) if timestamps else 0
        except Exception:
            ts = 0
    return {
        'ok': res.get('ok', False),
        'event_id': event_id,
        'last_relevant_timestamp': ts,
        'timeline': res.get('timeline', []),
        'errors': res.get('errors', [])
    }


# Build 19: Global recent timeline changes for control summary
def get_recent_timeline_changes(limit=5):
    # This is a global summary, not per-event
    from operator_dashboard.queue_utils import safe_read_queue
    queue = safe_read_queue()
    if isinstance(queue, dict):
        queue_rows = queue.get('rows', [])
    elif isinstance(queue, list):
        queue_rows = queue
    else:
        queue_rows = []
    
    all_events = []
    for row in queue_rows:
        if isinstance(row, dict):
            eid = row.get('event_id') or row.get('event_name')
            if eid:
                all_events.append(eid)
    
    changes = []
    for eid in all_events:
        res = get_event_timeline(eid)
        for t in res.get('timeline', [])[:limit]:
            if isinstance(t, dict):
                t_copy = t.copy()
                t_copy['event_id'] = eid
                t_copy['description'] = f"[{eid}] {t_copy.get('action','')} {t_copy.get('user_message','')}"
                changes.append(t_copy)
    
    # Sort by timestamp descending
    changes_sorted = sorted(changes, key=lambda x: x.get('timestamp','') if x.get('timestamp') is not None else '', reverse=True)
    return changes_sorted[:limit]


def get_contract_status():
    return {'ok': True}
