"""Read-only runtime context loader for three-button local AI preview flows.

Builds sanitized context packs from existing local runtime state without mutation.
This module never performs queue/database writes, exports, applies, learning,
calibration, or live web execution.
"""

from __future__ import annotations

import csv
import json
import os
from typing import Any, Dict, List

from operator_dashboard.local_ai_orchestrator_input_context_pack import (
    ALLOWED_SOURCE_BUTTONS,
    LocalAIInputContextPack,
    build_button1_find_fights_context,
    build_button2_generate_pdfs_context,
    build_button3_find_results_context,
)


def _default_workspace_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _safe_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}


def _safe_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return list(value)
    return []


def _safe_list_of_dict(value: Any) -> List[Dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(v) for v in value if isinstance(v, dict)]


def _safe_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    return ""


def _read_text_file(path: str) -> str:
    try:
        if not os.path.exists(path):
            return ""
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return ""


def _read_json_file(path: str) -> Dict[str, Any]:
    try:
        if not os.path.exists(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _read_csv_rows(path: str, max_rows: int = 250) -> List[Dict[str, Any]]:
    try:
        if not os.path.exists(path):
            return []
        rows: List[Dict[str, Any]] = []
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if isinstance(row, dict):
                    rows.append(dict(row))
                if len(rows) >= max_rows:
                    break
        return rows
    except Exception:
        return []


def _normalize_runtime_state(runtime_state: Dict[str, Any]) -> Dict[str, Any]:
    state = _safe_dict(runtime_state)
    return {
        "manual_intake_text": _safe_text(state.get("manual_intake_text", "")),
        "discovered_candidate_rows": _safe_list_of_dict(state.get("discovered_candidate_rows", [])),
        "approved_source_preview_rows": _safe_list(state.get("approved_source_preview_rows", [])),
        "event_hint": _safe_text(state.get("event_hint", "")),
        "promotion_hint": _safe_text(state.get("promotion_hint", "")),
        "date_window": _safe_dict(state.get("date_window", {})),
        "local_candidate_rows": _safe_list_of_dict(state.get("local_candidate_rows", [])),
        "selected_fights": _safe_list_of_dict(state.get("selected_fights", [])),
        "saved_fight_queue_refs": _safe_list(state.get("saved_fight_queue_refs", [])),
        "report_status_refs": _safe_list(state.get("report_status_refs", [])),
        "analysis_ready_refs": _safe_list(state.get("analysis_ready_refs", [])),
        "customer_ready_refs": _safe_list(state.get("customer_ready_refs", [])),
        "selected_fight_refs": _safe_list(state.get("selected_fight_refs", [])),
        "waiting_result_rows": _safe_list_of_dict(state.get("waiting_result_rows", [])),
        "selected_result_keys": _safe_list(state.get("selected_result_keys", [])),
        "result_source_refs": _safe_list(state.get("result_source_refs", [])),
        "report_refs": _safe_list(state.get("report_refs", [])),
        "comparison_refs": _safe_list(state.get("comparison_refs", [])),
        "source_yield_preview_rows": _safe_list_of_dict(state.get("source_yield_preview_rows", [])),
    }


def load_readonly_runtime_state(
    runtime_state_override: Dict[str, Any] | None = None,
    workspace_root: str | None = None,
) -> Dict[str, Any]:
    """Load read-only runtime state with safe defaults and optional override.

    If a key is present in runtime_state_override, it takes precedence.
    Missing keys are populated from local files when safely available.
    """
    root = workspace_root or _default_workspace_root()
    override = _safe_dict(runtime_state_override)

    status_text = _read_text_file(os.path.join(root, "status.txt"))
    event_rows = _read_csv_rows(os.path.join(root, "event_coverage_queue.csv"))
    queue_rows = _read_csv_rows(os.path.join(root, "fighter_intake_unresolved_queue.csv"))
    bout_rows = _read_csv_rows(os.path.join(root, "one_samurai_1_bouts.csv"))
    ledger = _read_json_file(os.path.join(root, "ops", "accuracy", "accuracy_ledger.json"))

    state = {
        "manual_intake_text": status_text,
        "discovered_candidate_rows": event_rows,
        "approved_source_preview_rows": [],
        "event_hint": "",
        "promotion_hint": "",
        "date_window": {},
        "local_candidate_rows": queue_rows,
        "selected_fights": [],
        "saved_fight_queue_refs": [],
        "report_status_refs": [],
        "analysis_ready_refs": [],
        "customer_ready_refs": [],
        "selected_fight_refs": [
            row.get("fight_key") or row.get("fight_name")
            for row in bout_rows
            if isinstance(row, dict) and (row.get("fight_key") or row.get("fight_name"))
        ],
        "waiting_result_rows": _safe_list_of_dict(ledger.get("waiting_for_results", [])),
        "selected_result_keys": [],
        "result_source_refs": [],
        "report_refs": [],
        "comparison_refs": [],
        "source_yield_preview_rows": _safe_list_of_dict(ledger.get("waiting_for_results", [])),
    }

    state.update(override)
    return _normalize_runtime_state(state)


def build_button1_runtime_context(
    runtime_state_override: Dict[str, Any] | None = None,
    workspace_root: str | None = None,
) -> LocalAIInputContextPack:
    state = load_readonly_runtime_state(runtime_state_override, workspace_root=workspace_root)
    candidate_rows = _safe_list_of_dict(state.get("discovered_candidate_rows", [])) + _safe_list_of_dict(
        state.get("local_candidate_rows", [])
    )

    raw_input = {
        "manual_text": state.get("manual_intake_text", ""),
        "approved_source_refs": _safe_list(state.get("approved_source_preview_rows", [])),
        "event_hint": state.get("event_hint", ""),
        "promotion_hint": state.get("promotion_hint", ""),
        "date_window": _safe_dict(state.get("date_window", {})),
        "candidate_rows": candidate_rows,
    }
    return build_button1_find_fights_context(raw_input)


def build_button2_runtime_context(
    runtime_state_override: Dict[str, Any] | None = None,
    workspace_root: str | None = None,
) -> LocalAIInputContextPack:
    state = load_readonly_runtime_state(runtime_state_override, workspace_root=workspace_root)

    selected_fights = _safe_list_of_dict(state.get("selected_fights", []))
    if not selected_fights:
        selected_refs = _safe_list(state.get("selected_fight_refs", []))
        selected_fights = [{"fight_ref": str(ref)} for ref in selected_refs if isinstance(ref, str) and ref.strip()]

    raw_input = {
        "selected_fights": selected_fights,
        "queued_fight_refs": _safe_list(state.get("saved_fight_queue_refs", [])),
        "report_status_refs": _safe_list(state.get("report_status_refs", [])),
        "analysis_ready_refs": _safe_list(state.get("analysis_ready_refs", [])),
        "customer_ready_refs": _safe_list(state.get("customer_ready_refs", [])),
    }
    return build_button2_generate_pdfs_context(raw_input)


def build_button3_runtime_context(
    runtime_state_override: Dict[str, Any] | None = None,
    workspace_root: str | None = None,
) -> LocalAIInputContextPack:
    state = load_readonly_runtime_state(runtime_state_override, workspace_root=workspace_root)

    waiting_rows = _safe_list_of_dict(state.get("waiting_result_rows", []))
    if not waiting_rows:
        waiting_rows = _safe_list_of_dict(state.get("source_yield_preview_rows", []))

    raw_input = {
        "waiting_rows": waiting_rows,
        "selected_keys": _safe_list(state.get("selected_result_keys", [])),
        "result_source_refs": _safe_list(state.get("result_source_refs", [])),
        "report_refs": _safe_list(state.get("report_refs", [])),
        "comparison_refs": _safe_list(state.get("comparison_refs", [])),
    }
    return build_button3_find_results_context(raw_input)


def build_runtime_context_pack(
    source_button: str,
    runtime_state_override: Dict[str, Any] | None = None,
    workspace_root: str | None = None,
) -> LocalAIInputContextPack:
    if source_button not in ALLOWED_SOURCE_BUTTONS:
        raise ValueError(f"invalid source_button: {source_button}")

    if source_button == "button1_find_fights":
        return build_button1_runtime_context(runtime_state_override, workspace_root=workspace_root)
    if source_button == "button2_generate_pdfs":
        return build_button2_runtime_context(runtime_state_override, workspace_root=workspace_root)
    return build_button3_runtime_context(runtime_state_override, workspace_root=workspace_root)


def build_runtime_context_payload(
    source_button: str,
    runtime_state_override: Dict[str, Any] | None = None,
    workspace_root: str | None = None,
) -> Dict[str, Any]:
    """Return route-ready context_pack payload for workflow-preview API."""
    pack = build_runtime_context_pack(
        source_button,
        runtime_state_override=runtime_state_override,
        workspace_root=workspace_root,
    )
    return _safe_dict(pack.input_ref.get("payload", {}))


__all__ = [
    "build_button1_runtime_context",
    "build_button2_runtime_context",
    "build_button3_runtime_context",
    "build_runtime_context_pack",
    "build_runtime_context_payload",
    "load_readonly_runtime_state",
]
