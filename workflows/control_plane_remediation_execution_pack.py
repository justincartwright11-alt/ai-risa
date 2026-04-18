"""
control_plane_remediation_execution_pack

Consumes control_plane_remediation_pack output and emits a deterministic execution-ready remediation bundle.
"""

def control_plane_remediation_execution_pack(control_plane_remediation_pack_result):
    """
    Args:
        control_plane_remediation_pack_result (dict): Output from control_plane_remediation_pack
    Returns:
        dict: Control plane remediation execution artifact
    """
    remediation_status = control_plane_remediation_pack_result.get('control_plane_remediation_status', 'unknown')
    event_count = control_plane_remediation_pack_result.get('event_count', 0)
    remediation_actions = control_plane_remediation_pack_result.get('remediation_actions', [])
    blocked_remediations = control_plane_remediation_pack_result.get('blocked_remediations', [])
    ready_event_names = control_plane_remediation_pack_result.get('ready_event_names', [])
    blocked_event_names = control_plane_remediation_pack_result.get('blocked_event_names', [])
    priority_queue = control_plane_remediation_pack_result.get('priority_queue', [])
    escalation_queue = control_plane_remediation_pack_result.get('escalation_queue', [])
    blocker_summary = control_plane_remediation_pack_result.get('blocker_summary', {})
    control_plane_remediation_summary = control_plane_remediation_pack_result.get('control_plane_remediation_summary', {})

    execution_ready_remediations = []
    blocked_remediation_executions = []

    for action in remediation_actions:
        event_name = action.get('event_name')
        event_status = action.get('event_status')
        priority = action.get('priority')
        followup_action = action.get('followup_action')
        followup_reason = action.get('followup_reason')
        remediation_action = action.get('remediation_action')
        remediation_reason = action.get('remediation_reason')
        escalation_level = action.get('escalation_level', 0)
        source_card = action.get('source_card')
        remediation_snapshot = dict(action)
        # Determine execution_action and reason
        if remediation_action == 'remediate_proceed':
            execution_action = 'execute_remediate_proceed'
            execution_reason = 'Proceed with remediation execution'
        elif remediation_action == 'remediate_review':
            execution_action = 'execute_remediate_review'
            execution_reason = 'Remediation execution requires operator review'
        elif remediation_action == 'remediate_escalate':
            execution_action = 'execute_remediate_escalate'
            execution_reason = 'Remediation execution requires escalation'
        else:
            execution_action = 'execute_remediate_hold'
            execution_reason = 'Hold remediation execution pending resolution'
        execution_ready_remediations.append({
            'event_name': event_name,
            'event_status': event_status,
            'priority': priority,
            'followup_action': followup_action,
            'followup_reason': followup_reason,
            'remediation_action': remediation_action,
            'remediation_reason': remediation_reason,
            'execution_action': execution_action,
            'execution_reason': execution_reason,
            'escalation_level': escalation_level,
            'source_card': source_card,
            'remediation_snapshot': remediation_snapshot
        })

    for blocked in blocked_remediations:
        event_name = blocked.get('event_name')
        event_status = blocked.get('event_status')
        priority = blocked.get('priority')
        blocker_reason = blocked.get('blocker_reason', 'Blocked at remediation execution')
        remediation_snapshot = blocked.get('followup_snapshot') or dict(blocked)
        blocked_remediation_executions.append({
            'event_name': event_name,
            'event_status': event_status,
            'priority': priority,
            'blocker_reason': blocker_reason,
            'remediation_snapshot': remediation_snapshot
        })

    # Status rule
    if execution_ready_remediations and not blocked_remediation_executions:
        remediation_execution_status = 'ready'
    elif execution_ready_remediations and blocked_remediation_executions:
        remediation_execution_status = 'partial'
    else:
        remediation_execution_status = 'blocked'

    control_plane_remediation_execution_summary = {
        'remediation_execution_status': remediation_execution_status,
        'event_count': event_count,
        'execution_ready_count': len(execution_ready_remediations),
        'blocked_execution_count': len(blocked_remediation_executions),
        'ready_event_names': ready_event_names,
        'blocked_event_names': blocked_event_names,
        'priority_queue': priority_queue,
        'escalation_queue': escalation_queue,
        'blocker_summary': blocker_summary
    }

    return {
        'control_plane_remediation_execution_status': remediation_execution_status,
        'event_count': event_count,
        'execution_ready_remediations': execution_ready_remediations,
        'blocked_remediation_executions': blocked_remediation_executions,
        'ready_event_names': ready_event_names,
        'blocked_event_names': blocked_event_names,
        'priority_queue': priority_queue,
        'escalation_queue': escalation_queue,
        'blocker_summary': blocker_summary,
        'control_plane_remediation_execution_summary': control_plane_remediation_execution_summary
    }
