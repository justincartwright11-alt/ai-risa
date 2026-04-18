"""
control_plane_summary_pack

Consumes all frozen event and portfolio packs and emits a unified operator-facing system view for dashboards, triage, and orchestration.
"""

def control_plane_summary_pack(
    event_control_summary_pack,
    event_dashboard_pack,
    portfolio_summary_pack,
    portfolio_dashboard_pack,
    portfolio_control_summary_pack,
    portfolio_governance_pack,
    portfolio_resolution_decision_pack
):
    """
    Args:
        event_control_summary_pack (dict)
        event_dashboard_pack (dict)
        portfolio_summary_pack (dict)
        portfolio_dashboard_pack (dict)
        portfolio_control_summary_pack (dict)
        portfolio_governance_pack (dict)
        portfolio_resolution_decision_pack (dict)
    Returns:
        dict: Control plane summary artifact
    """
    # Deterministic extraction and composition
    ready_events = event_control_summary_pack.get('ready_events', [])
    partial_events = event_control_summary_pack.get('partial_events', [])
    blocked_events = event_control_summary_pack.get('blocked_events', [])
    event_count = event_control_summary_pack.get('event_count', 0)
    priority_queue = event_dashboard_pack.get('priority_queue', [])
    escalation_queue = portfolio_control_summary_pack.get('escalation_queue', [])
    dashboard_cards = portfolio_dashboard_pack.get('dashboard_cards', [])
    portfolio_status = portfolio_summary_pack.get('portfolio_status', 'unknown')
    control_plane_status = portfolio_resolution_decision_pack.get('portfolio_resolution_decision_status', 'unknown')
    control_plane_summary = {
        'event_count': event_count,
        'portfolio_status': portfolio_status,
        'ready_events': ready_events,
        'partial_events': partial_events,
        'blocked_events': blocked_events,
        'priority_queue': priority_queue,
        'escalation_queue': escalation_queue,
        'dashboard_cards': dashboard_cards,
        'portfolio_governance': portfolio_governance_pack.get('portfolio_governance_status', 'unknown'),
        'portfolio_resolution_decision': control_plane_status
    }
    return {
        'control_plane_status': control_plane_status,
        'event_count': event_count,
        'portfolio_status': portfolio_status,
        'ready_events': ready_events,
        'partial_events': partial_events,
        'blocked_events': blocked_events,
        'priority_queue': priority_queue,
        'escalation_queue': escalation_queue,
        'dashboard_cards': dashboard_cards,
        'control_plane_summary': control_plane_summary
    }
