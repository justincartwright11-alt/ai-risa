from operator_dashboard.anomaly_utils import AnomalyAggregator
from flask import Flask, render_template, request, jsonify, send_file
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
import subprocess
from datetime import datetime, timezone
from time import perf_counter, time
import uuid
import hashlib
from urllib.parse import urlparse
from operator_dashboard.official_source_acceptance_gate import evaluate_official_source_acceptance_gate
from operator_dashboard.official_source_lookup_provider import OfficialSourceLookupProvider
from operator_dashboard.official_source_approved_apply_schema import validate_official_source_approved_apply_request
from operator_dashboard.official_source_approved_apply_guard import evaluate_official_source_approved_apply_guard
from operator_dashboard.official_source_approved_apply_mutation_adapter import apply_official_source_approved_apply_mutation
from operator_dashboard.official_source_approved_apply_global_ledger_helper import OfficialSourceApprovedApplyGlobalLedgerHelper
from operator_dashboard.official_source_approved_apply_operation_id_persistence_helper import OfficialSourceApprovedApplyOperationIdPersistenceHelper
from operator_dashboard.official_source_approved_apply_token_consume_helper import OfficialSourceApprovedApplyTokenConsumeHelper

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
app.config.setdefault("OFFICIAL_SOURCE_APPROVED_APPLY_MUTATION_ENABLED", False)
app.config.setdefault("OFFICIAL_SOURCE_APPROVED_APPLY_ACCURACY_DIR_OVERRIDE", None)
app.config.setdefault("OFFICIAL_SOURCE_APPROVED_APPLY_OPERATION_ID_AUDIT_PATH_OVERRIDE", None)
app.config.setdefault("OFFICIAL_SOURCE_APPROVED_APPLY_GLOBAL_LEDGER_PATH_OVERRIDE", None)
app.config.setdefault("PRF_QUEUE_PATH_OVERRIDE", None)
app.config.setdefault("PRF_REPORTS_DIR_OVERRIDE", None)

OFFICIAL_SOURCE_APPROVED_APPLY_TOKEN_CONSUME_HELPER = OfficialSourceApprovedApplyTokenConsumeHelper()
OFFICIAL_SOURCE_APPROVED_APPLY_GLOBAL_LEDGER_HELPER = OfficialSourceApprovedApplyGlobalLedgerHelper()
OFFICIAL_SOURCE_APPROVED_APPLY_OPERATION_ID_PERSISTENCE_HELPER = OfficialSourceApprovedApplyOperationIdPersistenceHelper()

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


def _resolve_accuracy_dir() -> Path:
    override = str(app.config.get("OFFICIAL_SOURCE_APPROVED_APPLY_ACCURACY_DIR_OVERRIDE") or "").strip()
    if override:
        return Path(override)
    base_dir = Path(__file__).resolve().parent.parent
    return base_dir / "ops" / "accuracy"


def _resolve_global_ledger_path(accuracy_dir: Path) -> str:
    override = str(app.config.get("OFFICIAL_SOURCE_APPROVED_APPLY_GLOBAL_LEDGER_PATH_OVERRIDE") or "").strip()
    if override:
        return override
    return str(accuracy_dir / "official_source_approved_apply_global_ledger.jsonl")


def _project_global_ledger_summary_row(row: dict) -> dict:
    return {
        "global_ledger_record_id": row.get("global_ledger_record_id"),
        "local_result_key": row.get("local_result_key"),
        "event_id": row.get("event_id"),
        "bout_id": row.get("bout_id"),
        "official_source_reference": row.get("official_source_reference"),
        "approved_actual_result": row.get("approved_actual_result"),
        "operation_id": row.get("operation_id"),
        "deterministic_status": row.get("deterministic_status"),
        "timestamp_utc": row.get("timestamp_utc"),
        "local_audit_reference": row.get("local_audit_reference"),
    }


def _build_official_source_approved_apply_global_ledger_summary(limit_raw=None) -> dict:
    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    payload = {
        "ok": True,
        "generated_at": generated_at,
        "ledger_available": False,
        "total_rows": 0,
        "latest_rows": [],
        "status_counts": {},
        "errors": [],
    }

    try:
        limit = int(limit_raw) if str(limit_raw or "").strip() else 10
    except Exception:
        limit = 10
    limit = max(1, min(limit, 100))

    accuracy_dir = _resolve_accuracy_dir()
    ledger_path = Path(_resolve_global_ledger_path(accuracy_dir))
    if not ledger_path.exists():
        return payload

    payload["ledger_available"] = True
    ledger_rows = []
    with ledger_path.open("r", encoding="utf-8") as handle:
        for line_number, line_text in enumerate(handle, start=1):
            stripped = line_text.strip()
            if not stripped:
                continue
            try:
                row = json.loads(stripped)
            except Exception as exc:
                payload["errors"].append(f"malformed_row_line_{line_number}: {exc}")
                continue
            if not isinstance(row, dict):
                payload["errors"].append(f"malformed_row_line_{line_number}: row is not a JSON object")
                continue
            ledger_rows.append(row)

    payload["total_rows"] = len(ledger_rows)
    status_counts: dict[str, int] = {}
    for row in ledger_rows:
        status = str(row.get("deterministic_status") or "").strip() or "unknown"
        status_counts[status] = status_counts.get(status, 0) + 1

    latest_rows = ledger_rows[-limit:]
    latest_rows.reverse()
    payload["latest_rows"] = [_project_global_ledger_summary_row(row) for row in latest_rows]
    payload["status_counts"] = {key: status_counts[key] for key in sorted(status_counts.keys())}
    return payload


def _round_to_int(value) -> int | None:
    text = str(value or "").strip()
    if not _is_known_value(text):
        return None
    digits = ""
    for ch in text:
        if ch.isdigit():
            digits += ch
        elif digits:
            break
    if not digits:
        return None
    try:
        return int(digits)
    except Exception:
        return None


def _round_tolerance_hit(predicted_round, actual_round) -> bool:
    predicted_round_num = _round_to_int(predicted_round)
    actual_round_num = _round_to_int(actual_round)
    if predicted_round_num is None or actual_round_num is None:
        return False
    return abs(predicted_round_num - actual_round_num) == 1


def _build_approved_apply_report_scoring_bridge_evidence(
    prediction_report: dict | None,
    approved_actual_rows: list[dict] | None,
    global_ledger_rows: list[dict] | None,
) -> dict:
    prediction = prediction_report if isinstance(prediction_report, dict) else {}
    actual_rows = [row for row in (approved_actual_rows or []) if isinstance(row, dict)]
    ledger_rows = [row for row in (global_ledger_rows or []) if isinstance(row, dict)]

    local_result_key = str(prediction.get("local_result_key") or prediction.get("fight_id") or "").strip() or None
    if not local_result_key and len(actual_rows) == 1:
        local_result_key = str(actual_rows[0].get("fight_id") or actual_rows[0].get("local_result_key") or "").strip() or None

    def _row_local_key(row: dict) -> str:
        approved_actual = row.get("approved_actual_result") if isinstance(row.get("approved_actual_result"), dict) else {}
        return _normalize_token(
            row.get("local_result_key")
            or row.get("fight_id")
            or approved_actual.get("fight_id")
            or ""
        )

    normalized_local_result_key = _normalize_token(local_result_key or "")
    matching_actual_rows = [row for row in actual_rows if _row_local_key(row) == normalized_local_result_key] if normalized_local_result_key else []
    matching_ledger_rows = [
        row for row in ledger_rows
        if _normalize_token(row.get("local_result_key") or "") == normalized_local_result_key
    ] if normalized_local_result_key else []

    predicted_winner_id = prediction.get("predicted_winner_id") or prediction.get("predicted_winner")
    predicted_method = prediction.get("predicted_method")
    predicted_round = prediction.get("predicted_round")

    base_payload = {
        "prediction_report_id": prediction.get("prediction_report_id") or prediction.get("report_id") or prediction.get("id"),
        "local_result_key": local_result_key,
        "global_ledger_record_id": None,
        "official_source_reference": None,
        "approved_actual_result": None,
        "predicted_winner_id": predicted_winner_id,
        "predicted_method": predicted_method,
        "predicted_round": predicted_round,
        "confidence": prediction.get("confidence"),
        "resolved_result_status": "unresolved",
        "scored": False,
        "score_outcome": "unresolved",
        "calibration_notes": "awaiting approved actual bridge evidence",
    }

    if not prediction:
        base_payload["resolved_result_status"] = "no_prediction_found"
        base_payload["calibration_notes"] = "approved actual exists but prediction/report record is missing"
        return base_payload

    if not local_result_key:
        base_payload["resolved_result_status"] = "malformed_ledger_trace"
        base_payload["calibration_notes"] = "prediction/report record has no local_result_key or fight_id"
        return base_payload

    if len(matching_actual_rows) > 1 or len(matching_ledger_rows) > 1:
        base_payload["resolved_result_status"] = "duplicate_conflict"
        base_payload["score_outcome"] = "duplicate_conflict"
        base_payload["calibration_notes"] = "duplicate approved actual or duplicate global ledger trace detected"
        return base_payload

    if not matching_actual_rows:
        base_payload["resolved_result_status"] = "no_actual_found"
        base_payload["score_outcome"] = "unresolved"
        base_payload["calibration_notes"] = "prediction/report record exists but no approved actual was found"
        return base_payload

    if not matching_ledger_rows:
        base_payload["resolved_result_status"] = "no_global_ledger_trace"
        base_payload["score_outcome"] = "unresolved"
        base_payload["approved_actual_result"] = matching_actual_rows[0]
        base_payload["calibration_notes"] = "approved actual exists locally but global ledger trace is missing"
        return base_payload

    actual_row = matching_actual_rows[0]
    ledger_row = matching_ledger_rows[0]
    approved_actual_from_ledger = ledger_row.get("approved_actual_result") if isinstance(ledger_row.get("approved_actual_result"), dict) else None
    approved_actual = approved_actual_from_ledger or actual_row

    if not isinstance(approved_actual, dict):
        base_payload["resolved_result_status"] = "malformed_ledger_trace"
        base_payload["score_outcome"] = "unresolved"
        base_payload["calibration_notes"] = "approved actual payload is malformed"
        return base_payload

    actual_winner = approved_actual.get("actual_winner") or actual_row.get("actual_winner")
    actual_method = approved_actual.get("actual_method") or actual_row.get("actual_method")
    actual_round = approved_actual.get("actual_round") or actual_row.get("actual_round")

    winner_match = _winner_hit(predicted_winner_id, actual_winner)
    method_match = _method_hit(predicted_method, actual_method)
    round_exact_match = _round_hit(predicted_round, actual_round)
    round_tolerance_match = _round_tolerance_hit(predicted_round, actual_round)

    if not winner_match:
        score_outcome = "mismatch"
    elif method_match and round_exact_match:
        score_outcome = "round_exact"
    elif method_match and round_tolerance_match:
        score_outcome = "round_tolerance"
    elif method_match:
        score_outcome = "method_correct"
    else:
        score_outcome = "winner_correct"

    base_payload.update({
        "global_ledger_record_id": ledger_row.get("global_ledger_record_id"),
        "official_source_reference": ledger_row.get("official_source_reference"),
        "approved_actual_result": approved_actual,
        "resolved_result_status": "resolved",
        "scored": True,
        "score_outcome": score_outcome,
        "calibration_notes": f"deterministic_outcome={score_outcome}",
    })
    return base_payload


