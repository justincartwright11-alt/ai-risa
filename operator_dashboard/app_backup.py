
from flask import Flask, render_template, request, jsonify
import sys
from pathlib import Path
import subprocess
import os
from datetime import datetime
import uuid

app = Flask(__name__)

from operator_dashboard.review_queue_utils import aggregate_review_queue, aggregate_event_review_queue
# --- Build 15: Review Queue Endpoints ---
@app.route('/api/review-queue', methods=['GET'])
def api_review_queue():
    result = aggregate_review_queue()
    return jsonify(result)

@app.route('/api/queue/event/<event_id>/review-queue', methods=['GET'])
def api_event_review_queue(event_id):
    result = aggregate_event_review_queue(event_id)
    return jsonify(result)
# --- End Build 15 review queue endpoints ---

app = Flask(__name__)

from operator_dashboard.evidence_utils import aggregate_event_evidence
from operator_dashboard.safe_path_utils import is_safe_artifact_path
from operator_dashboard.queue_utils import safe_read_queue, summarize_queue, get_queue_row
from operator_dashboard.comparison_utils import get_event_comparison
from operator_dashboard.status_utils import get_status
import operator_dashboard.chat_actions as chat_actions
from operator_dashboard.chat_history_utils import load_chat_history, append_chat_message
from operator_dashboard.action_ledger_utils import append_ledger_entry, make_entry

# Build 11: Anomaly aggregation

from operator_dashboard.anomaly_utils import AnomalyAggregator
# Build 12: Watchlist endpoints
from operator_dashboard.watchlist_utils import aggregate_watchlist, aggregate_event_watchlist
# Build 13: Digest endpoints
from operator_dashboard.digest_utils import aggregate_digest, aggregate_event_digest
from operator_dashboard.escalation_utils import aggregate_escalations, aggregate_event_escalation

# API: Event evidence endpoint (read-only, safe)
@app.route('/api/queue/event/<event_id>/evidence', methods=['GET'])
def api_event_evidence(event_id):
    try:
        # Use get_queue_row to resolve event row with fallback
        queue_row = get_queue_row(event_id)
        evidence = aggregate_event_evidence(event_id) if queue_row else {'ok': False, 'event_found': False, 'event_id': event_id, 'errors': [f'Event {event_id} not found in queue']}
        return jsonify(evidence)
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e), 'event_found': False, 'event_id': event_id, 'errors': [str(e)]}), 500

# API: Open event artifact endpoint (read-only, safe)
@app.route('/api/queue/event/<event_id>/open_artifact', methods=['POST'])
def api_open_event_artifact(event_id):
    try:
        event = get_queue_row(event_id)
        if not event:
            return jsonify({'ok': False, 'error': f'Event {event_id} not found.'}), 404
        artifact = event.get('artifact')
        safe, result = is_safe_artifact_path(artifact)
        if not safe:
            return jsonify({'ok': False, 'error': result}), 400
        try:
            os.startfile(result)
            return jsonify({'ok': True, 'opened': result})
        except Exception as e:
            return jsonify({'ok': False, 'error': f'Failed to open artifact: {e}'})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

# API: Queue event drilldown endpoint
@app.route('/api/queue/event/<event_id>', methods=['GET'])
def api_queue_event(event_id):
    try:
        event = get_queue_row(event_id)
        found = event is not None
        rec = ''
        if found:
            status = (event.get('status') or '').strip().lower()
            if status == 'queued':
                rec = "Eligible for next execution"
            elif status == 'blocked':
                rec = "Resolve blockers before execution"
            elif status == 'in_progress':
                rec = "Already in progress"
            elif status == 'complete':
                rec = "Review artifact/output only"
            else:
                rec = "Unknown status"
        return jsonify({
            'ok': True,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'event_found': found,
            'event_id': event_id,
            'status': event.get('status') if found else None,
            'artifact': event.get('artifact') if found else None,
            'blockers': event.get('blockers') if found else None,
            'completed_at': event.get('completed_at') if found else None,
            'frozen_flag': event.get('frozen_flag') if found else None,
            'recommendation': rec,
            'errors': [] if found else [f'Event {event_id} not found']
        })
    except Exception as e:
        return jsonify({
            'ok': False,
            'event_found': False,
            'event_id': event_id,
            'status': None,
            'artifact': None,
            'blockers': None,
            'completed_at': None,
            'frozen_flag': None,
            'recommendation': '',
            'errors': [str(e)]
        }), 500

