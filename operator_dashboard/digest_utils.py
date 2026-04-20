"""
Digest aggregation helper for Build 13.
Aggregates watchlist, anomalies, timeline pressure, and triage summary for operator digest endpoints.
"""
import datetime
from operator_dashboard.queue_utils import safe_read_queue
from operator_dashboard.evidence_utils import queue_row_to_evidence
from operator_dashboard.comparison_utils import get_event_comparison
from operator_dashboard.timeline_utils import get_event_timeline
from operator_dashboard.anomaly_utils import AnomalyAggregator
from operator_dashboard.watchlist_utils import aggregate_watchlist
from operator_dashboard.action_ledger_utils import safe_read_ledger


def aggregate_digest():
    """
    Aggregates digest for /api/digest.
    Returns dict with keys: ok, timestamp, digest, summary, recommendation, errors
    """
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    errors = []
    try:
        queue = safe_read_queue()
        queue_rows = queue.get('rows', [])
        evidence_rows = [queue_row_to_evidence(q) for q in queue_rows]
        comparison_rows = [get_event_comparison(q.get('event_id') or q.get('event_name')) for q in queue_rows]
        timeline_rows = [get_event_timeline(q.get('event_id') or q.get('event_name')) for q in queue_rows]
        ledger_rows = safe_read_ledger()
        aggregator = AnomalyAggregator()
        anomaly_rows = aggregator.aggregate_anomalies(queue_rows, evidence_rows, comparison_rows, timeline_rows, ledger_rows=ledger_rows)
        watchlist = aggregate_watchlist(queue_rows, evidence_rows, comparison_rows, timeline_rows, anomaly_rows, ledger_rows)

        # Deterministic ranking and triage
        top_watchlist = sorted(watchlist, key=lambda x: (-x.get('watch_score', 0), x.get('event_id', '')))
        top_anomalies = sorted(anomaly_rows, key=lambda x: (-x.get('severity', 0), x.get('event_name', '')))
        timeline_pressure_events = [t for t in timeline_rows if t.get('pressure', False)]
        triage_counts = {
            'critical': sum(1 for w in watchlist if w.get('priority') == 'critical'),
            'high': sum(1 for w in watchlist if w.get('priority') == 'high'),
            'medium': sum(1 for w in watchlist if w.get('priority') == 'medium'),
            'low': sum(1 for w in watchlist if w.get('priority') == 'low'),
        }
        priority_bands = {
            'critical': [w for w in watchlist if w.get('priority') == 'critical'],
            'high': [w for w in watchlist if w.get('priority') == 'high'],
            'medium': [w for w in watchlist if w.get('priority') == 'medium'],
            'low': [w for w in watchlist if w.get('priority') == 'low'],
        }
        recent_attention_items = sorted(
            (w for w in watchlist if w.get('last_relevant_timestamp')), 
            key=lambda x: x.get('last_relevant_timestamp'), reverse=True
        )[:10]
        digest = {
            'top_watchlist': top_watchlist[:5],
            'top_anomalies': top_anomalies[:5],
            'timeline_pressure_events': timeline_pressure_events[:5],
            'triage_counts': triage_counts,
            'priority_bands': {k: [w.get('event_id') for w in v[:5]] for k, v in priority_bands.items()},
            'recent_attention_items': [w.get('event_id') for w in recent_attention_items],
        }
        summary = f"{len(top_watchlist)} watchlist, {len(top_anomalies)} anomalies, {len(timeline_pressure_events)} timeline pressure events"
        recommendation = "Review critical/high priority events first."
        return {
            'ok': True,
            'timestamp': now,
            'digest': digest,
            'summary': summary,
            'recommendation': recommendation,
            'errors': []
        }
    except Exception as e:
        errors.append(str(e))
        return {
            'ok': False,
            'timestamp': now,
            'digest': {},
            'summary': '',
            'recommendation': '',
            'errors': errors if errors else []
        }

def aggregate_event_digest(event_id):
    """
    Aggregates digest for /api/queue/event/<event_id>/digest.
    Returns dict with keys: ok, timestamp, event_found, event_id, watchlist_snapshot, anomaly_snapshot, timeline_snapshot, digest_summary, recommendation, errors
    """
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    errors = []
    try:
        queue = safe_read_queue()
        queue_rows = queue.get('rows', [])
        event_row = next((q for q in queue_rows if (q.get('event_id') or q.get('event_name')) == event_id), None)
        if not event_row:
            return {
                'ok': True,
                'timestamp': now,
                'event_found': False,
                'event_id': event_id,
                'watchlist_snapshot': {},
                'anomaly_snapshot': {},
                'timeline_snapshot': {},
                'digest_summary': 'Event not found in queue',
                'recommendation': '',
                'errors': [f'Event {event_id} not found in queue']
            }
        evidence = queue_row_to_evidence(event_row)
        comparison = get_event_comparison(event_id)
        timeline = get_event_timeline(event_id)
        ledger_rows = safe_read_ledger()
        aggregator = AnomalyAggregator()
        anomaly_rows = aggregator.aggregate_anomalies([event_row], [evidence], [comparison], [timeline], ledger_rows=ledger_rows, event_id=event_id)
        from operator_dashboard.watchlist_utils import aggregate_event_watchlist
        watchlist_row = aggregate_event_watchlist(event_id, queue_rows, [evidence], [comparison], [timeline], anomaly_rows, ledger_rows)
        digest_summary = f"Watchlist: {watchlist_row['priority'] if watchlist_row else 'low'}, Anomalies: {len(anomaly_rows)}, Timeline pressure: {timeline.get('pressure', False)}"
        recommendation = "Review if priority is high or anomalies present."
        return {
            'ok': True,
            'timestamp': now,
            'event_found': True,
            'event_id': event_id,
            'watchlist_snapshot': watchlist_row or {},
            'anomaly_snapshot': anomaly_rows,
            'timeline_snapshot': timeline,
            'digest_summary': digest_summary,
            'recommendation': recommendation,
            'errors': []
        }
    except Exception as e:
        errors.append(str(e))
        return {
            'ok': False,
            'timestamp': now,
            'event_found': False,
            'event_id': event_id,
            'watchlist_snapshot': {},
            'anomaly_snapshot': {},
            'timeline_snapshot': {},
            'digest_summary': '',
            'recommendation': '',
            'errors': errors if errors else []
        }


def get_contract_status():
    return {'ok': True}
