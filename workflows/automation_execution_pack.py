"""
AI-RISA automation_execution_pack workflow
Consumes automation_dispatch_pack output and emits deterministic automation execution bundle.
"""

def automation_execution_pack(automation_dispatch_pack_result):
    """
    Args:
        automation_dispatch_pack_result (dict):
            {
                'event_name': str,
                'automation_dispatch_status': str,
                'dispatch_ready_actions': list,
                'blocked_dispatches': list,
                'ready_bout_indices': list,
                'blocked_bout_indices': list,
                'blocker_summary': dict,
                'automation_dispatch_summary': dict
            }
    Returns:
        dict: {
            'event_name': str,
            'automation_execution_status': str,
            'execution_ready_actions': list,
            'blocked_executions': list,
            'ready_bout_indices': list,
            'blocked_bout_indices': list,
            'blocker_summary': dict,
            'automation_execution_summary': dict
        }
    """
    event_name = automation_dispatch_pack_result['event_name']
    dispatch_ready_actions = automation_dispatch_pack_result.get('dispatch_ready_actions', [])
    blocked_dispatches = automation_dispatch_pack_result.get('blocked_dispatches', [])
    ready_bout_indices = automation_dispatch_pack_result.get('ready_bout_indices', [])
    blocked_bout_indices = automation_dispatch_pack_result.get('blocked_bout_indices', [])
    blocker_summary = automation_dispatch_pack_result.get('blocker_summary', {})

    # Status rule
    if dispatch_ready_actions and not blocked_dispatches:
        automation_execution_status = 'ready'
    elif dispatch_ready_actions and blocked_dispatches:
        automation_execution_status = 'partial'
    else:
        automation_execution_status = 'blocked'

    execution_ready_actions = []
    for action in dispatch_ready_actions:
        execution_ready_actions.append({
            'event_name': event_name,
            'bout_index': action['bout_index'],
            'execution_status': 'ready',
            'delivery_key': action.get('delivery_key'),
            'publication_label': action.get('publication_label'),
            'publication_order': action.get('publication_order'),
            'queue_action': action.get('queue_action'),
            'queue_priority': action.get('queue_priority'),
            'dispatch_batch': action.get('dispatch_batch'),
            'dispatch_reason': action.get('dispatch_reason'),
            'execution_plan': {'plan_type': 'default', 'steps': ['execute']},
            'dispatch_snapshot': action
        })

    blocked_executions = []
    for action in blocked_dispatches:
        blocked_executions.append({
            'event_name': event_name,
            'bout_index': action['bout_index'],
            'execution_status': 'blocked',
            'blocker_reason': action.get('blocker_reason'),
            'dispatch_snapshot': action
        })

    automation_execution_summary = {
        'automation_execution_status': automation_execution_status,
        'execution_ready_count': len(execution_ready_actions),
        'blocked_execution_count': len(blocked_executions)
    }

    return {
        'event_name': event_name,
        'automation_execution_status': automation_execution_status,
        'execution_ready_actions': execution_ready_actions,
        'blocked_executions': blocked_executions,
        'ready_bout_indices': ready_bout_indices,
        'blocked_bout_indices': blocked_bout_indices,
        'blocker_summary': blocker_summary,
        'automation_execution_summary': automation_execution_summary
    }