@app.route('/api/queue/event/<event_id>/comparison', methods=['GET'])
def api_event_comparison(event_id):
    try:
        result = get_event_comparison(event_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'ok': False, 'event_id': event_id, 'errors': [str(e)]}), 500
# API: Queue recommendation endpoint

# API: Event timeline endpoint
@app.route('/api/queue/event/<event_id>/timeline', methods=['GET'])
def api_event_timeline(event_id):
    try:
        from operator_dashboard.timeline_utils import get_event_timeline
        result = get_event_timeline(event_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'ok': False, 'event_id': event_id, 'errors': [str(e)]}), 500
@app.route('/api/queue/recommendation', methods=['GET'])
def api_queue_recommendation():
    try:
        queue = safe_read_queue()
        rec = summarize_queue(queue.get('rows', []))
        return jsonify({'ok': True, **rec})
    except Exception as e:
        return jsonify({'ok': False, 'recommendation': 'Error: ' + str(e)})

# API: Queue snapshot endpoint
@app.route('/api/queue', methods=['GET'])
def api_queue():
    try:
        queue = safe_read_queue()
        return jsonify(queue)
    except Exception as e:
        return jsonify({
            'ok': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500

# Build 11: Anomaly aggregation endpoint
@app.route('/api/anomalies', methods=['GET'])
def api_anomalies():
    try:
        queue = safe_read_queue()
        queue_rows = queue.get('rows', [])
        from operator_dashboard.evidence_utils import queue_row_to_evidence
        evidence_rows = [queue_row_to_evidence(q) for q in queue_rows]
        from operator_dashboard.comparison_utils import get_event_comparison
        comparison_rows = [get_event_comparison(q.get('event_id') or q.get('event_name')) for q in queue_rows]
        from operator_dashboard.action_ledger_utils import safe_read_ledger
        ledger_rows = safe_read_ledger()
        aggregator = AnomalyAggregator()
        anomalies = aggregator.aggregate_anomalies(queue_rows, evidence_rows, comparison_rows, [], ledger_rows=ledger_rows)
        return jsonify({'ok': True, 'anomalies': anomalies, 'count': len(anomalies)})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e), 'anomalies': [], 'count': 0}), 500

# Build 11: Event anomaly endpoint
@app.route('/api/queue/event/<event_id>/anomalies', methods=['GET'])
def api_event_anomalies(event_id):
    try:
        queue = safe_read_queue()
        queue_rows = queue.get('rows', [])
        from operator_dashboard.evidence_utils import queue_row_to_evidence
        evidence_rows = [queue_row_to_evidence(q) for q in queue_rows]
        from operator_dashboard.comparison_utils import get_event_comparison
        comparison_rows = [get_event_comparison(q.get('event_id') or q.get('event_name')) for q in queue_rows]
        from operator_dashboard.action_ledger_utils import safe_read_ledger
        ledger_rows = safe_read_ledger()
        aggregator = AnomalyAggregator()
        anomalies = aggregator.aggregate_anomalies(queue_rows, evidence_rows, comparison_rows, [], ledger_rows=ledger_rows, event_id=event_id)
        return jsonify({'ok': True, 'anomalies': anomalies, 'count': len(anomalies)})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e), 'anomalies': [], 'count': 0}), 500


# Build 12: Watchlist index endpoint (runtime wiring fix)
@app.route('/api/watchlist', methods=['GET'])
def api_watchlist():
    try:
        queue = safe_read_queue()
        queue_rows = queue.get('rows', [])
        from operator_dashboard.evidence_utils import queue_row_to_evidence
        evidence_rows = [queue_row_to_evidence(q) for q in queue_rows]
        from operator_dashboard.comparison_utils import get_event_comparison
        comparison_rows = [get_event_comparison(q.get('event_id') or q.get('event_name')) for q in queue_rows]
        from operator_dashboard.timeline_utils import get_event_timeline
        timeline_rows = [get_event_timeline(q.get('event_id') or q.get('event_name')) for q in queue_rows]
        from operator_dashboard.anomaly_utils import AnomalyAggregator
        from operator_dashboard.action_ledger_utils import safe_read_ledger
        ledger_rows = safe_read_ledger()
        aggregator = AnomalyAggregator()
        anomaly_rows = aggregator.aggregate_anomalies(queue_rows, evidence_rows, comparison_rows, timeline_rows, ledger_rows=ledger_rows)
        watchlist = aggregate_watchlist(queue_rows, evidence_rows, comparison_rows, timeline_rows, anomaly_rows, ledger_rows)
        now = datetime.utcnow().isoformat() + 'Z'
        summary = f"Top {len(watchlist)} events needing monitoring"
        recommendation = "Monitor high-priority events first."
        return jsonify({
            'ok': True,
            'timestamp': now,
            'watchlist_count': len(watchlist),
            'watchlist': watchlist,
            'summary': summary,
            'recommendation': recommendation,
            'errors': []
        })
    except Exception as e:
        return jsonify({
            'ok': False,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'watchlist_count': 0,
            'watchlist': [],
            'summary': '',
            'recommendation': '',
            'errors': [str(e)]
        }), 500

