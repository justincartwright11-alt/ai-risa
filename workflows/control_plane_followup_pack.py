"""
control_plane_followup_pack

Consumes control_plane_reconciliation_pack output and emits a deterministic control-plane follow-up artifact.
"""

def control_plane_followup_pack(control_plane_reconciliation_pack_result):
    """
    Args:
        control_plane_reconciliation_pack_result (dict): Output from control_plane_reconciliation_pack
    Returns:
        dict: Control plane follow-up artifact
    """
    reconciliation_status = control_plane_reconciliation_pack_result.get('control_plane_reconciliation_status', 'unknown')
    event_count = control_plane_reconciliation_pack_result.get('event_count', 0)
    reconciled_entries = control_plane_reconciliation_pack_result.get('reconciled_entries', [])
    blocked_reconciliations = control_plane_reconciliation_pack_result.get('blocked_reconciliations', [])
    ready_event_names = control_plane_reconciliation_pack_result.get('ready_event_names', [])
    blocked_event_names = control_plane_reconciliation_pack_result.get('blocked_event_names', [])
    priority_queue = control_plane_reconciliation_pack_result.get('priority_queue', [])
    escalation_queue = control_plane_reconciliation_pack_result.get('escalation_queue', [])
    blocker_summary = control_plane_reconciliation_pack_result.get('blocker_summary', {})
    control_plane_reconciliation_summary = control_plane_reconciliation_pack_result.get('control_plane_reconciliation_summary', {})

    followup_actions = []
    blocked_followups = []

    for entry in reconciled_entries:
        event_name = entry.get('event_name')
        event_status = entry.get('event_status')
        priority = entry.get('priority')
        reconciliation_status_entry = entry.get('reconciliation_status')
        source_card = entry.get('source_card')
        reconciliation_snapshot = dict(entry)
        # Determine followup_action and escalation_level
        if event_status == 'ready':
            followup_action = 'proceed_followup'
            escalation_level = 0
            followup_reason = 'Ready for follow-up proceed'
        elif event_status == 'partial':
            followup_action = 'review_followup'
            escalation_level = 1
            followup_reason = 'Requires operator review follow-up'
        elif event_status == 'escalate':
            followup_action = 'escalate_followup'
            escalation_level = 2
            followup_reason = 'Escalation required for follow-up'
        else:
            followup_action = 'hold_followup'
            escalation_level = 0
            followup_reason = 'Hold for follow-up pending resolution'
        followup_actions.append({
            'event_name': event_name,
            'event_status': event_status,
            'priority': priority,
            'reconciliation_status': reconciliation_status_entry,
            'followup_action': followup_action,
            'followup_reason': followup_reason,
            'escalation_level': escalation_level,
            'source_card': source_card,
            'reconciliation_snapshot': reconciliation_snapshot
        })

    for blocked in blocked_reconciliations:
        event_name = blocked.get('event_name')
        event_status = blocked.get('event_status')
        priority = blocked.get('priority')
        blocker_reason = blocked.get('blocker_reason', 'Blocked at follow-up')
        reconciliation_snapshot = blocked.get('ledger_snapshot') or dict(blocked)
        blocked_followups.append({
            'event_name': event_name,
            'event_status': event_status,
            'priority': priority,
            'blocker_reason': blocker_reason,
            'reconciliation_snapshot': reconciliation_snapshot
        })

    # Status rule
    if followup_actions and not blocked_followups:
        followup_status = 'ready'
    elif followup_actions and blocked_followups:
        followup_status = 'partial'
    else:
        followup_status = 'blocked'

    control_plane_followup_summary = {
        'followup_status': followup_status,
        'event_count': event_count,
        'followup_count': len(followup_actions),
        'blocked_followup_count': len(blocked_followups),
        'ready_event_names': ready_event_names,
        'blocked_event_names': blocked_event_names,
        'priority_queue': priority_queue,
        'escalation_queue': escalation_queue,
        'blocker_summary': blocker_summary
    }

    return {
        'control_plane_followup_status': followup_status,
        'event_count': event_count,
        'followup_actions': followup_actions,
        'blocked_followups': blocked_followups,
        'ready_event_names': ready_event_names,
        'blocked_event_names': blocked_event_names,
        'priority_queue': priority_queue,
        'escalation_queue': escalation_queue,
        'blocker_summary': blocker_summary,
        'control_plane_followup_summary': control_plane_followup_summary
    }
