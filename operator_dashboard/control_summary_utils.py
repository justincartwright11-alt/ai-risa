# Control summary aggregation logic for Build 19
from datetime import datetime
from operator_dashboard.queue_utils import safe_read_queue
from operator_dashboard.portfolio_utils import aggregate_portfolio
from operator_dashboard.escalation_utils import aggregate_escalations
from operator_dashboard.review_queue_utils import aggregate_review_queue
from operator_dashboard.briefing_utils import aggregate_briefing
from operator_dashboard.timeline_utils import get_recent_timeline_changes
from operator_dashboard.action_ledger_utils import get_recent_operator_actions

def aggregate_control_summary():
    # Initialize summary dictionary
    summary = {
        'total_tracked_events': 0,
        'pressure_band_counts': {},
        'escalation_status_counts': {},
        'review_status_counts': {},
        'briefing_status_counts': {},
        'top_urgent_events': [],
        'recent_changes': [],
        'timestamp': '2000-01-01T00:00:00Z',
        'summary': '',
        'recommendation': '',
        'ok': True,
        'errors': []
    }
    
    try:
        # Total tracked events
        try:
            queue = safe_read_queue()
            if isinstance(queue, dict) and queue.get('ok') is False:
                summary['errors'].extend(queue.get('errors', []))
                queue_rows = []
            else:
                queue_rows = (queue.get('rows', []) if isinstance(queue, dict) else []) or []
        except Exception as e:
            summary['errors'].append(f"safe_read_queue error: {e}")
            queue_rows = []
        summary['total_tracked_events'] = len(queue_rows)

        # Pressure band counts
        try:
            portfolio = aggregate_portfolio()
            if isinstance(portfolio, dict) and portfolio.get('ok') is False:
                summary['errors'].extend(portfolio.get('errors', []))
                portfolio_events = []
            else:
                if isinstance(portfolio, dict):
                    portfolio_events = portfolio.get('portfolio') or portfolio.get('events') or []
                else:
                    portfolio_events = []
        except Exception as e:
            summary['errors'].append(f"aggregate_portfolio error: {e}")
            portfolio_events = []
        
        pb_counts = {}
        for event in portfolio_events:
            if isinstance(event, dict):
                band = event.get('pressure_band', 'unknown')
                pb_counts[band] = pb_counts.get(band, 0) + 1
        summary['pressure_band_counts'] = pb_counts

        # Escalation status counts
        try:
            esc = aggregate_escalations()
            if isinstance(esc, dict) and esc.get('ok') is False:
                summary['errors'].extend(esc.get('errors', []))
                esc_events = []
            else:
                if isinstance(esc, dict):
                    esc_events = esc.get('escalations') or esc.get('events') or []
                else:
                    esc_events = []
        except Exception as e:
            summary['errors'].append(f"aggregate_escalations error: {e}")
            esc_events = []
        
        esc_counts = {}
        for e in esc_events:
            if isinstance(e, dict):
                status = e.get('escalation_level', 'none')
                esc_counts[status] = esc_counts.get(status, 0) + 1
        summary['escalation_status_counts'] = esc_counts

        # Review status counts
        try:
            review = aggregate_review_queue()
            if isinstance(review, dict) and review.get('ok') is False:
                summary['errors'].extend(review.get('errors', []))
                review_events = []
            else:
                if isinstance(review, dict):
                    review_events = review.get('review_queue') or review.get('events') or []
                else:
                    review_events = []
        except Exception as e:
            summary['errors'].append(f"aggregate_review_queue error: {e}")
            review_events = []
        
        review_counts = {}
        for e in review_events:
            if isinstance(e, dict):
                status = e.get('review_status') or e.get('review_priority', 'none')
                review_counts[status] = review_counts.get(status, 0) + 1
        summary['review_status_counts'] = review_counts

        # Briefing status counts
        try:
            briefing = aggregate_briefing()
            if isinstance(briefing, dict) and briefing.get('ok') is False:
                summary['errors'].extend(briefing.get('errors', []))
                briefing_events = []
            else:
                if isinstance(briefing, dict):
                    briefing_events = briefing.get('briefings') or briefing.get('events') or []
                else:
                    briefing_events = []
        except Exception as e:
            summary['errors'].append(f"aggregate_briefing error: {e}")
            briefing_events = []
        
        briefing_counts = {}
        for e in briefing_events:
            if isinstance(e, dict):
                status = e.get('briefing_status', 'none')
                briefing_counts[status] = briefing_counts.get(status, 0) + 1
        summary['briefing_status_counts'] = briefing_counts

        # Top urgent events (by portfolio score, descending)
        if portfolio_events:
            valid_events = [e for e in portfolio_events if isinstance(e, dict)]
            events_sorted = sorted(valid_events, key=lambda x: -x.get('portfolio_score', 0))
            summary['top_urgent_events'] = [e.get('event_id') for e in events_sorted[:5]]
        else:
            summary['top_urgent_events'] = []

        # Recent changes (from timeline and ledger)
        try:
            timeline_changes = get_recent_timeline_changes(limit=5)
            ledger_changes = get_recent_operator_actions(limit=5)
            if not isinstance(timeline_changes, list): timeline_changes = []
            if not isinstance(ledger_changes, list): ledger_changes = []
            all_changes = [c for c in timeline_changes if isinstance(c, dict)] + [c for c in ledger_changes if isinstance(c, dict)]
            all_changes_sorted = sorted(all_changes, key=lambda x: x.get('timestamp', ''), reverse=True)
            summary['recent_changes'] = all_changes_sorted[:5]
        except Exception as e:
            summary['errors'].append(f"Recent changes error: {e}")
            summary['recent_changes'] = []

        # Deterministic timestamp: use most recent change, else fixed value
        if summary['recent_changes'] and 'timestamp' in summary['recent_changes'][0]:
            summary['timestamp'] = summary['recent_changes'][0]['timestamp']
        else:
            summary['timestamp'] = '2000-01-01T00:00:00Z'

        # Summary and recommendation
        if summary['top_urgent_events']:
            summary['summary'] = f"{len(summary['top_urgent_events'])} urgent events require attention."
            summary['recommendation'] = f"Review event(s): {', '.join(summary['top_urgent_events'])} immediately."
        elif summary['total_tracked_events'] == 0:
            summary['summary'] = "No events are currently tracked."
            summary['recommendation'] = "No action required."
        else:
            summary['summary'] = "System is stable. No urgent events."
            summary['recommendation'] = "Monitor for changes."
        
        summary['ok'] = len(summary['errors']) == 0
    except Exception as e:
        summary['ok'] = False
        summary['errors'].append(str(e))
    
    return summary


def get_contract_status():
    return {'ok': True}