# Build 12: Event watchlist endpoint (runtime wiring fix)
@app.route('/api/queue/event/<event_id>/watchlist', methods=['GET'])
def api_event_watchlist(event_id):
    try:
        queue = safe_read_queue()
        queue_rows = queue.get('rows', [])
        from operator_dashboard.evidence_utils import queue_row_to_evidence
        evidence_rows = [queue_row_to_evidence(q) for q in queue_rows]
        from operator_dashboard.comparison_utils import get_event_comparison
        comparison_rows = [get_event_comparison(q.get('event_id') or q.get('event_name')) for q in queue_rows]
        from operator_dashboard.timeline_utils import get_event_timeline
        timeline_rows = [get_event_timeline(q.get('event_id') or q.get('event_name')) for q in queue_rows]
        from operator_dashboard.anomaly_utils import AnomalyAggregator
        from operator_dashboard.action_ledger_utils import safe_read_ledger
        ledger_rows = safe_read_ledger()
        aggregator = AnomalyAggregator()
        anomaly_rows = aggregator.aggregate_anomalies(queue_rows, evidence_rows, comparison_rows, timeline_rows, ledger_rows=ledger_rows)
        row = aggregate_event_watchlist(event_id, queue_rows, evidence_rows, comparison_rows, timeline_rows, anomaly_rows, ledger_rows)
        now = datetime.utcnow().isoformat() + 'Z'
        found = row is not None
        return jsonify({
            'ok': True,
            'timestamp': now,
            'event_found': found,
            'event_id': event_id,
            'watch_score': row['watch_score'] if found else 0,
            'priority': row['priority'] if found else 'low',
            'reasons': row['reasons'] if found else [],
            'queue_status': row['queue_status'] if found else None,
            'anomaly_count': row['anomaly_count'] if found else 0,
            'recent_activity_count': row['recent_activity_count'] if found else 0,
            'last_relevant_timestamp': row['last_relevant_timestamp'] if found else '',
            'recommendation': row['recommendation'] if found else '',
            'errors': [] if found else [f'Event {event_id} not found or not on watchlist']
        })
    except Exception as e:
        return jsonify({
            'ok': False,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'event_found': False,
            'event_id': event_id,
            'watch_score': 0,
            'priority': 'low',
            'reasons': [],
            'queue_status': None,
            'anomaly_count': 0,
            'recent_activity_count': 0,
            'last_relevant_timestamp': '',
            'recommendation': '',
            'errors': [str(e)]
        }), 500

# Build 13: Digest index endpoint
@app.route('/api/digest', methods=['GET'])
def api_digest():
    try:
        result = aggregate_digest()
        return jsonify(result)
    except Exception as e:
        return jsonify({'ok': False, 'timestamp': datetime.utcnow().isoformat() + 'Z', 'digest': {}, 'summary': '', 'recommendation': '', 'errors': [str(e)]}), 500


# Build 13: Event digest endpoint
@app.route('/api/queue/event/<event_id>/digest', methods=['GET'])
def api_event_digest(event_id):
    try:
        result = aggregate_event_digest(event_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'ok': False, 'timestamp': datetime.utcnow().isoformat() + 'Z', 'event_found': False, 'event_id': event_id, 'watchlist_snapshot': {}, 'anomaly_snapshot': {}, 'timeline_snapshot': {}, 'digest_summary': '', 'recommendation': '', 'errors': [str(e)]}), 500

# --- Build 14: Escalation Endpoints ---
@app.route('/api/escalations', methods=['GET'])
def api_escalations():
    result = aggregate_escalations()
    return jsonify(result)

@app.route('/api/queue/event/<event_id>/escalation', methods=['GET'])
def api_event_escalation(event_id):
    result = aggregate_event_escalation(event_id)
    return jsonify(result)
