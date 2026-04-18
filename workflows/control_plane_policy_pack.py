"""
control_plane_policy_pack

Consumes control_plane_status_pack output and emits a deterministic policy decision artifact.
"""

def control_plane_policy_pack(control_plane_status_pack_result):
    """
    Args:
        control_plane_status_pack_result (dict): Output from control_plane_status_pack
    Returns:
        dict: Control plane policy artifact
    """
    control_plane_status = control_plane_status_pack_result.get('control_plane_status', 'unknown')
    event_count = control_plane_status_pack_result.get('event_count', 0)
    closed_events = control_plane_status_pack_result.get('closed_events', [])
    pending_events = control_plane_status_pack_result.get('pending_events', [])
    ready_event_names = control_plane_status_pack_result.get('ready_event_names', [])
    blocked_event_names = control_plane_status_pack_result.get('blocked_event_names', [])
    priority_queue = control_plane_status_pack_result.get('priority_queue', [])
    escalation_queue = control_plane_status_pack_result.get('escalation_queue', [])
    blocker_summary = control_plane_status_pack_result.get('blocker_summary', {})
    status_cards = control_plane_status_pack_result.get('status_cards', [])
    control_plane_status_summary = control_plane_status_pack_result.get('control_plane_status_summary', {})

    policy_ready_events = []
    blocked_policy_events = []
    policy_actions = []

    for card in status_cards:
        event_name = card.get('event_name')
        event_status = card.get('event_status')
        priority = card.get('priority')
        closure_action = card.get('closure_action')
        closure_reason = card.get('closure_reason')
        final_status = card.get('final_status')
        escalation_level = card.get('escalation_level', 0)
        status_snapshot = dict(card)
        # Determine policy_action and reason
        if final_status == 'closed':
            policy_action = 'proceed_policy'
            policy_reason = 'Event closed, proceed policy action'
        elif final_status == 'pending_review':
            policy_action = 'review_policy'
            policy_reason = 'Event pending review, review policy action'
        elif final_status == 'pending_manual_intervention':
            policy_action = 'escalate_policy'
            policy_reason = 'Event pending manual intervention, escalate policy action'
        else:
            policy_action = 'hold_policy'
            policy_reason = 'Event on hold, hold policy action'
        policy_ready_events.append({
            'event_name': event_name,
            'event_status': event_status,
            'priority': priority,
            'closure_action': closure_action,
            'closure_reason': closure_reason,
            'final_status': final_status,
            'policy_action': policy_action,
            'policy_reason': policy_reason,
            'escalation_level': escalation_level,
            'status_snapshot': status_snapshot
        })
        policy_actions.append(policy_action)

    for pending in pending_events:
        event_name = pending.get('event_name')
        event_status = pending.get('event_status')
        priority = pending.get('priority')
        blocker_reason = pending.get('blocker_reason', 'Blocked at policy')
        status_snapshot = pending.get('closure_snapshot') or dict(pending)
        blocked_policy_events.append({
            'event_name': event_name,
            'event_status': event_status,
            'priority': priority,
            'blocker_reason': blocker_reason,
            'status_snapshot': status_snapshot
        })

    # Status rule
    if policy_ready_events and not blocked_policy_events:
        policy_status = 'ready'
    elif policy_ready_events and blocked_policy_events:
        policy_status = 'partial'
    else:
        policy_status = 'blocked'

    control_plane_policy_summary = {
        'policy_status': policy_status,
        'event_count': event_count,
        'policy_ready_count': len(policy_ready_events),
        'blocked_policy_count': len(blocked_policy_events),
        'ready_event_names': ready_event_names,
        'blocked_event_names': blocked_event_names,
        'policy_actions': policy_actions,
        'priority_queue': priority_queue,
        'escalation_queue': escalation_queue,
        'blocker_summary': blocker_summary
    }

    return {
        'control_plane_policy_status': policy_status,
        'event_count': event_count,
        'policy_ready_events': policy_ready_events,
        'blocked_policy_events': blocked_policy_events,
        'ready_event_names': ready_event_names,
        'blocked_event_names': blocked_event_names,
        'policy_actions': policy_actions,
        'priority_queue': priority_queue,
        'escalation_queue': escalation_queue,
        'blocker_summary': blocker_summary,
        'control_plane_policy_summary': control_plane_policy_summary
    }
