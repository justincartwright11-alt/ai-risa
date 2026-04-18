"""
portfolio_summary_pack.py

Consumes a deterministic list of event_dashboard_pack outputs and emits a portfolio-level summary and cards.
"""
from typing import List, Dict, Any

def portfolio_summary_pack(event_dashboard_pack_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregates multiple event_dashboard_pack outputs into a portfolio summary.
    Args:
        event_dashboard_pack_results: List of event_dashboard_pack outputs (dicts)
    Returns:
        Dict with portfolio_status, total_events, ready_events, partial_events, blocked_events,
        event_names, ready_event_names, partial_event_names, blocked_event_names,
        portfolio_cards, portfolio_summary
    """
    portfolio_cards = []
    ready_event_names = []
    partial_event_names = []
    blocked_event_names = []
    event_names = []
    ready_events = 0
    partial_events = 0
    blocked_events = 0

    for event in event_dashboard_pack_results:
        card = {
            'event_name': event.get('event_name'),
            'event_status': event.get('event_status'),
            'total_bouts': event.get('total_bouts', 0),
            'publish_ready_count': event.get('publish_ready_count', 0),
            'review_required_count': event.get('review_required_count', 0),
            'manual_intervention_count': event.get('manual_intervention_count', 0),
            'blocked_count': event.get('blocked_count', 0),
            'priority': event.get('priority'),
            'notes': event.get('notes', ''),
        }
        portfolio_cards.append(card)
        event_names.append(card['event_name'])
        status = card['event_status']
        if status == 'ready':
            ready_events += 1
            ready_event_names.append(card['event_name'])
        elif status == 'partial':
            partial_events += 1
            partial_event_names.append(card['event_name'])
        elif status == 'blocked':
            blocked_events += 1
            blocked_event_names.append(card['event_name'])

    total_events = len(event_dashboard_pack_results)
    # Portfolio status rule
    if ready_events == total_events and total_events > 0:
        portfolio_status = 'ready'
    elif blocked_events == total_events and total_events > 0:
        portfolio_status = 'blocked'
    else:
        portfolio_status = 'partial'

    portfolio_summary = {
        'portfolio_status': portfolio_status,
        'total_events': total_events,
        'ready_events': ready_events,
        'partial_events': partial_events,
        'blocked_events': blocked_events,
        'event_names': event_names,
        'ready_event_names': ready_event_names,
        'partial_event_names': partial_event_names,
        'blocked_event_names': blocked_event_names,
        'portfolio_cards': portfolio_cards,
    }
    # For contract: flatten top-level keys
    result = dict(portfolio_summary)
    result['portfolio_summary'] = portfolio_summary
    return result
