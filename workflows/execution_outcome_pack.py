"""
execution_outcome_pack.py

Consumes operator_execution_session_pack output and emits a deterministic execution outcome bundle.
"""
from typing import Dict, Any, List

def execution_outcome_pack(operator_execution_session_pack_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build an execution outcome bundle from operator_execution_session_pack output.
    Args:
        operator_execution_session_pack_result: Output from operator_execution_session_pack
    Returns:
        Dict with keys:
            - event_name
            - execution_outcome_status
            - completed_actions
            - blocked_actions
            - ready_bout_indices
            - blocked_bout_indices
            - blocker_summary
            - execution_outcome_summary
    """
    event_name = operator_execution_session_pack_result.get("event_name")
    ready_session = operator_execution_session_pack_result.get("ready_session_actions", [])
    blocked_session = operator_execution_session_pack_result.get("blocked_session_actions", [])
    completed_actions = []
    blocked_actions = []
    ready_bout_indices = []
    blocked_bout_indices = []
    blocker_summary = []

    for action in ready_session:
        completed_actions.append({
            "event_name": event_name,
            "bout_index": action.get("bout_index"),
            "outcome_status": "completed",
            "delivery_key": action.get("delivery_key"),
            "publication_label": action.get("publication_label"),
            "publication_order": action.get("publication_order"),
            "action_sequence": action.get("action_sequence"),
            "preflight_checks": action.get("preflight_checks"),
            "session_snapshot": action.get("runbook_snapshot"),
        })
        ready_bout_indices.append(action.get("bout_index"))

    for action in blocked_session:
        blocked_actions.append({
            "event_name": event_name,
            "bout_index": action.get("bout_index"),
            "outcome_status": "blocked",
            "blocker_reason": action.get("blocker_reason"),
            "session_snapshot": action.get("runbook_snapshot"),
        })
        blocked_bout_indices.append(action.get("bout_index"))
        blocker_summary.append({
            "bout_index": action.get("bout_index"),
            "reason": action.get("blocker_reason"),
        })

    if completed_actions and not blocked_actions:
        execution_outcome_status = "ready"
    elif completed_actions and blocked_actions:
        execution_outcome_status = "partial"
    else:
        execution_outcome_status = "blocked"

    execution_outcome_summary = {
        "completed_count": len(completed_actions),
        "blocked_count": len(blocked_actions),
        "total": len(completed_actions) + len(blocked_actions),
    }

    return {
        "event_name": event_name,
        "execution_outcome_status": execution_outcome_status,
        "completed_actions": completed_actions,
        "blocked_actions": blocked_actions,
        "ready_bout_indices": ready_bout_indices,
        "blocked_bout_indices": blocked_bout_indices,
        "blocker_summary": blocker_summary,
        "execution_outcome_summary": execution_outcome_summary,
    }
