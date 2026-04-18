"""
AI-RISA automation_outcome_pack workflow
Consumes automation_execution_pack output and emits deterministic automation outcome bundle.
"""

def automation_outcome_pack(automation_execution_pack_result):
    """
    Args:
        automation_execution_pack_result (dict):
            {
                'event_name': str,
                'automation_execution_status': str,
                'execution_ready_actions': list,
                'blocked_executions': list,
                'ready_bout_indices': list,
                'blocked_bout_indices': list,
                'blocker_summary': dict,
                'automation_execution_summary': dict
            }
    Returns:
        dict: {
            'event_name': str,
            'automation_outcome_status': str,
            'completed_automation_actions': list,
            'blocked_automation_outcomes': list,
            'ready_bout_indices': list,
            'blocked_bout_indices': list,
            'blocker_summary': dict,
            'automation_outcome_summary': dict
        }
    """
    event_name = automation_execution_pack_result['event_name']
    execution_ready_actions = automation_execution_pack_result.get('execution_ready_actions', [])
    blocked_executions = automation_execution_pack_result.get('blocked_executions', [])
    ready_bout_indices = automation_execution_pack_result.get('ready_bout_indices', [])
    blocked_bout_indices = automation_execution_pack_result.get('blocked_bout_indices', [])
    blocker_summary = automation_execution_pack_result.get('blocker_summary', {})

    # Status rule
    if execution_ready_actions and not blocked_executions:
        automation_outcome_status = 'ready'
    elif execution_ready_actions and blocked_executions:
        automation_outcome_status = 'partial'
    else:
        automation_outcome_status = 'blocked'

    completed_automation_actions = []
    for action in execution_ready_actions:
        completed_automation_actions.append({
            'event_name': event_name,
            'bout_index': action['bout_index'],
            'automation_outcome_state': 'completed',
            'delivery_key': action.get('delivery_key'),
            'publication_label': action.get('publication_label'),
            'publication_order': action.get('publication_order'),
            'queue_action': action.get('queue_action'),
            'queue_priority': action.get('queue_priority'),
            'dispatch_batch': action.get('dispatch_batch'),
            'execution_plan': action.get('execution_plan'),
            'dispatch_snapshot': action,
            'execution_snapshot': action
        })

    blocked_automation_outcomes = []
    for action in blocked_executions:
        blocked_automation_outcomes.append({
            'event_name': event_name,
            'bout_index': action['bout_index'],
            'automation_outcome_state': 'blocked',
            'blocker_reason': action.get('blocker_reason'),
            'execution_snapshot': action
        })

    automation_outcome_summary = {
        'automation_outcome_status': automation_outcome_status,
        'completed_count': len(completed_automation_actions),
        'blocked_count': len(blocked_automation_outcomes)
    }

    return {
        'event_name': event_name,
        'automation_outcome_status': automation_outcome_status,
        'completed_automation_actions': completed_automation_actions,
        'blocked_automation_outcomes': blocked_automation_outcomes,
        'ready_bout_indices': ready_bout_indices,
        'blocked_bout_indices': blocked_bout_indices,
        'blocker_summary': blocker_summary,
        'automation_outcome_summary': automation_outcome_summary
    }
