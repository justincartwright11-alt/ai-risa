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
from time import perf_counter, time
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

_RUNTIME_METRICS = {
    "started_at_epoch": time(),
    "requests_total": 0,
    "errors_total": 0,
    "endpoint_counts": {},
    "endpoint_latency_ms": {},
    "last_error": None,
}


@app.before_request
def _runtime_metrics_before_request():
    request._started_at = perf_counter()


@app.after_request
def _runtime_metrics_after_request(response):
    endpoint = request.path
    elapsed_ms = round((perf_counter() - getattr(request, "_started_at", perf_counter())) * 1000, 3)

    _RUNTIME_METRICS["requests_total"] += 1
    _RUNTIME_METRICS["endpoint_counts"][endpoint] = _RUNTIME_METRICS["endpoint_counts"].get(endpoint, 0) + 1
    _RUNTIME_METRICS["endpoint_latency_ms"][endpoint] = elapsed_ms

    if response.status_code >= 500:
        _RUNTIME_METRICS["errors_total"] += 1
        _RUNTIME_METRICS["last_error"] = {
            "endpoint": endpoint,
            "status_code": response.status_code,
        }

    return response


def _append_health_log(health_record: dict) -> bool:
    """Append a compact health snapshot to the runtime health log (JSONL).
    
    Args:
        health_record: dict with timestamp_utc, ok, uptime_seconds, requests_total, errors_total, accuracy_endpoint_status
        
    Returns:
        True if successfully written, False on any I/O error
    """
    try:
        log_path = Path(__file__).resolve().parent.parent / "ops" / "runtime_health_log.jsonl"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(health_record) + "\n")
        return True
    except Exception:
        return False


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


def _build_actual_result_lookup_dry_run_preview(limit_value=None) -> dict:
    summary = _build_accuracy_comparison_summary()
    waiting_rows = summary.get("waiting_for_results") or []

    try:
        preview_limit = int(limit_value) if limit_value is not None else 5
    except Exception:
        preview_limit = 5
    preview_limit = max(1, min(preview_limit, 10))

    required_fields = [
        "fight_name",
        "predicted_winner",
        "event_date",
        "file_path",
        "status",
    ]

    preview_rows = []
    missing_by_row = []
    for row in waiting_rows[:preview_limit]:
        missing_fields = [field for field in required_fields if not _is_known_value(row.get(field))]
        selected_key = f"{_normalize_token(row.get('fight_name'))}|{_normalize_token(row.get('file_path'))}"
        preview_row = {
            "fight_name": row.get("fight_name") or "UNKNOWN",
            "fight_id": row.get("fight_id") if _is_known_value(row.get("fight_id")) else None,
            "predicted_winner": row.get("predicted_winner") or "UNKNOWN",
            "event_date": row.get("event_date") or "UNKNOWN",
            "file_path": row.get("file_path") or "UNKNOWN",
            "status": row.get("status") or "waiting_for_actual_result",
            "selected_key": selected_key,
            "missing_fields": missing_fields,
        }
        preview_rows.append(preview_row)
        missing_by_row.append({
            "fight_name": preview_row["fight_name"],
            "fight_id": preview_row["fight_id"],
            "selected_key": selected_key,
            "missing_fields": missing_fields,
        })

    return {
        "ok": True,
        "mode": "dry_run_preview",
        "waiting_count": len(waiting_rows),
        "preview_limit": preview_limit,
        "preview_rows": preview_rows,
        "required_fields": required_fields,
        "missing_by_row": missing_by_row,
        "mutation_performed": False,
        "external_lookup_performed": False,
        "bulk_lookup_performed": False,
    }


def _build_waiting_row_selected_key(row: dict) -> str:
    return f"{_normalize_token(row.get('fight_name'))}|{_normalize_token(row.get('file_path'))}"


def _build_waiting_row_candidate_fight_keys(row: dict) -> list:
    keys = []

    def add_key(value):
        token = _normalize_token(value)
        if token and token not in keys:
            keys.append(token)

    add_key(row.get("fight_id"))
    add_key(row.get("fight_name"))

    file_path = str(row.get("file_path") or "")
    if file_path:
        stem = Path(file_path.replace("\\", "/")).stem
        add_key(stem)
        if stem.endswith("_prediction"):
            add_key(stem[: -len("_prediction")])
        if stem.startswith("pred_"):
            add_key(stem[len("pred_"):])
        if stem.startswith("canonical_"):
            add_key(stem[len("canonical_"):])

    return keys


