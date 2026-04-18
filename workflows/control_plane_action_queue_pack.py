"""
control_plane_action_queue_pack

Consumes control_plane_dashboard_pack output and emits a deterministic operator workload queue artifact.
"""

def control_plane_action_queue_pack(control_plane_dashboard_pack_result):
    """
    Args:
        control_plane_dashboard_pack_result (dict): Output from control_plane_dashboard_pack
    Returns:
        dict: Control plane action queue artifact
    """
    dashboard_status = control_plane_dashboard_pack_result.get('control_plane_dashboard_status', 'unknown')
    event_count = control_plane_dashboard_pack_result.get('event_count', 0)
    dashboard_cards = control_plane_dashboard_pack_result.get('dashboard_cards', [])
    ready_event_names = control_plane_dashboard_pack_result.get('ready_events', [])
    blocked_event_names = control_plane_dashboard_pack_result.get('blocked_events', [])
    priority_queue = control_plane_dashboard_pack_result.get('priority_queue', [])
    escalation_queue = control_plane_dashboard_pack_result.get('escalation_queue', [])
    dashboard_sections = control_plane_dashboard_pack_result.get('dashboard_sections', {})

    queued_actions = []
    blocked_actions = []
    blocker_summary = {}

    for card in dashboard_cards:
        event_name = card.get('event_name')
        event_status = card.get('event_status')
        priority = card.get('priority')
        next_action = card.get('next_action')
        next_reason = card.get('next_reason')
        # Map event_status to queue_action
        if event_status == 'ready':
            queue_action = 'queue_proceed'
            queue_reason = 'Event ready to proceed'
            queued_actions.append({
                'event_name': event_name,
                'event_status': event_status,
                'priority': priority,
                'queue_action': queue_action,
                'queue_reason': queue_reason,
                'next_action': next_action,
                'next_reason': next_reason,
                'source_card': card
            })
        elif event_status == 'partial':
            queue_action = 'queue_review'
            queue_reason = 'Event requires operator review'
            queued_actions.append({
                'event_name': event_name,
                'event_status': event_status,
                'priority': priority,
                'queue_action': queue_action,
                'queue_reason': queue_reason,
                'next_action': next_action,
                'next_reason': next_reason,
                'source_card': card
            })
        elif event_status == 'manual_intervention':
            queue_action = 'queue_hold'
            queue_reason = 'Manual intervention required'
            queued_actions.append({
                'event_name': event_name,
                'event_status': event_status,
                'priority': priority,
                'queue_action': queue_action,
                'queue_reason': queue_reason,
                'next_action': next_action,
                'next_reason': next_reason,
                'source_card': card
            })
        elif event_status == 'blocked':
            blocker_reason = 'Event is blocked'
            blocked_actions.append({
                'event_name': event_name,
                'event_status': event_status,
                'priority': priority,
                'blocker_reason': blocker_reason,
                'source_card': card
            })
            blocker_summary[event_name] = blocker_reason
        else:
            blocker_reason = f'Unknown event status: {event_status}'
            blocked_actions.append({
                'event_name': event_name,
                'event_status': event_status,
                'priority': priority,
                'blocker_reason': blocker_reason,
                'source_card': card
            })
            blocker_summary[event_name] = blocker_reason

    # Status rule
    if queued_actions and not blocked_actions:
        queue_status = 'ready'
    elif queued_actions and blocked_actions:
        queue_status = 'partial'
    else:
        queue_status = 'blocked'

    control_plane_action_queue_summary = {
        'queue_status': queue_status,
        'event_count': event_count,
        'queued_count': len(queued_actions),
        'blocked_count': len(blocked_actions),
        'ready_event_names': ready_event_names,
        'blocked_event_names': blocked_event_names,
        'priority_queue': priority_queue,
        'escalation_queue': escalation_queue,
        'blocker_summary': blocker_summary
    }

    return {
        'control_plane_action_queue_status': queue_status,
        'event_count': event_count,
        'queued_actions': queued_actions,
        'blocked_actions': blocked_actions,
        'ready_event_names': ready_event_names,
        'blocked_event_names': blocked_event_names,
        'priority_queue': priority_queue,
        'escalation_queue': escalation_queue,
        'blocker_summary': blocker_summary,
        'control_plane_action_queue_summary': control_plane_action_queue_summary
    }
