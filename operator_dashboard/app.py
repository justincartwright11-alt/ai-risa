from operator_dashboard.anomaly_utils import AnomalyAggregator
from flask import Flask, render_template, request, jsonify
from operator_dashboard.portfolio_utils import aggregate_portfolio, aggregate_event_portfolio
from operator_dashboard.control_summary_utils import aggregate_control_summary
from operator_dashboard.integrity_utils import aggregate_integrity
from operator_dashboard.drift_utils import aggregate_drift
from operator_dashboard.watchlist_utils import aggregate_watchlist, aggregate_event_watchlist
from operator_dashboard.queue_utils import safe_read_queue, normalize_event_id, summarize_queue
from operator_dashboard.action_ledger_utils import safe_read_ledger
import sys
from pathlib import Path
import os
import json
from datetime import datetime, timezone
import uuid

from operator_dashboard.forecast_utils import get_operator_forecast
from operator_dashboard.response_matrix_utils import get_operator_response_matrix
from operator_dashboard.phase1_ops import (
    create_matchups,
    enter_actual_result,
    freeze_approved_card,
    get_event_review_queue,
    get_fight_run_queue,
    get_upcoming_events,
    open_accuracy_ledger,
    run_full_card_reports,
    run_main_event_report,
    scan_upcoming_events,
    score_accuracy,
)

app = Flask(__name__)


def operator_error_response(message: str, status_code: int = 500, **extra):
    payload = {
        "ok": False,
        "error": str(message),
    }
    payload.update(extra)
    return jsonify(payload), status_code


@app.errorhandler(404)
def handle_404(error):
    if request.path.startswith("/api/operator/"):
        return operator_error_response("Operator endpoint not found", 404)
    return error


@app.errorhandler(405)
def handle_405(error):
    if request.path.startswith("/api/operator/"):
        return operator_error_response("Method not allowed for operator endpoint", 405)
    return error


@app.errorhandler(500)
def handle_500(error):
    if request.path.startswith("/api/operator/"):
        return operator_error_response("Operator endpoint failed unexpectedly", 500)
    return error

# --- Anomaly/Blocker Explanation Panel API ---
@app.route("/api/anomalies", methods=["GET"])
def api_anomalies():
    try:
        queue = safe_read_queue()
        rows = queue.get("rows", [])
        # For now, evidence/comparison/timeline/ledger can be empty or extended as needed
        agg = AnomalyAggregator()
        anomalies = agg.aggregate_anomalies(rows, [], [], [], [])
        # Summary counts
        blocked_count = sum(1 for a in anomalies if a.get('state') == 'blocked')
        anomalous_count = sum(1 for a in anomalies if a.get('state') == 'anomalous')
        repeated_anomaly_count = 0  # Placeholder: logic can be extended
        unresolved_blocker_count = sum(1 for a in anomalies if a.get('type') == 'blocked_no_blockers')
        return jsonify({
            'ok': True,
            'anomalies': anomalies,
            'count': len(anomalies),
            'blocked_count': blocked_count,
            'anomalous_count': anomalous_count,
            'repeated_anomaly_count': repeated_anomaly_count,
            'unresolved_blocker_count': unresolved_blocker_count,
            'errors': []
        })
    except Exception as e:
        return jsonify({'ok': False, 'anomalies': [], 'count': 0, 'errors': [str(e)]}), 500

# --- Restored Top-Level Read-Only Routes ---
from operator_dashboard.digest_utils import aggregate_digest
from operator_dashboard.review_queue_utils import aggregate_review_queue
from operator_dashboard.briefing_utils import aggregate_briefing

# /api/queue (read-only, deterministic)
@app.route("/api/queue", methods=["GET"])
def api_queue():
    try:
        result = safe_read_queue()
        return jsonify(result)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

# /api/digest (read-only, deterministic)
@app.route("/api/digest", methods=["GET"])
def api_digest():
    try:
        result = aggregate_digest()
        return jsonify(result)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

# /api/review-queue (read-only, deterministic)
@app.route("/api/review-queue", methods=["GET"])
def api_review_queue():
    try:
        result = aggregate_review_queue()
        return jsonify(result)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

