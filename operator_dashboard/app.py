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
from datetime import datetime, timezone
import uuid

from operator_dashboard.forecast_utils import get_operator_forecast
from operator_dashboard.response_matrix_utils import get_operator_response_matrix


app = Flask(__name__)

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
        return jsonify({
            "ok": True,
            "app_name": "Operator Dashboard",
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "chat_history_available": True,
            "action_ledger_available": True,
            "total_logged_actions": len(ledger_rows),
            "total_chat_messages": len(history),
            "errors": []
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/watchlist", methods=["GET"])
def api_watchlist():
    try:
        queue = safe_read_queue()
        queue_rows = queue.get("rows", [])
        watchlist = aggregate_watchlist(queue_rows, [], [], [], [], safe_read_ledger())
        summary = summarize_queue(queue_rows)
        return jsonify({
            "ok": True,
            "watchlist": watchlist,
            "watchlist_count": len(watchlist),
            "summary": summary.get("recommendation", ""),
            "recommendation": summary.get("recommendation", "")
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

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
from operator_dashboard.chat_history_utils import load_chat_history, append_chat_message

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
    append_chat_message("assistant", result.get("response", ""),
                        action=result.get("action"),
                        normalized_event=result.get("normalized_event"))
    response_data = {
        "ok": result.get("ok", result.get("success", False)),
        "action": result.get("action", parsed.get("action", "unknown")),
        "response": result.get("response", ""),
        "normalized_event": result.get("normalized_event", parsed.get("normalized_event")),
        "details": result.get("details", ""),
        "error": result.get("error"),
        "timestamp": result.get("timestamp", datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'))
    }
    return jsonify(response_data)

@app.route("/chat/history", methods=["GET"])
def chat_history():
    return jsonify(load_chat_history())

@app.route("/")
def index():
    return "Operator Dashboard Running"

if __name__ == "__main__":
    app.run(port=5000, host="0.0.0.0")
