"""
AI-RISA escalation_routing_pack workflow
Consumes automation_governance_pack output and emits deterministic escalation routing bundle.
"""

def escalation_routing_pack(automation_governance_pack_result):
    """
    Args:
        automation_governance_pack_result (dict):
            {
                'event_name': str,
                'automation_governance_status': str,
                'governance_ready_entries': list,
                'blocked_governance_entries': list,
                'ready_bout_indices': list,
                'blocked_bout_indices': list,
                'blocker_summary': dict,
                'escalation_flags': dict,
                'automation_governance_summary': dict
            }
    Returns:
        dict: {
            'event_name': str,
            'escalation_routing_status': str,
            'routed_actions': list,
            'blocked_routes': list,
            'ready_bout_indices': list,
            'blocked_bout_indices': list,
            'blocker_summary': dict,
            'escalation_summary': dict
        }
    """
    event_name = automation_governance_pack_result['event_name']
    governance_ready_entries = automation_governance_pack_result.get('governance_ready_entries', [])
    blocked_governance_entries = automation_governance_pack_result.get('blocked_governance_entries', [])
    ready_bout_indices = automation_governance_pack_result.get('ready_bout_indices', [])
    blocked_bout_indices = automation_governance_pack_result.get('blocked_bout_indices', [])
    blocker_summary = automation_governance_pack_result.get('blocker_summary', {})

    # Status rule
    if governance_ready_entries and not blocked_governance_entries:
        escalation_routing_status = 'ready'
    elif governance_ready_entries and blocked_governance_entries:
        escalation_routing_status = 'partial'
    else:
        escalation_routing_status = 'blocked'

    routed_actions = []
    for entry in governance_ready_entries:
        action = entry.get('governance_action')
        escalation_level = entry.get('escalation_level')
        if action == 'proceed' and escalation_level == 'none':
            route_target = 'publish_path'
        elif action == 'escalate' or escalation_level == 'operator_review':
            route_target = 'operator_review'
        elif escalation_level == 'manual_intervention':
            route_target = 'manual_intervention'
        else:
            route_target = 'publish_path'
        routed_actions.append({
            'event_name': event_name,
            'bout_index': entry['bout_index'],
            'routing_status': 'ready',
            'delivery_key': entry.get('delivery_key'),
            'publication_label': entry.get('publication_label'),
            'publication_order': entry.get('publication_order'),
            'governance_action': action,
            'governance_reason': entry.get('governance_reason'),
            'escalation_level': escalation_level,
            'route_target': route_target,
            'automation_state_snapshot': entry
        })

    blocked_routes = []
    for entry in blocked_governance_entries:
        escalation_level = entry.get('escalation_level', 'manual_intervention')
        blocked_routes.append({
            'event_name': event_name,
            'bout_index': entry['bout_index'],
            'routing_status': 'blocked',
            'blocker_reason': entry.get('blocker_reason'),
            'automation_state_snapshot': entry
        })

    escalation_summary = {
        'escalation_routing_status': escalation_routing_status,
        'routed_count': len(routed_actions),
        'blocked_count': len(blocked_routes)
    }

    return {
        'event_name': event_name,
        'escalation_routing_status': escalation_routing_status,
        'routed_actions': routed_actions,
        'blocked_routes': blocked_routes,
        'ready_bout_indices': ready_bout_indices,
        'blocked_bout_indices': blocked_bout_indices,
        'blocker_summary': blocker_summary,
        'escalation_summary': escalation_summary
    }
