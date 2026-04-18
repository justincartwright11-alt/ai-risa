"""
AI-RISA system_status_pack workflow
Consumes remediation_outcome_pack_result and emits a deterministic event-level system status bundle.
"""

def system_status_pack(remediation_outcome_pack_result):
    """
    Args:
        remediation_outcome_pack_result (dict):
            {
                'event_name': str,
                'remediation_outcome_status': str,
                'completed_remediations': list,
                'blocked_remediation_outcomes': list,
                'ready_bout_indices': list,
                'blocked_bout_indices': list,
                'blocker_summary': dict,
                'remediation_outcome_summary': dict
            }
    Returns:
        dict: {
            'event_name': str,
            'system_status': str,
            'ready_bout_indices': list,
            'blocked_bout_indices': list,
            'completed_bout_indices': list,
            'blocked_bout_count': int,
            'completed_bout_count': int,
            'blocker_summary': dict,
            'system_status_summary': dict,
            'system_status_entries': list
        }
    """
    event_name = remediation_outcome_pack_result['event_name']
    ready_bout_indices = remediation_outcome_pack_result.get('ready_bout_indices', [])
    blocked_bout_indices = remediation_outcome_pack_result.get('blocked_bout_indices', [])
    completed_bout_indices = remediation_outcome_pack_result.get('completed_remediations', [])
    blocked_bout_count = len(blocked_bout_indices)
    completed_bout_count = len(completed_bout_indices)
    blocker_summary = remediation_outcome_pack_result.get('blocker_summary', {})
    remediation_outcome_summary = remediation_outcome_pack_result.get('remediation_outcome_summary', {})

    # Status rule
    if ready_bout_indices and not blocked_bout_indices:
        system_status = 'ready'
    elif ready_bout_indices and blocked_bout_indices:
        system_status = 'partial'
    else:
        system_status = 'blocked'

    # Compose system_status_entries
    system_status_entries = []
    for idx in ready_bout_indices:
        entry = {
            'event_name': event_name,
            'bout_index': idx,
            'system_state': 'ready',
            'delivery_key': remediation_outcome_summary.get('delivery_key', {}).get(idx),
            'publication_label': remediation_outcome_summary.get('publication_label', {}).get(idx),
            'publication_order': remediation_outcome_summary.get('publication_order', {}).get(idx),
            'outcome_state': 'completed',
            'final_resolution': remediation_outcome_summary.get('final_resolution', {}).get(idx),
            'remediation_snapshot': remediation_outcome_summary.get('remediation_snapshot', {}).get(idx)
        }
        system_status_entries.append(entry)
    for idx in blocked_bout_indices:
        entry = {
            'event_name': event_name,
            'bout_index': idx,
            'system_state': 'blocked',
            'blocker_reason': blocker_summary.get('blocker_reason', {}).get(idx),
            'remediation_snapshot': remediation_outcome_summary.get('remediation_snapshot', {}).get(idx)
        }
        system_status_entries.append(entry)

    system_status_summary = {
        'system_status': system_status,
        'ready_count': len(ready_bout_indices),
        'blocked_count': blocked_bout_count,
        'completed_count': completed_bout_count
    }

    return {
        'event_name': event_name,
        'system_status': system_status,
        'ready_bout_indices': ready_bout_indices,
        'blocked_bout_indices': blocked_bout_indices,
        'completed_bout_indices': completed_bout_indices,
        'blocked_bout_count': blocked_bout_count,
        'completed_bout_count': completed_bout_count,
        'blocker_summary': blocker_summary,
        'system_status_summary': system_status_summary,
        'system_status_entries': system_status_entries
    }
