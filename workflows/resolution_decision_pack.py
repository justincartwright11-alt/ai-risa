"""
AI-RISA resolution_decision_pack workflow
Consumes escalation_routing_pack output and emits deterministic resolution decision bundle.
"""

def resolution_decision_pack(escalation_routing_pack_result):
    """
    Args:
        escalation_routing_pack_result (dict):
            {
                'event_name': str,
                'escalation_routing_status': str,
                'routed_actions': list,
                'blocked_routes': list,
                'ready_bout_indices': list,
                'blocked_bout_indices': list,
                'blocker_summary': dict,
                'escalation_summary': dict
            }
    Returns:
        dict: {
            'event_name': str,
            'resolution_decision_status': str,
            'resolved_entries': list,
            'blocked_resolutions': list,
            'ready_bout_indices': list,
            'blocked_bout_indices': list,
            'blocker_summary': dict,
            'resolution_decision_summary': dict
        }
    """
    event_name = escalation_routing_pack_result['event_name']
    routed_actions = escalation_routing_pack_result.get('routed_actions', [])
    blocked_routes = escalation_routing_pack_result.get('blocked_routes', [])
    ready_bout_indices = escalation_routing_pack_result.get('ready_bout_indices', [])
    blocked_bout_indices = escalation_routing_pack_result.get('blocked_bout_indices', [])
    blocker_summary = escalation_routing_pack_result.get('blocker_summary', {})

    # Status rule
    if routed_actions and not blocked_routes:
        resolution_decision_status = 'ready'
    elif routed_actions and blocked_routes:
        resolution_decision_status = 'partial'
    else:
        resolution_decision_status = 'blocked'

    resolved_entries = []
    for action in routed_actions:
        route_target = action.get('route_target')
        if route_target == 'publish_path':
            resolution_action = 'publish'
            resolution_reason = 'publish-path'
        elif route_target == 'operator_review':
            resolution_action = 'review'
            resolution_reason = 'operator-review-path'
        elif route_target == 'manual_intervention':
            resolution_action = 'manual_hold'
            resolution_reason = 'manual-intervention-path'
        else:
            resolution_action = 'publish'
            resolution_reason = 'default-publish'
        resolved_entries.append({
            'event_name': event_name,
            'bout_index': action['bout_index'],
            'resolution_status': 'ready',
            'delivery_key': action.get('delivery_key'),
            'publication_label': action.get('publication_label'),
            'publication_order': action.get('publication_order'),
            'governance_action': action.get('governance_action'),
            'route_target': route_target,
            'resolution_action': resolution_action,
            'resolution_reason': resolution_reason,
            'routing_snapshot': action
        })

    blocked_resolutions = []
    for action in blocked_routes:
        blocked_resolutions.append({
            'event_name': event_name,
            'bout_index': action['bout_index'],
            'resolution_status': 'blocked',
            'blocker_reason': action.get('blocker_reason'),
            'routing_snapshot': action
        })

    resolution_decision_summary = {
        'resolution_decision_status': resolution_decision_status,
        'resolved_count': len(resolved_entries),
        'blocked_count': len(blocked_resolutions)
    }

    return {
        'event_name': event_name,
        'resolution_decision_status': resolution_decision_status,
        'resolved_entries': resolved_entries,
        'blocked_resolutions': blocked_resolutions,
        'ready_bout_indices': ready_bout_indices,
        'blocked_bout_indices': blocked_bout_indices,
        'blocker_summary': blocker_summary,
        'resolution_decision_summary': resolution_decision_summary
    }