# --- End Build 14 escalation endpoints ---

PROJECT_ROOT = Path(__file__).resolve().parent.parent
QUEUE_FILE = PROJECT_ROOT / 'event_coverage_queue.csv'
LIVE_LOG = PROJECT_ROOT / 'docs' / 'live_release_window_log.md'
MANIFEST = PROJECT_ROOT / 'docs' / 'runtime_release_manifest.md'
GO_NO_GO = PROJECT_ROOT / 'docs' / 'operator_release_go_no_go_note.md'

def contract_response(ok, action, response, normalized_event=None, details='', error=None):
    return {
        'ok': bool(ok),
        'action': action or '',
        'response': response or '',
        'normalized_event': normalized_event,
        'details': details or '',
        'error': error,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }

def dashboard_dispatcher(message):
    parsed = chat_actions.parse_chat_command(message)
    action = parsed.get('action', 'unknown')
    normalized_event = parsed.get('normalized_event')
    details = ''
    error = None
    correlation_id = str(uuid.uuid4())
    started_entry = make_entry(
        action=action,
        normalized_event=normalized_event,
        user_message=message,
        outcome_status='started',
        response='',
        error=None,
        details_summary='',
        correlation_id=correlation_id
    )
    append_ledger_entry(started_entry)
    try:
        result = chat_actions.handle_chat_action(parsed, str(PROJECT_ROOT))
        response = result.get('response', '')
        ok = bool(result.get('success', False))
        details = result.get('details', '') or ''
        error = result.get('error')
        if action == 'clarify':
            outcome_status = 'clarification'
        elif ok:
            outcome_status = 'succeeded'
        else:
            outcome_status = 'failed'
        outcome_entry = make_entry(
            action=action,
            normalized_event=normalized_event,
            user_message=message,
            outcome_status=outcome_status,
            response=response,
            error=error,
            details_summary=details,
            correlation_id=correlation_id
        )
        append_ledger_entry(outcome_entry)
        return contract_response(
            ok=ok,
            action=action,
            response=response,
            normalized_event=normalized_event,
            details=details,
            error=error
        )
    except Exception as e:
        fail_entry = make_entry(
            action=action,
            normalized_event=normalized_event,
            user_message=message,
            outcome_status='failed',
            response='An internal error occurred. Please try again.',
            error=str(e),
            details_summary='',
            correlation_id=correlation_id
        )
        append_ledger_entry(fail_entry)
        return contract_response(
            ok=False,
            action=action,
            response="An internal error occurred. Please try again.",
            normalized_event=normalized_event,
            details='',
            error=str(e)
        )

