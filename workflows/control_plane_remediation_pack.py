"""
control_plane_remediation_pack

Consumes control_plane_followup_pack output and emits a deterministic control-plane remediation artifact.
"""

def control_plane_remediation_pack(control_plane_followup_pack_result):
    """
    Args:
        control_plane_followup_pack_result (dict): Output from control_plane_followup_pack
    Returns:
        dict: Control plane remediation artifact
    """
    followup_status = control_plane_followup_pack_result.get('control_plane_followup_status', 'unknown')
    event_count = control_plane_followup_pack_result.get('event_count', 0)
    followup_actions = control_plane_followup_pack_result.get('followup_actions', [])
    blocked_followups = control_plane_followup_pack_result.get('blocked_followups', [])
    ready_event_names = control_plane_followup_pack_result.get('ready_event_names', [])
    blocked_event_names = control_plane_followup_pack_result.get('blocked_event_names', [])
    priority_queue = control_plane_followup_pack_result.get('priority_queue', [])
    escalation_queue = control_plane_followup_pack_result.get('escalation_queue', [])
    blocker_summary = control_plane_followup_pack_result.get('blocker_summary', {})
    control_plane_followup_summary = control_plane_followup_pack_result.get('control_plane_followup_summary', {})

    remediation_actions = []
    blocked_remediations = []

    for action in followup_actions:
        event_name = action.get('event_name')
        event_status = action.get('event_status')
        priority = action.get('priority')
        followup_action = action.get('followup_action')
        followup_reason = action.get('followup_reason')
        escalation_level = action.get('escalation_level', 0)
        source_card = action.get('source_card')
        followup_snapshot = dict(action)
        # Determine remediation_action and reason
        if followup_action == 'proceed_followup':
            remediation_action = 'remediate_proceed'
            remediation_reason = 'Proceed with remediation'
        elif followup_action == 'review_followup':
            remediation_action = 'remediate_review'
            remediation_reason = 'Remediation requires operator review'
        elif followup_action == 'escalate_followup':
            remediation_action = 'remediate_escalate'
            remediation_reason = 'Remediation requires escalation'
        else:
            remediation_action = 'remediate_hold'
            remediation_reason = 'Hold remediation pending resolution'
        remediation_actions.append({
            'event_name': event_name,
            'event_status': event_status,
            'priority': priority,
            'followup_action': followup_action,
            'followup_reason': followup_reason,
            'remediation_action': remediation_action,
            'remediation_reason': remediation_reason,
            'escalation_level': escalation_level,
            'source_card': source_card,
            'followup_snapshot': followup_snapshot
        })

    for blocked in blocked_followups:
        event_name = blocked.get('event_name')
        event_status = blocked.get('event_status')
        priority = blocked.get('priority')
        blocker_reason = blocked.get('blocker_reason', 'Blocked at remediation')
        followup_snapshot = blocked.get('reconciliation_snapshot') or dict(blocked)
        blocked_remediations.append({
            'event_name': event_name,
            'event_status': event_status,
            'priority': priority,
            'blocker_reason': blocker_reason,
            'followup_snapshot': followup_snapshot
        })

    # Status rule
    if remediation_actions and not blocked_remediations:
        remediation_status = 'ready'
    elif remediation_actions and blocked_remediations:
        remediation_status = 'partial'
    else:
        remediation_status = 'blocked'

    control_plane_remediation_summary = {
        'remediation_status': remediation_status,
        'event_count': event_count,
        'remediation_count': len(remediation_actions),
        'blocked_remediation_count': len(blocked_remediations),
        'ready_event_names': ready_event_names,
        'blocked_event_names': blocked_event_names,
        'priority_queue': priority_queue,
        'escalation_queue': escalation_queue,
        'blocker_summary': blocker_summary
    }

    return {
        'control_plane_remediation_status': remediation_status,
        'event_count': event_count,
        'remediation_actions': remediation_actions,
        'blocked_remediations': blocked_remediations,
        'ready_event_names': ready_event_names,
        'blocked_event_names': blocked_event_names,
        'priority_queue': priority_queue,
        'escalation_queue': escalation_queue,
        'blocker_summary': blocker_summary,
        'control_plane_remediation_summary': control_plane_remediation_summary
    }
