"""
operator_execution_session_pack.py

Consumes release_runbook_pack output and emits a deterministic, operator-facing execution session bundle.
"""
from typing import Dict, Any, List

def operator_execution_session_pack(release_runbook_pack_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build an operator execution session bundle from release_runbook_pack output.
    Args:
        release_runbook_pack_result: Output from release_runbook_pack
    Returns:
        Dict with keys:
            - event_name
            - execution_session_status
            - ready_session_actions
            - blocked_session_actions
            - ready_bout_indices
            - blocked_bout_indices
            - blocker_summary
            - execution_session_summary
    """
    event_name = release_runbook_pack_result.get("event_name")
    ready_runbook = release_runbook_pack_result.get("ready_release_actions", [])
    blocked_runbook = release_runbook_pack_result.get("blocked_release_actions", [])
    ready_session_actions = []
    blocked_session_actions = []
    ready_bout_indices = []
    blocked_bout_indices = []
    blocker_summary = []

    for action in ready_runbook:
        ready_session_actions.append({
            "event_name": event_name,
            "bout_index": action.get("bout_index"),
            "session_status": "ready",
            "delivery_key": action.get("delivery_key"),
            "publication_label": action.get("publication_label"),
            "publication_order": action.get("publication_order"),
            "action_sequence": action.get("action_sequence"),
            "preflight_checks": action.get("preflight_checks"),
            "runbook_snapshot": action.get("release_snapshot"),
        })
        ready_bout_indices.append(action.get("bout_index"))

    for action in blocked_runbook:
        blocked_session_actions.append({
            "event_name": event_name,
            "bout_index": action.get("bout_index"),
            "session_status": "blocked",
            "blocker_reason": action.get("blocker_reason"),
            "runbook_snapshot": action.get("release_snapshot"),
        })
        blocked_bout_indices.append(action.get("bout_index"))
        blocker_summary.append({
            "bout_index": action.get("bout_index"),
            "reason": action.get("blocker_reason"),
        })

    if ready_session_actions and not blocked_session_actions:
        execution_session_status = "ready"
    elif ready_session_actions and blocked_session_actions:
        execution_session_status = "partial"
    else:
        execution_session_status = "blocked"

    execution_session_summary = {
        "ready_count": len(ready_session_actions),
        "blocked_count": len(blocked_session_actions),
        "total": len(ready_session_actions) + len(blocked_session_actions),
    }

    return {
        "event_name": event_name,
        "execution_session_status": execution_session_status,
        "ready_session_actions": ready_session_actions,
        "blocked_session_actions": blocked_session_actions,
        "ready_bout_indices": ready_bout_indices,
        "blocked_bout_indices": blocked_bout_indices,
        "blocker_summary": blocker_summary,
        "execution_session_summary": execution_session_summary,
    }
