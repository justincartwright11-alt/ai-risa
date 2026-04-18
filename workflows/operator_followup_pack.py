"""
operator_followup_pack.py

Consumes state_reconciliation_pack output and emits a deterministic operator follow-up bundle.
"""
from typing import Dict, Any, List

def operator_followup_pack(state_reconciliation_pack_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build an operator follow-up bundle from state_reconciliation_pack output.
    Args:
        state_reconciliation_pack_result: Output from state_reconciliation_pack
    Returns:
        Dict with keys:
            - event_name
            - operator_followup_status
            - followup_actions
            - blocked_followups
            - ready_bout_indices
            - blocked_bout_indices
            - blocker_summary
            - operator_followup_summary
    """
    event_name = state_reconciliation_pack_result.get("event_name")
    reconciled_entries = state_reconciliation_pack_result.get("reconciled_entries", [])
    blocked_reconciliations = state_reconciliation_pack_result.get("blocked_reconciliations", [])
    followup_actions = []
    blocked_followups = []
    ready_bout_indices = []
    blocked_bout_indices = []
    blocker_summary = []

    for entry in reconciled_entries:
        # Only add follow-up if not fully clean (simulate with reconciliation_status != 'ready')
        status = entry.get("reconciliation_status", "ready")
        if status == "ready":
            followup_status = "ready"
            followup_action = "review"
            followup_reason = "Routine review"
        else:
            followup_status = "followup"
            followup_action = "investigate"
            followup_reason = "Requires operator intervention"
        followup_actions.append({
            "event_name": event_name,
            "bout_index": entry.get("bout_index"),
            "followup_status": followup_status,
            "delivery_key": entry.get("delivery_key"),
            "publication_label": entry.get("publication_label"),
            "publication_order": entry.get("publication_order"),
            "reconciliation_status": status,
            "followup_action": followup_action,
            "followup_reason": followup_reason,
            "reconciliation_snapshot": entry,
        })
        ready_bout_indices.append(entry.get("bout_index"))

    for entry in blocked_reconciliations:
        blocked_followups.append({
            "event_name": event_name,
            "bout_index": entry.get("bout_index"),
            "followup_status": "blocked",
            "blocker_reason": entry.get("blocker_reason"),
            "reconciliation_snapshot": entry,
        })
        blocked_bout_indices.append(entry.get("bout_index"))
        blocker_summary.append({
            "bout_index": entry.get("bout_index"),
            "reason": entry.get("blocker_reason"),
        })

    if followup_actions and not blocked_followups:
        operator_followup_status = "ready"
    elif followup_actions and blocked_followups:
        operator_followup_status = "partial"
    else:
        operator_followup_status = "blocked"

    operator_followup_summary = {
        "followup_count": len(followup_actions),
        "blocked_count": len(blocked_followups),
        "total": len(followup_actions) + len(blocked_followups),
    }

    return {
        "event_name": event_name,
        "operator_followup_status": operator_followup_status,
        "followup_actions": followup_actions,
        "blocked_followups": blocked_followups,
        "ready_bout_indices": ready_bout_indices,
        "blocked_bout_indices": blocked_bout_indices,
        "blocker_summary": blocker_summary,
        "operator_followup_summary": operator_followup_summary,
    }
