"""
portfolio_execution_pack.py

Consumes a portfolio_dispatch_pack result and emits a cross-event execution plan artifact.
"""
from typing import Dict, Any, List

def portfolio_execution_pack(portfolio_dispatch_pack_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforms a portfolio_dispatch_pack result into a cross-event execution plan.
    Args:
        portfolio_dispatch_pack_result: Output dict from portfolio_dispatch_pack
    Returns:
        Dict with portfolio_execution_status, total_events, execution_ready_events, blocked_executions,
        ready_event_names, blocked_event_names, execution_batches, blocker_summary, portfolio_execution_summary
    """
    dispatch_ready_events = portfolio_dispatch_pack_result.get('dispatch_ready_events', [])
    blocked_dispatches = portfolio_dispatch_pack_result.get('blocked_dispatches', [])
    ready_event_names = portfolio_dispatch_pack_result.get('ready_event_names', [])
    blocked_event_names = portfolio_dispatch_pack_result.get('blocked_event_names', [])
    execution_ready_events = []
    blocked_executions = []
    execution_batches = []
    blocker_summary = portfolio_dispatch_pack_result.get('blocker_summary', [])

    # Map dispatch_batch to execution_batch
    execution_map = {
        'dispatch_publish_batch': 'execute_publish_batch',
        'dispatch_review_batch': 'execute_review_batch',
        'dispatch_hold_batch': 'execute_hold_batch',
        'dispatch_escalation_batch': 'execute_escalation_batch',
    }

    for dispatch in dispatch_ready_events:
        event_name = dispatch.get('event_name')
        event_status = dispatch.get('event_status')
        priority = dispatch.get('priority')
        queue_action = dispatch.get('queue_action')
        queue_reason = dispatch.get('queue_reason')
        dispatch_batch = dispatch.get('dispatch_batch')
        dispatch_reason = dispatch.get('dispatch_reason')
        publish_ready_count = dispatch.get('publish_ready_count', 0)
        review_required_count = dispatch.get('review_required_count', 0)
        manual_intervention_count = dispatch.get('manual_intervention_count', 0)
        blocked_count = dispatch.get('blocked_count', 0)
        dispatch_snapshot = dispatch.copy()
        execution_batch = execution_map.get(dispatch_batch, 'execute_hold_batch')
        if dispatch_batch == 'dispatch_publish_batch':
            execution_reason = 'Ready for publication execution'
        elif dispatch_batch == 'dispatch_review_batch':
            execution_reason = 'Requires review before execution'
        elif dispatch_batch == 'dispatch_hold_batch':
            execution_reason = 'Hold event from execution'
        elif dispatch_batch == 'dispatch_escalation_batch':
            execution_reason = 'Escalate event for execution decision'
        else:
            execution_reason = 'Execution action required'
        execution_ready_events.append({
            'event_name': event_name,
            'event_status': event_status,
            'priority': priority,
            'queue_action': queue_action,
            'queue_reason': queue_reason,
            'dispatch_batch': dispatch_batch,
            'dispatch_reason': dispatch_reason,
            'execution_batch': execution_batch,
            'execution_reason': execution_reason,
            'publish_ready_count': publish_ready_count,
            'review_required_count': review_required_count,
            'manual_intervention_count': manual_intervention_count,
            'blocked_count': blocked_count,
            'dispatch_snapshot': dispatch_snapshot
        })
        execution_batches.append(execution_batch)

    for blocked in blocked_dispatches:
        event_name = blocked.get('event_name')
        event_status = blocked.get('event_status')
        priority = blocked.get('priority')
        blocker_reason = blocked.get('blocker_reason', 'Manual intervention required')
        dispatch_snapshot = blocked.copy()
        blocked_executions.append({
            'event_name': event_name,
            'event_status': event_status,
            'priority': priority,
            'blocker_reason': blocker_reason,
            'dispatch_snapshot': dispatch_snapshot
        })

    total_events = len(dispatch_ready_events) + len(blocked_dispatches)
    # Status rule
    if len(execution_ready_events) == total_events and total_events > 0:
        portfolio_execution_status = 'ready'
    elif len(execution_ready_events) > 0:
        portfolio_execution_status = 'partial'
    else:
        portfolio_execution_status = 'blocked'

    portfolio_execution_summary = {
        'portfolio_execution_status': portfolio_execution_status,
        'total_events': total_events,
        'execution_ready_events': execution_ready_events,
        'blocked_executions': blocked_executions,
        'ready_event_names': ready_event_names,
        'blocked_event_names': blocked_event_names,
        'execution_batches': execution_batches,
        'blocker_summary': blocker_summary,
    }
    # For contract: flatten top-level keys
    result = dict(portfolio_execution_summary)
    result['portfolio_execution_summary'] = portfolio_execution_summary
    return result