@app.route('/api/status', methods=['GET'])
def api_status():
    try:
        status = get_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({
            'ok': False,
            'error': str(e),
            'app_name': 'AI-RISA Local Operator Dashboard',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


# Chat send endpoint with explicit watchlist action handling
@app.route('/chat/send', methods=['POST'])
def chat_send():
    data = request.get_json()
    message = data.get('message', '')
    parsed = chat_actions.parse_chat_command(message)
    # Watchlist and digest chat commands
    if parsed.get('action') in ["show_watchlist", "show_event_watchlist", "show_digest", "operator_digest", "show_triage_summary", "what_needs_attention", "show_event_digest"]:
        # Use backend chat_actions handler for all allowlisted actions
        result = chat_actions.handle_chat_action(parsed)
        # For digest, return standard chat envelope
        if parsed.get('action') in ["show_digest", "operator_digest", "show_triage_summary", "what_needs_the_most_attention"]:
            from operator_dashboard.digest_utils import aggregate_digest
            digest = aggregate_digest()
            return jsonify({
                'ok': digest.get('ok', False),
                'action': parsed.get('action'),
                'response': digest.get('summary', ''),
                'normalized_event': None,
                'details': digest.get('recommendation', ''),
                'error': '; '.join(digest.get('errors', [])) if digest.get('errors') else None,
                'timestamp': digest.get('timestamp', ''),
            })
        elif parsed.get('action') == "show_event_digest":
            from operator_dashboard.digest_utils import aggregate_event_digest
            digest = aggregate_event_digest(parsed.get('event_id'))
            return jsonify({
                'ok': digest.get('ok', False),
                'action': parsed.get('action'),
                'response': digest.get('digest_summary', ''),
                'normalized_event': parsed.get('event_id'),
                'details': digest.get('recommendation', ''),
                'error': '; '.join(digest.get('errors', [])) if digest.get('errors') else None,
                'timestamp': digest.get('timestamp', ''),
            })
        elif parsed.get('action') == "show_watchlist":
            # Legacy: preserve watchlist summary
            queue = safe_read_queue()
            queue_rows = queue.get('rows', [])
            from operator_dashboard.evidence_utils import queue_row_to_evidence
            evidence_rows = [queue_row_to_evidence(q) for q in queue_rows]
            from operator_dashboard.comparison_utils import get_event_comparison
            comparison_rows = [get_event_comparison(q.get('event_id') or q.get('event_name')) for q in queue_rows]
            from operator_dashboard.timeline_utils import get_event_timeline
            timeline_rows = [get_event_timeline(q.get('event_id') or q.get('event_name')) for q in queue_rows]
            from operator_dashboard.anomaly_utils import AnomalyAggregator
            from operator_dashboard.action_ledger_utils import safe_read_ledger
            ledger_rows = safe_read_ledger()
            aggregator = AnomalyAggregator()
            anomaly_rows = aggregator.aggregate_anomalies(queue_rows, evidence_rows, comparison_rows, timeline_rows, ledger_rows=ledger_rows)
            watchlist = aggregate_watchlist(queue_rows, evidence_rows, comparison_rows, timeline_rows, anomaly_rows, ledger_rows)
            now = datetime.utcnow().isoformat() + 'Z'
            summary = f"Top {len(watchlist)} events needing monitoring"
            return jsonify({
                'ok': True,
                'action': 'show_watchlist',
                'response': summary,
                'watchlist_count': len(watchlist),
                'watchlist': watchlist,
                'timestamp': now,
                'errors': []
            })
        elif parsed.get('action') == "show_event_watchlist":
            event_id = parsed.get('event_id')
            queue = safe_read_queue()
            queue_rows = queue.get('rows', [])
            from operator_dashboard.evidence_utils import queue_row_to_evidence
            evidence_rows = [queue_row_to_evidence(q) for q in queue_rows]
            from operator_dashboard.comparison_utils import get_event_comparison
            comparison_rows = [get_event_comparison(q.get('event_id') or q.get('event_name')) for q in queue_rows]
            from operator_dashboard.timeline_utils import get_event_timeline
            timeline_rows = [get_event_timeline(q.get('event_id') or q.get('event_name')) for q in queue_rows]
            from operator_dashboard.anomaly_utils import AnomalyAggregator
            from operator_dashboard.action_ledger_utils import safe_read_ledger
            ledger_rows = safe_read_ledger()
            aggregator = AnomalyAggregator()
            anomaly_rows = aggregator.aggregate_anomalies(queue_rows, evidence_rows, comparison_rows, timeline_rows, ledger_rows=ledger_rows)
            row = aggregate_event_watchlist(event_id, queue_rows, evidence_rows, comparison_rows, timeline_rows, anomaly_rows, ledger_rows)
            now = datetime.utcnow().isoformat() + 'Z'
            found = row is not None
            return jsonify({
                'ok': True,
                'action': 'show_event_watchlist',
                'event_found': found,
                'event_id': event_id,
                'watch_score': row['watch_score'] if found else 0,
                'priority': row['priority'] if found else 'low',
                'reasons': row['reasons'] if found else [],
                'queue_status': row['queue_status'] if found else None,
                'anomaly_count': row['anomaly_count'] if found else 0,
                'recent_activity_count': row['recent_activity_count'] if found else 0,
                'last_relevant_timestamp': row['last_relevant_timestamp'] if found else '',
                'recommendation': row['recommendation'] if found else '',
                'timestamp': now,
                'errors': [] if found else [f'Event {event_id} not found or not on watchlist']
            })
    # Fallback to normal chat dispatcher
    user_msg = append_chat_message('user', message, action=parsed.get('action',''), normalized_event=parsed.get('normalized_event'))
    result = dashboard_dispatcher(message)
    append_chat_message('assistant', result['response'], action=result['action'], normalized_event=result['normalized_event'], details=result['details'], error=result['error'])
    return jsonify(result)

@app.route('/chat/history', methods=['GET'])
def chat_history():
    return jsonify(load_chat_history())

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run_local_ai', methods=['POST'])
def run_local_ai():
    args = [sys.executable, str(PROJECT_ROOT / 'ai_risa_local_agent.py'), '--execute']
    try:
        result = subprocess.run(args, capture_output=True, text=True, check=False, cwd=str(PROJECT_ROOT))
        return jsonify({
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
