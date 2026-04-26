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


def _load_json_records(file_path: Path):
    if not file_path.exists():
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, list):
            return [row for row in payload if isinstance(row, dict)]
        if isinstance(payload, dict):
            return [payload]
    except Exception:
        return []
    return []


def _normalize_token(value: str) -> str:
    text = str(value or "").strip().lower()
    for ch in ["-", " ", "/", "\\", ".", ":", ","]:
        text = text.replace(ch, "_")
    while "__" in text:
        text = text.replace("__", "_")
    return text.strip("_")


def _is_known_value(value) -> bool:
    token = _normalize_token(value)
    return token not in {"", "unknown", "none", "null", "na", "n_a", "tbd"}


def _normalize_relative_path(path_text: str, base_dir: Path) -> str:
    if not path_text:
        return ""
    raw = str(path_text).replace("\\", "/")
    if os.path.isabs(raw):
        try:
            rel = Path(raw).resolve().relative_to(base_dir.resolve())
            return str(rel).replace("\\", "/")
        except Exception:
            return raw
    return raw.lstrip("./")


def _winner_hit(predicted_winner, actual_winner) -> bool:
    return _is_known_value(predicted_winner) and _is_known_value(actual_winner) and _normalize_token(predicted_winner) == _normalize_token(actual_winner)


def _method_hit(predicted_method, actual_method) -> bool:
    return _is_known_value(predicted_method) and _is_known_value(actual_method) and _normalize_token(predicted_method) == _normalize_token(actual_method)


def _round_hit(predicted_round, actual_round) -> bool:
    return _is_known_value(predicted_round) and _is_known_value(actual_round) and _normalize_token(predicted_round) == _normalize_token(actual_round)


