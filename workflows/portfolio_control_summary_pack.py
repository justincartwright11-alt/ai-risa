"""
portfolio_control_summary_pack.py

Consumes a portfolio_outcome_pack result and emits a portfolio-level control summary artifact.
"""
from typing import Dict, Any, List

def portfolio_control_summary_pack(portfolio_outcome_pack_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aggregates a portfolio_outcome_pack result into a portfolio-level control summary.
    Args:
        portfolio_outcome_pack_result: Output dict from portfolio_outcome_pack
    Returns:
        Dict with portfolio_control_status, total_events, ready_events, partial_events, blocked_events,
        ready_event_names, partial_event_names, blocked_event_names, priority_queue, control_cards, blocker_summary, portfolio_control_summary
    """
    completed_events = portfolio_outcome_pack_result.get('completed_events', [])
    blocked_outcomes = portfolio_outcome_pack_result.get('blocked_outcomes', [])
    ready_event_names = portfolio_outcome_pack_result.get('ready_event_names', [])
    blocked_event_names = portfolio_outcome_pack_result.get('blocked_event_names', [])
    outcome_batches = portfolio_outcome_pack_result.get('outcome_batches', [])
    blocker_summary = portfolio_outcome_pack_result.get('blocker_summary', [])
    total_events = portfolio_outcome_pack_result.get('total_events', 0)

    control_cards = []
    priority_queue = []
    partial_event_names = []
    ready_events = 0
    partial_events = 0
    blocked_events = 0

    # Build control cards for completed events
    for event in completed_events:
        event_name = event.get('event_name')
        event_status = event.get('event_status')
        priority = event.get('priority')
        publish_ready_count = event.get('publish_ready_count', 0)
        review_required_count = event.get('review_required_count', 0)
        manual_intervention_count = event.get('manual_intervention_count', 0)
        blocked_count = event.get('blocked_count', 0)
        outcome_snapshot = event.copy()
        # Next action logic
        if event_status == 'ready':
            next_action = 'proceed_event'
            next_reason = 'Event completed and ready for next phase'
            ready_events += 1
        elif event_status == 'partial':
            next_action = 'review_event'
            next_reason = 'Event completed with partial issues'
            partial_events += 1
            partial_event_names.append(event_name)
        elif event_status == 'blocked':
            next_action = 'hold_event'
            next_reason = 'Event completed but blocked'
            blocked_events += 1
            blocked_event_names.append(event_name)
        else:
            next_action = 'proceed_event'
            next_reason = 'Event completed'
            ready_events += 1
        control_cards.append({
            'event_name': event_name,
            'event_status': event_status,
            'priority': priority,
            'next_action': next_action,
            'next_reason': next_reason,
            'publish_ready_count': publish_ready_count,
            'review_required_count': review_required_count,
            'manual_intervention_count': manual_intervention_count,
            'blocked_count': blocked_count,
            'outcome_snapshot': outcome_snapshot
        })
        priority_queue.append({
            'event_name': event_name,
            'event_status': event_status,
            'priority': priority,
            'reason': next_reason
        })

    # Build control cards for blocked outcomes
    for blocked in blocked_outcomes:
        event_name = blocked.get('event_name')
        event_status = blocked.get('event_status')
        priority = blocked.get('priority')
        outcome_snapshot = blocked.copy()
        next_action = 'hold_event'
        next_reason = blocked.get('blocker_reason', 'Manual intervention required')
        blocked_events += 1
        blocked_event_names.append(event_name)
        control_cards.append({
            'event_name': event_name,
            'event_status': event_status,
            'priority': priority,
            'next_action': next_action,
            'next_reason': next_reason,
            'publish_ready_count': 0,
            'review_required_count': 0,
            'manual_intervention_count': 0,
            'blocked_count': 0,
            'outcome_snapshot': outcome_snapshot
        })
        priority_queue.append({
            'event_name': event_name,
            'event_status': event_status,
            'priority': priority,
            'reason': next_reason
        })

    # Status rule
    if total_events == 0:
        portfolio_control_status = 'blocked'
    elif ready_events == total_events:
        portfolio_control_status = 'ready'
    elif blocked_events == total_events:
        portfolio_control_status = 'blocked'
    else:
        portfolio_control_status = 'partial'

    portfolio_control_summary = {
        'portfolio_control_status': portfolio_control_status,
        'total_events': total_events,
        'ready_events': ready_events,
        'partial_events': partial_events,
        'blocked_events': blocked_events,
        'ready_event_names': ready_event_names,
        'partial_event_names': partial_event_names,
        'blocked_event_names': blocked_event_names,
        'priority_queue': priority_queue,
        'control_cards': control_cards,
        'blocker_summary': blocker_summary,
    }
    # For contract: flatten top-level keys
    result = dict(portfolio_control_summary)
    result['portfolio_control_summary'] = portfolio_control_summary
    return result
