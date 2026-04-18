"""
control_plane_outcome_pack

Consumes control_plane_execution_pack output and emits a deterministic control-plane outcome artifact.
"""

def control_plane_outcome_pack(control_plane_execution_pack_result):
    """
    Args:
        control_plane_execution_pack_result (dict): Output from control_plane_execution_pack
    Returns:
        dict: Control plane outcome artifact
    """
    execution_status = control_plane_execution_pack_result.get('control_plane_execution_status', 'unknown')
    event_count = control_plane_execution_pack_result.get('event_count', 0)
    execution_ready_actions = control_plane_execution_pack_result.get('execution_ready_actions', [])
    blocked_executions = control_plane_execution_pack_result.get('blocked_executions', [])
    ready_event_names = control_plane_execution_pack_result.get('ready_event_names', [])
    blocked_event_names = control_plane_execution_pack_result.get('blocked_event_names', [])
    execution_batches = control_plane_execution_pack_result.get('execution_batches', {})
    priority_queue = control_plane_execution_pack_result.get('priority_queue', [])
    escalation_queue = control_plane_execution_pack_result.get('escalation_queue', [])
    blocker_summary = control_plane_execution_pack_result.get('blocker_summary', {})

    completed_actions = []
    blocked_outcomes = []
    outcome_batches = {
        'complete_proceed_batch': [],
        'complete_review_batch': [],
        'complete_hold_batch': [],
        'complete_escalation_batch': []
    }

    for action in execution_ready_actions:
        event_name = action.get('event_name')
        event_status = action.get('event_status')
        priority = action.get('priority')
        queue_action = action.get('queue_action')
        queue_reason = action.get('queue_reason')
        dispatch_batch = action.get('dispatch_batch')
        dispatch_reason = action.get('dispatch_reason')
        execution_batch = action.get('execution_batch')
        execution_reason = action.get('execution_reason')
        source_card = action.get('source_card')
        execution_snapshot = dict(action)
        # Map execution_batch to outcome_batch
        if execution_batch == 'execution_proceed_batch':
            outcome_batch = 'complete_proceed_batch'
            outcome_reason = 'Completed proceed batch'
        elif execution_batch == 'execution_review_batch':
            outcome_batch = 'complete_review_batch'
            outcome_reason = 'Completed review batch'
        elif execution_batch == 'execution_hold_batch':
            outcome_batch = 'complete_hold_batch'
            outcome_reason = 'Completed hold batch'
        elif execution_batch == 'execution_escalation_batch':
            outcome_batch = 'complete_escalation_batch'
            outcome_reason = 'Completed escalation batch'
        else:
            outcome_batch = 'complete_hold_batch'
            outcome_reason = f'Unknown execution_batch: {execution_batch}, defaulting to hold'
        completed = {
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
            'source_card': source_card,
            'execution_snapshot': execution_snapshot
        }
        completed_actions.append(completed)
        outcome_batches[outcome_batch].append(completed)

    for blocked in blocked_executions:
        event_name = blocked.get('event_name')
        event_status = blocked.get('event_status')
        priority = blocked.get('priority')
        blocker_reason = blocked.get('blocker_reason', 'Blocked at outcome')
        execution_snapshot = blocked.get('queue_snapshot')
        blocked_outcomes.append({
            'event_name': event_name,
            'event_status': event_status,
            'priority': priority,
            'blocker_reason': blocker_reason,
            'execution_snapshot': execution_snapshot
        })

    # Status rule
    if completed_actions and not blocked_outcomes:
        outcome_status = 'ready'
    elif completed_actions and blocked_outcomes:
        outcome_status = 'partial'
    else:
        outcome_status = 'blocked'

    control_plane_outcome_summary = {
        'outcome_status': outcome_status,
        'event_count': event_count,
        'completed_count': len(completed_actions),
        'blocked_count': len(blocked_outcomes),
        'ready_event_names': ready_event_names,
        'blocked_event_names': blocked_event_names,
        'outcome_batches': {k: [a['event_name'] for a in v] for k, v in outcome_batches.items()},
        'priority_queue': priority_queue,
        'escalation_queue': escalation_queue,
        'blocker_summary': blocker_summary
    }

    return {
        'control_plane_outcome_status': outcome_status,
        'event_count': event_count,
        'completed_actions': completed_actions,
        'blocked_outcomes': blocked_outcomes,
        'ready_event_names': ready_event_names,
        'blocked_event_names': blocked_event_names,
        'outcome_batches': outcome_batches,
        'priority_queue': priority_queue,
        'escalation_queue': escalation_queue,
        'blocker_summary': blocker_summary,
        'control_plane_outcome_summary': control_plane_outcome_summary
    }