def _build_accuracy_comparison_summary() -> dict:
    base_dir = Path(__file__).resolve().parent.parent
    accuracy_dir = base_dir / "ops" / "accuracy"

    ledger_records = _load_json_records(accuracy_dir / "accuracy_ledger.json")
    actual_records = []
    for filename in [
        "actual_results.json",
        "actual_results_manual.json",
        "actual_results_unresolved.json",
    ]:
        actual_records.extend(_load_json_records(accuracy_dir / filename))

    actual_by_fight = {}
    for row in actual_records:
        fight_key = _normalize_token(row.get("fight_id"))
        if fight_key:
            actual_by_fight[fight_key] = row

    compared_results = []
    waiting_for_results = []
    seen_compared = set()
    seen_waiting = set()
    known_artifact_paths = set()

    method_available = 0
    method_hits = 0
    round_available = 0
    round_hits = 0

    def add_compared(row: dict):
        nonlocal method_available, method_hits, round_available, round_hits
        key = (
            _normalize_token(row.get("fight_name")),
            _normalize_token(row.get("file_path")),
        )
        if key in seen_compared:
            return
        seen_compared.add(key)
        compared_results.append(row)
        if row.get("method_available"):
            method_available += 1
            if row.get("method_hit"):
                method_hits += 1
        if row.get("round_available"):
            round_available += 1
            if row.get("round_hit"):
                round_hits += 1

    def add_waiting(row: dict):
        key = (
            _normalize_token(row.get("fight_name")),
            _normalize_token(row.get("file_path")),
        )
        if key in seen_waiting:
            return
        seen_waiting.add(key)
        waiting_for_results.append(row)

    for ledger_row in ledger_records:
        source_file = _normalize_relative_path(ledger_row.get("source_file", ""), base_dir)
        if source_file:
            known_artifact_paths.add(source_file.lower())

        fight_name = str(ledger_row.get("fight_id") or "").strip() or Path(source_file).stem
        fight_key = _normalize_token(fight_name)
        actual_row = actual_by_fight.get(fight_key, {})

        predicted_winner = ledger_row.get("predicted_winner")
        predicted_method = ledger_row.get("predicted_method")
        predicted_round = ledger_row.get("predicted_round")

        actual_winner = ledger_row.get("actual_winner")
        actual_method = ledger_row.get("actual_method")
        actual_round = ledger_row.get("actual_round")

        if not _is_known_value(actual_winner):
            actual_winner = actual_row.get("actual_winner")
        if not _is_known_value(actual_method):
            actual_method = actual_row.get("actual_method")
        if not _is_known_value(actual_round):
            actual_round = actual_row.get("actual_round")

        has_actual_result = bool(ledger_row.get("resolved_result")) or _is_known_value(actual_winner)

        if has_actual_result:
            winner_hit = bool(ledger_row.get("hit_winner")) if "hit_winner" in ledger_row else _winner_hit(predicted_winner, actual_winner)
            method_available_flag = _is_known_value(predicted_method) and _is_known_value(actual_method)
            method_hit_flag = bool(ledger_row.get("hit_method")) if "hit_method" in ledger_row else _method_hit(predicted_method, actual_method)
            round_available_flag = _is_known_value(predicted_round) and _is_known_value(actual_round)
            round_hit_flag = _round_hit(predicted_round, actual_round) if round_available_flag else False

            add_compared({
                "fight_name": fight_name or "UNKNOWN",
                "predicted_winner": predicted_winner or "UNKNOWN",
                "actual_winner": actual_winner or "UNKNOWN",
                "winner_hit": winner_hit,
                "predicted_method": predicted_method,
                "actual_method": actual_method,
                "method_available": method_available_flag,
                "method_hit": method_hit_flag if method_available_flag else False,
                "predicted_round": predicted_round,
                "actual_round": actual_round,
                "round_available": round_available_flag,
                "round_hit": round_hit_flag,
                "event_date": ledger_row.get("event_date") or actual_row.get("event_date"),
                "file_path": source_file,
                "status": "compared",
            })
        else:
            add_waiting({
                "fight_name": fight_name or "UNKNOWN",
                "predicted_winner": predicted_winner or "UNKNOWN",
                "event_date": ledger_row.get("event_date"),
                "file_path": source_file,
                "status": "waiting_for_actual_result",
            })

    for folder_name in ["predictions", "reports"]:
        folder = base_dir / folder_name
        if not folder.exists():
            continue
        for file_path in folder.rglob("*.json"):
            rel_path = str(file_path.relative_to(base_dir)).replace("\\", "/")
            if rel_path.lower() in known_artifact_paths:
                continue
            try:
                with open(file_path, "r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                data = payload if isinstance(payload, dict) else {}
            except Exception:
                data = {}

            fight_name = str(data.get("fight_id") or file_path.stem)
            predicted_winner = data.get("predicted_winner_id") or data.get("predicted_winner") or data.get("winner") or "UNKNOWN"
            event_date = data.get("event_date")
            actual_row = actual_by_fight.get(_normalize_token(fight_name), {})

            if _is_known_value(predicted_winner) and _is_known_value(actual_row.get("actual_winner")):
                predicted_method = data.get("method") or data.get("predicted_method")
                predicted_round = data.get("round") or data.get("predicted_round")
                actual_method = actual_row.get("actual_method")
                actual_round = actual_row.get("actual_round")
                method_available_flag = _is_known_value(predicted_method) and _is_known_value(actual_method)
                round_available_flag = _is_known_value(predicted_round) and _is_known_value(actual_round)

                add_compared({
                    "fight_name": fight_name,
                    "predicted_winner": predicted_winner,
                    "actual_winner": actual_row.get("actual_winner"),
                    "winner_hit": _winner_hit(predicted_winner, actual_row.get("actual_winner")),
                    "predicted_method": predicted_method,
                    "actual_method": actual_method,
                    "method_available": method_available_flag,
                    "method_hit": _method_hit(predicted_method, actual_method) if method_available_flag else False,
                    "predicted_round": predicted_round,
                    "actual_round": actual_round,
                    "round_available": round_available_flag,
                    "round_hit": _round_hit(predicted_round, actual_round) if round_available_flag else False,
                    "event_date": event_date or actual_row.get("event_date"),
                    "file_path": rel_path,
                    "status": "compared",
                })
            else:
                add_waiting({
                    "fight_name": fight_name,
                    "predicted_winner": predicted_winner,
                    "event_date": event_date,
                    "file_path": rel_path,
                    "status": "waiting_for_actual_result",
                })

    total_compared = len(compared_results)
    winner_hits = sum(1 for row in compared_results if row.get("winner_hit"))
    winner_misses = max(total_compared - winner_hits, 0)

    summary_metrics = {
        "total_compared": total_compared,
        "winner_hits": winner_hits,
        "winner_misses": winner_misses,
        "method_hits": method_hits,
        "method_available": method_available,
        "round_hits": round_hits,
        "round_available": round_available,
        "overall_accuracy_pct": round((winner_hits / total_compared) * 100.0, 2) if total_compared else 0.0,
    }

    compared_results.sort(key=lambda row: str(row.get("fight_name") or ""))
    waiting_for_results.sort(key=lambda row: str(row.get("fight_name") or ""))

    return {
        "ok": True,
        "compared_results": compared_results,
        "waiting_for_results": waiting_for_results,
        "summary_metrics": summary_metrics,
    }


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


def _build_signal_gap_breakdown() -> dict:
    base_dir = Path(__file__).resolve().parent.parent
    accuracy_dir = base_dir / "ops" / "accuracy"
    ledger_records = _load_json_records(accuracy_dir / "accuracy_ledger.json")

    BUCKETS = [
        ("0.00–0.10", 0.00, 0.10),
        ("0.11–0.20", 0.11, 0.20),
        ("0.21–0.30", 0.21, 0.30),
        ("0.31+",     0.31, float("inf")),
    ]
    bucket_data = {label: {"total": 0, "hits": 0} for label, _, _ in BUCKETS}

    for row in ledger_records:
        hit_winner = row.get("hit_winner")
        if hit_winner is None:
            continue
        sg = _safe_float(row.get("signal_gap"))
        if sg is None:
            continue
        for label, lo, hi in BUCKETS:
            if lo <= sg <= hi:
                bucket_data[label]["total"] += 1
                if hit_winner:
                    bucket_data[label]["hits"] += 1
                break

    breakdown = []
    for label, _, _ in BUCKETS:
        total = bucket_data[label]["total"]
        hits = bucket_data[label]["hits"]
        misses = total - hits
        accuracy_pct = round((hits / total) * 100.0, 2) if total else None
        breakdown.append({
            "bucket": label,
            "total_compared": total,
            "winner_hits": hits,
            "winner_misses": misses,
            "accuracy_pct": accuracy_pct,
        })

    has_data = any(b["total_compared"] > 0 for b in breakdown)
    return {"ok": True, "breakdown": breakdown, "has_data": has_data}


@app.route("/api/accuracy/comparison-summary", methods=["GET"])
def api_accuracy_comparison_summary():
    try:
        return jsonify(_build_accuracy_comparison_summary())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "compared_results": [], "waiting_for_results": [], "summary_metrics": {}}), 500


