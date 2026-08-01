"""
button2_queue_loader_readonly_v1.py

Button 2 queue loader: load and normalize approved fight queue rows from canonical source.

This module provides read-only access to the operator-approved fight queue for Button 2
PDF generation. Queue rows are loaded from the canonical source (JSON file), never from
browser localStorage or preview objects.

Requirements:
- Load rows from canonical source only (ops/prf_queue/button2_approved_fight_queue.json)
- Normalize rows to standard schema
- Support single/multiple/all-ready/event-card selection
- Never use stale preview objects or browser-persisted data
- Server-side resolution of matchup_ids from canonical queue
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any


_CANONICAL_QUEUE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "ops",
    "prf_queue",
    "button2_approved_fight_queue.json"
)
_FIXTURES_ROOT = Path(__file__).resolve().parent / "fixtures"
_LAST_LOAD_METADATA: Dict[str, Any] = {
    "mode": "canonical_queue",
    "source_path": _CANONICAL_QUEUE_PATH,
    "fixture_id": None,
    "row_count": 0,
    "blocked_reason": None,
    "read_only": True,
}


def get_button2_queue_loader_metadata() -> Dict[str, Any]:
    """Return bounded metadata for the most recent read-only queue load."""
    return dict(_LAST_LOAD_METADATA)


def _set_load_metadata(**values: Any) -> None:
    _LAST_LOAD_METADATA.clear()
    _LAST_LOAD_METADATA.update(values)


def _resolve_queue_source() -> Optional[Path]:
    """Resolve the canonical queue or a governed local fixture override."""
    if os.environ.get("AI_RISA_LOCAL_FIXTURE_MODE") != "1":
        return Path(_CANONICAL_QUEUE_PATH)

    raw_path = os.environ.get("AI_RISA_BUTTON2_QUEUE_PATH", "").strip()
    if not raw_path:
        _set_load_metadata(
            mode="governed_local_fixture",
            source_path=None,
            fixture_id=None,
            row_count=0,
            blocked_reason="local_fixture_path_required",
            read_only=True,
        )
        return None

    resolved_path = Path(raw_path).expanduser().resolve()
    fixtures_root = _FIXTURES_ROOT.resolve()
    try:
        resolved_path.relative_to(fixtures_root)
    except ValueError:
        reason = "local_fixture_path_outside_fixtures"
    else:
        reason = None
    if reason is None and resolved_path.suffix.lower() != ".json":
        reason = "local_fixture_path_must_be_json"
    if reason is None and not resolved_path.is_file():
        reason = "local_fixture_path_not_found"
    if reason:
        _set_load_metadata(
            mode="governed_local_fixture",
            source_path=None,
            fixture_id=None,
            row_count=0,
            blocked_reason=reason,
            read_only=True,
        )
        return None
    return resolved_path


def _fixture_is_governed(data: Dict[str, Any]) -> bool:
    if data.get("fixture_only") is not True:
        return False
    if data.get("customer_release_authorized") is True:
        return False
    for authority_key in ("learning_authorized", "calibration_write_authorized", "queue_write_authorized"):
        if data.get(authority_key) is True:
            return False
    queue_data = data.get("queue", data.get("rows", []))
    if not isinstance(queue_data, list):
        return False
    for row in queue_data:
        if not isinstance(row, dict):
            continue
        if row.get("customer_release_authorized") is True:
            return False
        for authority_key in ("learning_authorized", "calibration_write_authorized", "queue_write_authorized"):
            if row.get(authority_key) is True:
                return False
    return True


def _fixture_internal_preview_is_valid(row: Dict[str, Any]) -> bool:
    prediction = row.get("structured_prediction")
    return (
        row.get("internal_preview_selectable") is True
        and row.get("internal_test_only") is True
        and row.get("read_only") is True
        and row.get("customer_ready_possible") is False
        and row.get("customer_release_authorized") is False
        and isinstance(row.get("report_id"), str)
        and bool(row["report_id"].strip())
        and isinstance(row.get("report_version"), str)
        and bool(row["report_version"].strip())
        and isinstance(row.get("prediction_schema_version"), str)
        and bool(row["prediction_schema_version"].strip())
        and isinstance(prediction, dict)
        and prediction.get("contract_version") == row.get("prediction_schema_version")
        and bool(str(row.get("prediction_provenance", "")).strip())
        and bool(str(row.get("source_provenance", "")).strip())
        and row.get("queue_write_performed") is False
        and row.get("pdf_generation_performed") is False
        and row.get("permanent_mutation_performed") is False
    )


def _normalize_queue_row(row: Dict[str, Any], index: int, *, local_fixture_mode: bool = False) -> Optional[Dict[str, Any]]:
    """Normalize a queue row to standard schema. Return None if invalid."""
    if not isinstance(row, dict):
        return None

    # Extract matchup ID (required)
    matchup_id = row.get("matchup_id") or row.get("candidate_id") or row.get("fight_id")
    if not isinstance(matchup_id, str) or not matchup_id.strip():
        return None
    matchup_id = matchup_id.strip()

    # Extract fighters
    fighter_a = str(row.get("fighter_a", "")).strip()
    fighter_b = str(row.get("fighter_b", "")).strip()
    if not fighter_a or not fighter_b:
        return None
    if local_fixture_mode and not _fixture_internal_preview_is_valid(row):
        return None

    # Extract event info
    event_name = str(row.get("event_name") or row.get("event") or row.get("event_title") or "").strip()
    event_id = str(row.get("event_id") or "").strip()
    if not event_id and event_name:
        event_id = re.sub(r"[^a-z0-9]+", "_", event_name.strip().lower()).strip("_")

    event_date = str(row.get("event_date", "")).strip()
    promotion = str(row.get("promotion", "")).strip()

    # Extract source
    source_url = str(
        row.get("source_url")
        or row.get("canonical_source_url")
        or row.get("event_url")
        or row.get("provenance_url")
        or row.get("official_url")
        or row.get("url")
        or ""
    ).strip()
    source_type = str(row.get("source_type", "official")).strip()

    # Button 2 readiness
    report_ready_status = str(
        row.get("report_ready_status")
        or row.get("button2_readiness_status")
        or row.get("readiness")
        or row.get("button2_readiness")
        or ""
    ).strip()
    if not report_ready_status:
        report_ready_status = "ready_for_button2_generation"

    # Optional fields
    weight_class = str(row.get("weight_class", "")).strip()
    bout_order = row.get("bout_order")
    if isinstance(bout_order, int):
        bout_order = bout_order
    else:
        bout_order = None

    provenance_status = str(row.get("provenance_status", "source_backed")).strip()
    customer_ready_possible = bool(row.get("customer_ready_possible", True))
    blocked_reason = str(row.get("blocked_reason", "")).strip()

    return {
        "matchup_id": matchup_id,
        "event_id": event_id,
        "event_name": event_name,
        "event_date": event_date,
        "promotion": promotion,
        "fighter_a": fighter_a,
        "fighter_b": fighter_b,
        "weight_class": weight_class,
        "bout_order": bout_order,
        "source_url": source_url,
        "source_type": source_type,
        "provenance_status": provenance_status,
        "button2_readiness_status": report_ready_status,
        "customer_ready_possible": customer_ready_possible,
        "customer_release_authorized": row.get("customer_release_authorized") is True,
        "fixture_only": row.get("fixture_only") is True,
        "read_only": True,
        "blocked_reason": blocked_reason,
        "report_ready_status": report_ready_status,
        "queue_index": index,
        "internal_preview_selectable": row.get("internal_preview_selectable") is True,
        "internal_test_only": row.get("internal_test_only") is True,
        "report_id": str(row.get("report_id", "")).strip(),
        "report_version": str(row.get("report_version", "")).strip(),
        "prediction_schema_version": str(row.get("prediction_schema_version", "")).strip(),
        "structured_prediction": row.get("structured_prediction") if isinstance(row.get("structured_prediction"), dict) else {},
        "prediction_provenance": str(row.get("prediction_provenance", "")).strip(),
        "source_provenance": str(row.get("source_provenance", "")).strip(),
        "queue_write_performed": row.get("queue_write_performed") is True,
        "pdf_generation_performed": row.get("pdf_generation_performed") is True,
        "permanent_mutation_performed": row.get("permanent_mutation_performed") is True,
    }


def load_button2_queue_readonly() -> List[Dict[str, Any]]:
    """
    Load approved fight queue from canonical source.

    Returns list of normalized rows, or empty list if source not found/invalid.
    """
    rows = []
    source_path = _resolve_queue_source()
    local_fixture_mode = os.environ.get("AI_RISA_LOCAL_FIXTURE_MODE") == "1"
    if source_path is None:
        return rows

    try:
        with open(source_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError):
        _set_load_metadata(
            mode="governed_local_fixture" if local_fixture_mode else "canonical_queue",
            source_path=str(source_path) if not local_fixture_mode else None,
            fixture_id=None,
            row_count=0,
            blocked_reason="queue_source_invalid",
            read_only=True,
        )
        return rows

    if not isinstance(data, dict):
        return rows

    if local_fixture_mode and not _fixture_is_governed(data):
        _set_load_metadata(
            mode="governed_local_fixture",
            source_path=None,
            fixture_id=None,
            row_count=0,
            blocked_reason="fixture_governance_metadata_invalid",
            read_only=True,
        )
        return rows

    queue_data = data.get("queue", data.get("rows", []))
    if not isinstance(queue_data, list):
        return rows

    seen_ids = set()
    for idx, row in enumerate(queue_data):
        normalized = _normalize_queue_row(row, idx, local_fixture_mode=local_fixture_mode)
        if not normalized:
            continue
        matchup_id = normalized.get("matchup_id")
        if matchup_id in seen_ids:
            continue
        seen_ids.add(matchup_id)
        rows.append(normalized)

    _set_load_metadata(
        mode="governed_local_fixture" if local_fixture_mode else "canonical_queue",
        source_path=str(source_path),
        fixture_id=data.get("fixture_id") if local_fixture_mode else None,
        row_count=len(rows),
        blocked_reason=None,
        read_only=True,
    )

    return rows


def get_queue_ready_rows() -> List[Dict[str, Any]]:
    """
    Get all ready rows from canonical queue.

    A row is "ready" if button2_readiness_status indicates it can be used for generation.
    """
    all_rows = load_button2_queue_readonly()
    ready_statuses = {
        "ready",
        "ready_for_button2_generation",
        "ready_for_button2_preview",
        "ready_for_button2",
        "customer_ready",
        "customer_ready_verified",
    }
    ready_rows = []
    for row in all_rows:
        status = str(row.get("button2_readiness_status") or row.get("report_ready_status") or "").strip().lower()
        if status not in ready_statuses:
            continue
        if str(row.get("blocked_reason") or "").strip():
            continue
        if not bool(row.get("customer_ready_possible", True)):
            continue
        ready_rows.append(row)
    return ready_rows


def resolve_matchup_id_from_queue(
    matchup_id: str,
    queue_rows: Optional[List[Dict[str, Any]]] = None
) -> Tuple[Optional[Dict[str, Any]], Optional[str], int]:
    """
    Resolve a matchup_id to a queue row using canonical source.

    Returns:
      (row_dict, error_reason, status_code)

    On success: (row, None, 200)
    On error: (None, reason, error_code)
    """
    if not isinstance(matchup_id, str) or not matchup_id.strip():
        return None, "invalid_matchup_id", 400

    matchup_id = matchup_id.strip()

    # If queue_rows provided, use those (server-side approved list)
    # Otherwise load from canonical source
    if queue_rows is None or not isinstance(queue_rows, list):
        queue_rows = load_button2_queue_readonly()

    if not queue_rows:
        return None, "queue_empty", 404

    matching = [r for r in queue_rows if r.get("matchup_id") == matchup_id]

    if not matching:
        return None, "matchup_id_not_found", 404

    if len(matching) > 1:
        return None, "matchup_id_duplicated", 409

    row = matching[0]

    return row, None, 200


def get_rows_for_event(
    event_name: str,
    queue_rows: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """
    Get all ready rows for a specific event.
    """
    if not isinstance(event_name, str) or not event_name.strip():
        return []

    event_name = event_name.strip()

    if queue_rows is None:
        queue_rows = load_button2_queue_readonly()

    event_name_lower = event_name.lower()
    event_rows = []
    for row in queue_rows:
        row_event_name = str(row.get("event_name") or "").strip()
        row_event_id = str(row.get("event_id") or "").strip()
        if row_event_name == event_name or row_event_name.lower() == event_name_lower or row_event_id.lower() == event_name_lower:
            event_rows.append(row)

    return event_rows