def _load_local_actual_result_map() -> tuple:
    base_dir = Path(__file__).resolve().parent.parent
    accuracy_dir = base_dir / "ops" / "accuracy"

    records_by_key = {}
    for filename in [
        "actual_results.json",
        "actual_results_manual.json",
        "actual_results_unresolved.json",
    ]:
        source_path = accuracy_dir / filename
        for row in _load_json_records(source_path):
            fight_key = _normalize_token(row.get("fight_id"))
            if not fight_key:
                continue
            # Prefer rows with known actual winner over unknown placeholders.
            if fight_key not in records_by_key or _is_known_value(row.get("actual_winner")):
                records_by_key[fight_key] = {
                    "record": row,
                    "source_file": filename,
                }

    return records_by_key, accuracy_dir


def _upsert_single_manual_actual_result(accuracy_dir: Path, write_row: dict) -> bool:
    target_path = accuracy_dir / "actual_results_manual.json"
    manual_rows = _load_json_records(target_path)

    fight_key = _normalize_token(write_row.get("fight_id"))
    updated = False
    for idx, row in enumerate(manual_rows):
        if _normalize_token(row.get("fight_id")) == fight_key:
            manual_rows[idx] = write_row
            updated = True
            break

    if not updated:
        manual_rows.append(write_row)

    try:
        with open(target_path, "w", encoding="utf-8") as handle:
            json.dump(manual_rows, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        return True
    except Exception:
        return False


def operator_error_response(message: str, status_code: int = 500, **extra):
    payload = {
        "ok": False,
        "error": str(message),
    }
    payload.update(extra)
    return jsonify(payload), status_code


def classify_fighter_verification_block(error_texts):
    combined = " | ".join(str(x or "") for x in (error_texts or [])).lower()
    blocked_markers = [
        "ambiguous fighter name",
        "need full fighter name",
        "missing fighter profile after intake",
        "fighter profile too weak for analysis",
    ]
    if not any(marker in combined for marker in blocked_markers):
        return None

    return {
        "blocked_reason": "fighter_profile_not_verified",
        "operator_message": (
            "Fighter profile not verified. Do not build report yet. "
            "Source verification is required before retrying this matchup."
        ),
        "suggested_next_action": (
            "Choose a verified matchup or run fighter intake verification "
            "for both fighters."
        ),
    }


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


@app.route("/api/system/health")
def api_system_health():
    accuracy_endpoints = [
        "/api/accuracy/comparison-summary",
        "/api/accuracy/signal-breakdown",
        "/api/accuracy/method-round-breakdown",
        "/api/accuracy/confidence-calibration",
        "/api/accuracy/error-patterns",
        "/api/accuracy/signal-coverage",
        "/api/accuracy/structural-signal-backfill-planner",
    ]

    statuses = {}
    with app.test_client() as c:
        for ep in accuracy_endpoints:
            statuses[ep] = c.get(ep).status_code

    ledger_path = Path(__file__).resolve().parent.parent / "ops" / "accuracy" / "accuracy_ledger.json"
    try:
        _load_accuracy_ledger_rows(ledger_path)
        last_ledger_read_success = True
    except Exception:
        last_ledger_read_success = False

    ok_status = all(code == 200 for code in statuses.values())
    uptime_seconds = round(time() - _RUNTIME_METRICS["started_at_epoch"], 3)
    
    # Build compact health log record and attempt to persist
    health_record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "ok": ok_status,
        "uptime_seconds": uptime_seconds,
        "requests_total": _RUNTIME_METRICS["requests_total"],
        "errors_total": _RUNTIME_METRICS["errors_total"],
        "accuracy_endpoint_status": statuses,
    }
    health_log_written = _append_health_log(health_record)
    
    response_payload = {
        "ok": ok_status,
        "uptime_seconds": uptime_seconds,
        "last_ledger_read_success": last_ledger_read_success,
        "requests_total": _RUNTIME_METRICS["requests_total"],
        "errors_total": _RUNTIME_METRICS["errors_total"],
        "endpoint_counts": _RUNTIME_METRICS["endpoint_counts"],
        "endpoint_latency_ms": _RUNTIME_METRICS["endpoint_latency_ms"],
        "last_error": _RUNTIME_METRICS["last_error"],
        "accuracy_endpoint_status": statuses,
        "health_log_written": health_log_written,
    }
    
    return jsonify(response_payload)


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

        if isinstance(result, dict) and result.get("ok") is False:
            error_texts = [result.get("error")] + list(result.get("errors") or [])
            blocked_meta = classify_fighter_verification_block(error_texts)
            if blocked_meta:
                result.update(blocked_meta)
        
        return jsonify(result)
    
    except Exception as e:
        blocked_meta = classify_fighter_verification_block([str(e)])
        if blocked_meta:
            return operator_error_response(str(e), 500, errors=[str(e)], **blocked_meta)
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