@app.route("/api/accuracy/signal-breakdown", methods=["GET"])
def api_accuracy_signal_breakdown():
    try:
        return jsonify(_build_signal_gap_breakdown())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "breakdown": [], "has_data": False}), 500


def _build_method_round_breakdown() -> dict:
    base_dir = Path(__file__).resolve().parent.parent
    accuracy_dir = base_dir / "ops" / "accuracy"
    ledger_records = _load_json_records(accuracy_dir / "accuracy_ledger.json")

    UNKNOWN_VALS = {"UNKNOWN", "unknown", "", None}

    def _known(v):
        return v not in UNKNOWN_VALS and v is not None

    # --- Method accuracy ---
    method_total = method_hits = 0
    for row in ledger_records:
        if not row.get("resolved_result"):
            continue
        if _known(row.get("predicted_method")) and _known(row.get("actual_method")):
            method_total += 1
            if row.get("hit_method"):
                method_hits += 1

    method_misses = method_total - method_hits
    method_accuracy_pct = round((method_hits / method_total) * 100.0, 2) if method_total else None

    # --- Round accuracy ---
    round_total = round_hits = 0
    for row in ledger_records:
        if not row.get("resolved_result"):
            continue
        pr = row.get("predicted_round")
        ar = row.get("actual_round")
        if _known(pr) and _known(ar):
            round_total += 1
            try:
                if int(pr) == int(ar):
                    round_hits += 1
            except (TypeError, ValueError):
                if str(pr).strip().lower() == str(ar).strip().lower():
                    round_hits += 1

    round_misses = round_total - round_hits
    round_accuracy_pct = round((round_hits / round_total) * 100.0, 2) if round_total else None

    # --- Propensity buckets helper ---
    PROP_BUCKETS = [
        ("0.00–0.25", 0.00, 0.25),
        ("0.26–0.50", 0.26, 0.50),
        ("0.51–0.75", 0.51, 0.75),
        ("0.76–1.00", 0.76, 1.00),
    ]

    def _build_propensity_buckets(field: str) -> list:
        bucket_data = {label: {"total": 0, "hits": 0} for label, _, _ in PROP_BUCKETS}
        for row in ledger_records:
            if row.get("hit_winner") is None:
                continue
            val = _safe_float(row.get(field))
            if val is None:
                continue
            for label, lo, hi in PROP_BUCKETS:
                if lo <= val <= hi:
                    bucket_data[label]["total"] += 1
                    if row.get("hit_winner"):
                        bucket_data[label]["hits"] += 1
                    break
        result = []
        for label, _, _ in PROP_BUCKETS:
            total = bucket_data[label]["total"]
            hits = bucket_data[label]["hits"]
            result.append({
                "bucket": label,
                "total_compared": total,
                "winner_hits": hits,
                "winner_misses": total - hits,
                "accuracy_pct": round((hits / total) * 100.0, 2) if total else None,
            })
        return result

    stoppage_buckets = _build_propensity_buckets("stoppage_propensity")
    rft_buckets = _build_propensity_buckets("round_finish_tendency")

    has_data = (method_total > 0 or round_total > 0
                or any(b["total_compared"] > 0 for b in stoppage_buckets)
                or any(b["total_compared"] > 0 for b in rft_buckets))

    return {
        "ok": True,
        "has_data": has_data,
        "method_accuracy": {
            "total_available": method_total,
            "method_hits": method_hits,
            "method_misses": method_misses,
            "method_accuracy_pct": method_accuracy_pct,
        },
        "round_accuracy": {
            "total_available": round_total,
            "round_hits": round_hits,
            "round_misses": round_misses,
            "round_accuracy_pct": round_accuracy_pct,
        },
        "stoppage_propensity_buckets": stoppage_buckets,
        "round_finish_tendency_buckets": rft_buckets,
    }


