"""
control_plane_status_pack

Consumes control_plane_closure_pack output and emits a deterministic control-plane status artifact.
"""

def control_plane_status_pack(control_plane_closure_pack_result):
    """
    Args:
        control_plane_closure_pack_result (dict): Output from control_plane_closure_pack
    Returns:
        dict: Control plane status artifact
    """
    closure_status = control_plane_closure_pack_result.get('control_plane_closure_status', 'unknown')
    event_count = control_plane_closure_pack_result.get('event_count', 0)
    closed_events = control_plane_closure_pack_result.get('closed_events', [])
    pending_events = control_plane_closure_pack_result.get('pending_events', [])
    ready_event_names = control_plane_closure_pack_result.get('ready_event_names', [])
    blocked_event_names = control_plane_closure_pack_result.get('blocked_event_names', [])
    priority_queue = control_plane_closure_pack_result.get('priority_queue', [])
    escalation_queue = control_plane_closure_pack_result.get('escalation_queue', [])
    blocker_summary = control_plane_closure_pack_result.get('blocker_summary', {})
    control_plane_closure_summary = control_plane_closure_pack_result.get('control_plane_closure_summary', {})

    status_cards = []
    pending_status_entries = []

    for event in closed_events:
        event_name = event.get('event_name')
        event_status = event.get('event_status')
        priority = event.get('priority')
        closure_action = event.get('closure_action')
        closure_reason = event.get('closure_reason')
        escalation_level = event.get('escalation_level', 0)
        source_card = event.get('source_card')
        closure_snapshot = dict(event)
        # Determine final_status and reason
        if closure_action == 'close_event':
            final_status = 'closed'
            final_reason = 'Event closed in control-plane status pack'
        elif closure_action == 'hold_open':
            final_status = 'pending_review'
            final_reason = 'Event pending operator review in status pack'
        elif closure_action == 'escalate_followup':
            final_status = 'pending_manual_intervention'
            final_reason = 'Event pending manual intervention in status pack'
        else:
            final_status = 'pending_review'
            final_reason = 'Event pending review in status pack'
        status_cards.append({
            'event_name': event_name,
            'event_status': event_status,
            'priority': priority,
            'closure_action': closure_action,
            'closure_reason': closure_reason,
            'final_status': final_status,
            'final_reason': final_reason,
            'escalation_level': escalation_level,
            'source_card': source_card,
            'closure_snapshot': closure_snapshot
        })

    for pending in pending_events:
        event_name = pending.get('event_name')
        event_status = pending.get('event_status')
        priority = pending.get('priority')
        blocker_reason = pending.get('blocker_reason', 'Pending in status pack')
        closure_snapshot = pending.get('remediation_outcome_snapshot') or dict(pending)
        pending_status_entries.append({
            'event_name': event_name,
            'event_status': event_status,
            'priority': priority,
            'blocker_reason': blocker_reason,
            'closure_snapshot': closure_snapshot
        })

    # Status rule
    if status_cards and not pending_status_entries:
        control_plane_status = 'ready'
    elif status_cards and pending_status_entries:
        control_plane_status = 'partial'
    else:
        control_plane_status = 'blocked'

    control_plane_status_summary = {
        'status': control_plane_status,
        'event_count': event_count,
        'closed_count': len(status_cards),
        'pending_count': len(pending_status_entries),
        'ready_event_names': ready_event_names,
        'blocked_event_names': blocked_event_names,
        'priority_queue': priority_queue,
        'escalation_queue': escalation_queue,
        'blocker_summary': blocker_summary
    }

    return {
        'control_plane_status': control_plane_status,
        'event_count': event_count,
        'closed_events': closed_events,
        'pending_events': pending_events,
        'ready_event_names': ready_event_names,
        'blocked_event_names': blocked_event_names,
        'priority_queue': priority_queue,
        'escalation_queue': escalation_queue,
        'blocker_summary': blocker_summary,
        'status_cards': status_cards,
        'control_plane_status_summary': control_plane_status_summary
    }
