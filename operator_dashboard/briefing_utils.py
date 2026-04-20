"""
Read-only operator briefing aggregation for Build 16.
Aggregates top review-queue events with triage context for operator handoff.
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
from operator_dashboard.review_queue_utils import aggregate_review_queue

BRIEFING_PRIORITIES = ["handoff_now", "high", "medium", "low"]


def aggregate_briefing():
    """
    Aggregates briefing for /api/briefing.
    Returns dict with keys: ok, timestamp, briefing_count, briefings, summary, recommendation, errors
    """
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    errors = []
    try:
        review = aggregate_review_queue()
        review_queue = review.get('review_queue', [])
        briefings = []
        for rq in review_queue:
            event_id = rq.get('event_id')
            escalation_level = rq.get('escalation_level', 'low')
            watch_score = rq.get('watch_score', 0)
            digest_pressure = rq.get('digest_pressure', 'low')
            anomaly_count = rq.get('anomaly_count', 0)
            queue_status = rq.get('queue_status')
            last_relevant_timestamp = rq.get('last_relevant_timestamp', '')
            review_priority = rq.get('review_priority', 'low')
            review_score = rq.get('review_score', 0)
            reasons = rq.get('reasons', [])
            recommendation = rq.get('recommendation', '')
            # Briefing priority logic
            if review_priority == 'review_now' or escalation_level == 'immediate_review':
                briefing_priority = 'handoff_now'
            elif review_priority == 'high' or escalation_level == 'high':
                briefing_priority = 'high'
            elif review_priority == 'medium' or escalation_level == 'moderate':
                briefing_priority = 'medium'
            else:
                briefing_priority = 'low'
            # Score: review_score + watch_score + anomaly_count + digest_pressure weight
            score = float(review_score) + float(watch_score) + float(anomaly_count)
            if digest_pressure == 'critical':
                score += 3
            elif digest_pressure == 'high':
                score += 2
            elif digest_pressure == 'medium':
                score += 1
            # Handoff summary
            handoff_summary = f"{event_id}: {', '.join(reasons[:2])}" if reasons else f"{event_id}: No significant review pressure"
            operator_recommendation = recommendation or 'Monitor'
            next_review_note = 'Review at next operator handoff' if briefing_priority in ['handoff_now', 'high'] else 'Monitor until next review'
            briefings.append({
                'event_id': event_id,
                'briefing_priority': briefing_priority,
                'briefing_score': score,
                'handoff_summary': handoff_summary,
                'top_reasons': reasons[:3],
                'escalation_level': escalation_level,
                'watch_score': watch_score,
                'digest_pressure': digest_pressure,
                'anomaly_count': anomaly_count,
                'queue_status': queue_status,
                'last_relevant_timestamp': last_relevant_timestamp,
                'operator_recommendation': operator_recommendation,
                'next_review_note': next_review_note,
                'source_layers': ['queue', 'anomalies', 'watchlist', 'digest', 'escalation', 'review_queue', 'timeline', 'ledger'],
            })
        # Deterministic ranking
        def briefing_sort_key(e):
            try:
                score = float(e.get('briefing_score', 0))
            except Exception:
                score = 0.0
            try:
                priority = BRIEFING_PRIORITIES.index(e.get('briefing_priority', 'low'))
            except Exception:
                priority = 3
            try:
                review_priority = ["review_now", "high", "medium", "low"].index(rq.get('review_priority', 'low'))
            except Exception:
                review_priority = 3
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
        briefings = sorted(briefings, key=briefing_sort_key)
        summary = f"{len(briefings)} events in operator briefing"
        recommendation = "Review handoff_now and high-priority events first."
        return {
            'ok': True,
            'timestamp': now,
            'briefing_count': len(briefings),
            'briefings': briefings,
            'summary': summary,
            'recommendation': recommendation,
            'errors': []
        }
    except Exception as e:
        errors.append(str(e))
        return {
            'ok': False,
            'timestamp': now,
            'briefing_count': 0,
            'briefings': [],
            'summary': '',
            'recommendation': '',
            'errors': errors if errors else []
        }

def aggregate_event_briefing(event_id):
    """
    Aggregates briefing for /api/queue/event/<event_id>/briefing.
    Returns dict with required contract.
    """
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    errors = []
    try:
        review = aggregate_review_queue()
        review_queue = review.get('review_queue', [])
        row = next((b for b in review_queue if (b.get('event_id')) == event_id), None)
        if row:
            escalation_level = row.get('escalation_level', 'low')
            watch_score = row.get('watch_score', 0)
            digest_pressure = row.get('digest_pressure', 'low')
            anomaly_count = row.get('anomaly_count', 0)
            queue_status = row.get('queue_status')
            last_relevant_timestamp = row.get('last_relevant_timestamp', '')
            review_priority = row.get('review_priority', 'low')
            review_score = row.get('review_score', 0)
            reasons = row.get('reasons', [])
            recommendation = row.get('recommendation', '')
            # Briefing priority logic
            if review_priority == 'review_now' or escalation_level == 'immediate_review':
                briefing_priority = 'handoff_now'
            elif review_priority == 'high' or escalation_level == 'high':
                briefing_priority = 'high'
            elif review_priority == 'medium' or escalation_level == 'moderate':
                briefing_priority = 'medium'
            else:
                briefing_priority = 'low'
            score = float(review_score) + float(watch_score) + float(anomaly_count)
            if digest_pressure == 'critical':
                score += 3
            elif digest_pressure == 'high':
                score += 2
            elif digest_pressure == 'medium':
                score += 1
            handoff_summary = f"{event_id}: {', '.join(reasons[:2])}" if reasons else f"{event_id}: No significant review pressure"
            operator_recommendation = recommendation or 'Monitor'
            next_review_note = 'Review at next operator handoff' if briefing_priority in ['handoff_now', 'high'] else 'Monitor until next review'
            return {
                'ok': True,
                'timestamp': now,
                'event_found': True,
                'event_id': event_id,
                'briefing_priority': briefing_priority,
                'briefing_score': score,
                'handoff_summary': handoff_summary,
                'top_reasons': reasons[:3],
                'escalation_level': escalation_level,
                'watch_score': watch_score,
                'digest_pressure': digest_pressure,
                'anomaly_count': anomaly_count,
                'queue_status': queue_status,
                'timeline_pressure': False,
                'operator_recommendation': operator_recommendation,
                'next_review_note': next_review_note,
                'errors': []
            }
        # If not in review queue, check main queue
        from operator_dashboard.queue_utils import get_queue_row
        queue_row = get_queue_row(event_id)
        if queue_row:
            # Return a valid low-pressure briefing
            return {
                'ok': True,
                'timestamp': now,
                'event_found': True,
                'event_id': event_id,
                'briefing_priority': 'low',
                'briefing_score': 0,
                'handoff_summary': f'{event_id}: No significant review pressure',
                'top_reasons': ['No significant review pressure'],
                'escalation_level': 'low',
                'watch_score': 0,
                'digest_pressure': 'low',
                'anomaly_count': 0,
                'queue_status': queue_row.get('status'),
                'timeline_pressure': False,
                'operator_recommendation': 'Monitor',
                'next_review_note': 'Monitor until next review',
                'errors': []
            }
        # Not found in any queue
        return {
            'ok': True,
            'timestamp': now,
            'event_found': False,
            'event_id': event_id,
            'briefing_priority': 'low',
            'briefing_score': 0,
            'handoff_summary': f'{event_id}: Not found in queue',
            'top_reasons': ['Event not found in queue'],
            'escalation_level': 'low',
            'watch_score': 0,
            'digest_pressure': 'low',
            'anomaly_count': 0,
            'queue_status': None,
            'timeline_pressure': False,
            'operator_recommendation': '',
            'next_review_note': '',
            'errors': [f'Event {event_id} not found in queue']
        }
    except Exception as e:
        errors.append(str(e))
        return {
            'ok': False,
            'timestamp': now,
            'event_found': False,
            'event_id': event_id,
            'briefing_priority': 'low',
            'briefing_score': 0,
            'handoff_summary': '',
            'top_reasons': [],
            'escalation_level': 'low',
            'watch_score': 0,
            'digest_pressure': 'low',
            'anomaly_count': 0,
            'queue_status': None,
            'timeline_pressure': False,
            'operator_recommendation': '',
            'next_review_note': '',
            'errors': errors if errors else []
        }


def get_contract_status():
    return {'ok': True}