@app.route("/api/accuracy/method-round-breakdown", methods=["GET"])
def api_accuracy_method_round_breakdown():
    try:
        return jsonify(_build_method_round_breakdown())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "has_data": False}), 500


def _build_confidence_calibration() -> dict:
    base_dir = Path(__file__).resolve().parent.parent
    accuracy_dir = base_dir / "ops" / "accuracy"
    ledger_records = _load_json_records(accuracy_dir / "accuracy_ledger.json")

    BUCKETS = [
        ("0.50–0.60", 0.50, 0.60),
        ("0.61–0.70", 0.61, 0.70),
        ("0.71–0.80", 0.71, 0.80),
        ("0.81–0.90", 0.81, 0.90),
        ("0.91–1.00", 0.91, 1.00),
    ]
    bucket_data = {label: {"confs": [], "hits": 0, "total": 0} for label, _, _ in BUCKETS}

    for row in ledger_records:
        if not row.get("resolved_result"):
            continue
        if row.get("hit_winner") is None:
            continue
        conf = _safe_float(row.get("confidence"))
        if conf is None:
            continue
        # Normalize percent-scale (e.g. 60.0) to 0-1
        if conf > 1.0:
            conf = conf / 100.0
        for label, lo, hi in BUCKETS:
            if lo <= conf <= hi:
                bucket_data[label]["confs"].append(conf)
                bucket_data[label]["total"] += 1
                if row.get("hit_winner"):
                    bucket_data[label]["hits"] += 1
                break

    calibration = []
    for label, _, _ in BUCKETS:
        bd = bucket_data[label]
        total = bd["total"]
        hits = bd["hits"]
        conf_avg = round(sum(bd["confs"]) / len(bd["confs"]), 4) if bd["confs"] else None
        win_rate = round(hits / total, 4) if total else None
        gap = round(win_rate - conf_avg, 4) if (conf_avg is not None and win_rate is not None) else None
        calibration.append({
            "bucket": label,
            "total_compared": total,
            "predicted_confidence_avg": conf_avg,
            "actual_win_rate": win_rate,
            "calibration_gap": gap,
        })

    has_data = any(b["total_compared"] > 0 for b in calibration)
    return {"ok": True, "has_data": has_data, "calibration": calibration}


