"""
Read-only operator casefile aggregation for Build 17.
Aggregates all relevant event-centered signals into a unified casefile snapshot.
"""
import datetime
from operator_dashboard.queue_utils import get_queue_row
from operator_dashboard.evidence_utils import aggregate_event_evidence
from operator_dashboard.comparison_utils import get_event_comparison
from operator_dashboard.timeline_utils import get_event_timeline
from operator_dashboard.anomaly_utils import AnomalyAggregator
from operator_dashboard.watchlist_utils import aggregate_event_watchlist
from operator_dashboard.digest_utils import aggregate_event_digest
from operator_dashboard.escalation_utils import aggregate_event_escalation
from operator_dashboard.review_queue_utils import aggregate_event_review_queue
from operator_dashboard.briefing_utils import aggregate_event_briefing
from operator_dashboard.action_ledger_utils import safe_read_ledger

def aggregate_event_casefile(event_id):
    """
    Aggregates a unified casefile for /api/queue/event/<event_id>/casefile.
    Returns dict with required contract.
    """
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    errors = []
    queue_row = get_queue_row(event_id)
    event_found = queue_row is not None
    # Snapshots
    queue_snapshot = queue_row if queue_row else None
    evidence_snapshot = aggregate_event_evidence(event_id)
    comparison_snapshot = get_event_comparison(event_id)
    timeline_snapshot = get_event_timeline(event_id)
    # Anomaly snapshot
    try:
        queue = [queue_row] if queue_row else []
        evidence_rows = [evidence_snapshot] if evidence_snapshot.get('ok') else []
        comparison_rows = [comparison_snapshot] if comparison_snapshot.get('ok', True) else []
        timeline_rows = [timeline_snapshot] if timeline_snapshot.get('ok', True) else []
        ledger_rows = safe_read_ledger()
        aggregator = AnomalyAggregator()
        anomaly_rows = aggregator.aggregate_anomalies(queue, evidence_rows, comparison_rows, timeline_rows, ledger_rows=ledger_rows, event_id=event_id)
        anomaly_snapshot = {'ok': True, 'anomalies': anomaly_rows, 'count': len(anomaly_rows)}
    except Exception as e:
        anomaly_snapshot = {'ok': False, 'anomalies': [], 'count': 0, 'errors': [str(e)]}
        errors.append(f'anomaly: {e}')
    # Watchlist, digest, escalation, review queue, briefing
    watchlist_snapshot = aggregate_event_watchlist(event_id, [queue_row] if queue_row else [], [evidence_snapshot] if evidence_snapshot.get('ok') else [], [comparison_snapshot] if comparison_snapshot.get('ok', True) else [], [timeline_snapshot] if timeline_snapshot.get('ok', True) else [], anomaly_rows if 'anomaly_rows' in locals() else [], ledger_rows if 'ledger_rows' in locals() else [])
    digest_snapshot = aggregate_event_digest(event_id)
    escalation_snapshot = aggregate_event_escalation(event_id)
    review_queue_snapshot = aggregate_event_review_queue(event_id)
    briefing_snapshot = aggregate_event_briefing(event_id)
    # Casefile summary and recommendations
    if event_found:
        summary = f"Casefile for {event_id}: "
        if review_queue_snapshot.get('event_found') and review_queue_snapshot.get('review_priority') in ['review_now', 'high', 'medium']:
            summary += f"Review pressure: {review_queue_snapshot.get('review_priority')}"
        elif escalation_snapshot.get('event_found') and escalation_snapshot.get('escalation_level') in ['immediate_review', 'high', 'moderate']:
            summary += f"Escalation: {escalation_snapshot.get('escalation_level')}"
        elif watchlist_snapshot and watchlist_snapshot.get('priority') in ['high', 'medium']:
            summary += f"Watchlist: {watchlist_snapshot.get('priority')}"
        elif digest_snapshot and digest_snapshot.get('digest_summary'):
            summary += f"Digest: {digest_snapshot.get('digest_summary')}"
        elif anomaly_snapshot and anomaly_snapshot.get('count', 0) > 0:
            summary += f"Anomalies: {anomaly_snapshot.get('count')} detected"
        else:
            summary += "No significant review pressure"
        operator_recommendation = (review_queue_snapshot.get('recommendation') or briefing_snapshot.get('operator_recommendation') or 'Monitor')
        next_review_note = (briefing_snapshot.get('next_review_note') or 'Monitor until next review')
    else:
        summary = f"Event {event_id} not found in queue"
        operator_recommendation = ''
        next_review_note = ''
    return {
        'ok': True,
        'timestamp': now,
        'event_found': event_found,
        'event_id': event_id,
        'queue_snapshot': queue_snapshot,
        'evidence_snapshot': evidence_snapshot,
        'comparison_snapshot': comparison_snapshot,
        'timeline_snapshot': timeline_snapshot,
        'anomaly_snapshot': anomaly_snapshot,
        'watchlist_snapshot': watchlist_snapshot,
        'digest_snapshot': digest_snapshot,
        'escalation_snapshot': escalation_snapshot,
        'review_queue_snapshot': review_queue_snapshot,
        'briefing_snapshot': briefing_snapshot,
        'casefile_summary': summary,
        'operator_recommendation': operator_recommendation,
        'next_review_note': next_review_note,
        'errors': errors
    }


def get_contract_status():
    return {'ok': True}
