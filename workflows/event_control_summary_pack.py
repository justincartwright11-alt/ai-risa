"""
AI-RISA event_control_summary_pack workflow
Consumes automation_closure_pack output and emits deterministic event-level control summary.
"""

def event_control_summary_pack(automation_closure_pack_result):
    """
    Args:
        automation_closure_pack_result (dict):
            {
                'event_name': str,
                'automation_closure_status': str,
                'closed_entries': list,
                'pending_entries': list,
                'ready_bout_indices': list,
                'blocked_bout_indices': list,
                'blocker_summary': dict,
                'automation_closure_summary': dict
            }
    Returns:
        dict: {
            'event_name': str,
            'event_control_status': str,
            'total_bouts': int,
            'publish_ready_count': int,
            'review_required_count': int,
            'manual_intervention_count': int,
            'blocked_count': int,
            'ready_bout_indices': list,
            'blocked_bout_indices': list,
            'blocker_summary': dict,
            'decision_summary': dict,
            'event_control_summary': dict
        }
    """
    event_name = automation_closure_pack_result['event_name']
    closed_entries = automation_closure_pack_result.get('closed_entries', [])
    pending_entries = automation_closure_pack_result.get('pending_entries', [])
    ready_bout_indices = automation_closure_pack_result.get('ready_bout_indices', [])
    blocked_bout_indices = automation_closure_pack_result.get('blocked_bout_indices', [])
    blocker_summary = automation_closure_pack_result.get('blocker_summary', {})

    publish_ready_count = 0
    review_required_count = 0
    manual_intervention_count = 0
    blocked_count = len(pending_entries)
    total_bouts = len(closed_entries) + len(pending_entries)

    for entry in closed_entries:
        action = entry.get('closure_action')
        if action == 'close':
            publish_ready_count += 1
        elif action == 'hold_open':
            review_required_count += 1
        elif action == 'escalate_followup':
            manual_intervention_count += 1

    # Status rule
    if publish_ready_count == total_bouts and total_bouts > 0:
        event_control_status = 'ready'
    elif publish_ready_count > 0:
        event_control_status = 'partial'
    else:
        event_control_status = 'blocked'

    decision_summary = {
        'publish_ready_count': publish_ready_count,
        'review_required_count': review_required_count,
        'manual_intervention_count': manual_intervention_count,
        'blocked_count': blocked_count
    }

    event_control_summary = {
        'event_control_status': event_control_status,
        'total_bouts': total_bouts,
        'decision_summary': decision_summary
    }

    return {
        'event_name': event_name,
        'event_control_status': event_control_status,
        'total_bouts': total_bouts,
        'publish_ready_count': publish_ready_count,
        'review_required_count': review_required_count,
        'manual_intervention_count': manual_intervention_count,
        'blocked_count': blocked_count,
        'ready_bout_indices': ready_bout_indices,
        'blocked_bout_indices': blocked_bout_indices,
        'blocker_summary': blocker_summary,
        'decision_summary': decision_summary,
        'event_control_summary': event_control_summary
    }
