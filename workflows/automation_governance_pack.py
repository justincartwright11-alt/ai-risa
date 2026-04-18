"""
AI-RISA automation_governance_pack workflow
Consumes automation_state_ledger_pack output and emits deterministic automation governance bundle.
"""

def automation_governance_pack(automation_state_ledger_pack_result):
    """
    Args:
        automation_state_ledger_pack_result (dict):
            {
                'event_name': str,
                'automation_state_ledger_status': str,
                'ledger_entries': list,
                'blocked_ledger_entries': list,
                'ready_bout_indices': list,
                'blocked_bout_indices': list,
                'blocker_summary': dict,
                'automation_state_ledger_summary': dict
            }
    Returns:
        dict: {
            'event_name': str,
            'automation_governance_status': str,
            'governance_ready_entries': list,
            'blocked_governance_entries': list,
            'ready_bout_indices': list,
            'blocked_bout_indices': list,
            'blocker_summary': dict,
            'escalation_flags': dict,
            'automation_governance_summary': dict
        }
    """
    event_name = automation_state_ledger_pack_result['event_name']
    ledger_entries = automation_state_ledger_pack_result.get('ledger_entries', [])
    blocked_ledger_entries = automation_state_ledger_pack_result.get('blocked_ledger_entries', [])
    ready_bout_indices = automation_state_ledger_pack_result.get('ready_bout_indices', [])
    blocked_bout_indices = automation_state_ledger_pack_result.get('blocked_bout_indices', [])
    blocker_summary = automation_state_ledger_pack_result.get('blocker_summary', {})

    # Status rule
    if ledger_entries and not blocked_ledger_entries:
        automation_governance_status = 'ready'
    elif ledger_entries and blocked_ledger_entries:
        automation_governance_status = 'partial'
    else:
        automation_governance_status = 'blocked'

    governance_ready_entries = []
    escalation_flags = {}
    for entry in ledger_entries:
        # Deterministic governance logic: escalate if publication_label == 'ESCALATE', else proceed
        label = entry.get('publication_label')
        if label == 'ESCALATE':
            action = 'escalate'
            reason = 'label-triggered escalation'
            escalation_level = 'operator_review'
        else:
            action = 'proceed'
            reason = 'default-proceed'
            escalation_level = 'none'
        governance_ready_entries.append({
            'event_name': event_name,
            'bout_index': entry['bout_index'],
            'governance_status': 'ready',
            'delivery_key': entry.get('delivery_key'),
            'publication_label': label,
            'publication_order': entry.get('publication_order'),
            'ledger_status': entry.get('ledger_status'),
            'governance_action': action,
            'governance_reason': reason,
            'escalation_level': escalation_level,
            'automation_state_snapshot': entry
        })
        escalation_flags[entry['bout_index']] = escalation_level

    blocked_governance_entries = []
    for entry in blocked_ledger_entries:
        blocked_governance_entries.append({
            'event_name': event_name,
            'bout_index': entry['bout_index'],
            'governance_status': 'blocked',
            'blocker_reason': entry.get('blocker_reason'),
            'escalation_level': 'manual_intervention',
            'automation_state_snapshot': entry
        })
        escalation_flags[entry['bout_index']] = 'manual_intervention'

    automation_governance_summary = {
        'automation_governance_status': automation_governance_status,
        'governance_ready_count': len(governance_ready_entries),
        'blocked_count': len(blocked_governance_entries)
    }

    return {
        'event_name': event_name,
        'automation_governance_status': automation_governance_status,
        'governance_ready_entries': governance_ready_entries,
        'blocked_governance_entries': blocked_governance_entries,
        'ready_bout_indices': ready_bout_indices,
        'blocked_bout_indices': blocked_bout_indices,
        'blocker_summary': blocker_summary,
        'escalation_flags': escalation_flags,
        'automation_governance_summary': automation_governance_summary
    }
