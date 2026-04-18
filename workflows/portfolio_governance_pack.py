"""
portfolio_governance_pack.py

Consumes a portfolio_control_summary_pack result and emits a portfolio-level governance decision artifact.
"""
from typing import Dict, Any, List

def portfolio_governance_pack(portfolio_control_summary_pack_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aggregates a portfolio_control_summary_pack result into a portfolio-level governance decision artifact.
    Args:
        portfolio_control_summary_pack_result: Output dict from portfolio_control_summary_pack
    Returns:
        Dict with portfolio_governance_status, total_events, governance_ready_events, blocked_governance_events,
        ready_event_names, blocked_event_names, escalation_flags, governance_cards, blocker_summary, portfolio_governance_summary
    """
    control_cards = portfolio_control_summary_pack_result.get('control_cards', [])
    ready_event_names = portfolio_control_summary_pack_result.get('ready_event_names', [])
    blocked_event_names = portfolio_control_summary_pack_result.get('blocked_event_names', [])
    blocker_summary = portfolio_control_summary_pack_result.get('blocker_summary', [])
    total_events = portfolio_control_summary_pack_result.get('total_events', 0)

    governance_ready_events = []
    blocked_governance_events = []
    escalation_flags = []
    governance_cards = []

    for card in control_cards:
        event_name = card.get('event_name')
        event_status = card.get('event_status')
        priority = card.get('priority')
        next_action = card.get('next_action')
        next_reason = card.get('next_reason')
        control_snapshot = card.copy()
        # Governance action and escalation logic
        if event_status == 'ready':
            governance_action = 'proceed_portfolio_event'
            governance_reason = 'Event ready for portfolio proceed'
            escalation_level = 'none'
            governance_ready_events.append(event_name)
        elif event_status == 'partial':
            governance_action = 'review_portfolio_event'
            governance_reason = 'Event requires operator review'
            escalation_level = 'operator_review'
            escalation_flags.append({'event_name': event_name, 'escalation_level': escalation_level})
        elif event_status == 'blocked':
            governance_action = 'escalate_portfolio_event'
            governance_reason = 'Event requires manual intervention'
            escalation_level = 'manual_intervention'
            blocked_governance_events.append(event_name)
            escalation_flags.append({'event_name': event_name, 'escalation_level': escalation_level})
        else:
            governance_action = 'hold_portfolio_event'
            governance_reason = 'Event held for governance decision'
            escalation_level = 'none'
        governance_cards.append({
            'event_name': event_name,
            'event_status': event_status,
            'priority': priority,
            'governance_action': governance_action,
            'governance_reason': governance_reason,
            'escalation_level': escalation_level,
            'next_action': next_action,
            'next_reason': next_reason,
            'control_snapshot': control_snapshot
        })

    # Status rule
    if total_events == 0:
        portfolio_governance_status = 'blocked'
    elif len(governance_ready_events) == total_events:
        portfolio_governance_status = 'ready'
    elif len(blocked_governance_events) == total_events:
        portfolio_governance_status = 'blocked'
    else:
        portfolio_governance_status = 'partial'

    portfolio_governance_summary = {
        'portfolio_governance_status': portfolio_governance_status,
        'total_events': total_events,
        'governance_ready_events': governance_ready_events,
        'blocked_governance_events': blocked_governance_events,
        'ready_event_names': ready_event_names,
        'blocked_event_names': blocked_event_names,
        'escalation_flags': escalation_flags,
        'governance_cards': governance_cards,
        'blocker_summary': blocker_summary,
    }
    # For contract: flatten top-level keys
    result = dict(portfolio_governance_summary)
    result['portfolio_governance_summary'] = portfolio_governance_summary
    return result
