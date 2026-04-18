"""
control_plane_dashboard_pack

Consumes control_plane_summary_pack output and emits a deterministic dashboard/export artifact for operator use.
"""

def control_plane_dashboard_pack(control_plane_summary):
    """
    Args:
        control_plane_summary (dict): Output from control_plane_summary_pack
    Returns:
        dict: Control plane dashboard artifact
    """
    control_plane_status = control_plane_summary.get('control_plane_status', 'unknown')
    event_count = control_plane_summary.get('event_count', 0)
    portfolio_status = control_plane_summary.get('portfolio_status', 'unknown')
    ready_events = control_plane_summary.get('ready_events', [])
    partial_events = control_plane_summary.get('partial_events', [])
    blocked_events = control_plane_summary.get('blocked_events', [])
    dashboard_cards = control_plane_summary.get('dashboard_cards', [])
    priority_queue = control_plane_summary.get('priority_queue', [])
    escalation_queue = control_plane_summary.get('escalation_queue', [])

    # Status rule
    if ready_events and not partial_events and not blocked_events:
        dashboard_status = 'ready'
    elif ready_events or partial_events:
        dashboard_status = 'partial'
    else:
        dashboard_status = 'blocked'

    # Dashboard sections
    dashboard_sections = {
        'status_overview': {
            'control_plane_status': control_plane_status,
            'portfolio_status': portfolio_status,
            'event_count': event_count,
            'ready_events': ready_events,
            'partial_events': partial_events,
            'blocked_events': blocked_events
        },
        'priority_overview': {
            'priority_queue': priority_queue
        },
        'escalation_overview': {
            'escalation_queue': escalation_queue
        },
        'operator_queue': {
            'dashboard_cards': dashboard_cards
        },
        'blocked_items': {
            'blocked_events': blocked_events
        }
    }

    # Dashboard card enrichment
    enriched_cards = []
    for card in dashboard_cards:
        enriched = dict(card)
        enriched['publish_ready_count'] = 1 if card.get('event_status') == 'ready' else 0
        enriched['review_required_count'] = 1 if card.get('event_status') == 'partial' else 0
        enriched['manual_intervention_count'] = 1 if card.get('event_status') == 'manual_intervention' else 0
        enriched['blocked_count'] = 1 if card.get('event_status') == 'blocked' else 0
        enriched['source_summary'] = card.get('source_summary', {})
        enriched_cards.append(enriched)

    # Dashboard summary
    control_plane_dashboard_summary = {
        'dashboard_status': dashboard_status,
        'event_count': event_count,
        'portfolio_status': portfolio_status,
        'ready_events': ready_events,
        'partial_events': partial_events,
        'blocked_events': blocked_events,
        'dashboard_cards': enriched_cards,
        'priority_queue': priority_queue,
        'escalation_queue': escalation_queue,
        'dashboard_sections': dashboard_sections
    }

    return {
        'control_plane_dashboard_status': dashboard_status,
        'event_count': event_count,
        'portfolio_status': portfolio_status,
        'ready_events': ready_events,
        'partial_events': partial_events,
        'blocked_events': blocked_events,
        'dashboard_cards': enriched_cards,
        'priority_queue': priority_queue,
        'escalation_queue': escalation_queue,
        'dashboard_sections': dashboard_sections,
        'control_plane_dashboard_summary': control_plane_dashboard_summary
    }
