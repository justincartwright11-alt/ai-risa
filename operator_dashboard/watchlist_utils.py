# operator_dashboard/watchlist_utils.py
"""
Watchlist aggregation logic for Build 12: deterministic, read-only, safe.
"""
import operator_dashboard.queue_utils as queue_utils
import operator_dashboard.evidence_utils as evidence_utils
import operator_dashboard.comparison_utils as comparison_utils
import operator_dashboard.timeline_utils as timeline_utils
import operator_dashboard.anomaly_utils as anomaly_utils
import operator_dashboard.action_ledger_utils as ledger_utils
from datetime import datetime

WATCH_PRIORITIES = ['critical', 'high', 'medium', 'low']

# Deterministic scoring rules
WATCH_RULES = [
    # (rule_name, score, priority, lambda row: bool, reason)
    ('completed_missing_artifact', 100, 'high', lambda q, e, a: (q.get('status','').strip().lower() == 'complete' and not e.get('artifact_exists')), 'Completed event missing artifact'),
    ('blocked_blank_blockers', 80, 'high', lambda q, e, a: (q.get('status','').strip().lower() == 'blocked' and not q.get('blockers')), 'Blocked event with no blockers'),
    ('repeated_anomalies', 60, 'medium', lambda q, e, a: (a and len(a) >= 2), 'Repeated anomalies'),
    ('repeated_activity', 40, 'medium', lambda q, e, a, ledger=None: (ledger and len(ledger) >= 3), 'Repeated recent activity'),
    ('timeline_unresolved', 30, 'medium', lambda q, e, a, t=None: (t and any(x.get('unresolved') for x in t)), 'Timeline shows unresolved issue'),
]

def aggregate_watchlist(queue_rows, evidence_rows, comparison_rows, timeline_rows, anomaly_rows, ledger_rows):
    """
    Returns a list of watchlist rows, each with required fields and deterministic ranking.
    """
    watchlist = []
    for q in queue_rows:
        eid = queue_utils.normalize_event_id(q.get('event_id') or q.get('event_name'))
        e = next((ev for ev in evidence_rows if queue_utils.normalize_event_id(ev.get('event_id') or ev.get('event_name')) == eid), {})
        a = [an for an in anomaly_rows if queue_utils.normalize_event_id(an.get('event_id') or an.get('event_name')) == eid]
        ledger = [l for l in ledger_rows if queue_utils.normalize_event_id(l.get('event_id') or l.get('normalized_event')) == eid]
        t = [tl for tl in timeline_rows if queue_utils.normalize_event_id(tl.get('event_id') or tl.get('event_name')) == eid]
        reasons = []
        score = 0
        priority = 'low'
        for rule in WATCH_RULES:
            try:
                if rule[0] == 'repeated_activity':
                    if rule[3](q, e, a, ledger):
                        score += rule[1]
                        reasons.append(rule[4])
                        priority = max(priority, rule[2], key=WATCH_PRIORITIES.index)
                elif rule[0] == 'timeline_unresolved':
                    if rule[3](q, e, a, t):
                        score += rule[1]
                        reasons.append(rule[4])
                        priority = max(priority, rule[2], key=WATCH_PRIORITIES.index)
                else:
                    if rule[3](q, e, a):
                        score += rule[1]
                        reasons.append(rule[4])
                        priority = max(priority, rule[2], key=WATCH_PRIORITIES.index)
            except Exception:
                continue
        # Only include if score > 0
        if score > 0:
            watchlist.append({
                'event_id': eid,
                'watch_score': score,
                'priority': priority,
                'reasons': reasons,
                'queue_status': q.get('status'),
                'anomaly_count': len(a),
                'recent_activity_count': len(ledger),
                'last_relevant_timestamp': max([l.get('timestamp','') for l in ledger if l.get('timestamp')], default=q.get('completed_at','')),
                'recommendation': '',
            })
    # Deterministic sort
    def sort_key(row):
        return (-row['watch_score'], WATCH_PRIORITIES.index(row['priority']), row['last_relevant_timestamp'], row['event_id'])
    watchlist.sort(key=sort_key)
    return watchlist

def aggregate_event_watchlist(event_id, queue_rows, evidence_rows, comparison_rows, timeline_rows, anomaly_rows, ledger_rows):
    eid = queue_utils.normalize_event_id(event_id)
    wl = aggregate_watchlist(queue_rows, evidence_rows, comparison_rows, timeline_rows, anomaly_rows, ledger_rows)
    for row in wl:
        if queue_utils.normalize_event_id(row['event_id']) == eid:
            return row
    return None


def get_contract_status():
    return {'ok': True}
