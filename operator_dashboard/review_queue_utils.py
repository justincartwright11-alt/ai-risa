"""
Review queue aggregation helper for Build 15.
Aggregates review pressure from escalation, watchlist, digest, anomaly, timeline, queue, and ledger.
"""
import datetime
from operator_dashboard.queue_utils import safe_read_queue
from operator_dashboard.evidence_utils import queue_row_to_evidence
from operator_dashboard.comparison_utils import get_event_comparison
from operator_dashboard.timeline_utils import get_event_timeline
from operator_dashboard.anomaly_utils import AnomalyAggregator
from operator_dashboard.watchlist_utils import aggregate_watchlist
from operator_dashboard.digest_utils import aggregate_digest
from operator_dashboard.escalation_utils import aggregate_escalations
from operator_dashboard.action_ledger_utils import safe_read_ledger

REVIEW_PRIORITIES = ["review_now", "high", "medium", "low"]


def aggregate_review_queue():
    """
    Aggregates review queue for /api/review-queue.
    Returns dict with keys: ok, timestamp, review_count, review_queue, summary, recommendation, errors
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
        digest = aggregate_digest()
        digest_map = {e.get('event_id'): e for e in (digest.get('digest', {}).get('top_watchlist', []) or [])}
        # Escalation index
        escalations = aggregate_escalations().get('escalations', [])
        escalation_map = {e.get('event_id'): e for e in escalations}
        review_queue = []
        for q in queue_rows:
            event_id = q.get('event_id') or q.get('event_name')
            escalation = escalation_map.get(event_id, {})
            anomaly_count = escalation.get('anomaly_count', 0)
            watch_score = escalation.get('watch_score', 0)
            digest_pressure = escalation.get('digest_pressure', 'low')
            escalation_level = escalation.get('escalation_level', 'low')
            last_relevant_timestamp = escalation.get('last_relevant_timestamp', q.get('completed_at') or q.get('updated_at') or q.get('created_at') or '')
            queue_status = escalation.get('queue_status', q.get('status'))
            reasons = []
            review_score = 0
            review_priority = 'low'
            # --- Review pressure rules ---
            if escalation_level in ['immediate_review', 'high']:
                review_score += 5
                review_priority = 'review_now'
                reasons.append(f'Escalation level: {escalation_level}')
            if watch_score >= 7 and digest_pressure in ['high', 'critical']:
                review_score += 3
                if review_priority == 'low':
                    review_priority = 'high'
                reasons.append('High watchlist score and digest pressure')
            if anomaly_count >= 2 and escalation_level not in ['immediate_review', 'high']:
                review_score += 2
                if review_priority == 'low':
                    review_priority = 'medium'
                reasons.append('Repeated anomalies')
            if escalation_level == 'moderate' and review_priority == 'low':
                review_score += 1
                review_priority = 'medium'
                reasons.append('Moderate escalation')
            if not reasons:
                reasons.append('No significant review pressure')
            # Omit events with only clean/low state
            if review_score == 0 and (escalation_level == 'low' and watch_score < 4 and digest_pressure == 'low' and anomaly_count == 0):
                continue
            review_queue.append({
                'event_id': event_id,
                'review_score': review_score,
                'review_priority': review_priority,
                'reasons': reasons,
                'escalation_level': escalation_level,
                'watch_score': watch_score,
                'digest_pressure': digest_pressure,
                'anomaly_count': anomaly_count,
                'queue_status': queue_status,
                'last_relevant_timestamp': last_relevant_timestamp,
                'recommendation': 'Review now' if review_priority == 'review_now' else 'Review soon' if review_priority == 'high' else 'Monitor',
                'source_layers': ['queue', 'anomalies', 'watchlist', 'digest', 'escalation', 'timeline', 'ledger'],
            })
        # Deterministic ranking
        def review_sort_key(e):
            try:
                score = float(e.get('review_score', 0))
            except Exception:
                score = 0.0
            try:
                priority = REVIEW_PRIORITIES.index(e.get('review_priority', 'low'))
            except Exception:
                priority = 3
            try:
                escalation_rank = ['immediate_review', 'high', 'moderate', 'low'].index(e.get('escalation_level', 'low'))
            except Exception:
                escalation_rank = 3
            try:
                ts_val = e.get('last_relevant_timestamp', '')
                if ts_val:
                    ts_val = ts_val.rstrip('Z')
                    dt = datetime.datetime.fromisoformat(ts_val)
                    ts_val = dt.timestamp()
                else:
                    ts_val = 0.0
            except Exception:
                ts_val = 0.0
            event_id_str = str(e.get('event_id', ''))
            return (-score, priority, escalation_rank, -ts_val, event_id_str)
        review_queue = sorted(review_queue, key=review_sort_key)
        summary = f"{len(review_queue)} events in review queue"
        recommendation = "Review highest priority events first."
        return {
            'ok': True,
            'timestamp': now,
            'review_count': len(review_queue),
            'review_queue': review_queue,
            'summary': summary,
            'recommendation': recommendation,
            'errors': []
        }
    except Exception as e:
        errors.append(str(e))
        return {
            'ok': False,
            'timestamp': now,
            'review_count': 0,
            'review_queue': [],
            'summary': '',
            'recommendation': '',
            'errors': errors if errors else []
        }

def aggregate_event_review_queue(event_id):
    """
    Aggregates review for /api/queue/event/<event_id>/review-queue.
    Returns dict with required contract.
    """
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    errors = []
    try:
        queue = safe_read_queue()
        queue_rows = queue.get('rows', [])
        q = next((row for row in queue_rows if (row.get('event_id') or row.get('event_name')) == event_id), None)
        if not q:
            return {
                'ok': True,
                'timestamp': now,
                'event_found': False,
                'event_id': event_id,
                'review_score': 0,
                'review_priority': 'low',
                'reasons': ['Event not found in queue'],
                'escalation_level': 'low',
                'watch_score': 0,
                'digest_pressure': 'low',
                'anomaly_count': 0,
                'queue_status': None,
                'timeline_pressure': False,
                'recommendation': '',
                'errors': [f'Event {event_id} not found in queue']
            }
        # Use same logic as aggregate_review_queue
        escalations = aggregate_escalations().get('escalations', [])
        escalation_map = {e.get('event_id'): e for e in escalations}
        escalation = escalation_map.get(event_id, {})
        anomaly_count = escalation.get('anomaly_count', 0)
        watch_score = escalation.get('watch_score', 0)
        digest_pressure = escalation.get('digest_pressure', 'low')
        escalation_level = escalation.get('escalation_level', 'low')
        queue_status = escalation.get('queue_status', q.get('status'))
        timeline_pressure = escalation.get('timeline_pressure', False)
        last_relevant_timestamp = escalation.get('last_relevant_timestamp', q.get('completed_at') or q.get('updated_at') or q.get('created_at') or '')
        reasons = []
        review_score = 0
        review_priority = 'low'
        if escalation_level in ['immediate_review', 'high']:
            review_score += 5
            review_priority = 'review_now'
            reasons.append(f'Escalation level: {escalation_level}')
        if watch_score >= 7 and digest_pressure in ['high', 'critical']:
            review_score += 3
            if review_priority == 'low':
                review_priority = 'high'
            reasons.append('High watchlist score and digest pressure')
        if anomaly_count >= 2 and escalation_level not in ['immediate_review', 'high']:
            review_score += 2
            if review_priority == 'low':
                review_priority = 'medium'
            reasons.append('Repeated anomalies')
        if escalation_level == 'moderate' and review_priority == 'low':
            review_score += 1
            review_priority = 'medium'
            reasons.append('Moderate escalation')
        if not reasons:
            reasons.append('No significant review pressure')
        return {
            'ok': True,
            'timestamp': now,
            'event_found': True,
            'event_id': event_id,
            'review_score': review_score,
            'review_priority': review_priority,
            'reasons': reasons,
            'escalation_level': escalation_level,
            'watch_score': watch_score,
            'digest_pressure': digest_pressure,
            'anomaly_count': anomaly_count,
            'queue_status': queue_status,
            'timeline_pressure': timeline_pressure,
            'last_relevant_timestamp': last_relevant_timestamp,
            'recommendation': 'Review now' if review_priority == 'review_now' else 'Review soon' if review_priority == 'high' else 'Monitor',
            'errors': []
        }
    except Exception as e:
        errors.append(str(e))
        return {
            'ok': False,
            'timestamp': now,
            'event_found': False,
            'event_id': event_id,
            'review_score': 0,
            'review_priority': 'low',
            'reasons': reasons if reasons else ['Error'],
            'escalation_level': 'low',
            'watch_score': 0,
            'digest_pressure': 'low',
            'anomaly_count': 0,
            'queue_status': None,
            'timeline_pressure': False,
            'recommendation': '',
            'errors': errors if errors else []
        }


def get_contract_status():
    return {'ok': True}
