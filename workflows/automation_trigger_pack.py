"""
AI-RISA automation_trigger_pack workflow
Consumes system_status_pack output and emits deterministic automation trigger bundle.
"""

def automation_trigger_pack(system_status_pack_result):
    """
    Args:
        system_status_pack_result (dict):
            {
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
    Returns:
        dict: {
            'event_name': str,
            'automation_trigger_status': str,
            'ready_triggers': list,
            'blocked_triggers': list,
            'ready_bout_indices': list,
            'blocked_bout_indices': list,
            'blocker_summary': dict,
            'automation_trigger_summary': dict
        }
    """
    event_name = system_status_pack_result['event_name']
    ready_bout_indices = system_status_pack_result.get('ready_bout_indices', [])
    blocked_bout_indices = system_status_pack_result.get('blocked_bout_indices', [])
    blocker_summary = system_status_pack_result.get('blocker_summary', {})
    system_status_entries = system_status_pack_result.get('system_status_entries', [])

    # Status rule
    if ready_bout_indices and not blocked_bout_indices:
        automation_trigger_status = 'ready'
    elif ready_bout_indices and blocked_bout_indices:
        automation_trigger_status = 'partial'
    else:
        automation_trigger_status = 'blocked'

    ready_triggers = []
    blocked_triggers = []
    for entry in system_status_entries:
        idx = entry['bout_index']
        snapshot = entry
        if entry.get('system_state') == 'ready':
            ready_triggers.append({
                'event_name': event_name,
                'bout_index': idx,
                'trigger_status': 'ready',
                'delivery_key': entry.get('delivery_key'),
                'publication_label': entry.get('publication_label'),
                'publication_order': entry.get('publication_order'),
                'system_state': entry.get('system_state'),
                'trigger_action': 'proceed',
                'trigger_reason': 'automation-ready',
                'system_status_snapshot': snapshot
            })
        elif entry.get('system_state') == 'blocked':
            blocked_triggers.append({
                'event_name': event_name,
                'bout_index': idx,
                'trigger_status': 'blocked',
                'blocker_reason': entry.get('blocker_reason'),
                'system_status_snapshot': snapshot
            })

    automation_trigger_summary = {
        'automation_trigger_status': automation_trigger_status,
        'ready_count': len(ready_triggers),
        'blocked_count': len(blocked_triggers)
    }

    return {
        'event_name': event_name,
        'automation_trigger_status': automation_trigger_status,
        'ready_triggers': ready_triggers,
        'blocked_triggers': blocked_triggers,
        'ready_bout_indices': ready_bout_indices,
        'blocked_bout_indices': blocked_bout_indices,
        'blocker_summary': blocker_summary,
        'automation_trigger_summary': automation_trigger_summary
    }
