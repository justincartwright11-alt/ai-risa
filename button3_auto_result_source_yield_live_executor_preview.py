"""
button3_auto_result_source_yield_live_executor_preview.py

Read-only live executor preview for Button 3.
Executes source search tasks and classifies results into 5 states.

GOVERNANCE: preview_only=True, no mutations, no writes, no learning, no calibration.
"""

from button3_improved_source_yield_engine import (
    RESULT_SUMMARY_STATES,
    build_source_search_tasks,
    classify_result_state,
    _score_candidate_match,
)

EXECUTOR_VERSION = "button3-auto-result-source-yield-live-executor-preview-v1"

_EMPTY_TELEMETRY = {
    "preview_only": True,
    "mutation_performed": False,
    "durable_write_performed": False,
    "learning_apply_performed": False,
    "calibration_write_performed": False,
    "queue_write_performed": False,
    "auto_apply_performed": False,
}


# ─── Single Task Execution (Preview Only) ─────────────────────────────────────

def execute_source_search_task_preview(task, provider=None):
    """
    Execute a single source search task against available candidates.

    Args:
        task: dict from build_source_search_tasks()
        provider: optional object with search_candidates(query, patterns) method

    Returns:
        list of candidate dicts (may be empty)
    """
    if provider is None:
        return []
    try:
        raw = provider.search_candidates(
            query=task.get("query", ""),
            source_patterns=task.get("source_patterns", []),
        )
        if not isinstance(raw, list):
            return []
        # Normalize candidate structure
        return [_normalize_candidate(c) for c in raw if isinstance(c, dict)]
    except Exception:
        return []


def _normalize_candidate(raw):
    """Normalize a raw provider candidate into internal structure."""
    return {
        "fighter_a": raw.get("fighter_a") or raw.get("fighter_1") or "",
        "fighter_b": raw.get("fighter_b") or raw.get("fighter_2") or "",
        "event_name": raw.get("event_name") or raw.get("event") or "",
        "event_date": raw.get("event_date") or raw.get("date") or "",
        "promotion": raw.get("promotion") or raw.get("org") or "",
        "declared_winner": raw.get("declared_winner") or raw.get("winner") or "",
        "source_url": raw.get("source_url") or raw.get("url") or "",
        "tier": raw.get("tier") or "",
    }


# ─── All Tasks for One Row ─────────────────────────────────────────────────────

def execute_source_search_tasks(row, provider=None):
    """
    Execute all source search tasks for a single waiting row.

    Args:
        row: waiting row dict
        provider: optional search provider

    Returns:
        list of all candidates found across all tasks
    """
    tasks = build_source_search_tasks(row)
    all_candidates = []
    for task in tasks:
        candidates = execute_source_search_task_preview(task, provider=provider)
        all_candidates.extend(candidates)
    return all_candidates


# ─── Main Executor — All Waiting Rows ─────────────────────────────────────────

def execute_live_result_discovery_for_all_waiting_rows(waiting_rows, provider=None):
    """
    Main executor: process all waiting rows and classify into 5 states.

    Args:
        waiting_rows: list of row dicts (each needs fight_name, event_name, etc.)
        provider: optional search provider with search_candidates() method

    Returns:
        dict with summary, row_states, row_details, telemetry
    """
    summary = {state: 0 for state in RESULT_SUMMARY_STATES}
    summary["total_rows"] = len(waiting_rows)

    row_states = {}
    row_details = {}

    for row in waiting_rows:
        key = row.get("selected_key") or row.get("fight_name") or str(id(row))
        candidates = execute_source_search_tasks(row, provider=provider)
        state = classify_result_state(row, candidates)
        row_states[key] = state
        summary[state] = summary.get(state, 0) + 1
        row_details[key] = {
            "state": state,
            "candidates_found": len(candidates),
            "fight_name": row.get("fight_name", ""),
            "event_name": row.get("event_name", ""),
        }

    return {
        "executor_version": EXECUTOR_VERSION,
        "summary": summary,
        "row_states": row_states,
        "row_details": row_details,
        "telemetry": dict(_EMPTY_TELEMETRY),
    }


# ─── API Response Builder ──────────────────────────────────────────────────────

def build_readonly_executor_preview_response(waiting_rows, provider=None, include_diagnostics=False):
    """
    Build the structured API response for the executor preview endpoint.

    Args:
        waiting_rows: list of waiting row dicts
        provider: optional search provider
        include_diagnostics: if True, include row_details in response

    Returns:
        dict suitable for JSON response
    """
    result = execute_live_result_discovery_for_all_waiting_rows(waiting_rows, provider=provider)

    response = {
        "ok": True,
        "preview_only": True,
        "executor_version": result["executor_version"],
        "summary": result["summary"],
        "row_states": result["row_states"],
        "telemetry": result["telemetry"],
    }

    if include_diagnostics:
        response["row_details"] = result["row_details"]

    return response