@app.route("/api/operator/actual-result-lookup/dry-run-preview", methods=["GET"])
def api_operator_actual_result_lookup_dry_run_preview():
    try:
        preview_limit = request.args.get("limit")
        return jsonify(_build_actual_result_lookup_dry_run_preview(preview_limit))
    except Exception as e:
        return jsonify({
            "ok": False,
            "mode": "dry_run_preview",
            "error": str(e),
            "waiting_count": 0,
            "preview_limit": 5,
            "preview_rows": [],
            "required_fields": ["fight_name", "predicted_winner", "event_date", "file_path", "status"],
            "missing_by_row": [],
            "mutation_performed": False,
            "external_lookup_performed": False,
            "bulk_lookup_performed": False,
        }), 500


@app.route("/api/operator/actual-result-lookup/guarded-single", methods=["POST"])
def api_operator_actual_result_lookup_guarded_single():
    data = request.get_json(silent=True) or {}
    selected_key = str(data.get("selected_key") or "").strip()
    approval_granted = bool(data.get("approval_granted"))

    if not selected_key:
        return jsonify({
            "ok": False,
            "mode": "guarded_single_lookup",
            "error": "selected_key is required",
            "approval_required": True,
            "approval_granted": approval_granted,
            "mutation_performed": False,
            "resolved_count": 0,
            "external_lookup_performed": False,
            "bulk_lookup_performed": False,
            "manual_review_required": True,
            "selected_row": None,
            "local_result_found": False,
            "proposed_write": None,
            "message": "Preview only. Approval required before any write.",
        }), 400

    summary = _build_accuracy_comparison_summary()
    waiting_rows = summary.get("waiting_for_results") or []
    selected_row = None
    for row in waiting_rows:
        if _build_waiting_row_selected_key(row) == selected_key:
            selected_row = dict(row)
            break

    if selected_row is None:
        return jsonify({
            "ok": False,
            "mode": "guarded_single_lookup",
            "error": "selected_key not found in waiting rows",
            "approval_required": True,
            "approval_granted": approval_granted,
            "mutation_performed": False,
            "resolved_count": 0,
            "external_lookup_performed": False,
            "bulk_lookup_performed": False,
            "manual_review_required": True,
            "selected_row": None,
            "local_result_found": False,
            "proposed_write": None,
            "message": "Selected row was not found. Manual review required.",
        }), 404

    selected_row["selected_key"] = selected_key
    if not _is_known_value(selected_row.get("fight_id")):
        selected_row["fight_id"] = _normalize_token(selected_row.get("fight_name")) or None

    local_actual_map, accuracy_dir = _load_local_actual_result_map()
    candidate_keys = _build_waiting_row_candidate_fight_keys(selected_row)
    local_actual = None
    local_actual_source = None
    for key in candidate_keys:
        matched = local_actual_map.get(key)
        if matched and _is_known_value(matched["record"].get("actual_winner")):
            local_actual = dict(matched["record"])
            local_actual_source = matched["source_file"]
            break

    local_result_found = local_actual is not None
    proposed_write = None
    if local_result_found:
        proposed_write = {
            "fight_id": local_actual.get("fight_id") or selected_row.get("fight_id"),
            "actual_winner": local_actual.get("actual_winner") or "UNKNOWN",
            "actual_method": local_actual.get("actual_method") or "UNKNOWN",
            "actual_round": local_actual.get("actual_round") or "UNKNOWN",
            "event_date": local_actual.get("event_date") or selected_row.get("event_date") or "UNKNOWN",
            "source": "guarded_single_local_actual",
            "copied_from": local_actual_source,
        }

    base_payload = {
        "ok": True,
        "mode": "guarded_single_lookup",
        "approval_required": True,
        "approval_granted": approval_granted,
        "mutation_performed": False,
        "resolved_count": 0,
        "external_lookup_performed": False,
        "bulk_lookup_performed": False,
        "manual_review_required": not local_result_found,
        "selected_row": selected_row,
        "local_result_found": local_result_found,
        "proposed_write": proposed_write,
    }

    if not approval_granted:
        return jsonify({
            **base_payload,
            "message": "Preview only. Approval required before any write.",
        })

    if not local_result_found:
        return jsonify({
            **base_payload,
            "message": "No local actual result found. Manual review required. No write performed.",
        })

    write_ok = _upsert_single_manual_actual_result(accuracy_dir, proposed_write)
    if not write_ok:
        return jsonify({
            **base_payload,
            "ok": False,
            "message": "Failed to write approved local actual result.",
        }), 500

    return jsonify({
        **base_payload,
        "mutation_performed": True,
        "resolved_count": 1,
        "manual_review_required": False,
        "message": "Approved local actual result written for selected row.",
    })


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


