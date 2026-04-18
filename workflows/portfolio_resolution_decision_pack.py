"""
portfolio_resolution_decision_pack

Consumes portfolio_escalation_routing_pack output and emits a unified resolution decision artifact for dashboards, operator triage, or automation policy.
"""

def portfolio_resolution_decision_pack(portfolio_escalation_routing):
    """
    Args:
        portfolio_escalation_routing (dict): Output from portfolio_escalation_routing_pack
    Returns:
        dict: Portfolio resolution decision artifact
    """
    # Deterministic ordering
    routed_events = portfolio_escalation_routing.get('routed_events', [])
    blocked_routes = portfolio_escalation_routing.get('blocked_routes', [])
    ready_event_names = portfolio_escalation_routing.get('ready_event_names', [])
    blocked_event_names = portfolio_escalation_routing.get('blocked_event_names', [])
    route_targets = portfolio_escalation_routing.get('route_targets', [])
    blocker_summary = portfolio_escalation_routing.get('blocker_summary', {})
    total_events = portfolio_escalation_routing.get('total_events', 0)
    routing_status = portfolio_escalation_routing.get('portfolio_escalation_routing_status', 'blocked')
    routing_summary = portfolio_escalation_routing.get('portfolio_escalation_routing_summary', {})

    resolved_events = []
    blocked_resolutions = []
    resolution_actions = []

    for routed in routed_events:
        event_name = routed.get('event_name')
        event_status = routed.get('event_status')
        priority = routed.get('priority')
        governance_action = routed.get('governance_action')
        route_target = routed.get('route_target')
        escalation_level = routed.get('escalation_level')
        routing_snapshot = dict(routed)
        # Map route_target to resolution_action
        if route_target == 'portfolio_proceed_path':
            resolution_action = 'proceed'
            resolution_reason = 'Event cleared for portfolio proceed'
        elif route_target == 'portfolio_operator_review':
            resolution_action = 'review'
            resolution_reason = 'Event requires operator review'
        elif route_target == 'portfolio_manual_intervention':
            resolution_action = 'manual_intervention'
            resolution_reason = 'Manual intervention required for event'
        else:
            resolution_action = 'manual_intervention'
            resolution_reason = 'Unknown route target, defaulting to manual intervention'
        resolved_events.append({
            'event_name': event_name,
            'event_status': event_status,
            'priority': priority,
            'governance_action': governance_action,
            'route_target': route_target,
            'resolution_action': resolution_action,
            'resolution_reason': resolution_reason,
            'escalation_level': escalation_level,
            'routing_snapshot': routing_snapshot
        })
        resolution_actions.append(resolution_action)

    for blocked in blocked_routes:
        event_name = blocked.get('event_name')
        event_status = blocked.get('event_status')
        priority = blocked.get('priority')
        blocker_reason = blocked.get('blocker_reason', 'Blocked by escalation routing')
        routing_snapshot = dict(blocked)
        blocked_resolutions.append({
            'event_name': event_name,
            'event_status': event_status,
            'priority': priority,
            'blocker_reason': blocker_reason,
            'routing_snapshot': routing_snapshot
        })

    # Status rule
    if resolved_events and not blocked_resolutions:
        decision_status = 'ready'
    elif resolved_events and blocked_resolutions:
        decision_status = 'partial'
    else:
        decision_status = 'blocked'

    # Summary
    portfolio_resolution_decision_summary = {
        'total_events': total_events,
        'resolved_count': len(resolved_events),
        'blocked_count': len(blocked_resolutions),
        'resolution_actions': resolution_actions,
        'routing_status': routing_status,
        'routing_summary': routing_summary
    }

    return {
        'portfolio_resolution_decision_status': decision_status,
        'total_events': total_events,
        'resolved_events': resolved_events,
        'blocked_resolutions': blocked_resolutions,
        'ready_event_names': ready_event_names,
        'blocked_event_names': blocked_event_names,
        'resolution_actions': resolution_actions,
        'blocker_summary': blocker_summary,
        'portfolio_resolution_decision_summary': portfolio_resolution_decision_summary
    }
