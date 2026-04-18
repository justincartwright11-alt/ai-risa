"""
AI-RISA automation_reconciliation_pack workflow
Consumes automation_execution_pack output and emits deterministic automation reconciliation bundle.
"""

def automation_reconciliation_pack(automation_execution_pack_result):
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
            'automation_reconciliation_status': str,
            'reconciled_actions': list,
            'blocked_reconciliations': list,
            'ready_bout_indices': list,
            'blocked_bout_indices': list,
            'blocker_summary': dict,
            'automation_reconciliation_summary': dict
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
        automation_reconciliation_status = 'ready'
    elif execution_ready_actions and blocked_executions:
        automation_reconciliation_status = 'partial'
    else:
        automation_reconciliation_status = 'blocked'

    reconciled_actions = []
    for action in execution_ready_actions:
        reconciled_actions.append({
            'event_name': event_name,
            'bout_index': action['bout_index'],
            'reconciliation_status': 'ready',
            'delivery_key': action.get('delivery_key'),
            'publication_label': action.get('publication_label'),
            'publication_order': action.get('publication_order'),
            'queue_action': action.get('queue_action'),
            'dispatch_batch': action.get('dispatch_batch'),
            'execution_status': action.get('execution_status'),
            'execution_plan': action.get('execution_plan'),
            'execution_snapshot': action
        })

    blocked_reconciliations = []
    for action in blocked_executions:
        blocked_reconciliations.append({
            'event_name': event_name,
            'bout_index': action['bout_index'],
            'reconciliation_status': 'blocked',
            'blocker_reason': action.get('blocker_reason'),
            'execution_snapshot': action
        })

    automation_reconciliation_summary = {
        'automation_reconciliation_status': automation_reconciliation_status,
        'reconciled_count': len(reconciled_actions),
        'blocked_reconciliation_count': len(blocked_reconciliations)
    }

    return {
        'event_name': event_name,
        'automation_reconciliation_status': automation_reconciliation_status,
        'reconciled_actions': reconciled_actions,
        'blocked_reconciliations': blocked_reconciliations,
        'ready_bout_indices': ready_bout_indices,
        'blocked_bout_indices': blocked_bout_indices,
        'blocker_summary': blocker_summary,
        'automation_reconciliation_summary': automation_reconciliation_summary
    }
