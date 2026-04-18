"""
AI-RISA automation_action_queue_pack workflow
Consumes automation_trigger_pack output and emits deterministic automation action queue bundle.
"""

def automation_action_queue_pack(automation_trigger_pack_result):
    """
    Args:
        automation_trigger_pack_result (dict):
            {
                'event_name': str,
                'automation_trigger_status': str,
                'ready_triggers': list,
                'blocked_triggers': list,
                'ready_bout_indices': list,
                'blocked_bout_indices': list,
                'blocker_summary': dict,
                'automation_trigger_summary': dict
            }
    Returns:
        dict: {
            'event_name': str,
            'automation_action_queue_status': str,
            'queued_actions': list,
            'blocked_actions': list,
            'ready_bout_indices': list,
            'blocked_bout_indices': list,
            'blocker_summary': dict,
            'automation_action_queue_summary': dict
        }
    """
    event_name = automation_trigger_pack_result['event_name']
    ready_triggers = automation_trigger_pack_result.get('ready_triggers', [])
    blocked_triggers = automation_trigger_pack_result.get('blocked_triggers', [])
    ready_bout_indices = automation_trigger_pack_result.get('ready_bout_indices', [])
    blocked_bout_indices = automation_trigger_pack_result.get('blocked_bout_indices', [])
    blocker_summary = automation_trigger_pack_result.get('blocker_summary', {})

    # Status rule
    if ready_triggers and not blocked_triggers:
        automation_action_queue_status = 'ready'
    elif ready_triggers and blocked_triggers:
        automation_action_queue_status = 'partial'
    else:
        automation_action_queue_status = 'blocked'

    queued_actions = []
    for trig in ready_triggers:
        queued_actions.append({
            'event_name': event_name,
            'bout_index': trig['bout_index'],
            'queue_status': 'queued',
            'delivery_key': trig.get('delivery_key'),
            'publication_label': trig.get('publication_label'),
            'publication_order': trig.get('publication_order'),
            'trigger_action': trig.get('trigger_action'),
            'trigger_reason': trig.get('trigger_reason'),
            'queue_action': 'enqueue',
            'queue_priority': 1,  # deterministic for now
            'automation_trigger_snapshot': trig
        })

    blocked_actions = []
    for trig in blocked_triggers:
        blocked_actions.append({
            'event_name': event_name,
            'bout_index': trig['bout_index'],
            'queue_status': 'blocked',
            'blocker_reason': trig.get('blocker_reason'),
            'automation_trigger_snapshot': trig
        })

    automation_action_queue_summary = {
        'automation_action_queue_status': automation_action_queue_status,
        'queued_count': len(queued_actions),
        'blocked_count': len(blocked_actions)
    }

    return {
        'event_name': event_name,
        'automation_action_queue_status': automation_action_queue_status,
        'queued_actions': queued_actions,
        'blocked_actions': blocked_actions,
        'ready_bout_indices': ready_bout_indices,
        'blocked_bout_indices': blocked_bout_indices,
        'blocker_summary': blocker_summary,
        'automation_action_queue_summary': automation_action_queue_summary
    }
