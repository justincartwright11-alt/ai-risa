"""
control_plane_reconciliation_pack

Consumes control_plane_state_ledger_pack output and emits a deterministic control-plane reconciliation artifact.
"""

def control_plane_reconciliation_pack(control_plane_state_ledger_pack_result):
    """
    Args:
        control_plane_state_ledger_pack_result (dict): Output from control_plane_state_ledger_pack
    Returns:
        dict: Control plane reconciliation artifact
    """
    ledger_status = control_plane_state_ledger_pack_result.get('control_plane_state_ledger_status', 'unknown')
    event_count = control_plane_state_ledger_pack_result.get('event_count', 0)
    ledger_entries = control_plane_state_ledger_pack_result.get('ledger_entries', [])
    blocked_ledger_entries = control_plane_state_ledger_pack_result.get('blocked_ledger_entries', [])
    ready_event_names = control_plane_state_ledger_pack_result.get('ready_event_names', [])
    blocked_event_names = control_plane_state_ledger_pack_result.get('blocked_event_names', [])
    priority_queue = control_plane_state_ledger_pack_result.get('priority_queue', [])
    escalation_queue = control_plane_state_ledger_pack_result.get('escalation_queue', [])
    blocker_summary = control_plane_state_ledger_pack_result.get('blocker_summary', {})
    control_plane_state_ledger_summary = control_plane_state_ledger_pack_result.get('control_plane_state_ledger_summary', {})

    reconciled_entries = []
    blocked_reconciliations = []

    for entry in ledger_entries:
        event_name = entry.get('event_name')
        event_status = entry.get('event_status')
        priority = entry.get('priority')
        queue_action = entry.get('queue_action')
        dispatch_batch = entry.get('dispatch_batch')
        execution_batch = entry.get('execution_batch')
        outcome_batch = entry.get('outcome_batch')
        ledger_status_entry = entry.get('ledger_status')
        source_card = entry.get('source_card')
        ledger_snapshot = dict(entry)
        # Reconciliation status and reason
        reconciliation_status = 'reconciled'
        reconciliation_reason = 'Ledger entry reconciled in control-plane reconciliation pack'
        reconciled_entries.append({
            'event_name': event_name,
            'event_status': event_status,
            'priority': priority,
            'queue_action': queue_action,
            'dispatch_batch': dispatch_batch,
            'execution_batch': execution_batch,
            'outcome_batch': outcome_batch,
            'ledger_status': ledger_status_entry,
            'reconciliation_status': reconciliation_status,
            'reconciliation_reason': reconciliation_reason,
            'source_card': source_card,
            'ledger_snapshot': ledger_snapshot
        })

    for blocked in blocked_ledger_entries:
        event_name = blocked.get('event_name')
        event_status = blocked.get('event_status')
        priority = blocked.get('priority')
        blocker_reason = blocked.get('blocker_reason', 'Blocked at reconciliation')
        ledger_snapshot = blocked.get('outcome_snapshot') or dict(blocked)
        blocked_reconciliations.append({
            'event_name': event_name,
            'event_status': event_status,
            'priority': priority,
            'blocker_reason': blocker_reason,
            'ledger_snapshot': ledger_snapshot
        })

    # Status rule
    if reconciled_entries and not blocked_reconciliations:
        reconciliation_status = 'ready'
    elif reconciled_entries and blocked_reconciliations:
        reconciliation_status = 'partial'
    else:
        reconciliation_status = 'blocked'

    control_plane_reconciliation_summary = {
        'reconciliation_status': reconciliation_status,
        'event_count': event_count,
        'reconciled_count': len(reconciled_entries),
        'blocked_reconciled_count': len(blocked_reconciliations),
        'ready_event_names': ready_event_names,
        'blocked_event_names': blocked_event_names,
        'priority_queue': priority_queue,
        'escalation_queue': escalation_queue,
        'blocker_summary': blocker_summary
    }

    return {
        'control_plane_reconciliation_status': reconciliation_status,
        'event_count': event_count,
        'reconciled_entries': reconciled_entries,
        'blocked_reconciliations': blocked_reconciliations,
        'ready_event_names': ready_event_names,
        'blocked_event_names': blocked_event_names,
        'priority_queue': priority_queue,
        'escalation_queue': escalation_queue,
        'blocker_summary': blocker_summary,
        'control_plane_reconciliation_summary': control_plane_reconciliation_summary
    }
