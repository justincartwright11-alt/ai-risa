"""
portfolio_dispatch_pack.py

Consumes a portfolio_action_queue_pack result and emits a cross-event dispatch plan artifact.
"""
from typing import Dict, Any, List

def portfolio_dispatch_pack(portfolio_action_queue_pack_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforms a portfolio_action_queue_pack result into a cross-event dispatch plan.
    Args:
        portfolio_action_queue_pack_result: Output dict from portfolio_action_queue_pack
    Returns:
        Dict with portfolio_dispatch_status, total_events, dispatch_ready_events, blocked_dispatches,
        ready_event_names, blocked_event_names, dispatch_batches, blocker_summary, portfolio_dispatch_summary
    """
    queued_event_actions = portfolio_action_queue_pack_result.get('queued_event_actions', [])
    blocked_event_actions = portfolio_action_queue_pack_result.get('blocked_event_actions', [])
    ready_event_names = []
    blocked_event_names = []
    dispatch_ready_events = []
    blocked_dispatches = []
    dispatch_batches = []
    blocker_summary = portfolio_action_queue_pack_result.get('blocker_summary', [])

    # Map queue_action to dispatch_batch
    dispatch_map = {
        'proceed_event': 'dispatch_publish_batch',
        'review_event': 'dispatch_review_batch',
        'hold_event': 'dispatch_hold_batch',
        'escalate_event': 'dispatch_escalation_batch',
    }

    for action in queued_event_actions:
        event_name = action.get('event_name')
        event_status = action.get('event_status')
        priority = action.get('priority')
        queue_action = action.get('queue_action')
        queue_reason = action.get('queue_reason')
        publish_ready_count = action.get('publish_ready_count', 0)
        review_required_count = action.get('review_required_count', 0)
        manual_intervention_count = action.get('manual_intervention_count', 0)
        blocked_count = action.get('blocked_count', 0)
        queue_snapshot = action.copy()
        dispatch_batch = dispatch_map.get(queue_action, 'dispatch_hold_batch')
        if queue_action == 'proceed_event':
            dispatch_reason = 'Ready for publication dispatch'
        elif queue_action == 'review_event':
            dispatch_reason = 'Requires review before dispatch'
        elif queue_action == 'hold_event':
            dispatch_reason = 'Hold event from dispatch'
        elif queue_action == 'escalate_event':
            dispatch_reason = 'Escalate event for dispatch decision'
        else:
            dispatch_reason = 'Dispatch action required'
        ready_event_names.append(event_name)
        dispatch_ready_events.append({
            'event_name': event_name,
            'event_status': event_status,
            'priority': priority,
            'queue_action': queue_action,
            'queue_reason': queue_reason,
            'dispatch_batch': dispatch_batch,
            'dispatch_reason': dispatch_reason,
            'publish_ready_count': publish_ready_count,
            'review_required_count': review_required_count,
            'manual_intervention_count': manual_intervention_count,
            'blocked_count': blocked_count,
            'queue_snapshot': queue_snapshot
        })
        dispatch_batches.append(dispatch_batch)

    for blocked in blocked_event_actions:
        event_name = blocked.get('event_name')
        event_status = blocked.get('event_status')
        priority = blocked.get('priority')
        blocker_reason = blocked.get('blocker_reason', 'Manual intervention required')
        queue_snapshot = blocked.copy()
        blocked_event_names.append(event_name)
        blocked_dispatches.append({
            'event_name': event_name,
            'event_status': event_status,
            'priority': priority,
            'blocker_reason': blocker_reason,
            'queue_snapshot': queue_snapshot
        })

    total_events = len(queued_event_actions) + len(blocked_event_actions)
    # Status rule
    if len(dispatch_ready_events) == total_events and total_events > 0:
        portfolio_dispatch_status = 'ready'
    elif len(dispatch_ready_events) > 0:
        portfolio_dispatch_status = 'partial'
    else:
        portfolio_dispatch_status = 'blocked'

    portfolio_dispatch_summary = {
        'portfolio_dispatch_status': portfolio_dispatch_status,
        'total_events': total_events,
        'dispatch_ready_events': dispatch_ready_events,
        'blocked_dispatches': blocked_dispatches,
        'ready_event_names': ready_event_names,
        'blocked_event_names': blocked_event_names,
        'dispatch_batches': dispatch_batches,
        'blocker_summary': blocker_summary,
    }
    # For contract: flatten top-level keys
    result = dict(portfolio_dispatch_summary)
    result['portfolio_dispatch_summary'] = portfolio_dispatch_summary
    return result
