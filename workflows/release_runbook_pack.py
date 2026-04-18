"""
release_runbook_pack.py

Consumes publication_release_pack output and emits a deterministic, operator-executable release runbook bundle.
"""

from typing import Dict, Any, List

def release_runbook_pack(publication_release_pack_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a release runbook bundle from publication_release_pack output.
    Args:
        publication_release_pack_result: Output from publication_release_pack
    Returns:
        Dict with keys:
            - event_name
            - release_runbook_status
            - ready_release_actions
            - blocked_release_actions
            - ready_bout_indices
            - blocked_bout_indices
            - blocker_summary
            - release_runbook_summary
    """
    event_name = publication_release_pack_result.get("event_name")
    release_actions = publication_release_pack_result.get("release_actions", [])
    ready_release_actions = []
    blocked_release_actions = []
    ready_bout_indices = []
    blocked_bout_indices = []
    blocker_summary = []

    for action in release_actions:
        status = action.get("release_status")
        bout_index = action.get("bout_index")
        if status == "ready":
            ready_release_actions.append({
                "event_name": event_name,
                "bout_index": bout_index,
                "runbook_status": "ready",
                "delivery_key": action.get("delivery_key"),
                "publication_label": action.get("publication_label"),
                "publication_order": action.get("publication_order"),
                "action_sequence": action.get("action_sequence"),
                "preflight_checks": action.get("preflight_checks"),
                "release_snapshot": action.get("release_snapshot"),
            })
            ready_bout_indices.append(bout_index)
        else:
            blocked_release_actions.append({
                "event_name": event_name,
                "bout_index": bout_index,
                "runbook_status": "blocked",
                "blocker_reason": action.get("blocker_reason"),
                "release_snapshot": action.get("release_snapshot"),
            })
            blocked_bout_indices.append(bout_index)
            blocker_summary.append({
                "bout_index": bout_index,
                "reason": action.get("blocker_reason"),
            })

    if ready_release_actions and not blocked_release_actions:
        release_runbook_status = "ready"
    elif ready_release_actions and blocked_release_actions:
        release_runbook_status = "partial"
    else:
        release_runbook_status = "blocked"

    release_runbook_summary = {
        "ready_count": len(ready_release_actions),
        "blocked_count": len(blocked_release_actions),
        "total": len(release_actions),
    }

    return {
        "event_name": event_name,
        "release_runbook_status": release_runbook_status,
        "ready_release_actions": ready_release_actions,
        "blocked_release_actions": blocked_release_actions,
        "ready_bout_indices": ready_bout_indices,
        "blocked_bout_indices": blocked_bout_indices,
        "blocker_summary": blocker_summary,
        "release_runbook_summary": release_runbook_summary,
    }
