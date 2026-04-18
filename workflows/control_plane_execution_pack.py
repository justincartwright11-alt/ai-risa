"""
control_plane_execution_pack

Consumes control_plane_dispatch_pack output and emits a deterministic execution-ready control-plane bundle.
"""

def control_plane_execution_pack(control_plane_dispatch_pack_result):
    """
    Args:
        control_plane_dispatch_pack_result (dict): Output from control_plane_dispatch_pack
    Returns:
        dict: Control plane execution artifact
    """
    dispatch_status = control_plane_dispatch_pack_result.get('control_plane_dispatch_status', 'unknown')
    event_count = control_plane_dispatch_pack_result.get('event_count', 0)
    dispatch_ready_actions = control_plane_dispatch_pack_result.get('dispatch_ready_actions', [])
    blocked_dispatches = control_plane_dispatch_pack_result.get('blocked_dispatches', [])
    ready_event_names = control_plane_dispatch_pack_result.get('ready_event_names', [])
    blocked_event_names = control_plane_dispatch_pack_result.get('blocked_event_names', [])
    dispatch_batches = control_plane_dispatch_pack_result.get('dispatch_batches', {})
    priority_queue = control_plane_dispatch_pack_result.get('priority_queue', [])
    escalation_queue = control_plane_dispatch_pack_result.get('escalation_queue', [])
    blocker_summary = control_plane_dispatch_pack_result.get('blocker_summary', {})

    execution_ready_actions = []
    blocked_executions = []
    execution_batches = {
        'execution_proceed_batch': [],
        'execution_review_batch': [],
        'execution_hold_batch': [],
        'execution_escalation_batch': []
    }

    for action in dispatch_ready_actions:
        event_name = action.get('event_name')
        event_status = action.get('event_status')
        priority = action.get('priority')
        dispatch_batch = action.get('dispatch_batch')
        dispatch_reason = action.get('dispatch_reason')
        next_action = action.get('next_action')
        next_reason = action.get('next_reason')
        source_card = action.get('source_card')
        queue_snapshot = action.get('queue_snapshot')
        # Map dispatch_batch to execution_batch
        if dispatch_batch == 'dispatch_proceed_batch':
            execution_batch = 'execution_proceed_batch'
            execution_reason = 'Proceed batch for ready events'
        elif dispatch_batch == 'dispatch_review_batch':
            execution_batch = 'execution_review_batch'
            execution_reason = 'Review batch for operator review events'
        elif dispatch_batch == 'dispatch_hold_batch':
            execution_batch = 'execution_hold_batch'
            execution_reason = 'Hold batch for manual intervention events'
        elif dispatch_batch == 'dispatch_escalation_batch':
            execution_batch = 'execution_escalation_batch'
            execution_reason = 'Escalation batch for escalated events'
        else:
            execution_batch = 'execution_hold_batch'
            execution_reason = f'Unknown dispatch_batch: {dispatch_batch}, defaulting to hold'
        exec_action = {
            'event_name': event_name,
            'event_status': event_status,
            'priority': priority,
            'execution_batch': execution_batch,
            'execution_reason': execution_reason,
            'dispatch_batch': dispatch_batch,
            'dispatch_reason': dispatch_reason,
            'next_action': next_action,
            'next_reason': next_reason,
            'source_card': source_card,
            'queue_snapshot': queue_snapshot
        }
        execution_ready_actions.append(exec_action)
        execution_batches[execution_batch].append(exec_action)

    for blocked in blocked_dispatches:
        event_name = blocked.get('event_name')
        event_status = blocked.get('event_status')
        priority = blocked.get('priority')
        blocker_reason = blocked.get('blocker_reason', 'Blocked at execution')
        queue_snapshot = blocked.get('queue_snapshot')
        blocked_executions.append({
            'event_name': event_name,
            'event_status': event_status,
            'priority': priority,
            'blocker_reason': blocker_reason,
            'queue_snapshot': queue_snapshot
        })

    # Status rule
    if execution_ready_actions and not blocked_executions:
        execution_status = 'ready'
    elif execution_ready_actions and blocked_executions:
        execution_status = 'partial'
    else:
        execution_status = 'blocked'

    control_plane_execution_summary = {
        'execution_status': execution_status,
        'event_count': event_count,
        'execution_ready_count': len(execution_ready_actions),
        'blocked_execution_count': len(blocked_executions),
        'ready_event_names': ready_event_names,
        'blocked_event_names': blocked_event_names,
        'execution_batches': {k: [a['event_name'] for a in v] for k, v in execution_batches.items()},
        'priority_queue': priority_queue,
        'escalation_queue': escalation_queue,
        'blocker_summary': blocker_summary
    }

    return {
        'control_plane_execution_status': execution_status,
        'event_count': event_count,
        'execution_ready_actions': execution_ready_actions,
        'blocked_executions': blocked_executions,
        'ready_event_names': ready_event_names,
        'blocked_event_names': blocked_event_names,
        'execution_batches': execution_batches,
        'priority_queue': priority_queue,
        'escalation_queue': escalation_queue,
        'blocker_summary': blocker_summary,
        'control_plane_execution_summary': control_plane_execution_summary
    }
