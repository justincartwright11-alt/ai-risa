"""
AI-RISA automation_state_ledger_pack workflow
Consumes automation_outcome_pack output and emits deterministic automation state ledger bundle.
"""

def automation_state_ledger_pack(automation_outcome_pack_result):
    """
    Args:
        automation_outcome_pack_result (dict):
            {
                'event_name': str,
                'automation_outcome_status': str,
                'completed_automation_actions': list,
                'blocked_automation_outcomes': list,
                'ready_bout_indices': list,
                'blocked_bout_indices': list,
                'blocker_summary': dict,
                'automation_outcome_summary': dict
            }
    Returns:
        dict: {
            'event_name': str,
            'automation_state_ledger_status': str,
            'ledger_entries': list,
            'blocked_ledger_entries': list,
            'ready_bout_indices': list,
            'blocked_bout_indices': list,
            'blocker_summary': dict,
            'automation_state_ledger_summary': dict
        }
    """
    event_name = automation_outcome_pack_result['event_name']
    completed_automation_actions = automation_outcome_pack_result.get('completed_automation_actions', [])
    blocked_automation_outcomes = automation_outcome_pack_result.get('blocked_automation_outcomes', [])
    ready_bout_indices = automation_outcome_pack_result.get('ready_bout_indices', [])
    blocked_bout_indices = automation_outcome_pack_result.get('blocked_bout_indices', [])
    blocker_summary = automation_outcome_pack_result.get('blocker_summary', {})

    # Status rule
    if completed_automation_actions and not blocked_automation_outcomes:
        automation_state_ledger_status = 'ready'
    elif completed_automation_actions and blocked_automation_outcomes:
        automation_state_ledger_status = 'partial'
    else:
        automation_state_ledger_status = 'blocked'

    ledger_entries = []
    for action in completed_automation_actions:
        ledger_entries.append({
            'event_name': event_name,
            'bout_index': action['bout_index'],
            'ledger_status': 'ready',
            'delivery_key': action.get('delivery_key'),
            'publication_label': action.get('publication_label'),
            'publication_order': action.get('publication_order'),
            'automation_outcome_state': action.get('automation_outcome_state'),
            'queue_action': action.get('queue_action'),
            'dispatch_batch': action.get('dispatch_batch'),
            'execution_plan': action.get('execution_plan'),
            'execution_snapshot': action.get('execution_snapshot'),
            'automation_outcome_snapshot': action
        })

    blocked_ledger_entries = []
    for action in blocked_automation_outcomes:
        blocked_ledger_entries.append({
            'event_name': event_name,
            'bout_index': action['bout_index'],
            'ledger_status': 'blocked',
            'blocker_reason': action.get('blocker_reason'),
            'automation_outcome_snapshot': action
        })

    automation_state_ledger_summary = {
        'automation_state_ledger_status': automation_state_ledger_status,
        'ledger_ready_count': len(ledger_entries),
        'blocked_count': len(blocked_ledger_entries)
    }

    return {
        'event_name': event_name,
        'automation_state_ledger_status': automation_state_ledger_status,
        'ledger_entries': ledger_entries,
        'blocked_ledger_entries': blocked_ledger_entries,
        'ready_bout_indices': ready_bout_indices,
        'blocked_bout_indices': blocked_bout_indices,
        'blocker_summary': blocker_summary,
        'automation_state_ledger_summary': automation_state_ledger_summary
    }