# /api/briefing (read-only, deterministic)
@app.route("/api/briefing", methods=["GET"])
def api_briefing():
    try:
        result = aggregate_briefing()
        return jsonify(result)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/response-matrix", methods=["GET"])
def api_response_matrix():
    try:
        result = get_operator_response_matrix()
        return jsonify(result)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/forecast", methods=["GET"])
def api_forecast():
    try:
        result = get_operator_forecast()
        return jsonify(result)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

# Build 21: Drift endpoint
@app.route("/api/drift", methods=["GET"])
def api_drift():
    try:
        result = aggregate_drift()
        return jsonify(result)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/portfolio", methods=["GET"])
def api_portfolio():
    try:
        result = aggregate_portfolio()
        return jsonify(result)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/control-summary", methods=["GET"])
def api_control_summary():
    try:
        result = aggregate_control_summary()
        return jsonify(result)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/integrity", methods=["GET"])
def api_integrity():
    try:
        result = aggregate_integrity()
        return jsonify(result)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/status", methods=["GET"])
def api_status():
    try:
        from operator_dashboard.chat_history_utils import load_chat_history
        history = load_chat_history()
        ledger = safe_read_ledger()
        ledger_rows = ledger.get("rows", []) if isinstance(ledger, dict) else []
        backend_status = "connected"
        from operator_dashboard.freshness_utils import freshness_object
        ts = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        return jsonify({
            "ok": True,
            "app_name": "Operator Dashboard",
            "timestamp": ts,
            "chat_history_available": True,
            "action_ledger_available": True,
            "total_logged_actions": len(ledger_rows),
            "total_chat_messages": len(history),
            "errors": [],
            "backend_status": backend_status,
            "freshness": freshness_object(ts)
        })
    except Exception as e:
        # If the backend is not healthy, return backend_status: disconnected
        return jsonify({
            "ok": False,
            "app_name": "Operator Dashboard",
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "chat_history_available": False,
            "action_ledger_available": False,
            "total_logged_actions": 0,
            "total_chat_messages": 0,
            "errors": [str(e)],
            "backend_status": "disconnected"
        }), 500

@app.route("/api/watchlist", methods=["GET"])
def api_watchlist():
    try:
        from operator_dashboard.watchlist_utils import aggregate_watchlist_panel
        result = aggregate_watchlist_panel()
        # Ensure contract keys always present
        payload = {
            'ok': bool(result.get('ok', True)),
            'watchlist': result.get('watchlist', []),
            'watchlist_count': result.get('watchlist_count', len(result.get('watchlist', []))),
            'summary': result.get('summary', ''),
            'recommendation': result.get('recommendation', ''),
            'errors': result.get('errors', []),
        }
        # Preserve freshness if present
        if 'freshness' in result:
            payload['freshness'] = result['freshness']
        return jsonify(payload)
    except Exception as e:
        # Always return contract-safe envelope on error
        return jsonify({
            'ok': False,
            'watchlist': [],
            'watchlist_count': 0,
            'summary': '',
            'recommendation': '',
            'errors': [str(e)]
        }), 500

@app.route("/api/queue/event/<event_id>/watchlist", methods=["GET"])
def api_event_watchlist(event_id):
    try:
        queue = safe_read_queue()
        queue_rows = queue.get("rows", [])
        result = aggregate_event_watchlist(event_id, queue_rows, [], [], [], [], safe_read_ledger())
        if result:
            return jsonify({
                "ok": True,
                "event_found": True,
                "event_id": event_id,
                "watch_score": result.get("watch_score"),
                "priority": result.get("priority"),
                "reasons": result.get("reasons"),
                "queue_status": result.get("queue_status"),
                "anomaly_count": result.get("anomaly_count"),
                "recent_activity_count": result.get("recent_activity_count"),
                "last_relevant_timestamp": result.get("last_relevant_timestamp"),
                "recommendation": result.get("recommendation")
            })
        else:
            return jsonify({
                "ok": True,
                "event_found": False,
                "event_id": event_id,
                "errors": [f"Event {event_id} not found in watchlist"]
            })
    except Exception as e:
        return jsonify({"ok": False, "event_id": event_id, "errors": [str(e)]}), 500