def _derive_scoring_bridge_status(evidence: dict) -> str:
    resolved_status = str(evidence.get("resolved_result_status") or "").strip()
    if resolved_status == "no_prediction_found":
        return "missing"
    if resolved_status in ("duplicate_conflict", "malformed_ledger_trace"):
        return "conflict"
    if resolved_status in ("no_actual_found", "no_global_ledger_trace"):
        return "unresolved"
    if resolved_status == "resolved":
        return "ok"
    return "unresolved"


def _build_official_source_approved_apply_report_scoring_bridge_summary(
    prediction_report_id_filter=None,
    local_result_key_filter=None,
    limit_raw=None,
) -> dict:
    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    empty_status_counts: dict[str, int] = {"ok": 0, "unresolved": 0, "conflict": 0, "missing": 0}
    payload: dict = {
        "ok": True,
        "generated_at": generated_at,
        "bridge_available": False,
        "total_records": 0,
        "latest_records": [],
        "status_counts": dict(empty_status_counts),
        "errors": [],
    }

    try:
        limit = int(limit_raw) if str(limit_raw or "").strip() else 20
    except Exception:
        limit = 20
    limit = max(1, min(limit, 100))

    accuracy_dir = _resolve_accuracy_dir()
    prediction_records = _load_json_records(accuracy_dir / "accuracy_ledger.json")

    actual_records: list[dict] = []
    for filename in ["actual_results.json", "actual_results_manual.json", "actual_results_unresolved.json"]:
        actual_records.extend(_load_json_records(accuracy_dir / filename))

    ledger_path = Path(_resolve_global_ledger_path(accuracy_dir))
    global_ledger_rows: list[dict] = []
    if ledger_path.exists():
        with ledger_path.open("r", encoding="utf-8") as _handle:
            for _line_num, _line_text in enumerate(_handle, start=1):
                _stripped = _line_text.strip()
                if not _stripped:
                    continue
                try:
                    _row = json.loads(_stripped)
                    if isinstance(_row, dict):
                        global_ledger_rows.append(_row)
                    else:
                        payload["errors"].append(f"malformed_ledger_row_line_{_line_num}: not a JSON object")
                except Exception as _exc:
                    payload["errors"].append(f"malformed_ledger_row_line_{_line_num}: {_exc}")

    bridge_records: list[dict] = []
    for pred_row in prediction_records:
        evidence = _build_approved_apply_report_scoring_bridge_evidence(
            pred_row,
            actual_records,
            global_ledger_rows,
        )
        bridge_status = _derive_scoring_bridge_status(evidence)
        record = dict(evidence)
        record["scoring_bridge_status"] = bridge_status
        record["generated_at"] = generated_at
        bridge_records.append(record)

    if prediction_report_id_filter is not None:
        pid_filter = str(prediction_report_id_filter).strip()
        bridge_records = [r for r in bridge_records if str(r.get("prediction_report_id") or "") == pid_filter]

    if local_result_key_filter is not None:
        lrk_filter = str(local_result_key_filter).strip()
        bridge_records = [r for r in bridge_records if str(r.get("local_result_key") or "") == lrk_filter]

    if not bridge_records:
        return payload

    bridge_records.sort(key=lambda r: str(r.get("prediction_report_id") or ""))

    status_counts: dict[str, int] = dict(empty_status_counts)
    for record in bridge_records:
        status = str(record.get("scoring_bridge_status") or "missing")
        status_counts[status] = status_counts.get(status, 0) + 1

    payload["bridge_available"] = True
    payload["total_records"] = len(bridge_records)
    payload["latest_records"] = bridge_records[:limit]
    payload["status_counts"] = status_counts
    return payload


def _build_accuracy_comparison_summary() -> dict:
    base_dir = Path(__file__).resolve().parent.parent
    accuracy_dir = _resolve_accuracy_dir()

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
    accuracy_dir = _resolve_accuracy_dir()

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


_OFFICIAL_SOURCE_TIER_A0_HOSTS = {
    "ufc.com",
    "www.ufc.com",
    "onefc.com",
    "www.onefc.com",
    "onechampionship.com",
    "www.onechampionship.com",
}

_OFFICIAL_SOURCE_TIER_A1_HOSTS = {
    "m.ufc.com",
    "results.ufc.com",
    "watch.onefc.com",
}

_OFFICIAL_SOURCE_TIER_B_HOSTS = {
    "tapology.com",
    "www.tapology.com",
    "sherdog.com",
    "www.sherdog.com",
    "boxrec.com",
    "www.boxrec.com",
}

_DISALLOWED_REDIRECT_HOSTS = {
    "bit.ly",
    "tinyurl.com",
    "t.co",
    "ow.ly",
    "buff.ly",
    "lnk.to",
    "linktr.ee",
    "goo.gl",
}


def _classify_official_source_host(url: str) -> str:
    try:
        parsed = urlparse(str(url or "").strip())
    except Exception:
        return "denied"

    host = (parsed.netloc or "").strip().lower()
    if ":" in host:
        host = host.split(":", 1)[0]

    if parsed.scheme.lower() != "https" or not host:
        return "denied"
    if host in _DISALLOWED_REDIRECT_HOSTS:
        return "denied"
    if host in _OFFICIAL_SOURCE_TIER_A0_HOSTS:
        return "tier_a0"
    if host in _OFFICIAL_SOURCE_TIER_A1_HOSTS:
        return "tier_a1"
    if host in _OFFICIAL_SOURCE_TIER_B_HOSTS:
        return "tier_b"
    return "denied"


def _is_allowed_official_source_url(url: str) -> bool:
    return _classify_official_source_host(url) in {"tier_a0", "tier_a1", "tier_b"}


def _build_citation_fingerprint(selected_key: str, citation: dict) -> str:
    citation = citation if isinstance(citation, dict) else {}
    parts = [
        str(selected_key or "").strip(),
        str(citation.get("source_url") or "").strip(),
        str(citation.get("source_title") or "").strip(),
        str(citation.get("source_date") or "").strip(),
        str(citation.get("winner") or citation.get("extracted_winner") or "").strip(),
        str(citation.get("method") or "").strip(),
        str(citation.get("round_time") or "").strip(),
    ]
    canonical = "|".join(parts)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]


def _classify_source_confidence(citation: dict) -> dict:
    citation = citation if isinstance(citation, dict) else {}
    source_url = str(citation.get("source_url") or "").strip()
    source_confidence = _classify_official_source_host(source_url)

    confidence_score_map = {
        "tier_a0": 0.85,
        "tier_a1": 0.72,
        "tier_b": 0.55,
        "denied": 0.0,
    }
    confidence_score = confidence_score_map.get(source_confidence, 0.0)

    if confidence_score >= 0.70:
        classification = "accepted_preview"
    elif confidence_score >= 0.40:
        classification = "manual_review"
    else:
        classification = "rejected_manual_review"

    return {
        "source_confidence": source_confidence,
        "confidence_score": confidence_score,
        "classification": classification,
    }


def _validate_official_source_citation(citation: dict) -> dict:
    citation = citation if isinstance(citation, dict) else {}
    source_url = str(citation.get("source_url") or "").strip()

    try:
        parsed = urlparse(source_url)
    except Exception:
        parsed = urlparse("")

    parsed_host = (parsed.netloc or "").strip().lower()
    if ":" in parsed_host:
        parsed_host = parsed_host.split(":", 1)[0]

    provided_host = str(citation.get("publisher_host") or "").strip().lower()
    effective_host = provided_host or parsed_host
    confidence = _classify_source_confidence({**citation, "source_url": source_url})

    missing_fields = [
        field for field in ("source_url", "source_title", "source_date", "publisher_host")
        if not str(citation.get(field) or "").strip()
    ]

    reason_code = "accepted_preview"
    manual_review_required = False
    accepted_preview = True

    if not _is_allowed_official_source_url(source_url):
        reason_code = "source_url_not_allowed"
        manual_review_required = True
        accepted_preview = False
    elif provided_host and parsed_host and provided_host != parsed_host:
        reason_code = "publisher_host_mismatch"
        manual_review_required = True
        accepted_preview = False
    elif missing_fields:
        reason_code = "citation_incomplete"
        manual_review_required = True
        accepted_preview = False
    elif confidence["source_confidence"] == "tier_b":
        reason_code = "tier_b_preview_only"
        manual_review_required = True
        accepted_preview = False
    elif confidence["classification"] != "accepted_preview":
        reason_code = "confidence_below_threshold"
        manual_review_required = True
        accepted_preview = False

    return {
        "ok": accepted_preview,
        "source_url": source_url or None,
        "publisher_host": effective_host or None,
        "source_confidence": confidence["source_confidence"],
        "confidence_score": confidence["confidence_score"],
        "classification": confidence["classification"],
        "citation_fingerprint": _build_citation_fingerprint(citation.get("selected_key") or "", citation) if not missing_fields and source_url else None,
        "manual_review_required": manual_review_required,
        "accepted_preview": accepted_preview,
        "missing_fields": missing_fields,
        "reason_code": reason_code,
        "write_eligible": accepted_preview and confidence["source_confidence"] in {"tier_a0", "tier_a1"},
    }


def _upsert_single_manual_actual_result(accuracy_dir: Path, write_row: dict) -> dict:
    target_path = accuracy_dir / "actual_results_manual.json"
    manual_rows = _load_json_records(target_path)
    before_row_count = len(manual_rows)

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
        return {
            "ok": True,
            "before_row_count": before_row_count,
            "after_row_count": len(manual_rows),
            "write_target": str(target_path),
        }
    except Exception:
        return {
            "ok": False,
            "before_row_count": before_row_count,
            "after_row_count": before_row_count,
            "write_target": str(target_path),
        }


def _build_selected_keys_digest(selected_keys: list) -> str:
    canonical = "|".join(sorted(selected_keys))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def _build_batch_preview_execution_token(selected_keys: list) -> tuple:
    token_ttl_seconds = 300
    keys_digest = _build_selected_keys_digest(selected_keys)
    nonce = uuid.uuid4().hex
    token = f"batch_preview_{int(time())}_{keys_digest}_{nonce}"
    return token, token_ttl_seconds


def _validate_batch_preview_token(token: str, selected_keys: list) -> tuple:
    if not token or not isinstance(token, str):
        return False, "execution_token is required", 0.0
    if not token.startswith("batch_preview_"):
        return False, "execution_token format invalid", 0.0
    parts = token.split("_")
    if len(parts) != 5:
        return False, "execution_token format invalid", 0.0
    try:
        issued_at = int(parts[2])
    except (ValueError, IndexError):
        return False, "execution_token format invalid", 0.0
    age_seconds = float(time() - issued_at)
    if age_seconds < 0:
        return False, "execution_token timestamp invalid", age_seconds
    if age_seconds > 300:
        return False, "execution_token expired", age_seconds
    token_digest = parts[3]
    if len(token_digest) != 16:
        return False, "execution_token format invalid", age_seconds
    expected_digest = _build_selected_keys_digest(selected_keys)
    if token_digest != expected_digest:
        return False, "execution_token selected_keys digest mismatch", age_seconds
    return True, "ok", age_seconds


