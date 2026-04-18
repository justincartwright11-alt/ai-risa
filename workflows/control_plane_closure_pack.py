"""
control_plane_closure_pack

Consumes control_plane_remediation_outcome_pack output and emits a deterministic closure artifact.
"""

def control_plane_closure_pack(control_plane_remediation_outcome_pack_result):
    """
    Args:
        control_plane_remediation_outcome_pack_result (dict): Output from control_plane_remediation_outcome_pack
    Returns:
        dict: Control plane closure artifact
    """
    remediation_outcome_status = control_plane_remediation_outcome_pack_result.get('control_plane_remediation_outcome_status', 'unknown')
    event_count = control_plane_remediation_outcome_pack_result.get('event_count', 0)
    completed_remediations = control_plane_remediation_outcome_pack_result.get('completed_remediations', [])
    blocked_remediation_outcomes = control_plane_remediation_outcome_pack_result.get('blocked_remediation_outcomes', [])
    ready_event_names = control_plane_remediation_outcome_pack_result.get('ready_event_names', [])
    blocked_event_names = control_plane_remediation_outcome_pack_result.get('blocked_event_names', [])
    priority_queue = control_plane_remediation_outcome_pack_result.get('priority_queue', [])
    escalation_queue = control_plane_remediation_outcome_pack_result.get('escalation_queue', [])
    blocker_summary = control_plane_remediation_outcome_pack_result.get('blocker_summary', {})
    control_plane_remediation_outcome_summary = control_plane_remediation_outcome_pack_result.get('control_plane_remediation_outcome_summary', {})

    closed_events = []
    pending_events = []

    for action in completed_remediations:
        event_name = action.get('event_name')
        event_status = action.get('event_status')
        priority = action.get('priority')
        followup_action = action.get('followup_action')
        remediation_action = action.get('remediation_action')
        execution_action = action.get('execution_action')
        outcome_action = action.get('outcome_action')
        escalation_level = action.get('escalation_level', 0)
        source_card = action.get('source_card')
        remediation_outcome_snapshot = dict(action)
        # Determine closure_action and reason
        if outcome_action == 'complete_remediate_proceed':
            closure_action = 'close_event'
            closure_reason = 'Event closed after successful remediation'
        elif outcome_action == 'complete_remediate_review':
            closure_action = 'hold_open'
            closure_reason = 'Event held open for operator review'
        elif outcome_action == 'complete_remediate_escalate':
            closure_action = 'escalate_followup'
            closure_reason = 'Event escalated for follow-up'
        else:
            closure_action = 'hold_open'
            closure_reason = 'Event held open pending resolution'
        closed_events.append({
            'event_name': event_name,
            'event_status': event_status,
            'priority': priority,
            'followup_action': followup_action,
            'remediation_action': remediation_action,
            'execution_action': execution_action,
            'outcome_action': outcome_action,
            'closure_action': closure_action,
            'closure_reason': closure_reason,
            'escalation_level': escalation_level,
            'source_card': source_card,
            'remediation_outcome_snapshot': remediation_outcome_snapshot
        })

    for blocked in blocked_remediation_outcomes:
        event_name = blocked.get('event_name')
        event_status = blocked.get('event_status')
        priority = blocked.get('priority')
        blocker_reason = blocked.get('blocker_reason', 'Pending at closure')
        remediation_outcome_snapshot = blocked.get('execution_snapshot') or dict(blocked)
        pending_events.append({
            'event_name': event_name,
            'event_status': event_status,
            'priority': priority,
            'blocker_reason': blocker_reason,
            'remediation_outcome_snapshot': remediation_outcome_snapshot
        })

    # Status rule
    if closed_events and not pending_events:
        closure_status = 'ready'
    elif closed_events and pending_events:
        closure_status = 'partial'
    else:
        closure_status = 'blocked'

    control_plane_closure_summary = {
        'closure_status': closure_status,
        'event_count': event_count,
        'closed_count': len(closed_events),
        'pending_count': len(pending_events),
        'ready_event_names': ready_event_names,
        'blocked_event_names': blocked_event_names,
        'priority_queue': priority_queue,
        'escalation_queue': escalation_queue,
        'blocker_summary': blocker_summary
    }

    return {
        'control_plane_closure_status': closure_status,
        'event_count': event_count,
        'closed_events': closed_events,
        'pending_events': pending_events,
        'ready_event_names': ready_event_names,
        'blocked_event_names': blocked_event_names,
        'priority_queue': priority_queue,
        'escalation_queue': escalation_queue,
        'blocker_summary': blocker_summary,
        'control_plane_closure_summary': control_plane_closure_summary
    }
