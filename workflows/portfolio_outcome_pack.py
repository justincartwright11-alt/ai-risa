"""
portfolio_outcome_pack.py

Consumes a portfolio_execution_pack result and emits a cross-event outcome bundle.
"""
from typing import Dict, Any, List

def portfolio_outcome_pack(portfolio_execution_pack_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aggregates a portfolio_execution_pack result into a cross-event outcome bundle.
    Args:
        portfolio_execution_pack_result: Output dict from portfolio_execution_pack
    Returns:
        Dict with portfolio_outcome_status, total_events, completed_events, blocked_outcomes,
        ready_event_names, blocked_event_names, outcome_batches, blocker_summary, portfolio_outcome_summary
    """
    execution_ready_events = portfolio_execution_pack_result.get('execution_ready_events', [])
    blocked_executions = portfolio_execution_pack_result.get('blocked_executions', [])
    ready_event_names = portfolio_execution_pack_result.get('ready_event_names', [])
    blocked_event_names = portfolio_execution_pack_result.get('blocked_event_names', [])
    completed_events = []
    blocked_outcomes = []
    outcome_batches = []
    blocker_summary = portfolio_execution_pack_result.get('blocker_summary', [])

    # Map execution_batch to outcome_batch
    outcome_map = {
        'execute_publish_batch': 'complete_publish_batch',
        'execute_review_batch': 'complete_review_batch',
        'execute_hold_batch': 'complete_hold_batch',
        'execute_escalation_batch': 'complete_escalation_batch',
    }

    for exe in execution_ready_events:
        event_name = exe.get('event_name')
        event_status = exe.get('event_status')
        priority = exe.get('priority')
        queue_action = exe.get('queue_action')
        queue_reason = exe.get('queue_reason')
        dispatch_batch = exe.get('dispatch_batch')
        dispatch_reason = exe.get('dispatch_reason')
        execution_batch = exe.get('execution_batch')
        execution_reason = exe.get('execution_reason')
        publish_ready_count = exe.get('publish_ready_count', 0)
        review_required_count = exe.get('review_required_count', 0)
        manual_intervention_count = exe.get('manual_intervention_count', 0)
        blocked_count = exe.get('blocked_count', 0)
        execution_snapshot = exe.copy()
        outcome_batch = outcome_map.get(execution_batch, 'complete_hold_batch')
        if execution_batch == 'execute_publish_batch':
            outcome_reason = 'Event completed and published'
        elif execution_batch == 'execute_review_batch':
            outcome_reason = 'Event completed after review'
        elif execution_batch == 'execute_hold_batch':
            outcome_reason = 'Event held from completion'
        elif execution_batch == 'execute_escalation_batch':
            outcome_reason = 'Event escalated for completion decision'
        else:
            outcome_reason = 'Outcome action required'
        completed_events.append({
            'event_name': event_name,
            'event_status': event_status,
            'priority': priority,
            'queue_action': queue_action,
            'queue_reason': queue_reason,
            'dispatch_batch': dispatch_batch,
            'dispatch_reason': dispatch_reason,
            'execution_batch': execution_batch,
            'execution_reason': execution_reason,
            'outcome_batch': outcome_batch,
            'outcome_reason': outcome_reason,
            'publish_ready_count': publish_ready_count,
            'review_required_count': review_required_count,
            'manual_intervention_count': manual_intervention_count,
            'blocked_count': blocked_count,
            'execution_snapshot': execution_snapshot
        })
        outcome_batches.append(outcome_batch)

    for blocked in blocked_executions:
        event_name = blocked.get('event_name')
        event_status = blocked.get('event_status')
        priority = blocked.get('priority')
        blocker_reason = blocked.get('blocker_reason', 'Manual intervention required')
        execution_snapshot = blocked.get('execution_snapshot', blocked.copy())
        blocked_outcomes.append({
            'event_name': event_name,
            'event_status': event_status,
            'priority': priority,
            'blocker_reason': blocker_reason,
            'execution_snapshot': execution_snapshot
        })

    total_events = len(execution_ready_events) + len(blocked_executions)
    # Status rule
    if len(completed_events) == total_events and total_events > 0:
        portfolio_outcome_status = 'ready'
    elif len(completed_events) > 0:
        portfolio_outcome_status = 'partial'
    else:
        portfolio_outcome_status = 'blocked'

    portfolio_outcome_summary = {
        'portfolio_outcome_status': portfolio_outcome_status,
        'total_events': total_events,
        'completed_events': completed_events,
        'blocked_outcomes': blocked_outcomes,
        'ready_event_names': ready_event_names,
        'blocked_event_names': blocked_event_names,
        'outcome_batches': outcome_batches,
        'blocker_summary': blocker_summary,
    }
    # For contract: flatten top-level keys
    result = dict(portfolio_outcome_summary)
    result['portfolio_outcome_summary'] = portfolio_outcome_summary
    return result