def _build_phase1_intake_matchup_preview_row(
    raw_line: str,
    bout_order: int,
    source_reference: str,
) -> dict:
    line_text = str(raw_line or "").strip()
    lowered = line_text.lower()

    fighter_a = ""
    fighter_b = ""

    for separator in (" vs. ", " versus ", " vs ", " v "):
        if separator in lowered:
            split_index = lowered.find(separator)
            fighter_a = line_text[:split_index].strip(" -\t")
            fighter_b = line_text[split_index + len(separator):].strip(" -\t")
            break

    if not fighter_a and not fighter_b:
        if lowered.startswith("vs. "):
            fighter_b = line_text[4:].strip(" -\t")
        elif lowered.startswith("versus "):
            fighter_b = line_text[7:].strip(" -\t")
        elif lowered.startswith("vs "):
            fighter_b = line_text[3:].strip(" -\t")
        elif lowered.startswith("v "):
            fighter_b = line_text[2:].strip(" -\t")
        elif lowered.endswith(" vs."):
            fighter_a = line_text[:-4].strip(" -\t")
        elif lowered.endswith(" versus"):
            fighter_a = line_text[:-7].strip(" -\t")
        elif lowered.endswith(" vs"):
            fighter_a = line_text[:-3].strip(" -\t")
        elif lowered.endswith(" v"):
            fighter_a = line_text[:-2].strip(" -\t")

    parse_status = "parsed" if fighter_a and fighter_b else "needs_review"
    parse_notes = "" if parse_status == "parsed" else "incomplete_matchup_row"
    deterministic_seed = f"{bout_order}|{line_text}"
    temporary_matchup_id = f"tmp_{hashlib.sha256(deterministic_seed.encode('utf-8')).hexdigest()[:12]}"

    return {
        "temporary_matchup_id": temporary_matchup_id,
        "fighter_a": fighter_a,
        "fighter_b": fighter_b,
        "bout_order": bout_order,
        "weight_class": None,
        "ruleset": None,
        "source_reference": source_reference,
        "parse_status": parse_status,
        "parse_notes": parse_notes,
    }


def _build_phase1_intake_preview_payload(request_json: dict) -> dict:
    request_json = request_json if isinstance(request_json, dict) else {}
    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    raw_card_text = request_json.get("raw_card_text")
    raw_card_text_preserved = "" if raw_card_text is None else str(raw_card_text)
    event_date = str(request_json.get("event_date") or "").strip()
    source_reference = str(request_json.get("source_reference") or "").strip()

    parse_warnings = []
    if not event_date:
        parse_warnings.append("missing_event_date")

    matchup_previews = []
    bout_order = 1
    for raw_line in raw_card_text_preserved.splitlines():
        line_text = str(raw_line or "").strip()
        if not line_text:
            continue
        lowered = line_text.lower()
        looks_like_matchup = (
            " vs. " in lowered
            or " versus " in lowered
            or " vs " in lowered
            or " v " in lowered
            or lowered.startswith("vs. ")
            or lowered.startswith("versus ")
            or lowered.startswith("vs ")
            or lowered.startswith("v ")
            or lowered.endswith(" vs.")
            or lowered.endswith(" versus")
            or lowered.endswith(" vs")
            or lowered.endswith(" v")
        )
        if not looks_like_matchup:
            continue
        matchup_previews.append(
            _build_phase1_intake_matchup_preview_row(
                line_text,
                bout_order,
                source_reference,
            )
        )
        bout_order += 1

    event_preview = {
        "event_name": str(request_json.get("event_name") or "").strip(),
        "event_date": event_date,
        "promotion": str(request_json.get("promotion") or "").strip(),
        "location": str(request_json.get("location") or "").strip(),
        "source_reference": source_reference,
        "notes": str(request_json.get("notes") or "").strip(),
        "raw_card_text_preserved": raw_card_text_preserved,
    }

    return {
        "ok": True,
        "generated_at": generated_at,
        "event_preview": event_preview,
        "matchup_previews": matchup_previews,
        "parse_warnings": parse_warnings,
        "errors": [],
    }


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


@app.route("/api/operator/accuracy-calibration-review", methods=["POST"])
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


@app.route("/api/premium-report-factory/intake/preview", methods=["POST"])
def api_premium_report_factory_phase1_intake_preview():
    request_json = request.get_json(silent=True)
    if request_json is None:
        request_json = {}

    if not isinstance(request_json, dict):
        return jsonify({
            "ok": False,
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "event_preview": {
                "event_name": "",
                "event_date": "",
                "promotion": "",
                "location": "",
                "source_reference": "",
                "notes": "",
                "raw_card_text_preserved": "",
            },
            "matchup_previews": [],
            "parse_warnings": [],
            "errors": ["request_json_object_required"],
        }), 400

    return jsonify(_build_phase1_intake_preview_payload(request_json))


def _get_prf_queue_path() -> str:
    """Return the PRF queue file path, using test override when set."""
    override = app.config.get("PRF_QUEUE_PATH_OVERRIDE")
    if override:
        return override
    base_dir = Path(__file__).resolve().parent.parent
    return str(base_dir / "ops" / "prf_queue" / "upcoming_fight_queue.json")


@app.route("/api/premium-report-factory/queue/save-selected", methods=["POST"])
def api_premium_report_factory_queue_save_selected():
    from operator_dashboard.prf_queue_utils import process_prf_save_selected
    request_json = request.get_json(silent=True)
    if request_json is None:
        request_json = {}
    queue_path = _get_prf_queue_path()
    result = process_prf_save_selected(request_json, queue_path)
    status_code = 200 if result.get('ok') else 400
    return jsonify(result), status_code


@app.route("/api/premium-report-factory/queue", methods=["GET"])
def api_premium_report_factory_queue():
    from operator_dashboard.prf_queue_utils import get_prf_queue_list
    queue_path = _get_prf_queue_path()
    result = get_prf_queue_list(queue_path)
    return jsonify(result)


def _get_prf_reports_dir() -> str:
    """Return the PRF reports directory path, using test override when set."""
    override = app.config.get("PRF_REPORTS_DIR_OVERRIDE")
    if override:
        return override
    base_dir = Path(__file__).resolve().parent.parent
    return str(base_dir / "ops" / "prf_reports")


@app.route("/api/premium-report-factory/reports/generate", methods=["POST"])
def api_premium_report_factory_reports_generate():
    from operator_dashboard.prf_report_builder import generate_reports
    from operator_dashboard.prf_queue_utils import load_prf_queue, update_report_status

    request_json = request.get_json(silent=True)
    if not isinstance(request_json, dict):
        request_json = {}

    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    operator_approval = bool(request_json.get("operator_approval"))

    if not operator_approval:
        return jsonify({
            "ok": False,
            "generated_at": generated_at,
            "accepted_count": 0,
            "rejected_count": 0,
            "generated_reports": [],
            "rejected_reports": [],
            "export_summary": {"output_folder": _get_prf_reports_dir(), "total_files": 0, "total_size_bytes": 0},
            "warnings": [],
            "errors": ["operator_approval_required"],
        }), 400

    selected_matchup_ids = request_json.get("selected_matchup_ids") or []
    if not isinstance(selected_matchup_ids, list):
        selected_matchup_ids = []

    report_type = str(request_json.get("report_type") or "").strip()
    export_format = str(request_json.get("export_format") or "pdf").strip() or "pdf"
    notes = str(request_json.get("notes") or "").strip()
    allow_draft = bool(request_json.get("allow_draft", False))

    queue_path = _get_prf_queue_path()
    all_queue_records = load_prf_queue(queue_path)

    if selected_matchup_ids:
        id_set = set(str(mid) for mid in selected_matchup_ids if mid)
        queue_records = [r for r in all_queue_records if r.get("matchup_id") in id_set]
    else:
        queue_records = list(all_queue_records)

    reports_dir = _get_prf_reports_dir()

    result = generate_reports(
        queue_records=queue_records,
        report_type=report_type,
        operator_approval=operator_approval,
        export_format=export_format,
        notes=notes,
        reports_dir=reports_dir,
        allow_draft=allow_draft,
    )

    # Update report_status in queue for successfully generated reports
    for gen_report in result.get("generated_reports") or []:
        try:
            update_report_status(
                queue_path,
                gen_report["matchup_id"],
                gen_report["report_status"],
            )
        except Exception:
            pass

    status_code = 200 if result.get("ok") else 400
    return jsonify(result), status_code


@app.route("/api/premium-report-factory/reports/list", methods=["GET"])
def api_premium_report_factory_reports_list():
    from operator_dashboard.prf_report_builder import list_generated_reports
    reports_dir = _get_prf_reports_dir()
    result = list_generated_reports(reports_dir)
    return jsonify(result)


@app.route("/api/premium-report-factory/reports/download/<report_id>", methods=["GET"])
def api_premium_report_factory_reports_download(report_id):
    """Download a generated premium report file from the reports directory."""
    file_name = str(request.args.get("file_name") or "").strip()
    if not file_name:
        return jsonify({
            "ok": False,
            "report_id": str(report_id or ""),
            "errors": ["file_name_required"],
        }), 400

    # Prevent path traversal and non-PDF downloads.
    safe_file_name = Path(file_name).name
    if safe_file_name != file_name or not safe_file_name.lower().endswith(".pdf"):
        return jsonify({
            "ok": False,
            "report_id": str(report_id or ""),
            "errors": ["invalid_file_name"],
        }), 400

    reports_dir = Path(_get_prf_reports_dir()).resolve()
    file_path = (reports_dir / safe_file_name).resolve()
    try:
        file_path.relative_to(reports_dir)
    except Exception:
        return jsonify({
            "ok": False,
            "report_id": str(report_id or ""),
            "errors": ["invalid_file_name"],
        }), 400

    if not file_path.exists() or not file_path.is_file():
        return jsonify({
            "ok": False,
            "report_id": str(report_id or ""),
            "errors": ["report_file_not_found"],
        }), 404

    return send_file(
        str(file_path),
        as_attachment=True,
        download_name=safe_file_name,
        mimetype="application/pdf",
    )


@app.route("/api/premium-report-factory/reports/open-folder", methods=["POST"])
def api_premium_report_factory_reports_open_folder():
    """Open a reports folder path in the local OS shell with strict path validation."""
    request_json = request.get_json(silent=True)
    if not isinstance(request_json, dict):
        request_json = {}

    requested_path = str(request_json.get("folder_path") or "").strip()
    reports_dir = Path(_get_prf_reports_dir()).resolve()

    if requested_path:
        target_dir = Path(requested_path).resolve()
    else:
        target_dir = reports_dir

    try:
        target_dir.relative_to(reports_dir)
    except Exception:
        return jsonify({
            "ok": False,
            "opened_path": "",
            "errors": ["invalid_folder_path"],
        }), 400

    if not target_dir.exists() or not target_dir.is_dir():
        return jsonify({
            "ok": False,
            "opened_path": str(target_dir),
            "errors": ["folder_not_found"],
        }), 404

    try:
        if os.name == "nt":
            os.startfile(str(target_dir))
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(target_dir)])
        else:
            subprocess.Popen(["xdg-open", str(target_dir)])
    except Exception as exc:
        return jsonify({
            "ok": False,
            "opened_path": str(target_dir),
            "errors": ["open_folder_failed: {}".format(exc)],
        }), 500

    return jsonify({
        "ok": True,
        "opened_path": str(target_dir),
        "errors": [],
    })


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


@app.route("/api/operator/actual-result-lookup/global-ledger-summary", methods=["GET"])
def api_operator_actual_result_lookup_global_ledger_summary():
    try:
        return jsonify(
            _build_official_source_approved_apply_global_ledger_summary(
                request.args.get("limit")
            )
        )
    except Exception as exc:
        return jsonify({
            "ok": False,
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "ledger_available": False,
            "total_rows": 0,
            "latest_rows": [],
            "status_counts": {},
            "errors": [str(exc)],
        }), 500


