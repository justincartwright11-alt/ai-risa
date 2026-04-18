"""
AI-RISA event_dashboard_pack workflow
Consumes event_control_summary_pack output and emits a dashboard-ready event view.
"""

def event_dashboard_pack(event_control_summary_pack_result, bout_metadata=None):
    """
    Args:
        event_control_summary_pack_result (dict):
            {
                'event_name': str,
                'event_control_status': str,
                'total_bouts': int,
                'publish_ready_count': int,
                'review_required_count': int,
                'manual_intervention_count': int,
                'blocked_count': int,
                'ready_bout_indices': list,
                'blocked_bout_indices': list,
                'blocker_summary': dict,
                'decision_summary': dict,
                'event_control_summary': dict
            }
        bout_metadata (dict or None):
            Optional. Dict mapping bout_index to metadata, e.g. {'fighter_a': ..., 'fighter_b': ..., 'priority': ..., 'notes': ...}
    Returns:
        dict: {
            'event_name': str,
            'event_dashboard_status': str,
            'total_bouts': int,
            'publish_ready_count': int,
            'review_required_count': int,
            'manual_intervention_count': int,
            'blocked_count': int,
            'ready_bout_indices': list,
            'blocked_bout_indices': list,
            'blocker_summary': dict,
            'dashboard_cards': list,
            'event_dashboard_summary': dict
        }
    """
    event_name = event_control_summary_pack_result['event_name']
    total_bouts = event_control_summary_pack_result['total_bouts']
    publish_ready_count = event_control_summary_pack_result['publish_ready_count']
    review_required_count = event_control_summary_pack_result['review_required_count']
    manual_intervention_count = event_control_summary_pack_result['manual_intervention_count']
    blocked_count = event_control_summary_pack_result['blocked_count']
    ready_bout_indices = event_control_summary_pack_result['ready_bout_indices']
    blocked_bout_indices = event_control_summary_pack_result['blocked_bout_indices']
    blocker_summary = event_control_summary_pack_result['blocker_summary']
    decision_summary = event_control_summary_pack_result.get('decision_summary', {})

    # Status rule
    if publish_ready_count == total_bouts and total_bouts > 0:
        event_dashboard_status = 'ready'
    elif publish_ready_count > 0:
        event_dashboard_status = 'partial'
    else:
        event_dashboard_status = 'blocked'

    dashboard_cards = []
    for i in range(total_bouts):
        if bout_metadata and i in bout_metadata:
            meta = bout_metadata[i]
            fighter_a = meta.get('fighter_a', f'FighterA_{i}')
            fighter_b = meta.get('fighter_b', f'FighterB_{i}')
            priority = meta.get('priority', 'normal')
            notes = meta.get('notes', '')
        else:
            fighter_a = f'FighterA_{i}'
            fighter_b = f'FighterB_{i}'
            priority = 'normal'
            notes = ''
        if i in ready_bout_indices:
            status = 'publish-ready'
            decision = 'publish'
        elif i in blocked_bout_indices:
            status = 'blocked'
            decision = 'block'
        else:
            status = 'pending'
            decision = 'review'
        dashboard_cards.append({
            'bout_index': i,
            'fighter_a': fighter_a,
            'fighter_b': fighter_b,
            'status': status,
            'decision': decision,
            'priority': priority,
            'notes': notes
        })

    event_dashboard_summary = {
        'event_dashboard_status': event_dashboard_status,
        'total_bouts': total_bouts,
        'dashboard_cards': dashboard_cards
    }

    return {
        'event_name': event_name,
        'event_dashboard_status': event_dashboard_status,
        'total_bouts': total_bouts,
        'publish_ready_count': publish_ready_count,
        'review_required_count': review_required_count,
        'manual_intervention_count': manual_intervention_count,
        'blocked_count': blocked_count,
        'ready_bout_indices': ready_bout_indices,
        'blocked_bout_indices': blocked_bout_indices,
        'blocker_summary': blocker_summary,
        'dashboard_cards': dashboard_cards,
        'event_dashboard_summary': event_dashboard_summary
    }
