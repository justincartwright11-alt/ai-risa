"""
control_plane_remediation_outcome_pack

Consumes control_plane_remediation_execution_pack output and emits a deterministic remediation outcome artifact.
"""

def control_plane_remediation_outcome_pack(control_plane_remediation_execution_pack_result):
    """
    Args:
        control_plane_remediation_execution_pack_result (dict): Output from control_plane_remediation_execution_pack
    Returns:
        dict: Control plane remediation outcome artifact
    """
    remediation_execution_status = control_plane_remediation_execution_pack_result.get('control_plane_remediation_execution_status', 'unknown')
    event_count = control_plane_remediation_execution_pack_result.get('event_count', 0)
    execution_ready_remediations = control_plane_remediation_execution_pack_result.get('execution_ready_remediations', [])
    blocked_remediation_executions = control_plane_remediation_execution_pack_result.get('blocked_remediation_executions', [])
    ready_event_names = control_plane_remediation_execution_pack_result.get('ready_event_names', [])
    blocked_event_names = control_plane_remediation_execution_pack_result.get('blocked_event_names', [])
    priority_queue = control_plane_remediation_execution_pack_result.get('priority_queue', [])
    escalation_queue = control_plane_remediation_execution_pack_result.get('escalation_queue', [])
    blocker_summary = control_plane_remediation_execution_pack_result.get('blocker_summary', {})
    control_plane_remediation_execution_summary = control_plane_remediation_execution_pack_result.get('control_plane_remediation_execution_summary', {})

    completed_remediations = []
    blocked_remediation_outcomes = []

    for action in execution_ready_remediations:
        event_name = action.get('event_name')
        event_status = action.get('event_status')
        priority = action.get('priority')
        followup_action = action.get('followup_action')
        followup_reason = action.get('followup_reason')
        remediation_action = action.get('remediation_action')
        remediation_reason = action.get('remediation_reason')
        execution_action = action.get('execution_action')
        execution_reason = action.get('execution_reason')
        escalation_level = action.get('escalation_level', 0)
        source_card = action.get('source_card')
        execution_snapshot = dict(action)
        # Determine outcome_action and reason
        if execution_action == 'execute_remediate_proceed':
            outcome_action = 'complete_remediate_proceed'
            outcome_reason = 'Remediation completed: proceed'
        elif execution_action == 'execute_remediate_review':
            outcome_action = 'complete_remediate_review'
            outcome_reason = 'Remediation completed: review'
        elif execution_action == 'execute_remediate_escalate':
            outcome_action = 'complete_remediate_escalate'
            outcome_reason = 'Remediation completed: escalate'
        else:
            outcome_action = 'complete_remediate_hold'
            outcome_reason = 'Remediation completed: hold'
        completed_remediations.append({
            'event_name': event_name,
            'event_status': event_status,
            'priority': priority,
            'followup_action': followup_action,
            'followup_reason': followup_reason,
            'remediation_action': remediation_action,
            'remediation_reason': remediation_reason,
            'execution_action': execution_action,
            'execution_reason': execution_reason,
            'outcome_action': outcome_action,
            'outcome_reason': outcome_reason,
            'escalation_level': escalation_level,
            'source_card': source_card,
            'execution_snapshot': execution_snapshot
        })

    for blocked in blocked_remediation_executions:
        event_name = blocked.get('event_name')
        event_status = blocked.get('event_status')
        priority = blocked.get('priority')
        blocker_reason = blocked.get('blocker_reason', 'Blocked at remediation outcome')
        execution_snapshot = blocked.get('remediation_snapshot') or dict(blocked)
        blocked_remediation_outcomes.append({
            'event_name': event_name,
            'event_status': event_status,
            'priority': priority,
            'blocker_reason': blocker_reason,
            'execution_snapshot': execution_snapshot
        })

    # Status rule
    if completed_remediations and not blocked_remediation_outcomes:
        remediation_outcome_status = 'ready'
    elif completed_remediations and blocked_remediation_outcomes:
        remediation_outcome_status = 'partial'
    else:
        remediation_outcome_status = 'blocked'

    control_plane_remediation_outcome_summary = {
        'remediation_outcome_status': remediation_outcome_status,
        'event_count': event_count,
        'completed_count': len(completed_remediations),
        'blocked_count': len(blocked_remediation_outcomes),
        'ready_event_names': ready_event_names,
        'blocked_event_names': blocked_event_names,
        'priority_queue': priority_queue,
        'escalation_queue': escalation_queue,
        'blocker_summary': blocker_summary
    }

    return {
        'control_plane_remediation_outcome_status': remediation_outcome_status,
        'event_count': event_count,
        'completed_remediations': completed_remediations,
        'blocked_remediation_outcomes': blocked_remediation_outcomes,
        'ready_event_names': ready_event_names,
        'blocked_event_names': blocked_event_names,
        'priority_queue': priority_queue,
        'escalation_queue': escalation_queue,
        'blocker_summary': blocker_summary,
        'control_plane_remediation_outcome_summary': control_plane_remediation_outcome_summary
    }