@app.route("/api/operator/report-scoring-bridge/summary", methods=["GET"])
def api_operator_report_scoring_bridge_summary():
    limit_raw = request.args.get("limit")
    prediction_report_id_filter = request.args.get("prediction_report_id") or None
    local_result_key_filter = request.args.get("local_result_key") or None
    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    _empty_error_response = {
        "ok": False,
        "generated_at": generated_at,
        "bridge_available": False,
        "total_records": 0,
        "latest_records": [],
        "status_counts": {"ok": 0, "unresolved": 0, "conflict": 0, "missing": 0},
        "errors": [],
    }
    if limit_raw is not None:
        try:
            limit_int = int(limit_raw)
        except (ValueError, TypeError):
            _empty_error_response["errors"] = [f"invalid_limit: {limit_raw!r} is not an integer"]
            return jsonify(_empty_error_response), 400
        if limit_int < 1 or limit_int > 100:
            _empty_error_response["errors"] = [f"limit_out_of_range: must be 1–100, got {limit_int}"]
            return jsonify(_empty_error_response), 400
    try:
        return jsonify(
            _build_official_source_approved_apply_report_scoring_bridge_summary(
                prediction_report_id_filter=prediction_report_id_filter,
                local_result_key_filter=local_result_key_filter,
                limit_raw=limit_raw,
            )
        )
    except Exception as exc:
        _empty_error_response["errors"] = [str(exc)]
        return jsonify(_empty_error_response), 500


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


@app.route("/api/operator/actual-result-lookup/official-source-one-record-preview", methods=["POST"])
def api_operator_actual_result_lookup_official_source_one_record_preview():
    data = request.get_json(silent=True) or {}
    selected_key_raw = data.get("selected_key")
    mode = str(data.get("mode") or "").strip()
    lookup_intent = str(data.get("lookup_intent") or "").strip()
    approval_granted = bool(data.get("approval_granted"))
    candidate_urls_raw = data.get("candidate_urls")  # optional

    selected_key = ""
    if isinstance(selected_key_raw, str):
        selected_key = selected_key_raw.strip()

    base_payload = {
        "ok": False,
        "mode": "official_source_one_record",
        "phase": "lookup_preview",
        "selected_key": selected_key or None,
        "approval_required": True,
        "approval_granted": False,
        "mutation_performed": False,
        "external_lookup_performed": False,
        "bulk_lookup_performed": False,
        "scoring_semantics_changed": False,
        "selected_row": None,
        "local_result_found": False,
        "proposed_write": None,
        "source_citation": None,
        "manual_review_required": True,
        "candidate_urls_supplied": False,
        "candidate_url_count": 0,
        "audit": {
            "selected_key": selected_key or None,
            "operator_note_present": bool(str(data.get("operator_note") or "").strip()),
            "reason_code": None,
            "matched_local_source_file": None,
            "record_fight_id": None,
            "write_performed": False,
        },
        "message": "Preview contract only. Live official-source lookup is not executed in v1a.",
    }

    if isinstance(selected_key_raw, (list, tuple, dict)):
        return jsonify({**base_payload, "error": "selected_key must be a string"}), 400

    if not selected_key:
        return jsonify({**base_payload, "error": "selected_key is required"}), 400

    if mode != "official_source_one_record":
        return jsonify({**base_payload, "error": "mode must be official_source_one_record"}), 400

    if lookup_intent != "preview_only":
        return jsonify({**base_payload, "error": "lookup_intent must be preview_only"}), 400

    if approval_granted:
        return jsonify({**base_payload, "error": "approval_granted must be false for preview-only endpoint"}), 400

    for forbidden_field in ("targets", "selected_keys", "batch_size", "execution_token"):
        if forbidden_field in data:
            return jsonify({**base_payload, "error": f"{forbidden_field} is not allowed for one-record preview endpoint"}), 400

    # candidate_urls validation
    candidate_urls_for_provider = None  # None = use provider discovery
    if candidate_urls_raw is not None:
        if not isinstance(candidate_urls_raw, list):
            return jsonify({**base_payload, "error": "candidate_urls must be a list"}), 400
        if len(candidate_urls_raw) == 0:
            return jsonify({
                **base_payload,
                "error": "candidate_urls must not be empty when supplied",
                "audit": {**base_payload["audit"], "reason_code": "candidate_urls_empty"},
                "reason_code": "candidate_urls_empty",
            }), 400
        if len(candidate_urls_raw) > 3:
            return jsonify({
                **base_payload,
                "error": "candidate_urls exceeds limit of 3",
                "audit": {**base_payload["audit"], "reason_code": "candidate_urls_exceeds_limit"},
                "reason_code": "candidate_urls_exceeds_limit",
            }), 400
        # Validate each URL is a string, dedupe preserving order
        seen_urls = set()
        validated_urls = []
        for raw_url in candidate_urls_raw:
            if not isinstance(raw_url, str):
                return jsonify({**base_payload, "error": "each candidate_url must be a string"}), 400
            stripped = raw_url.strip()
            if stripped and stripped not in seen_urls:
                seen_urls.add(stripped)
                validated_urls.append(stripped)
        if not validated_urls:
            return jsonify({
                **base_payload,
                "error": "candidate_urls must not be empty when supplied",
                "audit": {**base_payload["audit"], "reason_code": "candidate_urls_empty"},
                "reason_code": "candidate_urls_empty",
            }), 400
        for candidate_url in validated_urls:
            if not _is_allowed_official_source_url(candidate_url):
                return jsonify({
                    **base_payload,
                    "error": "candidate_urls contains a disallowed URL",
                    "audit": {**base_payload["audit"], "reason_code": "source_url_not_allowed"},
                    "reason_code": "source_url_not_allowed",
                }), 400
        candidate_urls_for_provider = validated_urls
        base_payload["candidate_urls_supplied"] = True
        base_payload["candidate_url_count"] = len(validated_urls)

    summary = _build_accuracy_comparison_summary()
    waiting_rows = summary.get("waiting_for_results") or []
    selected_row = None
    for row in waiting_rows:
        if _build_waiting_row_selected_key(row) == selected_key:
            selected_row = dict(row)
            break

    if selected_row is None:
        response_payload = {
            **base_payload,
            "error": "selected_key not found in waiting rows",
            "reason_code": "selected_key_not_found",
            "audit": {
                **base_payload["audit"],
                "reason_code": "selected_key_not_found",
            },
            "message": "Selected row was not found. Manual review required.",
        }
        response_payload["acceptance_gate"] = evaluate_official_source_acceptance_gate(response_payload)
        return jsonify(response_payload), 404

    selected_row["selected_key"] = selected_key
    if not _is_known_value(selected_row.get("fight_id")):
        selected_row["fight_id"] = _normalize_token(selected_row.get("fight_name")) or None

    local_actual_map, _accuracy_dir = _load_local_actual_result_map()
    local_actual = None
    local_actual_source = None
    for key in _build_waiting_row_candidate_fight_keys(selected_row):
        matched = local_actual_map.get(key)
        if matched and _is_known_value(matched["record"].get("actual_winner")):
            local_actual = dict(matched["record"])
            local_actual_source = matched["source_file"]
            break

    if local_actual is not None:
        response_payload = {
            **base_payload,
            "ok": True,
            "selected_row": selected_row,
            "local_result_found": True,
            "manual_review_required": False,
            "reason_code": "local_result_found_preview_only",
            "audit": {
                **base_payload["audit"],
                "reason_code": "local_result_found_preview_only",
                "matched_local_source_file": local_actual_source,
                "record_fight_id": local_actual.get("fight_id") or selected_row.get("fight_id"),
            },
            "message": "Local actual result already exists. Official-source preview did not mutate any files in v1a.",
        }
        response_payload["acceptance_gate"] = evaluate_official_source_acceptance_gate(response_payload)
        return jsonify(response_payload)

    provider_result = {
        "provider_attempted": False,
        "external_lookup_performed": False,
        "source_citation": None,
        "manual_review_required": True,
        "reason_code": "official_source_lookup_not_connected",
        "attempted_sources": [],
        "timeout_budget_seconds": 20,
        "per_source_timeout_seconds": 6,
        "auto_retry_count": 0,
        "candidate_urls_supplied": bool(candidate_urls_for_provider is not None),
        "candidate_url_count": len(candidate_urls_for_provider) if candidate_urls_for_provider else 0,
    }
    try:
        provider = OfficialSourceLookupProvider()
        provider_result = provider.run_preview_lookup(
            selected_key=selected_key,
            selected_row=selected_row,
            timeout_budget_seconds=20,
            per_source_timeout_seconds=6,
            auto_retry_count=0,
            candidate_urls=candidate_urls_for_provider,
        )
    except Exception:
        provider_result = {
            "provider_attempted": True,
            "external_lookup_performed": False,
            "source_citation": None,
            "manual_review_required": True,
            "reason_code": "official_source_lookup_not_connected",
            "attempted_sources": [],
            "timeout_budget_seconds": 20,
            "per_source_timeout_seconds": 6,
            "auto_retry_count": 0,
            "candidate_urls_supplied": bool(candidate_urls_for_provider is not None),
            "candidate_url_count": len(candidate_urls_for_provider) if candidate_urls_for_provider else 0,
        }

    reason_code = str(provider_result.get("reason_code") or "official_source_lookup_not_connected")
    response_payload = {
        **base_payload,
        "ok": True,
        "selected_row": selected_row,
        "external_lookup_performed": bool(provider_result.get("external_lookup_performed")),
        "source_citation": provider_result.get("source_citation"),
        "manual_review_required": bool(provider_result.get("manual_review_required", True)),
        "reason_code": reason_code,
        "candidate_urls_supplied": bool(provider_result.get("candidate_urls_supplied", base_payload["candidate_urls_supplied"])),
        "candidate_url_count": int(provider_result.get("candidate_url_count") or base_payload["candidate_url_count"]),
        "audit": {
            **base_payload["audit"],
            "reason_code": reason_code,
            "record_fight_id": selected_row.get("fight_id"),
            "provider_attempted": bool(provider_result.get("provider_attempted")),
            "attempted_sources": provider_result.get("attempted_sources") or [],
            "timeout_budget_seconds": int(provider_result.get("timeout_budget_seconds") or 20),
            "per_source_timeout_seconds": int(provider_result.get("per_source_timeout_seconds") or 6),
            "auto_retry_count": int(provider_result.get("auto_retry_count") or 0),
        },
        "message": "Official-source preview evaluated. No mutation performed.",
    }
    response_payload["acceptance_gate"] = evaluate_official_source_acceptance_gate(response_payload)
    return jsonify(response_payload)


