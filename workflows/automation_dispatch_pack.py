"""
AI-RISA automation_dispatch_pack workflow
Consumes automation_action_queue_pack output and emits deterministic automation dispatch bundle.
"""

def automation_dispatch_pack(automation_action_queue_pack_result):
    """
    Args:
        automation_action_queue_pack_result (dict):
            {
                'event_name': str,
                'automation_action_queue_status': str,
                'queued_actions': list,
                'blocked_actions': list,
                'ready_bout_indices': list,
                'blocked_bout_indices': list,
                'blocker_summary': dict,
                'automation_action_queue_summary': dict
            }
    Returns:
        dict: {
            'event_name': str,
            'automation_dispatch_status': str,
            'dispatch_ready_actions': list,
            'blocked_dispatches': list,
            'ready_bout_indices': list,
            'blocked_bout_indices': list,
            'blocker_summary': dict,
            'automation_dispatch_summary': dict
        }
    """
    event_name = automation_action_queue_pack_result['event_name']
    queued_actions = automation_action_queue_pack_result.get('queued_actions', [])
    blocked_actions = automation_action_queue_pack_result.get('blocked_actions', [])
    ready_bout_indices = automation_action_queue_pack_result.get('ready_bout_indices', [])
    blocked_bout_indices = automation_action_queue_pack_result.get('blocked_bout_indices', [])
    blocker_summary = automation_action_queue_pack_result.get('blocker_summary', {})

    # Status rule
    if queued_actions and not blocked_actions:
        automation_dispatch_status = 'ready'
    elif queued_actions and blocked_actions:
        automation_dispatch_status = 'partial'
    else:
        automation_dispatch_status = 'blocked'

    dispatch_ready_actions = []
    for action in queued_actions:
        dispatch_ready_actions.append({
            'event_name': event_name,
            'bout_index': action['bout_index'],
            'dispatch_status': 'ready',
            'delivery_key': action.get('delivery_key'),
            'publication_label': action.get('publication_label'),
            'publication_order': action.get('publication_order'),
            'queue_action': action.get('queue_action'),
            'queue_priority': action.get('queue_priority'),
            'dispatch_batch': action.get('dispatch_batch', 1),
            'dispatch_reason': action.get('dispatch_reason', 'dispatch-ready'),
            'automation_trigger_snapshot': action.get('automation_trigger_snapshot', action)
        })

    blocked_dispatches = []
    for action in blocked_actions:
        blocked_dispatches.append({
            'event_name': event_name,
            'bout_index': action['bout_index'],
            'dispatch_status': 'blocked',
            'blocker_reason': action.get('blocker_reason'),
            'automation_trigger_snapshot': action.get('automation_trigger_snapshot', action)
        })

    automation_dispatch_summary = {
        'automation_dispatch_status': automation_dispatch_status,
        'dispatch_ready_count': len(dispatch_ready_actions),
        'blocked_dispatch_count': len(blocked_dispatches)
    }

    return {
        'event_name': event_name,
        'automation_dispatch_status': automation_dispatch_status,
        'dispatch_ready_actions': dispatch_ready_actions,
        'blocked_dispatches': blocked_dispatches,
        'ready_bout_indices': ready_bout_indices,
        'blocked_bout_indices': blocked_bout_indices,
        'blocker_summary': blocker_summary,
        'automation_dispatch_summary': automation_dispatch_summary
    }
