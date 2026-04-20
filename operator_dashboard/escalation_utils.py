"""
Escalation aggregation helper for Build 14.
Aggregates escalation signals from queue, anomaly, watchlist, digest, timeline, and ledger.
"""
import datetime
from operator_dashboard.queue_utils import safe_read_queue
from operator_dashboard.evidence_utils import queue_row_to_evidence
from operator_dashboard.comparison_utils import get_event_comparison
from operator_dashboard.timeline_utils import get_event_timeline
from operator_dashboard.anomaly_utils import AnomalyAggregator
from operator_dashboard.watchlist_utils import aggregate_watchlist
from operator_dashboard.digest_utils import aggregate_digest, aggregate_event_digest
from operator_dashboard.action_ledger_utils import safe_read_ledger

ESCALATION_LEVELS = ["immediate_review", "high", "moderate", "low"]


def aggregate_escalations():
    """
    Aggregates escalations for /api/escalations.
    Returns dict with keys: ok, timestamp, escalation_count, escalations, summary, recommendation, errors
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
        # Build event_id set
        event_ids = set((q.get('event_id') or q.get('event_name')) for q in queue_rows)
        escalations = []
        for q in queue_rows:
            event_id = q.get('event_id') or q.get('event_name')
            # Gather signals
            anomaly_count = sum(1 for a in anomaly_rows if a.get('event_name') == event_id)
            watch_row = next((w for w in watchlist if w.get('event_id') == event_id), None)
            digest_pressure = digest_map.get(event_id, {}).get('priority', 'low')
            timeline = next((t for t in timeline_rows if (t.get('event_id') or t.get('event_name')) == event_id), {})
            timeline_pressure = timeline.get('pressure', False)
            last_relevant_timestamp = q.get('completed_at') or q.get('updated_at') or q.get('created_at') or ''
            reasons = []
            escalation_score = 0
            escalation_level = 'low'
            # Escalation rules
            if q.get('status') == 'blocked' and not q.get('blockers') and timeline_pressure:
                escalation_score += 4
                escalation_level = 'immediate_review'
                reasons.append('Blocked with no blockers and timeline pressure')
            if anomaly_count >= 2:
                escalation_score += 3
                escalation_level = 'high'
                reasons.append('Repeated anomalies across layers')
            if watch_row and watch_row.get('watch_score', 0) >= 7 and digest_pressure in ['high', 'critical']:
                escalation_score += 3
                escalation_level = 'high'
                reasons.append('High watchlist score and digest pressure')
            if anomaly_count == 1:
                escalation_score += 2
                escalation_level = 'moderate'
                reasons.append('Single anomaly present')
            if watch_row and watch_row.get('watch_score', 0) >= 4:
                escalation_score += 1
                escalation_level = 'moderate'
                reasons.append('Moderate watchlist score')
            if timeline_pressure:
                escalation_score += 1
                escalation_level = 'moderate'
                reasons.append('Timeline pressure')
            if not reasons:
                escalation_level = 'low'
                reasons.append('No significant escalation signals')
            escalations.append({
                'event_id': event_id,
                'escalation_score': escalation_score,
                'escalation_level': escalation_level,
                'reasons': reasons,
                'queue_status': q.get('status'),
                'anomaly_count': anomaly_count,
                'watch_score': watch_row.get('watch_score', 0) if watch_row else 0,
                'digest_pressure': digest_pressure,
                'last_relevant_timestamp': last_relevant_timestamp,
                'recommendation': 'Review immediately' if escalation_level == 'immediate_review' else 'Review soon' if escalation_level == 'high' else 'Monitor',
                'source_layers': ['queue', 'anomalies', 'watchlist', 'digest', 'timeline', 'ledger'],
            })
        # Deterministic, type-safe ranking
        # --- Build 14: Robust normalization helpers for deterministic, type-safe ranking ---
        def score_to_num(val):
            try:
                if val is None:
                    return 0.0
                if isinstance(val, (int, float)):
                    return float(val)
                if isinstance(val, str):
                    return float(val.strip()) if val.strip() else 0.0
                return float(val)
            except Exception:
                return 0.0

        def level_to_rank(val):
            try:
                if val is None:
                    return 99
                if isinstance(val, str) and val in ESCALATION_LEVELS:
                    return ESCALATION_LEVELS.index(val)
                return int(val)
            except Exception:
                return 99

        def timestamp_to_rank(ts):
            if not ts:
                return 0.0
            try:
                if isinstance(ts, (int, float)):
                    return float(ts)
                if isinstance(ts, str):
                    ts = ts.strip()
                    if not ts:
                        return 0.0
                    ts = ts.rstrip('Z')
                    dt = datetime.datetime.fromisoformat(ts)
                    return dt.timestamp()
                return float(ts)
            except Exception:
                return 0.0

        def event_id_to_key(val):
            try:
                if val is None:
                    return ''
                return str(val)
            except Exception:
                return ''

        def escalation_sort_key(e):
            # Patch: forcibly cast all negated fields to float, event_id to string, fallback to 0.0/''
            try:
                score = float(score_to_num(e.get('escalation_score', 0)))
            except Exception:
                score = 0.0
            try:
                level = int(level_to_rank(e.get('escalation_level', 'low')))
            except Exception:
                level = 99
            try:
                ts_val = float(timestamp_to_rank(e.get('last_relevant_timestamp', None)))
            except Exception:
                ts_val = 0.0
            try:
                event_id_str = str(event_id_to_key(e.get('event_id', '')))
            except Exception:
                event_id_str = ''
            return (-score, level, -ts_val, event_id_str)
        escalations = sorted(escalations, key=escalation_sort_key)
        summary = f"{len(escalations)} events ranked by escalation pressure"
        recommendation = "Review highest escalation events first."
        return {
            'ok': True,
            'timestamp': now,
            'escalation_count': len(escalations),
            'escalations': escalations,
            'summary': summary,
            'recommendation': recommendation,
            'errors': []
        }
    except Exception as e:
        errors.append(str(e))
        return {
            'ok': False,
            'timestamp': now,
            'escalation_count': 0,
            'escalations': [],
            'summary': '',
            'recommendation': '',
            'errors': errors if errors else []
        }

def aggregate_event_escalation(event_id):
    """
    Aggregates escalation for /api/queue/event/<event_id>/escalation.
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
                'escalation_score': 0,
                'escalation_level': 'low',
                'reasons': ['Event not found in queue'],
                'queue_status': None,
                'anomaly_count': 0,
                'watch_score': 0,
                'digest_pressure': 'low',
                'timeline_pressure': False,
                'recommendation': '',
                'errors': [f'Event {event_id} not found in queue']
            }
        evidence = queue_row_to_evidence(q)
        comparison = get_event_comparison(event_id)
        timeline = get_event_timeline(event_id)
        ledger_rows = safe_read_ledger()
        aggregator = AnomalyAggregator()
        anomaly_rows = aggregator.aggregate_anomalies([q], [evidence], [comparison], [timeline], ledger_rows=ledger_rows, event_id=event_id)
        anomaly_count = len(anomaly_rows)
        from operator_dashboard.watchlist_utils import aggregate_event_watchlist
        watch_row = aggregate_event_watchlist(event_id, queue_rows, [evidence], [comparison], [timeline], anomaly_rows, ledger_rows)
        digest = aggregate_event_digest(event_id)
        digest_pressure = digest.get('watchlist_snapshot', {}).get('priority', 'low') if digest.get('watchlist_snapshot') else 'low'
        timeline_pressure = timeline.get('pressure', False)
        last_relevant_timestamp = q.get('completed_at') or q.get('updated_at') or q.get('created_at') or ''
        reasons = []
        escalation_score = 0
        escalation_level = 'low'
        # Escalation rules
        if q.get('status') == 'blocked' and not q.get('blockers') and timeline_pressure:
            escalation_score += 4
            escalation_level = 'immediate_review'
            reasons.append('Blocked with no blockers and timeline pressure')
        if anomaly_count >= 2:
            escalation_score += 3
            escalation_level = 'high'
            reasons.append('Repeated anomalies across layers')
        if watch_row and watch_row.get('watch_score', 0) >= 7 and digest_pressure in ['high', 'critical']:
            escalation_score += 3
            escalation_level = 'high'
            reasons.append('High watchlist score and digest pressure')
        if anomaly_count == 1:
            escalation_score += 2
            escalation_level = 'moderate'
            reasons.append('Single anomaly present')
        if watch_row and watch_row.get('watch_score', 0) >= 4:
            escalation_score += 1
            escalation_level = 'moderate'
            reasons.append('Moderate watchlist score')
        if timeline_pressure:
            escalation_score += 1
            escalation_level = 'moderate'
            reasons.append('Timeline pressure')
        if not reasons:
            escalation_level = 'low'
            reasons.append('No significant escalation signals')
        return {
            'ok': True,
            'timestamp': now,
            'event_found': True,
            'event_id': event_id,
            'escalation_score': escalation_score,
            'escalation_level': escalation_level,
            'reasons': reasons,
            'queue_status': q.get('status'),
            'anomaly_count': anomaly_count,
            'watch_score': watch_row.get('watch_score', 0) if watch_row else 0,
            'digest_pressure': digest_pressure,
            'timeline_pressure': timeline_pressure,
            'recommendation': 'Review immediately' if escalation_level == 'immediate_review' else 'Review soon' if escalation_level == 'high' else 'Monitor',
            'errors': []
        }
    except Exception as e:
        errors.append(str(e))
        return {
            'ok': False,
            'timestamp': now,
            'event_found': False,
            'event_id': event_id,
            'escalation_score': 0,
            'escalation_level': 'low',
            'reasons': reasons if reasons else ['Error'],
            'queue_status': None,
            'anomaly_count': 0,
            'watch_score': 0,
            'digest_pressure': 'low',
            'timeline_pressure': False,
            'recommendation': '',
            'errors': errors if errors else []
        }


def get_contract_status():
    return {'ok': True}