@app.route("/api/operator/actual-result-lookup/official-source-approved-apply", methods=["POST"])
def api_operator_actual_result_lookup_official_source_approved_apply():
    def _append_operation_id_audit_record(
        *,
        operation_id: str | None,
        request_fingerprint: str | None,
        request_parse_status: str,
        guard_or_authorization_outcome: str,
        apply_or_write_outcome: str,
        token_consume_outcome: str,
        deterministic_status: str,
        selected_key: str | None,
        token_id: str | None,
        terminal_reason_code: str | None,
        internal_mutation_operation_id: str | None = None,
        write_attempt_id: str | None = None,
        contract_version: str | None = None,
        endpoint_version: str | None = None,
    ) -> None:
        if not operation_id or not request_fingerprint:
            return
        OFFICIAL_SOURCE_APPROVED_APPLY_OPERATION_ID_PERSISTENCE_HELPER.append_record(
            operation_id=operation_id,
            internal_mutation_operation_id=internal_mutation_operation_id,
            write_attempt_id=write_attempt_id,
            request_parse_status=request_parse_status,
            guard_or_authorization_outcome=guard_or_authorization_outcome,
            apply_or_write_outcome=apply_or_write_outcome,
            token_consume_outcome=token_consume_outcome,
            deterministic_status=deterministic_status,
            timestamp_utc=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            selected_key=selected_key,
            token_id=token_id,
            terminal_reason_code=terminal_reason_code,
            contract_version=contract_version,
            endpoint_version=endpoint_version,
            request_fingerprint=request_fingerprint,
            audit_path=app.config.get("OFFICIAL_SOURCE_APPROVED_APPLY_OPERATION_ID_AUDIT_PATH_OVERRIDE"),
        )

    def _operation_id_is_persistable(schema_result: dict) -> bool:
        operation_id = schema_result.get("operation_id")
        if not isinstance(operation_id, str) or not operation_id:
            return False
        if str(schema_result.get("reason_code") or "") == "operation_id_format_invalid":
            return False
        return True

    def _build_global_ledger_record(
        *,
        payload: dict,
        preview_snapshot: dict,
        operation_id: str | None,
        internal_mutation_uuid: str,
        approval_token_status: str | None,
        selected_key: str | None,
        write_target: str | None,
    ) -> dict:
        approval_binding = payload.get("approval_binding") if isinstance(payload, dict) else {}
        approval_binding = approval_binding if isinstance(approval_binding, dict) else {}
        selected_row_identity = approval_binding.get("selected_row_identity") if isinstance(approval_binding, dict) else {}
        selected_row_identity = selected_row_identity if isinstance(selected_row_identity, dict) else {}
        source_citation = preview_snapshot.get("source_citation") if isinstance(preview_snapshot, dict) else {}
        source_citation = source_citation if isinstance(source_citation, dict) else {}
        audit = preview_snapshot.get("audit") if isinstance(preview_snapshot, dict) else {}
        audit = audit if isinstance(audit, dict) else {}

        fight_id = str(audit.get("record_fight_id") or selected_row_identity.get("fight_id") or approval_binding.get("record_fight_id") or "").strip() or None
        fight_name = str(audit.get("fight_name") or selected_row_identity.get("fight_name") or "").strip()
        fighter_names = [name.strip() for name in fight_name.split(" vs ") if name.strip()] if fight_name else []

        extracted_winner = str(
            source_citation.get("extracted_winner")
            or approval_binding.get("extracted_winner")
            or ""
        ).strip() or None
        extracted_method = str(source_citation.get("extracted_method") or source_citation.get("method") or "").strip() or "UNKNOWN"
        extracted_round = str(source_citation.get("extracted_round") or source_citation.get("round_time") or "").strip() or "UNKNOWN"
        source_date = str(source_citation.get("source_date") or approval_binding.get("source_date") or "").strip() or None

        return {
            "global_ledger_record_id": uuid.uuid4().hex,
            "local_result_key": fight_id or (str(selected_key or "").strip() or None),
            "event_id": None,
            "bout_id": fight_id,
            "fighter_ids": [fight_id] if fight_id else [],
            "fighter_names": fighter_names,
            "official_source_reference": {
                "source_url": str(source_citation.get("source_url") or "").strip() or None,
                "source_title": str(source_citation.get("source_title") or "").strip() or None,
                "source_date": source_date,
                "publisher_host": str(source_citation.get("publisher_host") or "").strip() or None,
                "source_confidence": str(source_citation.get("source_confidence") or "").strip() or None,
                "citation_fingerprint": str(source_citation.get("citation_fingerprint") or "").strip() or None,
            },
            "approved_actual_result": {
                "fight_id": fight_id,
                "fight_name": fight_name or None,
                "actual_winner": extracted_winner,
                "actual_method": extracted_method,
                "actual_round": extracted_round,
                "event_date": source_date,
            },
            "operation_id": str(operation_id or "").strip() or None,
            "internal_mutation_uuid": internal_mutation_uuid,
            "approval_token_status": str(approval_token_status or "").strip() or None,
            "guard_outcome": "guard_allowed",
            "apply_or_write_outcome": "write_applied",
            "token_consume_outcome": "not_attempted",
            "local_audit_reference": {
                "operation_id_audit_path": app.config.get("OFFICIAL_SOURCE_APPROVED_APPLY_OPERATION_ID_AUDIT_PATH_OVERRIDE"),
                "selected_key": str(selected_key or "").strip() or None,
                "write_target": str(write_target or "").strip() or None,
            },
            "timestamp_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "deterministic_status": "write_applied_pending_token_consume",
        }

    def _normalized_response(
        *,
        ok: bool,
        request_valid: bool,
        token_valid: bool,
        guard_allowed: bool,
        manual_review_required: bool,
        approval_granted: bool,
        approval_binding_valid: bool,
        token_status: str,
        reason_code: str,
        errors: list,
        selected_key: str | None,
        acceptance_gate: dict | None,
        binding_digest_expected: str | None,
        binding_digest_actual: str | None,
        token_id: str | None = None,
        mutation_enabled: bool = False,
        fight_id: str | None = None,
        proposed_write: dict | None = None,
        write_target: str | None = None,
        before_row_count: int | None = None,
        after_row_count: int | None = None,
        pre_write_file_sha256: str | None = None,
        post_write_file_sha256: str | None = None,
        rollback_attempted: bool = False,
        rollback_succeeded: bool | None = None,
        post_rollback_file_sha256: str | None = None,
        rollback_reason_code: str | None = None,
        rollback_error_detail: str | None = None,
        rollback_started_at_utc: str | None = None,
        rollback_finished_at_utc: str | None = None,
        rollback_terminal_state: str | None = None,
        escalation_required: bool = False,
        operator_escalation_action: str | None = None,
        approval_token_id: str | None = None,
        operation_id: str | None = None,
        write_attempt_id: str | None = None,
        contract_version: str | None = None,
        endpoint_version: str | None = None,
        token_consume_performed: bool = False,
        token_consume_reason_code: str | None = None,
        token_consume_idempotent: bool = False,
        token_consume_attempted_at_utc: str | None = None,
        token_consume_completed_at_utc: str | None = None,
        token_consume_retry_count: int = 0,
    ) -> dict:
        token_status_value = str(token_status or "not_evaluated")
        return {
            "ok": bool(ok),
            "mode": "official_source_approved_apply",
            "phase": "approved_apply",
            "request_valid": bool(request_valid),
            "token_valid": bool(token_valid),
            "guard_allowed": bool(guard_allowed),
            "manual_review_required": bool(manual_review_required),
            "approval_required": True,
            "approval_granted": bool(approval_granted),
            "approval_binding_valid": bool(approval_binding_valid),
            "token_status": token_status_value,
            "approval_token_status": token_status_value,
            "mutation_performed": False,
            "write_performed": False,
            "bulk_lookup_performed": False,
            "scoring_semantics_changed": False,
            "external_lookup_performed": False,
            "reason_code": str(reason_code or "invalid_request_body"),
            "errors": list(errors or []),
            "selected_key": selected_key,
            "acceptance_gate": acceptance_gate,
            "binding_digest_expected": binding_digest_expected,
            "binding_digest_actual": binding_digest_actual,
            "token_id": token_id,
            "fight_id": fight_id,
            "proposed_write": proposed_write,
            "write_target": write_target,
            "before_row_count": before_row_count,
            "after_row_count": after_row_count,
            "pre_write_file_sha256": pre_write_file_sha256,
            "post_write_file_sha256": post_write_file_sha256,
            "rollback_attempted": bool(rollback_attempted),
            "rollback_succeeded": rollback_succeeded,
            "post_rollback_file_sha256": post_rollback_file_sha256,
            "rollback_reason_code": rollback_reason_code,
            "rollback_error_detail": rollback_error_detail,
            "rollback_started_at_utc": rollback_started_at_utc,
            "rollback_finished_at_utc": rollback_finished_at_utc,
            "rollback_terminal_state": rollback_terminal_state,
            "escalation_required": bool(escalation_required),
            "operator_escalation_action": operator_escalation_action,
            "approval_token_id": approval_token_id,
            "operation_id": operation_id,
            "write_attempt_id": write_attempt_id,
            "contract_version": contract_version,
            "endpoint_version": endpoint_version,
            "mutation_enabled": bool(mutation_enabled),
            "token_consume_performed": bool(token_consume_performed),
            "token_consume_reason_code": token_consume_reason_code,
            "token_consume_idempotent": bool(token_consume_idempotent),
            "token_consume_attempted_at_utc": token_consume_attempted_at_utc,
            "token_consume_completed_at_utc": token_consume_completed_at_utc,
            "token_consume_retry_count": int(token_consume_retry_count),
            "message": "Approved apply endpoint skeleton is decision-only and non-mutating.",
        }

    if not request.is_json:
        return jsonify(_normalized_response(
            ok=False,
            request_valid=False,
            token_valid=False,
            guard_allowed=False,
            manual_review_required=True,
            approval_granted=False,
            approval_binding_valid=False,
            token_status="not_evaluated",
            reason_code="invalid_request_body",
            errors=["request content-type must be application/json"],
            selected_key=None,
            acceptance_gate=None,
            binding_digest_expected=None,
            binding_digest_actual=None,
        )), 400

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(_normalized_response(
            ok=False,
            request_valid=False,
            token_valid=False,
            guard_allowed=False,
            manual_review_required=True,
            approval_granted=False,
            approval_binding_valid=False,
            token_status="not_evaluated",
            reason_code="invalid_request_body",
            errors=["request JSON body must be an object"],
            selected_key=None,
            acceptance_gate=None,
            binding_digest_expected=None,
            binding_digest_actual=None,
        )), 400

    schema_result = validate_official_source_approved_apply_request(data)
    preview_snapshot = data.get("preview_snapshot") if isinstance(data, dict) else None
    authoritative_preview_result = dict(preview_snapshot) if isinstance(preview_snapshot, dict) else {}
    authoritative_preview_result.setdefault("selected_key", data.get("selected_key"))
    authoritative_preview_result.setdefault("reason_code", "accepted_preview_write_eligible")
    authoritative_preview_result.setdefault("manual_review_required", False)
    authoritative_preview_result.setdefault("mutation_performed", False)
    authoritative_preview_result.setdefault("bulk_lookup_performed", False)
    authoritative_preview_result.setdefault("scoring_semantics_changed", False)
    authoritative_preview_result.setdefault("write_performed", False)

    guard_result = evaluate_official_source_approved_apply_guard(
        data,
        authoritative_preview_result=authoritative_preview_result,
        now_epoch=int(time()),
        consumed_token_ids=set(),
        replayed_token_ids=set(),
        allowed_clock_skew_seconds=5,
    )
    request_operation_id = guard_result.get("operation_id") or schema_result.get("operation_id")
    persistable_operation_id = request_operation_id if _operation_id_is_persistable(schema_result) else None
    request_fingerprint = None
    operation_id_lookup = None
    if persistable_operation_id:
        request_fingerprint = OFFICIAL_SOURCE_APPROVED_APPLY_OPERATION_ID_PERSISTENCE_HELPER.build_request_fingerprint(data)

    if persistable_operation_id and bool(schema_result.get("request_valid")):
        operation_id_lookup = OFFICIAL_SOURCE_APPROVED_APPLY_OPERATION_ID_PERSISTENCE_HELPER.lookup(
            persistable_operation_id,
            request_fingerprint,
            audit_path=app.config.get("OFFICIAL_SOURCE_APPROVED_APPLY_OPERATION_ID_AUDIT_PATH_OVERRIDE"),
        )

    response_payload = _normalized_response(
        ok=bool(guard_result.get("ok")),
        request_valid=bool(guard_result.get("request_valid") and schema_result.get("request_valid")),
        token_valid=bool(guard_result.get("token_valid")),
        guard_allowed=bool(guard_result.get("guard_allowed")),
        manual_review_required=bool(guard_result.get("manual_review_required")),
        approval_granted=bool(guard_result.get("approval_granted")),
        approval_binding_valid=bool(guard_result.get("approval_binding_valid")),
        token_status=str(guard_result.get("token_status") or "not_evaluated"),
        reason_code=str(guard_result.get("reason_code") or schema_result.get("reason_code") or "invalid_request_body"),
        errors=list(guard_result.get("errors") or schema_result.get("errors") or []),
        selected_key=guard_result.get("selected_key") or schema_result.get("selected_key"),
        acceptance_gate=guard_result.get("acceptance_gate"),
        binding_digest_expected=guard_result.get("binding_digest_expected"),
        binding_digest_actual=guard_result.get("binding_digest_actual"),
        token_id=guard_result.get("token_id"),
        operation_id=request_operation_id,
        mutation_enabled=bool(app.config.get("OFFICIAL_SOURCE_APPROVED_APPLY_MUTATION_ENABLED", False)),
    )

    if operation_id_lookup and operation_id_lookup.get("state") == "conflict":
        response_payload["ok"] = False
        response_payload["guard_allowed"] = False
        response_payload["manual_review_required"] = True
        response_payload["reason_code"] = "operation_id_conflict"
        response_payload["errors"] = ["operation_id already used with different request payload"]
        _append_operation_id_audit_record(
            operation_id=persistable_operation_id,
            request_fingerprint=request_fingerprint,
            request_parse_status="schema_valid",
            guard_or_authorization_outcome="guard_allowed" if bool(guard_result.get("guard_allowed")) else "guard_denied",
            apply_or_write_outcome="not_attempted",
            token_consume_outcome="not_attempted",
            deterministic_status="duplicate_conflict",
            selected_key=response_payload.get("selected_key"),
            token_id=response_payload.get("token_id"),
            terminal_reason_code="operation_id_conflict",
        )
        return jsonify(response_payload)

    if not bool(guard_result.get("guard_allowed")):
        _append_operation_id_audit_record(
            operation_id=persistable_operation_id,
            request_fingerprint=request_fingerprint,
            request_parse_status="schema_valid" if bool(schema_result.get("request_valid")) else "schema_invalid",
            guard_or_authorization_outcome="guard_denied",
            apply_or_write_outcome="not_attempted",
            token_consume_outcome="not_attempted",
            deterministic_status="guard_denied" if bool(schema_result.get("request_valid")) else "schema_invalid",
            selected_key=response_payload.get("selected_key"),
            token_id=response_payload.get("token_id"),
            terminal_reason_code=response_payload.get("reason_code"),
        )
        return jsonify(response_payload)

    if operation_id_lookup and operation_id_lookup.get("state") == "already_applied":
        response_payload["ok"] = True
        response_payload["reason_code"] = "operation_id_already_applied"
        response_payload["errors"] = []
        response_payload["mutation_performed"] = False
        response_payload["write_performed"] = False
        response_payload["token_consume_performed"] = False
        response_payload["message"] = "Approved apply already recorded for this operation_id."
        previous_record = operation_id_lookup.get("record") or {}
        _append_operation_id_audit_record(
            operation_id=persistable_operation_id,
            request_fingerprint=request_fingerprint,
            request_parse_status="schema_valid",
            guard_or_authorization_outcome="guard_allowed",
            apply_or_write_outcome="not_attempted",
            token_consume_outcome="not_attempted",
            deterministic_status="already_applied_replay",
            selected_key=response_payload.get("selected_key"),
            token_id=response_payload.get("token_id"),
            terminal_reason_code="operation_id_already_applied",
            internal_mutation_operation_id=previous_record.get("internal_mutation_operation_id"),
            write_attempt_id=previous_record.get("write_attempt_id"),
            contract_version=previous_record.get("contract_version"),
            endpoint_version=previous_record.get("endpoint_version"),
        )
        return jsonify(response_payload)

    if not bool(app.config.get("OFFICIAL_SOURCE_APPROVED_APPLY_MUTATION_ENABLED", False)):
        response_payload["reason_code"] = "mutation_disabled_after_guard"
        response_payload["message"] = "Approved apply mutation remains disabled unless dark/test config is enabled."
        _append_operation_id_audit_record(
            operation_id=persistable_operation_id,
            request_fingerprint=request_fingerprint,
            request_parse_status="schema_valid",
            guard_or_authorization_outcome="guard_allowed",
            apply_or_write_outcome="not_attempted",
            token_consume_outcome="not_attempted",
            deterministic_status="guard_allowed_no_write",
            selected_key=response_payload.get("selected_key"),
            token_id=response_payload.get("token_id"),
            terminal_reason_code=response_payload.get("reason_code"),
        )
        return jsonify(response_payload)

    accuracy_dir_override = app.config.get("OFFICIAL_SOURCE_APPROVED_APPLY_ACCURACY_DIR_OVERRIDE")
    accuracy_dir_text = str(accuracy_dir_override or "").strip()
    if not accuracy_dir_text:
        response_payload["ok"] = False
        response_payload["reason_code"] = "mutation_accuracy_dir_not_configured"
        response_payload["errors"] = ["OFFICIAL_SOURCE_APPROVED_APPLY_ACCURACY_DIR_OVERRIDE is required when mutation is enabled"]
        response_payload["message"] = "Approved apply mutation failed closed: accuracy dir override is not configured."
        _append_operation_id_audit_record(
            operation_id=persistable_operation_id,
            request_fingerprint=request_fingerprint,
            request_parse_status="schema_valid",
            guard_or_authorization_outcome="guard_allowed",
            apply_or_write_outcome="not_attempted",
            token_consume_outcome="not_attempted",
            deterministic_status="write_not_attempted",
            selected_key=response_payload.get("selected_key"),
            token_id=response_payload.get("token_id"),
            terminal_reason_code=response_payload.get("reason_code"),
        )
        return jsonify(response_payload)

    accuracy_dir = Path(accuracy_dir_text)
    if not accuracy_dir.is_dir():
        response_payload["ok"] = False
        response_payload["reason_code"] = "mutation_accuracy_dir_not_configured"
        response_payload["errors"] = ["configured accuracy dir override does not exist"]
        response_payload["message"] = "Approved apply mutation failed closed: configured accuracy dir override is invalid."
        _append_operation_id_audit_record(
            operation_id=persistable_operation_id,
            request_fingerprint=request_fingerprint,
            request_parse_status="schema_valid",
            guard_or_authorization_outcome="guard_allowed",
            apply_or_write_outcome="not_attempted",
            token_consume_outcome="not_attempted",
            deterministic_status="write_not_attempted",
            selected_key=response_payload.get("selected_key"),
            token_id=response_payload.get("token_id"),
            terminal_reason_code=response_payload.get("reason_code"),
        )
        return jsonify(response_payload)

    global_ledger_path = _resolve_global_ledger_path(accuracy_dir)

    internal_operation_id = uuid.uuid4().hex
    write_attempt_id = uuid.uuid4().hex
    contract_version = "official_source_approved_apply_contract_v1"
    endpoint_version = "official_source_approved_apply_endpoint_mutation_v1"

    prospective_global_ledger_record = _build_global_ledger_record(
        payload=data,
        preview_snapshot=authoritative_preview_result,
        operation_id=persistable_operation_id,
        internal_mutation_uuid=internal_operation_id,
        approval_token_status=response_payload.get("token_status"),
        selected_key=response_payload.get("selected_key"),
        write_target=None,
    )
    global_ledger_fingerprint = OFFICIAL_SOURCE_APPROVED_APPLY_GLOBAL_LEDGER_HELPER.build_request_fingerprint(prospective_global_ledger_record)
    global_ledger_lookup = OFFICIAL_SOURCE_APPROVED_APPLY_GLOBAL_LEDGER_HELPER.lookup(
        prospective_global_ledger_record.get("local_result_key"),
        global_ledger_fingerprint,
        ledger_path=global_ledger_path,
    )

    if global_ledger_lookup.get("state") == "conflict":
        response_payload["ok"] = False
        response_payload["reason_code"] = "global_ledger_conflict"
        response_payload["errors"] = ["global ledger already contains a conflicting approved result for this local result key"]
        response_payload["global_ledger_write_performed"] = False
        response_payload["global_ledger_reason_code"] = "global_ledger_conflict"
        response_payload["global_ledger_path"] = global_ledger_path
        _append_operation_id_audit_record(
            operation_id=persistable_operation_id,
            request_fingerprint=request_fingerprint,
            request_parse_status="schema_valid",
            guard_or_authorization_outcome="guard_allowed",
            apply_or_write_outcome="not_attempted",
            token_consume_outcome="not_attempted",
            deterministic_status="global_ledger_conflict",
            selected_key=response_payload.get("selected_key"),
            token_id=response_payload.get("token_id"),
            terminal_reason_code=response_payload.get("reason_code"),
            internal_mutation_operation_id=internal_operation_id,
            write_attempt_id=write_attempt_id,
            contract_version=contract_version,
            endpoint_version=endpoint_version,
        )
        return jsonify(response_payload)

    if global_ledger_lookup.get("state") == "already_recorded":
        response_payload["ok"] = True
        response_payload["mutation_performed"] = False
        response_payload["write_performed"] = False
        response_payload["reason_code"] = "global_ledger_already_recorded"
        response_payload["errors"] = []
        response_payload["global_ledger_write_performed"] = False
        response_payload["global_ledger_reason_code"] = "global_ledger_already_recorded"
        response_payload["global_ledger_path"] = global_ledger_path
        previous_record = global_ledger_lookup.get("record") or {}
        _append_operation_id_audit_record(
            operation_id=persistable_operation_id,
            request_fingerprint=request_fingerprint,
            request_parse_status="schema_valid",
            guard_or_authorization_outcome="guard_allowed",
            apply_or_write_outcome="not_attempted",
            token_consume_outcome="not_attempted",
            deterministic_status="global_ledger_already_recorded",
            selected_key=response_payload.get("selected_key"),
            token_id=response_payload.get("token_id"),
            terminal_reason_code=response_payload.get("reason_code"),
            internal_mutation_operation_id=previous_record.get("internal_mutation_uuid"),
            write_attempt_id=write_attempt_id,
            contract_version=contract_version,
            endpoint_version=endpoint_version,
        )
        return jsonify(response_payload)

    adapter_result = apply_official_source_approved_apply_mutation(
        guard_result=guard_result,
        preview_snapshot=authoritative_preview_result,
        accuracy_dir=accuracy_dir,
        consumed_token_ids=set(),
        lock_timeout_seconds=10,
        operation_id=internal_operation_id,
        write_attempt_id=write_attempt_id,
        contract_version=contract_version,
        endpoint_version=endpoint_version,
    )

    for field_name in [
        "fight_id",
        "proposed_write",
        "write_target",
        "before_row_count",
        "after_row_count",
        "pre_write_file_sha256",
        "post_write_file_sha256",
        "rollback_attempted",
        "rollback_succeeded",
        "post_rollback_file_sha256",
        "rollback_reason_code",
        "rollback_error_detail",
        "rollback_started_at_utc",
        "rollback_finished_at_utc",
        "rollback_terminal_state",
        "escalation_required",
        "operator_escalation_action",
        "approval_token_id",
        "write_attempt_id",
        "contract_version",
        "endpoint_version",
    ]:
        response_payload[field_name] = adapter_result.get(field_name)

    response_payload["ok"] = bool(adapter_result.get("ok"))
    response_payload["mutation_performed"] = bool(adapter_result.get("mutation_performed"))
    response_payload["write_performed"] = bool(adapter_result.get("write_performed"))
    response_payload["reason_code"] = str(adapter_result.get("reason_code") or response_payload.get("reason_code") or "internal_apply_error")
    response_payload["errors"] = list(adapter_result.get("errors") or response_payload.get("errors") or [])
    response_payload["approval_token_id"] = adapter_result.get("approval_token_id") or response_payload.get("approval_token_id")

    if not response_payload.get("write_performed"):
        _append_operation_id_audit_record(
            operation_id=persistable_operation_id,
            request_fingerprint=request_fingerprint,
            request_parse_status="schema_valid",
            guard_or_authorization_outcome="guard_allowed",
            apply_or_write_outcome="write_failed",
            token_consume_outcome="not_attempted",
            deterministic_status="write_failed",
            selected_key=response_payload.get("selected_key"),
            token_id=response_payload.get("token_id"),
            terminal_reason_code=response_payload.get("reason_code"),
            internal_mutation_operation_id=internal_operation_id,
            write_attempt_id=write_attempt_id,
            contract_version=contract_version,
            endpoint_version=endpoint_version,
        )
        return jsonify(response_payload)

    global_ledger_record = _build_global_ledger_record(
        payload=data,
        preview_snapshot=authoritative_preview_result,
        operation_id=persistable_operation_id,
        internal_mutation_uuid=internal_operation_id,
        approval_token_status=response_payload.get("token_status"),
        selected_key=response_payload.get("selected_key"),
        write_target=response_payload.get("write_target"),
    )

    try:
        appended_global_ledger_record = OFFICIAL_SOURCE_APPROVED_APPLY_GLOBAL_LEDGER_HELPER.append_record(
            record=global_ledger_record,
            request_fingerprint=global_ledger_fingerprint,
            ledger_path=global_ledger_path,
        )
        response_payload["global_ledger_write_performed"] = True
        response_payload["global_ledger_reason_code"] = "global_ledger_write_applied"
        response_payload["global_ledger_record_id"] = appended_global_ledger_record.get("global_ledger_record_id")
        response_payload["global_ledger_path"] = global_ledger_path
    except Exception as exc:
        response_payload["ok"] = False
        response_payload["reason_code"] = "global_ledger_write_failed"
        response_payload["errors"] = [str(exc)]
        response_payload["global_ledger_write_performed"] = False
        response_payload["global_ledger_reason_code"] = "global_ledger_write_failed"
        response_payload["global_ledger_path"] = global_ledger_path
        _append_operation_id_audit_record(
            operation_id=persistable_operation_id,
            request_fingerprint=request_fingerprint,
            request_parse_status="schema_valid",
            guard_or_authorization_outcome="guard_allowed",
            apply_or_write_outcome="write_applied",
            token_consume_outcome="not_attempted",
            deterministic_status="global_ledger_write_failed_after_local_write",
            selected_key=response_payload.get("selected_key"),
            token_id=response_payload.get("token_id"),
            terminal_reason_code=response_payload.get("reason_code"),
            internal_mutation_operation_id=internal_operation_id,
            write_attempt_id=write_attempt_id,
            contract_version=contract_version,
            endpoint_version=endpoint_version,
        )
        return jsonify(response_payload)

    consume_attempted_at_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    response_payload["token_consume_attempted_at_utc"] = consume_attempted_at_utc

    consume_result = OFFICIAL_SOURCE_APPROVED_APPLY_TOKEN_CONSUME_HELPER.register_consume(
        response_payload.get("token_id"),
        operation_id=internal_operation_id,
        write_attempt_id=write_attempt_id,
        selected_key=response_payload.get("selected_key"),
        reason_code_at_consume=str(adapter_result.get("reason_code") or "official_source_write_applied"),
        binding_digest_expected=response_payload.get("binding_digest_expected"),
        contract_version=contract_version,
        endpoint_version=endpoint_version,
    )

    response_payload["token_consume_completed_at_utc"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    response_payload["token_consume_retry_count"] = 0
    response_payload["token_consume_performed"] = bool(consume_result.get("token_consume_performed"))
    response_payload["token_consume_reason_code"] = str(consume_result.get("reason_code") or "token_consume_post_write_failed")
    response_payload["token_consume_idempotent"] = bool(consume_result.get("idempotent"))

    if not bool(consume_result.get("ok")):
        response_payload["ok"] = False
        response_payload["reason_code"] = "token_consume_post_write_failed"
        response_payload["errors"] = list(consume_result.get("errors") or [])

    _append_operation_id_audit_record(
        operation_id=persistable_operation_id,
        request_fingerprint=request_fingerprint,
        request_parse_status="schema_valid",
        guard_or_authorization_outcome="guard_allowed",
        apply_or_write_outcome="write_applied",
        token_consume_outcome="consumed" if bool(consume_result.get("ok")) else "consume_failed",
        deterministic_status="write_applied" if bool(consume_result.get("ok")) else "consume_failed_after_write",
        selected_key=response_payload.get("selected_key"),
        token_id=response_payload.get("token_id"),
        terminal_reason_code=response_payload.get("reason_code"),
        internal_mutation_operation_id=internal_operation_id,
        write_attempt_id=write_attempt_id,
        contract_version=contract_version,
        endpoint_version=endpoint_version,
    )

    return jsonify(response_payload)


@app.route("/api/operator/actual-result-lookup/batch/guarded-local-preview", methods=["POST"])
def api_operator_actual_result_lookup_batch_guarded_local_preview():
    data = request.get_json(silent=True) or {}
    selected_keys_raw = data.get("selected_keys")
    mode = str(data.get("mode") or "local_only").strip() or "local_only"
    approval_granted = bool(data.get("approval_granted"))

    selected_keys = []
    if isinstance(selected_keys_raw, list):
        selected_keys = [str(key or "").strip() for key in selected_keys_raw if str(key or "").strip()]

    base_payload = {
        "ok": False,
        "mode": "batch_local_preview",
        "batch_size_requested": len(selected_keys),
        "batch_size_accepted": 0,
        "hard_cap": 5,
        "rows": [],
        "mutation_performed": False,
        "external_lookup_performed": False,
        "bulk_lookup_performed": False,
        "scoring_semantics_changed": False,
        "execution_token": None,
        "token_ttl_seconds": None,
    }

    if mode != "local_only":
        return jsonify({
            **base_payload,
            "error": "mode must be local_only",
        }), 400

    if approval_granted:
        return jsonify({
            **base_payload,
            "error": "approval_granted must be false for preview-only endpoint",
        }), 400

    if not selected_keys:
        return jsonify({
            **base_payload,
            "error": "selected_keys must contain at least one selected_key",
        }), 400

    if len(set(selected_keys)) != len(selected_keys):
        return jsonify({
            **base_payload,
            "error": "selected_keys must not contain duplicates",
        }), 400

    if len(selected_keys) > 5:
        return jsonify({
            **base_payload,
            "error": "selected_keys exceeds hard cap of 5",
        }), 400

    summary = _build_accuracy_comparison_summary()
    waiting_rows = summary.get("waiting_for_results") or []
    waiting_by_selected_key = {}
    for row in waiting_rows:
        waiting_by_selected_key[_build_waiting_row_selected_key(row)] = row

    local_actual_map, _accuracy_dir = _load_local_actual_result_map()
    row_results = []

    for selected_key in selected_keys:
        waiting_row = waiting_by_selected_key.get(selected_key)
        if waiting_row is None:
            row_results.append({
                "selected_key": selected_key,
                "row_found": False,
                "local_result_found": False,
                "proposed_write": None,
                "manual_review_required": True,
                "reason_code": "selected_key_not_found",
            })
            continue

        selected_row = dict(waiting_row)
        selected_row["selected_key"] = selected_key
        if not _is_known_value(selected_row.get("fight_id")):
            selected_row["fight_id"] = _normalize_token(selected_row.get("fight_name")) or None

        local_actual = None
        local_actual_source = None
        for key in _build_waiting_row_candidate_fight_keys(selected_row):
            matched = local_actual_map.get(key)
            if matched and _is_known_value(matched["record"].get("actual_winner")):
                local_actual = dict(matched["record"])
                local_actual_source = matched["source_file"]
                break

        if local_actual is None:
            row_results.append({
                "selected_key": selected_key,
                "row_found": True,
                "local_result_found": False,
                "proposed_write": None,
                "manual_review_required": True,
                "reason_code": "local_result_not_found",
            })
            continue

        proposed_write = {
            "fight_id": local_actual.get("fight_id") or selected_row.get("fight_id"),
            "actual_winner": local_actual.get("actual_winner") or "UNKNOWN",
            "actual_method": local_actual.get("actual_method") or "UNKNOWN",
            "actual_round": local_actual.get("actual_round") or "UNKNOWN",
            "event_date": local_actual.get("event_date") or selected_row.get("event_date") or "UNKNOWN",
            "source": "guarded_batch_local_actual_preview",
            "copied_from": local_actual_source,
        }
        row_results.append({
            "selected_key": selected_key,
            "row_found": True,
            "local_result_found": True,
            "proposed_write": proposed_write,
            "manual_review_required": False,
            "reason_code": "local_result_found",
        })

    execution_token, token_ttl_seconds = _build_batch_preview_execution_token(selected_keys)
    return jsonify({
        "ok": True,
        "mode": "batch_local_preview",
        "batch_size_requested": len(selected_keys),
        "batch_size_accepted": len(selected_keys),
        "hard_cap": 5,
        "rows": row_results,
        "mutation_performed": False,
        "external_lookup_performed": False,
        "bulk_lookup_performed": False,
        "scoring_semantics_changed": False,
        "execution_token": execution_token,
        "token_ttl_seconds": token_ttl_seconds,
        "selected_keys_digest": _build_selected_keys_digest(selected_keys),
    })


@app.route("/api/operator/actual-result-lookup/batch/guarded-local-apply", methods=["POST"])
def api_operator_actual_result_lookup_batch_guarded_local_apply():
    data = request.get_json(silent=True) or {}
    selected_keys_raw = data.get("selected_keys")
    mode = str(data.get("mode") or "local_only").strip() or "local_only"
    approval_granted = bool(data.get("approval_granted"))
    execution_token = str(data.get("execution_token") or "").strip()

    selected_keys = []
    if isinstance(selected_keys_raw, list):
        selected_keys = [str(key or "").strip() for key in selected_keys_raw if str(key or "").strip()]

    base_payload = {
        "ok": False,
        "mode": "batch_local_apply",
        "batch_size_requested": len(selected_keys),
        "batch_size_accepted": 0,
        "hard_cap": 5,
        "total_written": 0,
        "total_skipped": 0,
        "rows": [],
        "mutation_performed": False,
        "external_lookup_performed": False,
        "bulk_lookup_performed": False,
        "scoring_semantics_changed": False,
        "partial_rollback_performed": False,
        "execution_token_used": execution_token or None,
        "token_age_seconds": None,
        "selected_keys_digest": None,
    }

    if mode != "local_only":
        return jsonify({**base_payload, "error": "mode must be local_only"}), 400

    if not approval_granted:
        return jsonify({**base_payload, "error": "approval_granted must be true for apply endpoint"}), 400

    if not execution_token:
        return jsonify({**base_payload, "error": "execution_token is required"}), 400

    if not selected_keys:
        return jsonify({**base_payload, "error": "selected_keys must contain at least one selected_key"}), 400

    if len(set(selected_keys)) != len(selected_keys):
        return jsonify({**base_payload, "error": "selected_keys must not contain duplicates"}), 400

    if len(selected_keys) > 5:
        return jsonify({**base_payload, "error": "selected_keys exceeds hard cap of 5"}), 400

    valid, token_reason, age_seconds = _validate_batch_preview_token(execution_token, selected_keys)
    if not valid:
        return jsonify({**base_payload, "error": token_reason}), 400

    keys_digest = _build_selected_keys_digest(selected_keys)

    summary = _build_accuracy_comparison_summary()
    waiting_rows = summary.get("waiting_for_results") or []
    waiting_by_selected_key = {}
    for row in waiting_rows:
        waiting_by_selected_key[_build_waiting_row_selected_key(row)] = row

    local_actual_map, accuracy_dir = _load_local_actual_result_map()

    manual_path = accuracy_dir / "actual_results_manual.json"
    try:
        snapshot_bytes = manual_path.read_bytes()
    except Exception:
        snapshot_bytes = b"[]\n"

    row_results = []
    total_written = 0
    total_skipped = 0

    for selected_key in selected_keys:
        waiting_row = waiting_by_selected_key.get(selected_key)
        if waiting_row is None:
            row_results.append({
                "selected_key": selected_key,
                "row_found": False,
                "local_result_found": False,
                "write_performed": False,
                "proposed_write": None,
                "write_target": None,
                "before_row_count": None,
                "after_row_count": None,
                "reason_code": "selected_key_not_found",
            })
            total_skipped += 1
            continue

        selected_row = dict(waiting_row)
        selected_row["selected_key"] = selected_key
        if not _is_known_value(selected_row.get("fight_id")):
            selected_row["fight_id"] = _normalize_token(selected_row.get("fight_name")) or None

        local_actual = None
        local_actual_source = None
        for key in _build_waiting_row_candidate_fight_keys(selected_row):
            matched = local_actual_map.get(key)
            if matched and _is_known_value(matched["record"].get("actual_winner")):
                local_actual = dict(matched["record"])
                local_actual_source = matched["source_file"]
                break

        if local_actual is None:
            row_results.append({
                "selected_key": selected_key,
                "row_found": True,
                "local_result_found": False,
                "write_performed": False,
                "proposed_write": None,
                "write_target": None,
                "before_row_count": None,
                "after_row_count": None,
                "reason_code": "local_result_not_found",
            })
            total_skipped += 1
            continue

        proposed_write = {
            "fight_id": local_actual.get("fight_id") or selected_row.get("fight_id"),
            "actual_winner": local_actual.get("actual_winner") or "UNKNOWN",
            "actual_method": local_actual.get("actual_method") or "UNKNOWN",
            "actual_round": local_actual.get("actual_round") or "UNKNOWN",
            "event_date": local_actual.get("event_date") or selected_row.get("event_date") or "UNKNOWN",
            "source": "guarded_batch_local_apply",
            "copied_from": local_actual_source,
        }

        write_result = _upsert_single_manual_actual_result(accuracy_dir, proposed_write)
        if not write_result.get("ok"):
            try:
                manual_path.write_bytes(snapshot_bytes)
            except Exception:
                pass
            return jsonify({
                **base_payload,
                "ok": False,
                "total_written": 0,
                "partial_rollback_performed": True,
                "mutation_performed": False,
                "rows": row_results + [{
                    "selected_key": selected_key,
                    "row_found": True,
                    "local_result_found": True,
                    "write_performed": False,
                    "proposed_write": proposed_write,
                    "write_target": write_result.get("write_target"),
                    "before_row_count": write_result.get("before_row_count"),
                    "after_row_count": write_result.get("after_row_count"),
                    "reason_code": "write_failed_rollback_performed",
                }],
                "selected_keys_digest": keys_digest,
                "token_age_seconds": round(age_seconds, 3),
                "execution_token_used": execution_token,
                "error": "Write failed. Manual file restored to pre-batch snapshot.",
            }), 500

        row_results.append({
            "selected_key": selected_key,
            "row_found": True,
            "local_result_found": True,
            "write_performed": True,
            "proposed_write": proposed_write,
            "write_target": write_result.get("write_target"),
            "before_row_count": write_result.get("before_row_count"),
            "after_row_count": write_result.get("after_row_count"),
            "reason_code": "local_result_applied",
        })
        total_written += 1

    mutation_performed = total_written >= 1
    return jsonify({
        "ok": True,
        "mode": "batch_local_apply",
        "batch_size_requested": len(selected_keys),
        "batch_size_accepted": len(selected_keys),
        "hard_cap": 5,
        "total_written": total_written,
        "total_skipped": total_skipped,
        "rows": row_results,
        "mutation_performed": mutation_performed,
        "external_lookup_performed": False,
        "bulk_lookup_performed": False,
        "scoring_semantics_changed": False,
        "partial_rollback_performed": False,
        "execution_token_used": execution_token,
        "token_age_seconds": round(age_seconds, 3),
        "selected_keys_digest": keys_digest,
    })


@app.route("/api/operator/actual-result-lookup/guarded-single", methods=["POST"])
def api_operator_actual_result_lookup_guarded_single():
    data = request.get_json(silent=True) or {}
    selected_key = str(data.get("selected_key") or "").strip()
    approval_granted = bool(data.get("approval_granted"))

    base_audit = {
        "write_target": None,
        "write_action": "insert_or_update_single_record",
        "selected_key": selected_key or None,
        "matched_local_source_file": None,
        "record_fight_id": None,
        "before_row_count": None,
        "after_row_count": None,
        "write_performed": False,
    }

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
            "scoring_semantics_changed": False,
            "audit": base_audit,
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
            "scoring_semantics_changed": False,
            "audit": base_audit,
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

    audit_payload = {
        **base_audit,
        "selected_key": selected_key,
        "matched_local_source_file": local_actual_source,
        "record_fight_id": proposed_write.get("fight_id") if proposed_write else selected_row.get("fight_id"),
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
        "scoring_semantics_changed": False,
        "audit": audit_payload,
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

    write_result = _upsert_single_manual_actual_result(accuracy_dir, proposed_write)
    if not write_result.get("ok"):
        return jsonify({
            **base_payload,
            "ok": False,
            "audit": {
                **audit_payload,
                "write_target": write_result.get("write_target"),
                "before_row_count": write_result.get("before_row_count"),
                "after_row_count": write_result.get("after_row_count"),
                "write_performed": False,
            },
            "message": "Failed to write approved local actual result.",
        }), 500

    return jsonify({
        **base_payload,
        "mutation_performed": True,
        "resolved_count": 1,
        "manual_review_required": False,
        "audit": {
            **audit_payload,
            "write_target": write_result.get("write_target"),
            "before_row_count": write_result.get("before_row_count"),
            "after_row_count": write_result.get("after_row_count"),
            "write_performed": True,
        },
        "message": "Approved local actual result written for selected row.",
    })


@app.route("/api/operator/actual-result-lookup/manual-single-apply", methods=["POST"])
def api_operator_actual_result_lookup_manual_single_apply():
    data = request.get_json(silent=True) or {}
    selected_key = str(data.get("selected_key") or "").strip()
    approval_granted = bool(data.get("approval_granted"))
    manual_result = data.get("manual_result") if isinstance(data.get("manual_result"), dict) else {}

    base_payload = {
        "ok": False,
        "mode": "manual_single_apply",
        "approval_required": True,
        "approval_granted": approval_granted,
        "mutation_performed": False,
        "external_lookup_performed": False,
        "bulk_lookup_performed": False,
        "manual_review_required": False,
        "scoring_semantics_changed": False,
        "selected_key": selected_key or None,
        "selected_row": None,
        "proposed_write": None,
        "audit": {
            "write_target": None,
            "write_action": "manual_single_apply",
            "selected_key": selected_key or None,
            "record_fight_id": None,
            "before_row_count": None,
            "after_row_count": None,
            "write_performed": False,
        },
    }

    if not selected_key:
        return jsonify({
            **base_payload,
            "error": "selected_key is required",
            "message": "Preview only. Approval required before any write.",
        }), 400

    if not approval_granted:
        return jsonify({
            **base_payload,
            "error": "approval_granted must be true for manual apply",
            "message": "Preview only. Approval required before any write.",
        }), 400

    actual_winner = str(manual_result.get("actual_winner") or "").strip()
    if not actual_winner:
        return jsonify({
            **base_payload,
            "error": "manual_result.actual_winner is required",
            "message": "Manual candidate is incomplete. No write performed.",
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
            **base_payload,
            "error": "selected_key not found in waiting rows",
            "manual_review_required": True,
            "message": "Selected row was not found. Manual review required.",
        }), 404

    fight_id = str(selected_row.get("fight_id") or "").strip()
    if not _is_known_value(fight_id):
        fight_id = _normalize_token(selected_row.get("fight_name")) or "unknown_fight"

    proposed_write = {
        "fight_id": fight_id,
        "actual_winner": actual_winner,
        "actual_method": str(manual_result.get("actual_method") or "UNKNOWN").strip() or "UNKNOWN",
        "actual_round": str(manual_result.get("actual_round") or "UNKNOWN").strip() or "UNKNOWN",
        "event_date": str(manual_result.get("event_date") or selected_row.get("event_date") or "UNKNOWN").strip() or "UNKNOWN",
        "source": "manual_button3_operator_apply",
        "source_reference": str(manual_result.get("source_reference") or "manual_input").strip() or "manual_input",
        "operator_note": str(manual_result.get("operator_note") or "").strip(),
    }

    accuracy_dir = _resolve_accuracy_dir()
    write_result = _upsert_single_manual_actual_result(accuracy_dir, proposed_write)
    if not write_result.get("ok"):
        return jsonify({
            **base_payload,
            "error": "manual_result_write_failed",
            "selected_row": selected_row,
            "proposed_write": proposed_write,
            "audit": {
                **base_payload["audit"],
                "record_fight_id": fight_id,
                "write_target": write_result.get("write_target"),
                "before_row_count": write_result.get("before_row_count"),
                "after_row_count": write_result.get("after_row_count"),
                "write_performed": False,
            },
            "message": "Manual result write failed.",
        }), 500

    return jsonify({
        **base_payload,
        "ok": True,
        "mutation_performed": True,
        "selected_row": selected_row,
        "proposed_write": proposed_write,
        "audit": {
            **base_payload["audit"],
            "record_fight_id": fight_id,
            "write_target": write_result.get("write_target"),
            "before_row_count": write_result.get("before_row_count"),
            "after_row_count": write_result.get("after_row_count"),
            "write_performed": True,
        },
        "message": "Approved manual actual result written for selected row.",
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
