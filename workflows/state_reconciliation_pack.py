"""
state_reconciliation_pack.py

Consumes release_state_ledger_pack output and emits a deterministic event-level state reconciliation bundle.
"""
from typing import Dict, Any, List

def state_reconciliation_pack(release_state_ledger_pack_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a state reconciliation bundle from release_state_ledger_pack output.
    Args:
        release_state_ledger_pack_result: Output from release_state_ledger_pack
    Returns:
        Dict with keys:
            - event_name
            - state_reconciliation_status
            - reconciled_entries
            - blocked_reconciliations
            - ready_bout_indices
            - blocked_bout_indices
            - blocker_summary
            - state_reconciliation_summary
    """
    event_name = release_state_ledger_pack_result.get("event_name")
    ledger_entries = release_state_ledger_pack_result.get("ledger_entries", [])
    blocked_ledger_entries = release_state_ledger_pack_result.get("blocked_ledger_entries", [])
    reconciled_entries = []
    blocked_reconciliations = []
    ready_bout_indices = []
    blocked_bout_indices = []
    blocker_summary = []

    for entry in ledger_entries:
        reconciled_entries.append({
            "event_name": event_name,
            "bout_index": entry.get("bout_index"),
            "reconciliation_status": "ready",
            "delivery_key": entry.get("delivery_key"),
            "publication_label": entry.get("publication_label"),
            "publication_order": entry.get("publication_order"),
            "ledger_status": entry.get("ledger_status"),
            "outcome_status": entry.get("outcome_status"),
            "action_sequence": entry.get("action_sequence"),
            "ledger_snapshot": entry,
        })
        ready_bout_indices.append(entry.get("bout_index"))

    for entry in blocked_ledger_entries:
        blocked_reconciliations.append({
            "event_name": event_name,
            "bout_index": entry.get("bout_index"),
            "reconciliation_status": "blocked",
            "blocker_reason": entry.get("blocker_reason"),
            "ledger_snapshot": entry,
        })
        blocked_bout_indices.append(entry.get("bout_index"))
        blocker_summary.append({
            "bout_index": entry.get("bout_index"),
            "reason": entry.get("blocker_reason"),
        })

    if reconciled_entries and not blocked_reconciliations:
        state_reconciliation_status = "ready"
    elif reconciled_entries and blocked_reconciliations:
        state_reconciliation_status = "partial"
    else:
        state_reconciliation_status = "blocked"

    state_reconciliation_summary = {
        "reconciled_count": len(reconciled_entries),
        "blocked_count": len(blocked_reconciliations),
        "total": len(reconciled_entries) + len(blocked_reconciliations),
    }

    return {
        "event_name": event_name,
        "state_reconciliation_status": state_reconciliation_status,
        "reconciled_entries": reconciled_entries,
        "blocked_reconciliations": blocked_reconciliations,
        "ready_bout_indices": ready_bout_indices,
        "blocked_bout_indices": blocked_bout_indices,
        "blocker_summary": blocker_summary,
        "state_reconciliation_summary": state_reconciliation_summary,
    }
