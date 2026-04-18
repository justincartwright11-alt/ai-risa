"""
control_plane_state_ledger_pack

Consumes control_plane_outcome_pack output and emits a deterministic control-plane system-of-record ledger artifact.
"""

def control_plane_state_ledger_pack(control_plane_outcome_pack_result):
    """
    Args:
        control_plane_outcome_pack_result (dict): Output from control_plane_outcome_pack
    Returns:
        dict: Control plane state ledger artifact
    """
    outcome_status = control_plane_outcome_pack_result.get('control_plane_outcome_status', 'unknown')
    event_count = control_plane_outcome_pack_result.get('event_count', 0)
    completed_actions = control_plane_outcome_pack_result.get('completed_actions', [])
    blocked_outcomes = control_plane_outcome_pack_result.get('blocked_outcomes', [])
    ready_event_names = control_plane_outcome_pack_result.get('ready_event_names', [])
    blocked_event_names = control_plane_outcome_pack_result.get('blocked_event_names', [])
    outcome_batches = control_plane_outcome_pack_result.get('outcome_batches', {})
    priority_queue = control_plane_outcome_pack_result.get('priority_queue', [])
    escalation_queue = control_plane_outcome_pack_result.get('escalation_queue', [])
    blocker_summary = control_plane_outcome_pack_result.get('blocker_summary', {})

    ledger_entries = []
    blocked_ledger_entries = []

    for action in completed_actions:
        event_name = action.get('event_name')
        event_status = action.get('event_status')
        priority = action.get('priority')
        queue_action = action.get('queue_action')
        queue_reason = action.get('queue_reason')
        dispatch_batch = action.get('dispatch_batch')
        dispatch_reason = action.get('dispatch_reason')
        execution_batch = action.get('execution_batch')
        execution_reason = action.get('execution_reason')
        outcome_batch = action.get('outcome_batch')
        outcome_reason = action.get('outcome_reason')
        source_card = action.get('source_card')
        outcome_snapshot = dict(action)
        # Ledger status and reason
        ledger_status = 'ledger_ready'
        ledger_reason = 'Outcome recorded in system-of-record ledger'
        ledger_entry = {
            'event_name': event_name,
            'event_status': event_status,
            'priority': priority,
            'queue_action': queue_action,
            'queue_reason': queue_reason,
            'dispatch_batch': dispatch_batch,
            'dispatch_reason': dispatch_reason,
            'execution_batch': execution_batch,
            'execution_reason': execution_reason,
            'outcome_batch': outcome_batch,
            'outcome_reason': outcome_reason,
            'ledger_status': ledger_status,
            'ledger_reason': ledger_reason,
            'source_card': source_card,
            'outcome_snapshot': outcome_snapshot
        }
        ledger_entries.append(ledger_entry)

    for blocked in blocked_outcomes:
        event_name = blocked.get('event_name')
        event_status = blocked.get('event_status')
        priority = blocked.get('priority')
        blocker_reason = blocked.get('blocker_reason', 'Blocked at ledger')
        outcome_snapshot = blocked.get('execution_snapshot')
        blocked_ledger_entries.append({
            'event_name': event_name,
            'event_status': event_status,
            'priority': priority,
            'blocker_reason': blocker_reason,
            'outcome_snapshot': outcome_snapshot
        })

    # Status rule
    if ledger_entries and not blocked_ledger_entries:
        ledger_status = 'ready'
    elif ledger_entries and blocked_ledger_entries:
        ledger_status = 'partial'
    else:
        ledger_status = 'blocked'

    control_plane_state_ledger_summary = {
        'ledger_status': ledger_status,
        'event_count': event_count,
        'ledger_count': len(ledger_entries),
        'blocked_ledger_count': len(blocked_ledger_entries),
        'ready_event_names': ready_event_names,
        'blocked_event_names': blocked_event_names,
        'priority_queue': priority_queue,
        'escalation_queue': escalation_queue,
        'blocker_summary': blocker_summary
    }

    return {
        'control_plane_state_ledger_status': ledger_status,
        'event_count': event_count,
        'ledger_entries': ledger_entries,
        'blocked_ledger_entries': blocked_ledger_entries,
        'ready_event_names': ready_event_names,
        'blocked_event_names': blocked_event_names,
        'priority_queue': priority_queue,
        'escalation_queue': escalation_queue,
        'blocker_summary': blocker_summary,
        'control_plane_state_ledger_summary': control_plane_state_ledger_summary
    }