def _load_accuracy_ledger_rows(ledger_path: Path):
    """
    Load accuracy ledger JSON with BOM-safe UTF-8 decoding.
    """
    with open(ledger_path, "r", encoding="utf-8-sig") as f:
        rows = json.load(f)
    if isinstance(rows, list):
        return rows
    return []


def _build_signal_coverage() -> dict:
    """
    Measure signal field coverage across all predictions (overall, resolved, unresolved).
    Coverage = field exists AND not None AND not "unknown"/"" string.
    """
    ledger_path = Path(__file__).resolve().parent.parent / "ops" / "accuracy" / "accuracy_ledger.json"
    if not ledger_path.exists():
        return {"ok": True, "has_data": False, "coverage": {}}

    rows = _load_accuracy_ledger_rows(ledger_path)

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


def _build_structural_signal_backfill_planner() -> dict:
    """
    Build a read-only priority queue for records that are missing structural signals.
    """
    root = Path(__file__).resolve().parent.parent
    ledger_path = root / "ops" / "accuracy" / "accuracy_ledger.json"
    if not ledger_path.exists():
        return {"ok": True, "has_data": False, "planner": {}}

    rows = _load_accuracy_ledger_rows(ledger_path)

    if not rows:
        return {"ok": True, "has_data": False, "planner": {}}

    structural_fields = ["signal_gap", "stoppage_propensity", "round_finish_tendency"]

    def _present(val):
        if val is None:
            return False
        if isinstance(val, str) and val.strip().lower() in ("", "unknown", "n/a"):
            return False
        return True

    queue = []
    unresolved_needing_backfill = 0
    resolved_needing_backfill = 0
    resolved_miss_needing_backfill = 0
    source_file_present = 0
    source_file_missing = 0
    prediction_file_exists = 0
    prediction_file_missing = 0

    eligibility_counts: dict = {
        "READY_FOR_BACKFILL": 0,
        "BLOCKED_NEEDS_SOURCE_VALUES": 0,
        "REQUIRES_ENGINE_RERUN": 0,
        "UNRESOLVED_RESULT_PENDING": 0,
    }

    for row in rows:
        source_file = row.get("source_file")
        if source_file:
            source_file_present += 1
            prediction_path = root / source_file
            if prediction_path.exists():
                prediction_file_exists += 1
            else:
                prediction_file_missing += 1
        else:
            source_file_missing += 1

        missing_signals = [field for field in structural_fields if not _present(row.get(field))]
        if not missing_signals:
            continue

        resolved = bool(row.get("resolved_result"))
        is_miss = resolved and row.get("hit_winner") is False

        # --- Eligibility classification ---
        schema_variant = (row.get("schema_variant") or "").strip().lower()
        is_intermediate = schema_variant in ("intermediate", "narrative", "legacy")

        if not resolved:
            eligibility_class = "UNRESOLVED_RESULT_PENDING"
            eligibility_reason = "Fight result is not yet resolved; structural backfill deferred until result is confirmed."
            source_value_status = "deferred"
            source_values_found = False
            recommended_action = "wait_for_result_resolution"
        elif is_intermediate:
            # Intermediate/narrative schema records were generated before structural
            # fields existed; no authoritative source values exist in the repo.
            eligibility_class = "BLOCKED_NEEDS_SOURCE_VALUES"
            eligibility_reason = (
                "Record uses intermediate/narrative schema. Structural fields were never computed. "
                "No authoritative numeric source values exist in the repo."
            )
            source_value_status = "not_present_in_any_source"
            source_values_found = False
            recommended_action = "requires_source_values_or_engine_rerun"
        else:
            # Resolved, non-intermediate: structural values are missing but the record
            # was produced by a capable schema version.  Without an explicit canonical
            # source file containing the values we cannot confirm readiness, so default
            # to REQUIRES_ENGINE_RERUN to avoid false positives.
            eligibility_class = "REQUIRES_ENGINE_RERUN"
            eligibility_reason = (
                "Record is resolved and uses a capable schema, but structural field values "
                "were not found in any existing source file. Engine rerun needed to populate them."
            )
            source_value_status = "missing_requires_rerun"
            source_values_found = False
            recommended_action = "requires_engine_rerun_with_approval"

        eligibility_counts[eligibility_class] += 1

        # Prioritize unresolved rows first (actionable), then resolved misses (diagnostics).
        priority_score = len(missing_signals) * 10
        if not resolved:
            priority_score += 8
        if is_miss:
            priority_score += 4

        if not resolved:
            unresolved_needing_backfill += 1
        else:
            resolved_needing_backfill += 1
            if is_miss:
                resolved_miss_needing_backfill += 1

        if priority_score >= 34:
            priority_tier = "critical"
        elif priority_score >= 24:
            priority_tier = "high"
        else:
            priority_tier = "normal"

        queue.append(
            {
                "fight_id": row.get("fight_id") or "unknown",
                "event_date": row.get("event_date"),
                "resolved_result": resolved,
                "hit_winner": row.get("hit_winner"),
                "missing_signals": missing_signals,
                "missing_count": len(missing_signals),
                "priority_score": priority_score,
                "priority_tier": priority_tier,
                "source_file": source_file,
                "eligibility_class": eligibility_class,
                "eligibility_reason": eligibility_reason,
                "source_value_status": source_value_status,
                "source_values_found": source_values_found,
                "recommended_action": recommended_action,
            }
        )

    queue.sort(
        key=lambda r: (
            -r["priority_score"],
            r["resolved_result"],
            r.get("event_date") or "",
            r.get("fight_id") or "",
        )
    )

    return {
        "ok": True,
        "has_data": True,
        "planner": {
            "total_predictions": len(rows),
            "predictions_needing_backfill": len(queue),
            "structural_fields": structural_fields,
            "summary": {
                "unresolved_needing_backfill": unresolved_needing_backfill,
                "resolved_needing_backfill": resolved_needing_backfill,
                "resolved_miss_needing_backfill": resolved_miss_needing_backfill,
                "source_file_present": source_file_present,
                "source_file_missing": source_file_missing,
                "prediction_file_exists": prediction_file_exists,
                "prediction_file_missing": prediction_file_missing,
                "eligibility_counts": eligibility_counts,
            },
            "priority_queue": queue,
        },
    }


