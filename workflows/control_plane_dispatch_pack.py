"""
control_plane_dispatch_pack

Consumes control_plane_action_queue_pack output and emits a deterministic dispatch-ready control-plane bundle.
"""

def control_plane_dispatch_pack(control_plane_action_queue_pack_result):
    """
    Args:
        control_plane_action_queue_pack_result (dict): Output from control_plane_action_queue_pack
    Returns:
        dict: Control plane dispatch artifact
    """
    queue_status = control_plane_action_queue_pack_result.get('control_plane_action_queue_status', 'unknown')
    event_count = control_plane_action_queue_pack_result.get('event_count', 0)
    queued_actions = control_plane_action_queue_pack_result.get('queued_actions', [])
    blocked_actions = control_plane_action_queue_pack_result.get('blocked_actions', [])
    ready_event_names = control_plane_action_queue_pack_result.get('ready_event_names', [])
    blocked_event_names = control_plane_action_queue_pack_result.get('blocked_event_names', [])
    priority_queue = control_plane_action_queue_pack_result.get('priority_queue', [])
    escalation_queue = control_plane_action_queue_pack_result.get('escalation_queue', [])
    blocker_summary = control_plane_action_queue_pack_result.get('blocker_summary', {})

    dispatch_ready_actions = []
    blocked_dispatches = []
    dispatch_batches = {
        'dispatch_proceed_batch': [],
        'dispatch_review_batch': [],
        'dispatch_hold_batch': [],
        'dispatch_escalation_batch': []
    }

    for action in queued_actions:
        event_name = action.get('event_name')
        event_status = action.get('event_status')
        priority = action.get('priority')
        queue_action = action.get('queue_action')
        queue_reason = action.get('queue_reason')
        next_action = action.get('next_action')
        next_reason = action.get('next_reason')
        source_card = action.get('source_card')
        queue_snapshot = dict(action)
        # Map queue_action to dispatch_batch
        if queue_action == 'queue_proceed':
            dispatch_batch = 'dispatch_proceed_batch'
            dispatch_reason = 'Proceed batch for ready events'
        elif queue_action == 'queue_review':
            dispatch_batch = 'dispatch_review_batch'
            dispatch_reason = 'Review batch for operator review events'
        elif queue_action == 'queue_hold':
            dispatch_batch = 'dispatch_hold_batch'
            dispatch_reason = 'Hold batch for manual intervention events'
        elif queue_action == 'queue_escalate':
            dispatch_batch = 'dispatch_escalation_batch'
            dispatch_reason = 'Escalation batch for escalated events'
        else:
            dispatch_batch = 'dispatch_hold_batch'
            dispatch_reason = f'Unknown queue_action: {queue_action}, defaulting to hold'
        dispatch_action = {
            'event_name': event_name,
            'event_status': event_status,
            'priority': priority,
            'queue_action': queue_action,
            'queue_reason': queue_reason,
            'dispatch_batch': dispatch_batch,
            'dispatch_reason': dispatch_reason,
            'next_action': next_action,
            'next_reason': next_reason,
            'source_card': source_card,
            'queue_snapshot': queue_snapshot
        }
        dispatch_ready_actions.append(dispatch_action)
        dispatch_batches[dispatch_batch].append(dispatch_action)

    for blocked in blocked_actions:
        event_name = blocked.get('event_name')
        event_status = blocked.get('event_status')
        priority = blocked.get('priority')
        blocker_reason = blocked.get('blocker_reason', 'Blocked at dispatch')
        queue_snapshot = dict(blocked)
        blocked_dispatches.append({
            'event_name': event_name,
            'event_status': event_status,
            'priority': priority,
            'blocker_reason': blocker_reason,
            'queue_snapshot': queue_snapshot
        })

    # Status rule
    if dispatch_ready_actions and not blocked_dispatches:
        dispatch_status = 'ready'
    elif dispatch_ready_actions and blocked_dispatches:
        dispatch_status = 'partial'
    else:
        dispatch_status = 'blocked'

    control_plane_dispatch_summary = {
        'dispatch_status': dispatch_status,
        'event_count': event_count,
        'dispatch_ready_count': len(dispatch_ready_actions),
        'blocked_dispatch_count': len(blocked_dispatches),
        'ready_event_names': ready_event_names,
        'blocked_event_names': blocked_event_names,
        'dispatch_batches': {k: [a['event_name'] for a in v] for k, v in dispatch_batches.items()},
        'priority_queue': priority_queue,
        'escalation_queue': escalation_queue,
        'blocker_summary': blocker_summary
    }

    return {
        'control_plane_dispatch_status': dispatch_status,
        'event_count': event_count,
        'dispatch_ready_actions': dispatch_ready_actions,
        'blocked_dispatches': blocked_dispatches,
        'ready_event_names': ready_event_names,
        'blocked_event_names': blocked_event_names,
        'dispatch_batches': dispatch_batches,
        'priority_queue': priority_queue,
        'escalation_queue': escalation_queue,
        'blocker_summary': blocker_summary,
        'control_plane_dispatch_summary': control_plane_dispatch_summary
    }
