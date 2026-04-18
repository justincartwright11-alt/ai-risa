"""
portfolio_escalation_routing_pack.py

Consumes a portfolio_governance_pack result and emits a routed handoff artifact for downstream paths.
"""
from typing import Dict, Any, List

def portfolio_escalation_routing_pack(portfolio_governance_pack_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aggregates a portfolio_governance_pack result into a routed handoff artifact.
    Args:
        portfolio_governance_pack_result: Output dict from portfolio_governance_pack
    Returns:
        Dict with portfolio_escalation_routing_status, total_events, routed_events, blocked_routes,
        ready_event_names, blocked_event_names, route_targets, blocker_summary, portfolio_escalation_routing_summary
    """
    governance_cards = portfolio_governance_pack_result.get('governance_cards', [])
    ready_event_names = portfolio_governance_pack_result.get('ready_event_names', [])
    blocked_event_names = portfolio_governance_pack_result.get('blocked_event_names', [])
    blocker_summary = portfolio_governance_pack_result.get('blocker_summary', [])
    total_events = portfolio_governance_pack_result.get('total_events', 0)

    routed_events = []
    blocked_routes = []
    route_targets = []

    for card in governance_cards:
        event_name = card.get('event_name')
        event_status = card.get('event_status')
        priority = card.get('priority')
        governance_action = card.get('governance_action')
        governance_reason = card.get('governance_reason')
        escalation_level = card.get('escalation_level')
        governance_snapshot = card.copy()
        # Routing logic
        if governance_action == 'proceed_portfolio_event' and escalation_level == 'none':
            route_target = 'portfolio_proceed_path'
            route_reason = 'Proceed event through portfolio'
            routed_events.append({
                'event_name': event_name,
                'event_status': event_status,
                'priority': priority,
                'governance_action': governance_action,
                'governance_reason': governance_reason,
                'escalation_level': escalation_level,
                'route_target': route_target,
                'route_reason': route_reason,
                'governance_snapshot': governance_snapshot
            })
            route_targets.append(route_target)
        elif governance_action == 'review_portfolio_event' and escalation_level == 'operator_review':
            route_target = 'portfolio_operator_review'
            route_reason = 'Route event for operator review'
            routed_events.append({
                'event_name': event_name,
                'event_status': event_status,
                'priority': priority,
                'governance_action': governance_action,
                'governance_reason': governance_reason,
                'escalation_level': escalation_level,
                'route_target': route_target,
                'route_reason': route_reason,
                'governance_snapshot': governance_snapshot
            })
            route_targets.append(route_target)
        elif governance_action == 'escalate_portfolio_event' and escalation_level == 'manual_intervention':
            route_target = 'portfolio_manual_intervention'
            route_reason = 'Route event for manual intervention'
            routed_events.append({
                'event_name': event_name,
                'event_status': event_status,
                'priority': priority,
                'governance_action': governance_action,
                'governance_reason': governance_reason,
                'escalation_level': escalation_level,
                'route_target': route_target,
                'route_reason': route_reason,
                'governance_snapshot': governance_snapshot
            })
            route_targets.append(route_target)
        else:
            # Blocked route
            blocker_reason = governance_reason or 'Route blocked by governance decision'
            blocked_routes.append({
                'event_name': event_name,
                'event_status': event_status,
                'priority': priority,
                'blocker_reason': blocker_reason,
                'governance_snapshot': governance_snapshot
            })

    # Status rule
    if total_events == 0:
        portfolio_escalation_routing_status = 'blocked'
    elif len(routed_events) == total_events:
        portfolio_escalation_routing_status = 'ready'
    elif len(routed_events) > 0:
        portfolio_escalation_routing_status = 'partial'
    else:
        portfolio_escalation_routing_status = 'blocked'

    portfolio_escalation_routing_summary = {
        'portfolio_escalation_routing_status': portfolio_escalation_routing_status,
        'total_events': total_events,
        'routed_events': routed_events,
        'blocked_routes': blocked_routes,
        'ready_event_names': ready_event_names,
        'blocked_event_names': blocked_event_names,
        'route_targets': route_targets,
        'blocker_summary': blocker_summary,
    }
    # For contract: flatten top-level keys
    result = dict(portfolio_escalation_routing_summary)
    result['portfolio_escalation_routing_summary'] = portfolio_escalation_routing_summary
    return result