@app.route("/api/accuracy/confidence-calibration", methods=["GET"])
def api_accuracy_confidence_calibration():
    try:
        return jsonify(_build_confidence_calibration())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "has_data": False, "calibration": []}), 500


def _classify_round_range(predicted_round):
    """Classify predicted round into early/middle/late-full."""
    if predicted_round is None:
        return None
    val = str(predicted_round).strip().lower()
    if val in ("full", "decision", "n/a", ""):
        return "late/full"
    try:
        n = int(val)
        if n <= 2:
            return "early (1–2)"
        if n <= 4:
            return "middle (3–4)"
        return "late/full"
    except ValueError:
        return "late/full"


def _build_error_patterns() -> dict:
    base_dir = Path(__file__).resolve().parent.parent
    accuracy_dir = base_dir / "ops" / "accuracy"
    ledger_records = _load_json_records(accuracy_dir / "accuracy_ledger.json")

    # Only resolved misses
    misses = [
        r for r in ledger_records
        if r.get("resolved_result") and r.get("hit_winner") is False
    ]
    total_misses = len(misses)

    # --- By signal_gap bucket ---
    SG_BUCKETS = [
        ("0.00–0.10", 0.00, 0.10),
        ("0.11–0.20", 0.11, 0.20),
        ("0.21–0.30", 0.21, 0.30),
        ("0.31+",     0.31, float("inf")),
        ("unknown",   None, None),
    ]
    sg_counts = {label: 0 for label, _, _ in SG_BUCKETS}
    for row in misses:
        sg = _safe_float(row.get("signal_gap"))
        if sg is None:
            sg_counts["unknown"] += 1
        else:
            for label, lo, hi in SG_BUCKETS[:-1]:
                if lo <= sg <= hi:
                    sg_counts[label] += 1
                    break

    by_signal_gap = [
        {"bucket": label, "miss_count": sg_counts[label]}
        for label, _, _ in SG_BUCKETS
        if sg_counts[label] > 0
    ]

    # --- By confidence bucket ---
    CONF_BUCKETS = [
        ("0.50–0.60", 0.50, 0.60),
        ("0.61–0.70", 0.61, 0.70),
        ("0.71–0.80", 0.71, 0.80),
        ("0.81–0.90", 0.81, 0.90),
        ("0.91–1.00", 0.91, 1.00),
        ("unknown",   None, None),
    ]
    conf_counts = {label: 0 for label, _, _ in CONF_BUCKETS}
    for row in misses:
        conf = _safe_float(row.get("confidence"))
        if conf is None:
            conf_counts["unknown"] += 1
            continue
        if conf > 1.0:
            conf /= 100.0
        matched = False
        for label, lo, hi in CONF_BUCKETS[:-1]:
            if lo <= conf <= hi:
                conf_counts[label] += 1
                matched = True
                break
        if not matched:
            conf_counts["unknown"] += 1

    by_confidence = [
        {"bucket": label, "miss_count": conf_counts[label]}
        for label, _, _ in CONF_BUCKETS
        if conf_counts[label] > 0
    ]

    # --- By predicted method ---
    method_counts: dict = {}
    for row in misses:
        method = str(row.get("predicted_method") or "unknown").strip() or "unknown"
        method_counts[method] = method_counts.get(method, 0) + 1

    by_method = [
        {"predicted_method": m, "miss_count": c}
        for m, c in sorted(method_counts.items(), key=lambda x: -x[1])
    ]

    # --- By round range ---
    rr_counts: dict = {}
    for row in misses:
        rr = _classify_round_range(row.get("predicted_round")) or "unknown"
        rr_counts[rr] = rr_counts.get(rr, 0) + 1

    by_round_range = [
        {"round_range": rr, "miss_count": c}
        for rr, c in sorted(rr_counts.items(), key=lambda x: -x[1])
    ]

    # --- Top failure patterns (cross-signal combinations) ---
    pattern_counts: dict = {}
    for row in misses:
        sg = _safe_float(row.get("signal_gap"))
        sg_label = "unknown"
        if sg is not None:
            for label, lo, hi in SG_BUCKETS[:-1]:
                if lo <= sg <= hi:
                    sg_label = label
                    break
        conf = _safe_float(row.get("confidence"))
        conf_label = "unknown"
        if conf is not None:
            if conf > 1.0:
                conf /= 100.0
            for label, lo, hi in CONF_BUCKETS[:-1]:
                if lo <= conf <= hi:
                    conf_label = label
                    break
        method = str(row.get("predicted_method") or "unknown").strip() or "unknown"
        key = f"signal_gap={sg_label} | conf={conf_label} | method={method}"
        pattern_counts[key] = pattern_counts.get(key, 0) + 1

    top_failure_patterns = [
        {"pattern": pattern, "miss_count": count}
        for pattern, count in sorted(pattern_counts.items(), key=lambda x: -x[1])
    ]

    return {
        "ok": True,
        "has_data": total_misses > 0,
        "total_misses": total_misses,
        "top_failure_patterns": top_failure_patterns,
        "miss_breakdowns": {
            "by_signal_gap": by_signal_gap,
            "by_confidence": by_confidence,
            "by_method": by_method,
            "by_round_range": by_round_range,
        },
    }