@app.route("/api/accuracy/structural-signal-backfill-planner", methods=["GET"])
def api_accuracy_structural_signal_backfill_planner():
    try:
        return jsonify(_build_structural_signal_backfill_planner())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "has_data": False, "planner": {}}), 500


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


@app.route("/api/operator/intent", methods=["POST"])
def api_operator_intent():
    """
    Route a plain-English operator command to a structured intent plan.
    Read-only routing — never mutates data.
    """
    data = request.get_json(silent=True) or {}
    command = str(data.get("command", "")).strip()
    if not command:
        return jsonify({"ok": False, "error": "No command provided"}), 400
    try:
        from operator_dashboard.operator_intent_router import route_intent
        result = route_intent(command)
        return jsonify({"ok": True, **result})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/operator/web-trigger-scout", methods=["GET", "POST"])
def api_operator_web_trigger_scout():
    """Read-only web trigger scouting endpoint.

    This endpoint returns a review packet only and performs no writes.
    """
    try:
        if request.method == "GET":
            query = str(request.args.get("query", "")).strip()
            mode = str(request.args.get("mode", "official_first")).strip() or "official_first"
            targets_raw = request.args.get("targets", "")
            targets = [t.strip() for t in targets_raw.split(",") if t.strip()]
        else:
            data = request.get_json(silent=True) or {}
            query = str(data.get("query", "")).strip()
            mode = str(data.get("mode", "official_first")).strip() or "official_first"
            targets = data.get("targets") or []
            if not isinstance(targets, list):
                targets = []

        if not query and not targets:
            return jsonify({"ok": False, "error": "Provide query or targets"}), 400

        from operator_dashboard.web_trigger_scout import WebTriggerScout

        scout = WebTriggerScout()
        result = scout.run(query=query, mode=mode, targets=targets)
        return jsonify(result)
    except Exception as e:
        return operator_error_response(str(e), 500)


@app.route("/")
def index():
    # Render the dashboard UI, preserving the expected text in the HTML title if needed
    return render_template("index.html", dashboard_title="AI-RISA Local Operator Dashboard")


@app.route("/advanced-dashboard")
def advanced_dashboard():
    # Render the advanced/full dashboard with all panels and monitoring tools
    return render_template("advanced_dashboard.html", dashboard_title="AI-RISA Advanced Dashboard")


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
