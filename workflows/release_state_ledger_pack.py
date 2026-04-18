"""
release_state_ledger_pack.py

Consumes execution_outcome_pack output and emits a deterministic event-level release ledger bundle.
"""
from typing import Dict, Any, List

def release_state_ledger_pack(execution_outcome_pack_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a release state ledger bundle from execution_outcome_pack output.
    Args:
        execution_outcome_pack_result: Output from execution_outcome_pack
    Returns:
        Dict with keys:
            - event_name
            - release_state_ledger_status
            - ledger_entries
            - blocked_ledger_entries
            - ready_bout_indices
            - blocked_bout_indices
            - blocker_summary
            - release_state_ledger_summary
    """
    event_name = execution_outcome_pack_result.get("event_name")
    completed_actions = execution_outcome_pack_result.get("completed_actions", [])
    blocked_actions = execution_outcome_pack_result.get("blocked_actions", [])
    ledger_entries = []
    blocked_ledger_entries = []
    ready_bout_indices = []
    blocked_bout_indices = []
    blocker_summary = []

    for action in completed_actions:
        ledger_entries.append({
            "event_name": event_name,
            "bout_index": action.get("bout_index"),
            "ledger_status": "ready",
            "delivery_key": action.get("delivery_key"),
            "publication_label": action.get("publication_label"),
            "publication_order": action.get("publication_order"),
            "outcome_status": action.get("outcome_status"),
            "action_sequence": action.get("action_sequence"),
            "session_snapshot": action.get("session_snapshot"),
            "outcome_snapshot": action.get("session_snapshot"),
        })
        ready_bout_indices.append(action.get("bout_index"))

    for action in blocked_actions:
        blocked_ledger_entries.append({
            "event_name": event_name,
            "bout_index": action.get("bout_index"),
            "ledger_status": "blocked",
            "blocker_reason": action.get("blocker_reason"),
            "outcome_snapshot": action.get("session_snapshot"),
        })
        blocked_bout_indices.append(action.get("bout_index"))
        blocker_summary.append({
            "bout_index": action.get("bout_index"),
            "reason": action.get("blocker_reason"),
        })

    if ledger_entries and not blocked_ledger_entries:
        release_state_ledger_status = "ready"
    elif ledger_entries and blocked_ledger_entries:
        release_state_ledger_status = "partial"
    else:
        release_state_ledger_status = "blocked"

    release_state_ledger_summary = {
        "ledger_count": len(ledger_entries),
        "blocked_count": len(blocked_ledger_entries),
        "total": len(ledger_entries) + len(blocked_ledger_entries),
    }

    return {
        "event_name": event_name,
        "release_state_ledger_status": release_state_ledger_status,
        "ledger_entries": ledger_entries,
        "blocked_ledger_entries": blocked_ledger_entries,
        "ready_bout_indices": ready_bout_indices,
        "blocked_bout_indices": blocked_bout_indices,
        "blocker_summary": blocker_summary,
        "release_state_ledger_summary": release_state_ledger_summary,
    }