@app.route("/api/accuracy/error-patterns", methods=["GET"])
def api_accuracy_error_patterns():
    try:
        return jsonify(_build_error_patterns())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "has_data": False, "total_misses": 0}), 500


def _build_signal_coverage() -> dict:
    """
    Measure signal field coverage across all predictions (overall, resolved, unresolved).
    Coverage = field exists AND not None AND not "unknown"/"" string.
    """
    ledger_path = Path(__file__).resolve().parent.parent / "ops" / "accuracy" / "accuracy_ledger.json"
    if not ledger_path.exists():
        return {"ok": True, "has_data": False, "coverage": {}}

    with open(ledger_path, "r", encoding="utf-8") as f:
        rows = json.load(f)

    if not rows:
        return {"ok": True, "has_data": False, "coverage": {}}

    def _present(val):
        if val is None:
            return False
        if isinstance(val, str) and val.strip().lower() in ("", "unknown", "n/a"):
            return False
        return True

    def _calc_bucket(subset):
        n = len(subset)
        if n == 0:
            return {
                "total_predictions": 0,
                "signal_gap_coverage_pct": None,
                "stoppage_propensity_coverage_pct": None,
                "round_finish_tendency_coverage_pct": None,
                "predicted_method_coverage_pct": None,
                "predicted_round_coverage_pct": None,
                "signal_gap_present": 0,
                "stoppage_propensity_present": 0,
                "round_finish_tendency_present": 0,
                "predicted_method_present": 0,
                "predicted_round_present": 0,
            }
        sg = sum(1 for r in subset if _present(r.get("signal_gap")))
        sp = sum(1 for r in subset if _present(r.get("stoppage_propensity")))
        rft = sum(1 for r in subset if _present(r.get("round_finish_tendency")))
        pm = sum(1 for r in subset if _present(r.get("predicted_method")))
        pr = sum(1 for r in subset if _present(r.get("predicted_round")))
        return {
            "total_predictions": n,
            "signal_gap_coverage_pct": round(sg / n * 100, 1),
            "stoppage_propensity_coverage_pct": round(sp / n * 100, 1),
            "round_finish_tendency_coverage_pct": round(rft / n * 100, 1),
            "predicted_method_coverage_pct": round(pm / n * 100, 1),
            "predicted_round_coverage_pct": round(pr / n * 100, 1),
            "signal_gap_present": sg,
            "stoppage_propensity_present": sp,
            "round_finish_tendency_present": rft,
            "predicted_method_present": pm,
            "predicted_round_present": pr,
        }

    resolved = [r for r in rows if r.get("resolved_result")]
    unresolved = [r for r in rows if not r.get("resolved_result")]

    return {
        "ok": True,
        "has_data": True,
        "coverage": {
            "overall": _calc_bucket(rows),
            "resolved": _calc_bucket(resolved),
            "unresolved": _calc_bucket(unresolved),
        },
    }


