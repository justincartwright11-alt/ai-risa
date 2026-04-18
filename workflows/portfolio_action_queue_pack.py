"""
portfolio_action_queue_pack.py

Consumes a portfolio_dashboard_pack result and emits a cross-event action queue artifact.
"""
from typing import Dict, Any, List

def portfolio_action_queue_pack(portfolio_dashboard_pack_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforms a portfolio_dashboard_pack result into a cross-event action queue.
    Args:
        portfolio_dashboard_pack_result: Output dict from portfolio_dashboard_pack
    Returns:
        Dict with portfolio_action_queue_status, total_events, queued_event_actions, blocked_event_actions,
        ready_event_names, blocked_event_names, priority_queue, blocker_summary, portfolio_action_queue_summary
    """
    dashboard_cards = portfolio_dashboard_pack_result.get('dashboard_cards', [])
    priority_queue = portfolio_dashboard_pack_result.get('priority_queue', [])
    ready_event_names = []
    blocked_event_names = []
    queued_event_actions = []
    blocked_event_actions = []
    blocker_summary = []

    for card in dashboard_cards:
        event_name = card.get('event_name')
        event_status = card.get('event_status')
        priority = card.get('priority')
        dashboard_snapshot = card.copy()
        publish_ready_count = card.get('publish_ready_count', 0)
        review_required_count = card.get('review_required_count', 0)
        manual_intervention_count = card.get('manual_intervention_count', 0)
        blocked_count = card.get('blocked_count', 0)
        # Action and reason logic
        if event_status == 'ready':
            queue_action = 'proceed_event'
            queue_reason = 'All bouts ready for publication'
            ready_event_names.append(event_name)
            queued_event_actions.append({
                'event_name': event_name,
                'event_status': event_status,
                'priority': priority,
                'queue_action': queue_action,
                'queue_reason': queue_reason,
                'publish_ready_count': publish_ready_count,
                'review_required_count': review_required_count,
                'manual_intervention_count': manual_intervention_count,
                'blocked_count': blocked_count,
                'dashboard_snapshot': dashboard_snapshot
            })
        elif event_status == 'partial':
            queue_action = 'review_event'
            queue_reason = 'Some bouts require review or intervention'
            queued_event_actions.append({
                'event_name': event_name,
                'event_status': event_status,
                'priority': priority,
                'queue_action': queue_action,
                'queue_reason': queue_reason,
                'publish_ready_count': publish_ready_count,
                'review_required_count': review_required_count,
                'manual_intervention_count': manual_intervention_count,
                'blocked_count': blocked_count,
                'dashboard_snapshot': dashboard_snapshot
            })
        elif event_status == 'blocked':
            blocked_event_names.append(event_name)
            blocked_event_actions.append({
                'event_name': event_name,
                'event_status': event_status,
                'priority': priority,
                'blocker_reason': 'Manual intervention required',
                'dashboard_snapshot': dashboard_snapshot
            })
            blocker_summary.append({
                'event_name': event_name,
                'reason': 'Manual intervention required',
                'priority': priority
            })

    total_events = len(dashboard_cards)
    # Status rule
    if len(queued_event_actions) == total_events and total_events > 0:
        portfolio_action_queue_status = 'ready'
    elif len(queued_event_actions) > 0:
        portfolio_action_queue_status = 'partial'
    else:
        portfolio_action_queue_status = 'blocked'

    portfolio_action_queue_summary = {
        'portfolio_action_queue_status': portfolio_action_queue_status,
        'total_events': total_events,
        'queued_event_actions': queued_event_actions,
        'blocked_event_actions': blocked_event_actions,
        'ready_event_names': ready_event_names,
        'blocked_event_names': blocked_event_names,
        'priority_queue': priority_queue,
        'blocker_summary': blocker_summary,
    }
    # For contract: flatten top-level keys
    result = dict(portfolio_action_queue_summary)
    result['portfolio_action_queue_summary'] = portfolio_action_queue_summary
    return result
