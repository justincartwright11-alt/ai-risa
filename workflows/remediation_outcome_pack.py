"""
remediation_outcome_pack.py

Consumes remediation_execution_pack output and emits a deterministic remediation outcome bundle.
"""
from typing import Dict, Any, List

def remediation_outcome_pack(remediation_execution_pack_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a remediation outcome bundle from remediation_execution_pack output.
    Args:
        remediation_execution_pack_result: Output from remediation_execution_pack
    Returns:
        Dict with keys:
            - event_name
            - remediation_outcome_status
            - completed_remediations
            - blocked_remediation_outcomes
            - ready_bout_indices
            - blocked_bout_indices
            - blocker_summary
            - remediation_outcome_summary
    """
    event_name = remediation_execution_pack_result.get("event_name")
    ready_remediation_actions = remediation_execution_pack_result.get("ready_remediation_actions", [])
    blocked_remediation_actions = remediation_execution_pack_result.get("blocked_remediation_actions", [])
    completed_remediations = []
    blocked_remediation_outcomes = []
    ready_bout_indices = []
    blocked_bout_indices = []
    blocker_summary = []

    for action in ready_remediation_actions:
        completed_remediations.append({
            "event_name": event_name,
            "bout_index": action.get("bout_index"),
            "remediation_outcome_state": "completed",
            "delivery_key": action.get("delivery_key"),
            "publication_label": action.get("publication_label"),
            "publication_order": action.get("publication_order"),
            "remediation_action": action.get("remediation_action"),
            "remediation_reason": action.get("remediation_reason"),
            "execution_steps": action.get("execution_steps"),
            "execution_snapshot": action,
            "remediation_snapshot": action.get("remediation_snapshot"),
        })
        ready_bout_indices.append(action.get("bout_index"))

    for action in blocked_remediation_actions:
        blocked_remediation_outcomes.append({
            "event_name": event_name,
            "bout_index": action.get("bout_index"),
            "remediation_outcome_state": "blocked",
            "blocker_reason": action.get("blocker_reason"),
            "remediation_snapshot": action.get("remediation_snapshot"),
        })
        blocked_bout_indices.append(action.get("bout_index"))
        blocker_summary.append({
            "bout_index": action.get("bout_index"),
            "reason": action.get("blocker_reason"),
        })

    if completed_remediations and not blocked_remediation_outcomes:
        remediation_outcome_status = "ready"
    elif completed_remediations and blocked_remediation_outcomes:
        remediation_outcome_status = "partial"
    else:
        remediation_outcome_status = "blocked"

    remediation_outcome_summary = {
        "completed_count": len(completed_remediations),
        "blocked_count": len(blocked_remediation_outcomes),
        "total": len(completed_remediations) + len(blocked_remediation_outcomes),
    }

    return {
        "event_name": event_name,
        "remediation_outcome_status": remediation_outcome_status,
        "completed_remediations": completed_remediations,
        "blocked_remediation_outcomes": blocked_remediation_outcomes,
        "ready_bout_indices": ready_bout_indices,
        "blocked_bout_indices": blocked_bout_indices,
        "blocker_summary": blocker_summary,
        "remediation_outcome_summary": remediation_outcome_summary,
    }