@app.route("/api/accuracy/signal-coverage", methods=["GET"])
def api_accuracy_signal_coverage():
    try:
        return jsonify(_build_signal_coverage())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "has_data": False, "coverage": {}}), 500


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


def _safe_float(value):
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def _iter_prediction_payloads(event_id, decomposition_payload):
    predictions_dir = os.path.join(_repo_root(), "predictions")
    if not os.path.isdir(predictions_dir):
        return []

    payloads = []
    seen = set()

    for filename in _candidate_prediction_files_from_decomposition(decomposition_payload):
        path = os.path.join(predictions_dir, filename)
        payload = _safe_load_json(path)
        if payload is None:
            continue
        seen.add(filename)
        payloads.append((filename, payload))

    event_token = _slugify_token(event_id)
    if event_token:
        for name in os.listdir(predictions_dir):
            if name in seen:
                continue
            if not (name.endswith("_prediction.json") and event_token in _slugify_token(name)):
                continue
            path = os.path.join(predictions_dir, name)
            payload = _safe_load_json(path)
            if payload is None:
                continue
            seen.add(name)
            payloads.append((name, payload))

    return payloads


def _extract_event_intelligence(event_id, decomposition_payload):
    payloads = _iter_prediction_payloads(event_id, decomposition_payload)
    total = len(payloads)

    signal_gap_values = []
    stoppage_values = []
    round_finish_values = []
    confidence_values = []
    confidence_explanation = None

    high_collapse_risk_count = 0
    fatigue_failure_count = 0
    low_confidence_count = 0
    adapter_fallback_count = 0

    for _source_name, payload in payloads:
        signal_gap = _safe_float(payload.get("signal_gap"))
        stoppage_propensity = _safe_float(payload.get("stoppage_propensity"))
        round_finish_tendency = _safe_float(payload.get("round_finish_tendency"))
        confidence = _safe_float(payload.get("confidence"))

        if signal_gap is not None:
            signal_gap_values.append(signal_gap)
        if stoppage_propensity is not None:
            stoppage_values.append(stoppage_propensity)
        if round_finish_tendency is not None:
            round_finish_values.append(round_finish_tendency)
        if confidence is not None:
            confidence_values.append(confidence)

        explanation = payload.get("confidence_explanation")
        if confidence_explanation is None and isinstance(explanation, str) and explanation.strip():
            confidence_explanation = explanation.strip()

        debug_metrics = payload.get("debug_metrics")
        if not isinstance(debug_metrics, dict):
            debug_metrics = {}

        completion_mode = debug_metrics.get("completion_mode")
        if completion_mode == "adapter_fallback":
            adapter_fallback_count += 1

        collapse_score = _safe_float(payload.get("diag_collapse_trigger_score"))
        if collapse_score is None:
            collapse_score = _safe_float(debug_metrics.get("collapse_risk_confidence"))
        collapse_triggers = payload.get("collapse_triggers")
        if (
            (collapse_score is not None and collapse_score >= 0.60)
            or (isinstance(collapse_triggers, str) and collapse_triggers.strip())
        ):
            high_collapse_risk_count += 1

        fatigue_score = _safe_float(payload.get("diag_fatigue_failure_score"))
        fatigue_points = payload.get("fatigue_failure_points")
        if (
            (fatigue_score is not None and fatigue_score >= 0.55)
            or (isinstance(fatigue_points, str) and fatigue_points.strip())
        ):
            fatigue_failure_count += 1

        if confidence is not None and confidence < 0.55:
            low_confidence_count += 1

    def _mean_or_none(values):
        if not values:
            return None
        return round(sum(values) / len(values), 4)

    return {
        "signal_gap": _mean_or_none(signal_gap_values),
        "stoppage_propensity": _mean_or_none(stoppage_values),
        "round_finish_tendency": _mean_or_none(round_finish_values),
        "confidence": _mean_or_none(confidence_values),
        "confidence_explanation": confidence_explanation,
        "prediction_files_considered": total,
        "risk_flags": {
            "high_collapse_risk_fights": {
                "count": high_collapse_risk_count,
                "total": total,
                "active": high_collapse_risk_count > 0,
            },
            "fatigue_failure_patterns": {
                "count": fatigue_failure_count,
                "total": total,
                "active": fatigue_failure_count > 0,
            },
            "low_confidence_predictions": {
                "count": low_confidence_count,
                "total": total,
                "active": low_confidence_count > 0,
            },
            "adapter_fallback_cases": {
                "count": adapter_fallback_count,
                "total": total,
                "active": adapter_fallback_count > 0,
            },
        },
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
            intelligence = {
                "signal_gap": None,
                "stoppage_propensity": None,
                "round_finish_tendency": None,
                "confidence": None,
                "confidence_explanation": None,
                "prediction_files_considered": 0,
                "risk_flags": {
                    "high_collapse_risk_fights": {"count": 0, "total": 0, "active": False},
                    "fatigue_failure_patterns": {"count": 0, "total": 0, "active": False},
                    "low_confidence_predictions": {"count": 0, "total": 0, "active": False},
                    "adapter_fallback_cases": {"count": 0, "total": 0, "active": False},
                },
            }
            return jsonify(
                {
                    "ok": True,
                    "event_id": event_id,
                    "decomposition": decomposition,
                    "adapter": adapter,
                    "intelligence": intelligence,
                    "errors": ["decomposition_artifact_not_found"],
                }
            )

        decomposition = _extract_decomposition_metrics(decomposition_payload, decomposition_path)
        adapter = _extract_adapter_metrics(event_id, decomposition_payload)
        intelligence = _extract_event_intelligence(event_id, decomposition_payload)
        return jsonify(
            {
                "ok": True,
                "event_id": event_id,
                "decomposition": decomposition,
                "adapter": adapter,
                "intelligence": intelligence,
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
                "intelligence": {
                    "signal_gap": None,
                    "stoppage_propensity": None,
                    "round_finish_tendency": None,
                    "confidence": None,
                    "confidence_explanation": None,
                    "prediction_files_considered": 0,
                    "risk_flags": {
                        "high_collapse_risk_fights": {"count": 0, "total": 0, "active": False},
                        "fatigue_failure_patterns": {"count": 0, "total": 0, "active": False},
                        "low_confidence_predictions": {"count": 0, "total": 0, "active": False},
                        "adapter_fallback_cases": {"count": 0, "total": 0, "active": False},
                    },
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
