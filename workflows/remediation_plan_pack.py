"""
remediation_plan_pack.py

Consumes operator_followup_pack output and emits a deterministic remediation/retry plan bundle.
"""
from typing import Dict, Any, List

def remediation_plan_pack(operator_followup_pack_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a remediation plan bundle from operator_followup_pack output.
    Args:
        operator_followup_pack_result: Output from operator_followup_pack
    Returns:
        Dict with keys:
            - event_name
            - remediation_plan_status
            - remediation_actions
            - blocked_remediations
            - ready_bout_indices
            - blocked_bout_indices
            - blocker_summary
            - remediation_plan_summary
    """
    event_name = operator_followup_pack_result.get("event_name")
    followup_actions = operator_followup_pack_result.get("followup_actions", [])
    blocked_followups = operator_followup_pack_result.get("blocked_followups", [])
    remediation_actions = []
    blocked_remediations = []
    ready_bout_indices = []
    blocked_bout_indices = []
    blocker_summary = []

    for action in followup_actions:
        status = action.get("followup_status", "ready")
        if status == "ready":
            remediation_status = "ready"
            remediation_action = "none"
            remediation_reason = "No remediation needed"
        else:
            remediation_status = "remediation"
            remediation_action = "retry"
            remediation_reason = "Operator remediation required"
        remediation_actions.append({
            "event_name": event_name,
            "bout_index": action.get("bout_index"),
            "remediation_status": remediation_status,
            "delivery_key": action.get("delivery_key"),
            "publication_label": action.get("publication_label"),
            "publication_order": action.get("publication_order"),
            "followup_status": status,
            "remediation_action": remediation_action,
            "remediation_reason": remediation_reason,
            "followup_snapshot": action,
        })
        ready_bout_indices.append(action.get("bout_index"))

    for action in blocked_followups:
        blocked_remediations.append({
            "event_name": event_name,
            "bout_index": action.get("bout_index"),
            "remediation_status": "blocked",
            "blocker_reason": action.get("blocker_reason"),
            "followup_snapshot": action,
        })
        blocked_bout_indices.append(action.get("bout_index"))
        blocker_summary.append({
            "bout_index": action.get("bout_index"),
            "reason": action.get("blocker_reason"),
        })

    if remediation_actions and not blocked_remediations:
        remediation_plan_status = "ready"
    elif remediation_actions and blocked_remediations:
        remediation_plan_status = "partial"
    else:
        remediation_plan_status = "blocked"

    remediation_plan_summary = {
        "remediation_count": len(remediation_actions),
        "blocked_count": len(blocked_remediations),
        "total": len(remediation_actions) + len(blocked_remediations),
    }

    return {
        "event_name": event_name,
        "remediation_plan_status": remediation_plan_status,
        "remediation_actions": remediation_actions,
        "blocked_remediations": blocked_remediations,
        "ready_bout_indices": ready_bout_indices,
        "blocked_bout_indices": blocked_bout_indices,
        "blocker_summary": blocker_summary,
        "remediation_plan_summary": remediation_plan_summary,
    }
