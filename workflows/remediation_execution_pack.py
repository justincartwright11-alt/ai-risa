"""
remediation_execution_pack.py

Consumes remediation_plan_pack output and emits a deterministic operator-executable recovery bundle.
"""
from typing import Dict, Any, List

def remediation_execution_pack(remediation_plan_pack_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a remediation execution bundle from remediation_plan_pack output.
    Args:
        remediation_plan_pack_result: Output from remediation_plan_pack
    Returns:
        Dict with keys:
            - event_name
            - remediation_execution_status
            - ready_remediation_actions
            - blocked_remediation_actions
            - ready_bout_indices
            - blocked_bout_indices
            - blocker_summary
            - remediation_execution_summary
    """
    event_name = remediation_plan_pack_result.get("event_name")
    remediation_actions = remediation_plan_pack_result.get("remediation_actions", [])
    blocked_remediations = remediation_plan_pack_result.get("blocked_remediations", [])
    ready_remediation_actions = []
    blocked_remediation_actions = []
    ready_bout_indices = []
    blocked_bout_indices = []
    blocker_summary = []

    for action in remediation_actions:
        status = action.get("remediation_status", "ready")
        if status == "ready":
            remediation_execution_state = "ready"
            execution_steps = ["verify", "apply_fix", "validate"]
        else:
            remediation_execution_state = "pending"
            execution_steps = []
        ready_remediation_actions.append({
            "event_name": event_name,
            "bout_index": action.get("bout_index"),
            "remediation_execution_state": remediation_execution_state,
            "delivery_key": action.get("delivery_key"),
            "publication_label": action.get("publication_label"),
            "publication_order": action.get("publication_order"),
            "remediation_action": action.get("remediation_action"),
            "remediation_reason": action.get("remediation_reason"),
            "execution_steps": execution_steps,
            "followup_snapshot": action.get("followup_snapshot"),
            "remediation_snapshot": action,
        })
        ready_bout_indices.append(action.get("bout_index"))

    for action in blocked_remediations:
        blocked_remediation_actions.append({
            "event_name": event_name,
            "bout_index": action.get("bout_index"),
            "remediation_execution_state": "blocked",
            "blocker_reason": action.get("blocker_reason"),
            "remediation_snapshot": action,
        })
        blocked_bout_indices.append(action.get("bout_index"))
        blocker_summary.append({
            "bout_index": action.get("bout_index"),
            "reason": action.get("blocker_reason"),
        })

    if ready_remediation_actions and not blocked_remediation_actions:
        remediation_execution_status = "ready"
    elif ready_remediation_actions and blocked_remediation_actions:
        remediation_execution_status = "partial"
    else:
        remediation_execution_status = "blocked"

    remediation_execution_summary = {
        "ready_count": len(ready_remediation_actions),
        "blocked_count": len(blocked_remediation_actions),
        "total": len(ready_remediation_actions) + len(blocked_remediation_actions),
    }

    return {
        "event_name": event_name,
        "remediation_execution_status": remediation_execution_status,
        "ready_remediation_actions": ready_remediation_actions,
        "blocked_remediation_actions": blocked_remediation_actions,
        "ready_bout_indices": ready_bout_indices,
        "blocked_bout_indices": blocked_bout_indices,
        "blocker_summary": blocker_summary,
        "remediation_execution_summary": remediation_execution_summary,
    }