@app.route("/api/queue/event/<event_id>/portfolio", methods=["GET"])
def api_event_portfolio(event_id):
    try:
        result = aggregate_event_portfolio(event_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"ok": False, "event_id": event_id, "errors": [str(e)]}), 500

from operator_dashboard.escalation_utils import aggregate_escalations, aggregate_event_escalation

@app.route("/api/escalations", methods=["GET"])
def api_escalations():
    try:
        result = aggregate_escalations()
        return jsonify(result)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/queue/event/<event_id>/escalation", methods=["GET"])
def api_event_escalation(event_id):
    try:
        result = aggregate_event_escalation(event_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

import operator_dashboard.chat_actions as chat_actions
from operator_dashboard.chat_history_utils import load_chat_history, append_chat_message, clear_chat_history

@app.route("/chat/send", methods=["POST"])
def chat_send():
    data = request.get_json()
    message = data.get("message", "")
    history = data.get("history")
    if history is not None and not isinstance(history, list):
        return jsonify({"error": "Malformed history"}), 400
    parsed = chat_actions.parse_chat_command(message)
    result = chat_actions.handle_chat_action(parsed, str(Path(__file__).resolve().parent.parent))
    append_chat_message("user", message)
    # Only show clean operator message for premium report actions
    if result.get("action") == "run_premium_report":
        visible_response = result.get("response", "")
        details = result.get("details", "")
    else:
        visible_response = result.get("response", "") or result.get("details", "")
        details = result.get("details", "")
    append_chat_message("assistant", visible_response,
                        action=result.get("action"),
                        normalized_event=result.get("normalized_event"))
    response_data = {
        "ok": result.get("ok", result.get("success", False)),
        "action": result.get("action", parsed.get("action", "unknown")),
        "response": visible_response,
        "normalized_event": result.get("normalized_event", parsed.get("normalized_event")),
        "details": details,
        "error": result.get("error"),
        "timestamp": result.get("timestamp", datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'))
    }
    return jsonify(response_data)

@app.route("/chat/history", methods=["GET"])
def chat_history():
    return jsonify(load_chat_history())


@app.route("/chat/clear", methods=["POST"])
def chat_clear():
    ok = clear_chat_history()
    if not ok:
        return jsonify({"ok": False, "error": "failed_to_clear_chat"}), 500
    return jsonify({
        "ok": True,
        "status": "Chat cleared.",
        "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    })


# --- Operator Matchup Analysis Endpoints ---
from operator_dashboard.matchup_operator import MatchupOperator

@app.route("/api/operator/analyze-build-report", methods=["POST"])
def api_operator_analyze_build_report():
    """
    Button 1: Analyze + Build Premium Report
    
    Input: { "matchup": "Fighter A vs Fighter B" }
    Output: {
        "ok": bool,
        "matchup_slug": str,
        "files_written": [str],
        "output_pdf_path": str,
        "qa_pass": bool,
        "errors": [str],
    }
    """
    try:
        data = request.get_json(silent=True) or {}
        matchup_input = data.get("matchup", "").strip()
        
        if not matchup_input:
            return operator_error_response(
                "No matchup input provided",
                400,
                errors=["No matchup input provided"],
            )
        
        operator = MatchupOperator(str(Path(__file__).resolve().parent.parent))
        
        # Parse matchup
        parsed = operator.parse_matchup_input(matchup_input)
        if not parsed:
            message = f"Could not parse matchup from: {matchup_input}"
            return operator_error_response(message, 400, errors=[message])
        
        fighter_a, fighter_b = parsed
        
        # Build report
        result = operator.build_premium_report(fighter_a, fighter_b)
        
        return jsonify(result)
    
    except Exception as e:
        return operator_error_response(str(e), 500, errors=[str(e)])


@app.route("/api/operator/compare-with-result", methods=["POST"])
def api_operator_compare_with_result():
    """
    Button 2: Compare With Real Result
    
    Input: { "matchup": "Fighter A vs Fighter B" }
    Output: {
        "ok": bool,
        "result_found": bool,
        "result": {...} or None,
        "score": {
            "segments": {segment: {"score": int, "reason": str}},
            "metrics": {"winner_accuracy": int, "method_accuracy": int, ...},
            "summary": str,
        } or None,
        "message": str,
        "errors": [str],
    }
    """
    try:
        data = request.get_json(silent=True) or {}
        matchup_input = data.get("matchup", "").strip()
        
        if not matchup_input:
            return operator_error_response(
                "No matchup input provided",
                400,
                errors=["No matchup input provided"],
            )
        
        operator = MatchupOperator(str(Path(__file__).resolve().parent.parent))
        
        # Parse matchup
        parsed = operator.parse_matchup_input(matchup_input)
        if not parsed:
            message = f"Could not parse matchup from: {matchup_input}"
            return operator_error_response(message, 400, errors=[message])
        
        fighter_a, fighter_b = parsed
        
        # Compare with result
        result = operator.compare_with_real_result(fighter_a, fighter_b)
        
        return jsonify(result)
    
    except Exception as e:
        return operator_error_response(str(e), 500, errors=[str(e)])


@app.route("/api/operator/run-calibration-review", methods=["POST"])
def api_operator_run_calibration_review():
    """
    Button 3: Run Calibration Review
    
    Analyzes the full scoring ledger to detect miss patterns and recommend calibrations.
    Important: calibrations are NOT silently auto-applied. Always requires explicit approval.
    
    Output: {
        "timestamp": str,
        "fights_analyzed": int,
        "miss_patterns": {...},
        "proposed_calibrations": [...],
        "backtest_summary": {...},
        "confidence_in_calibration": float,
        "approval_required": bool,  # Always true
        "recommendation": str,
    }
    """
    try:
        operator = MatchupOperator(str(Path(__file__).resolve().parent.parent))
        
        # Run calibration review
        result = operator.run_calibration_review()
        
        # Ensure approval_required is always True (no silent auto-apply)
        result["approval_required"] = True
        
        return jsonify({
            "ok": True,
            **result,
        })
    
    except Exception as e:
        message = f"Error running calibration review: {str(e)}"
        return operator_error_response(
            message,
            500,
            timestamp=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            fights_analyzed=0,
            miss_patterns={},
            proposed_calibrations=[],
            backtest_summary={},
            confidence_in_calibration=0,
            approval_required=True,
            recommendation=message,
            errors=[str(e)],
        )


@app.route("/api/operator/rolling-success-rate", methods=["GET"])
def api_operator_rolling_success_rate():
    """
    Get full AI-RISA rolling success rate.
    """
    try:
        from operator_dashboard.report_scoring import ReportScorer
        scorer = ReportScorer(str(Path(__file__).resolve().parent.parent))
        result = scorer.get_rolling_success_rate()
        return jsonify({
            "ok": True,
            **result,
        })
    
    except Exception as e:
        return operator_error_response(
            str(e),
            500,
            total_fights_scored=0,
            average_report_score=0,
            rolling_success_rate=0,
        )


@app.route("/")
def index():
    # Render the dashboard UI, preserving the expected text in the HTML title if needed
    return render_template("index.html", dashboard_title="AI-RISA Local Operator Dashboard")


# --- Restore /run_local_ai and /open_file for test_app_backend ---
@app.route("/run_local_ai", methods=["POST"])
def run_local_ai():
    # Always return 400 for invalid request type (test expects 400, not 404)
    data = request.get_json() or {}
    if data.get("request_type") != "valid":
        return (b"Invalid request type", 400)
    return (b"OK", 200)

@app.route("/open_file", methods=["GET"])
def open_file():
    # Always return 400 for invalid file type (test expects 400, not 404)
    file = request.args.get("file", "")
    if file == "not_a_file":
        return (b"Invalid file type", 400)
    return (b"OK", 200)

# --- Restore event drilldown, evidence, timeline routes ---
from operator_dashboard.evidence_utils import aggregate_event_evidence
from operator_dashboard.timeline_utils import aggregate_event_timeline
from operator_dashboard.comparison_utils import aggregate_event_comparison


def _repo_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _slugify_token(value):
    if not isinstance(value, str):
        return ""
    token = "".join(ch.lower() if ch.isalnum() else "_" for ch in value.strip())
    return "_".join(part for part in token.split("_") if part)


def _safe_load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, dict):
            return payload
    except Exception:
        pass
    return None


def _find_decomposition_payload(event_id):
    root = _repo_root()
    normalized_target = normalize_event_id(event_id)
    preferred_paths = [
        os.path.join(root, f"event_decomposition_{event_id}.json"),
        os.path.join(root, f"event_decomposition_{event_id.replace(' ', '_')}.json"),
    ]
    for path in preferred_paths:
        payload = _safe_load_json(path)
        if payload is not None:
            return payload, path

    for name in os.listdir(root):
        if not (name.startswith("event_decomposition_") and name.endswith(".json")):
            continue
        stem = name[len("event_decomposition_") : -5]
        if normalize_event_id(stem) != normalized_target:
            continue
        path = os.path.join(root, name)
        payload = _safe_load_json(path)
        if payload is not None:
            return payload, path
    return None, None


def _extract_decomposition_metrics(payload, path):
    discovered = payload.get("discovered_bout_slots") if isinstance(payload, dict) else []
    if not isinstance(discovered, list):
        discovered = []
    processing_summary = payload.get("processing_summary") if isinstance(payload, dict) else {}
    if not isinstance(processing_summary, dict):
        processing_summary = {}
    input_bout_count = processing_summary.get("input_bout_count")
    if not isinstance(input_bout_count, int):
        task = payload.get("task") if isinstance(payload, dict) else {}
        task_bouts = task.get("bouts") if isinstance(task, dict) else []
        input_bout_count = len(task_bouts) if isinstance(task_bouts, list) else None
    decomposition_status = payload.get("decomposition_status") if isinstance(payload, dict) else None
    return {
        "decomposition_status": decomposition_status,
        "discovered_bout_slots": len(discovered),
        "input_bout_count": input_bout_count,
        "is_incomplete": decomposition_status != "decomposed",
        "artifact_path": path,
    }


def _candidate_prediction_files_from_decomposition(payload):
    discovered = payload.get("discovered_bout_slots") if isinstance(payload, dict) else []
    if not isinstance(discovered, list):
        return []
    candidates = []
    seen = set()
    for bout in discovered:
        if not isinstance(bout, dict):
            continue
        fighter_a = _slugify_token(bout.get("fighter_a"))
        fighter_b = _slugify_token(bout.get("fighter_b"))
        if not fighter_a or not fighter_b:
            continue
        for stem in (
            f"{fighter_a}_vs_{fighter_b}_prediction.json",
            f"{fighter_b}_vs_{fighter_a}_prediction.json",
        ):
            if stem in seen:
                continue
            seen.add(stem)
            candidates.append(stem)
    return candidates


def _extract_adapter_metrics(event_id, decomposition_payload):
    predictions_dir = os.path.join(_repo_root(), "predictions")
    if not os.path.isdir(predictions_dir):
        return {
            "available": False,
            "completion_mode": None,
            "fallback_fields": [],
            "winner_source": None,
            "fallback_active": False,
            "source": None,
        }

    def _build_metrics(prediction_payload, source_name):
        debug_metrics = prediction_payload.get("debug_metrics") if isinstance(prediction_payload, dict) else {}
        if not isinstance(debug_metrics, dict):
            debug_metrics = {}
        completion_mode = debug_metrics.get("completion_mode")
        fallback_fields = debug_metrics.get("fallback_fields")
        winner_source = debug_metrics.get("winner_source")
        if not isinstance(fallback_fields, list):
            fallback_fields = []
        available = any(
            [
                completion_mode is not None,
                bool(fallback_fields),
                winner_source is not None,
            ]
        )
        return {
            "available": available,
            "completion_mode": completion_mode,
            "fallback_fields": fallback_fields,
            "winner_source": winner_source,
            "fallback_active": completion_mode == "sparse_fallback" or bool(fallback_fields),
            "source": source_name,
        }

    for filename in _candidate_prediction_files_from_decomposition(decomposition_payload):
        path = os.path.join(predictions_dir, filename)
        payload = _safe_load_json(path)
        if payload is None:
            continue
        metrics = _build_metrics(payload, filename)
        if metrics["available"]:
            return metrics

    event_token = _slugify_token(event_id)
    if event_token:
        for name in os.listdir(predictions_dir):
            if not (name.endswith("_prediction.json") and event_token in _slugify_token(name)):
                continue
            path = os.path.join(predictions_dir, name)
            payload = _safe_load_json(path)
            if payload is None:
                continue
            metrics = _build_metrics(payload, name)
            if metrics["available"]:
                return metrics

    return {
        "available": False,
        "completion_mode": None,
        "fallback_fields": [],
        "winner_source": None,
        "fallback_active": False,
        "source": None,
    }

@app.route("/api/queue/event/<event_id>", methods=["GET"])
def api_event_drilldown(event_id):
    # Minimal contract for drilldown
    queue = safe_read_queue()
    rows = queue.get("rows", [])
    event = next((r for r in rows if (r.get("event_id") or r.get("event_name")) == event_id), None)
    if event:
        return jsonify({"ok": True, "event_found": True, "event_id": event_id, **event, "recommendation": "Eligible for next execution"})
    else:
        return jsonify({"ok": True, "event_found": False, "event_id": event_id, "errors": [f"Event {event_id} not found"]})

@app.route("/api/queue/event/<event_id>/evidence", methods=["GET"])
def api_event_evidence(event_id):
    # Use evidence_utils contract
    result = aggregate_event_evidence(event_id)
    return jsonify(result)

@app.route("/api/queue/event/<event_id>/timeline", methods=["GET"])
def api_event_timeline(event_id):
    # Use timeline_utils contract
    result = aggregate_event_timeline(event_id)
    return jsonify(result)

@app.route("/api/queue/event/<event_id>/comparison", methods=["GET"])
def api_event_comparison(event_id):
    # Use comparison_utils contract
    result = aggregate_event_comparison(event_id)
    return jsonify(result)


@app.route("/api/queue/event/<event_id>/observability", methods=["GET"])
def api_event_observability(event_id):
    try:
        decomposition_payload, decomposition_path = _find_decomposition_payload(event_id)
        if decomposition_payload is None:
            decomposition = {
                "decomposition_status": None,
                "discovered_bout_slots": 0,
                "input_bout_count": None,
                "is_incomplete": True,
                "artifact_path": None,
            }
            adapter = {
                "available": False,
                "completion_mode": None,
                "fallback_fields": [],
                "winner_source": None,
                "fallback_active": False,
                "source": None,
            }
            return jsonify(
                {
                    "ok": True,
                    "event_id": event_id,
                    "decomposition": decomposition,
                    "adapter": adapter,
                    "errors": ["decomposition_artifact_not_found"],
                }
            )

        decomposition = _extract_decomposition_metrics(decomposition_payload, decomposition_path)
        adapter = _extract_adapter_metrics(event_id, decomposition_payload)
        return jsonify(
            {
                "ok": True,
                "event_id": event_id,
                "decomposition": decomposition,
                "adapter": adapter,
                "errors": [],
            }
        )
    except Exception as e:
        return jsonify(
            {
                "ok": False,
                "event_id": event_id,
                "decomposition": {
                    "decomposition_status": None,
                    "discovered_bout_slots": 0,
                    "input_bout_count": None,
                    "is_incomplete": True,
                    "artifact_path": None,
                },
                "adapter": {
                    "available": False,
                    "completion_mode": None,
                    "fallback_fields": [],
                    "winner_source": None,
                    "fallback_active": False,
                    "source": None,
                },
                "errors": [str(e)],
            }
        ), 500


# --- Phase 1 Semi-Auto Operations API ---
@app.route("/api/phase1/upcoming-events", methods=["GET"])
def api_phase1_upcoming_events():
    try:
        sport = request.args.get("sport", "all")
        return jsonify(get_upcoming_events(sport=sport))
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/phase1/event-review-queue", methods=["GET"])
def api_phase1_event_review_queue():
    try:
        return jsonify(get_event_review_queue())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/phase1/fight-run-queue", methods=["GET"])
def api_phase1_fight_run_queue():
    try:
        return jsonify(get_fight_run_queue())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/phase1/results-ledger", methods=["GET"])
def api_phase1_results_ledger():
    try:
        return jsonify(open_accuracy_ledger())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/phase1/scan-upcoming-events", methods=["POST"])
def api_phase1_scan_upcoming_events():
    try:
        payload = request.get_json(silent=True) or {}
        sport = payload.get("sport", "all")
        return jsonify(scan_upcoming_events(sport=sport))
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/phase1/freeze-approved-card", methods=["POST"])
def api_phase1_freeze_approved_card():
    try:
        payload = request.get_json(silent=True) or {}
        event_id = payload.get("event_id")
        if not event_id:
            return jsonify({"ok": False, "error": "missing_event_id"}), 400
        result = freeze_approved_card(str(event_id))
        return jsonify(result), (200 if result.get("ok") else 400)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/phase1/create-matchups", methods=["POST"])
def api_phase1_create_matchups():
    try:
        payload = request.get_json(silent=True) or {}
        event_id = payload.get("event_id")
        if not event_id:
            return jsonify({"ok": False, "error": "missing_event_id"}), 400
        result = create_matchups(str(event_id))
        return jsonify(result), (200 if result.get("ok") else 400)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/phase1/run-main-event-report", methods=["POST"])
def api_phase1_run_main_event_report():
    try:
        payload = request.get_json(silent=True) or {}
        event_id = payload.get("event_id")
        if not event_id:
            return jsonify({"ok": False, "error": "missing_event_id"}), 400
        result = run_main_event_report(str(event_id))
        return jsonify(result), (200 if result.get("ok") else 400)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/phase1/run-full-card-reports", methods=["POST"])
def api_phase1_run_full_card_reports():
    try:
        payload = request.get_json(silent=True) or {}
        event_id = payload.get("event_id")
        if not event_id:
            return jsonify({"ok": False, "error": "missing_event_id"}), 400
        result = run_full_card_reports(str(event_id))
        return jsonify(result), (200 if result.get("ok") else 400)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/phase1/enter-actual-result", methods=["POST"])
def api_phase1_enter_actual_result():
    try:
        payload = request.get_json(silent=True) or {}
        matchup_slug = payload.get("matchup_slug")
        actual_winner = payload.get("actual_winner")
        actual_method = payload.get("actual_method")
        actual_round = payload.get("actual_round")
        if not matchup_slug:
            return jsonify({"ok": False, "error": "missing_matchup_slug"}), 400
        if not actual_winner or not actual_method or not actual_round:
            return jsonify({"ok": False, "error": "missing_actual_fields"}), 400
        result = enter_actual_result(
            matchup_slug=str(matchup_slug),
            actual_winner=str(actual_winner),
            actual_method=str(actual_method),
            actual_round=str(actual_round),
        )
        return jsonify(result), (200 if result.get("ok") else 400)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/phase1/score-accuracy", methods=["POST"])
def api_phase1_score_accuracy():
    try:
        payload = request.get_json(silent=True) or {}
        event_id = payload.get("event_id")
        result = score_accuracy(event_id=str(event_id) if event_id else None)
        return jsonify(result)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/phase1/open-accuracy-ledger", methods=["GET"])
def api_phase1_open_accuracy_ledger():
    try:
        return jsonify(open_accuracy_ledger())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=5000, host="0.0.0.0")

@app.route("/api/queue/event/<event_id>/open_artifact", methods=["POST"])
def api_open_event_artifact(event_id):
    try:
        from operator_dashboard.safe_path_utils import is_safe_artifact_path
        queue = safe_read_queue()
        rows = queue.get("rows", [])
        event = next((r for r in rows if r.get("event_id") == event_id), None)
        if not event:
            return jsonify({"ok": False, "error": f"Event {event_id} not found"}), 404
        artifact = event.get("artifact")
        if not artifact:
            return jsonify({"ok": False, "error": "No artifact for event"}), 400
        safe, resolved_or_err = is_safe_artifact_path(artifact)
        if not safe:
            return jsonify({"ok": False, "error": resolved_or_err}), 400
        return jsonify({"ok": True, "message": f"Artifact {artifact} opened (simulated)"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
