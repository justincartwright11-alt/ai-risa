"""
portfolio_dashboard_pack.py

Consumes a portfolio_summary_pack result and emits a dashboard-ready, operator-facing portfolio view.
"""
from typing import Dict, Any, List

def portfolio_dashboard_pack(portfolio_summary_pack_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforms a portfolio_summary_pack result into a dashboard-ready portfolio view.
    Args:
        portfolio_summary_pack_result: Output dict from portfolio_summary_pack
    Returns:
        Dict with portfolio_dashboard_status, total_events, ready_events, partial_events, blocked_events,
        dashboard_cards, priority_queue, blocked_event_names, portfolio_dashboard_summary
    """
    # Extract fields
    portfolio_status = portfolio_summary_pack_result.get('portfolio_status')
    total_events = portfolio_summary_pack_result.get('total_events', 0)
    ready_events = portfolio_summary_pack_result.get('ready_events', 0)
    partial_events = portfolio_summary_pack_result.get('partial_events', 0)
    blocked_events = portfolio_summary_pack_result.get('blocked_events', 0)
    blocked_event_names = portfolio_summary_pack_result.get('blocked_event_names', [])
    portfolio_cards = portfolio_summary_pack_result.get('portfolio_cards', [])

    dashboard_cards = []
    priority_queue = []

    for card in portfolio_cards:
        dashboard_card = dict(card)
        dashboard_card['source_summary'] = card.copy()
        dashboard_cards.append(dashboard_card)

    # Priority queue: sort by priority (ascending, lower = higher priority)
    sorted_cards = sorted(portfolio_cards, key=lambda c: (c.get('priority', 9999), c.get('event_name', '')))
    for card in sorted_cards:
        reason = None
        if card.get('event_status') == 'blocked':
            reason = 'Blocked event requires intervention'
        elif card.get('event_status') == 'partial':
            reason = 'Partial event needs review'
        elif card.get('event_status') == 'ready':
            reason = 'Ready for publication'
        priority_queue.append({
            'event_name': card.get('event_name'),
            'event_status': card.get('event_status'),
            'priority': card.get('priority'),
            'reason': reason
        })

    # Status rule
    if ready_events == total_events and total_events > 0:
        portfolio_dashboard_status = 'ready'
    elif blocked_events == total_events and total_events > 0:
        portfolio_dashboard_status = 'blocked'
    else:
        portfolio_dashboard_status = 'partial'

    portfolio_dashboard_summary = {
        'portfolio_dashboard_status': portfolio_dashboard_status,
        'total_events': total_events,
        'ready_events': ready_events,
        'partial_events': partial_events,
        'blocked_events': blocked_events,
        'dashboard_cards': dashboard_cards,
        'priority_queue': priority_queue,
        'blocked_event_names': blocked_event_names,
    }
    # For contract: flatten top-level keys
    result = dict(portfolio_dashboard_summary)
    result['portfolio_dashboard_summary'] = portfolio_dashboard_summary
    return result
