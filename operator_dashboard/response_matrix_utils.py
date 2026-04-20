"""
response_matrix_utils.py
Build 23: Aggregates a deterministic operator response matrix/playbook from backend signals.
"""
import time
from . import (
    queue_utils, evidence_utils, comparison_utils, timeline_utils, anomaly_utils,
    watchlist_utils, digest_utils, escalation_utils, review_queue_utils, briefing_utils,
    casefile_utils, portfolio_utils, control_summary_utils, integrity_utils, drift_utils, forecast_utils, action_ledger_utils
)

def get_operator_response_matrix():
    now = int(time.time())
    errors = []
    # Gather all signals (read-only, deterministic)
    try:
        control_summary = control_summary_utils.aggregate_control_summary()
    except Exception as e:
        control_summary = {}
        errors.append(f"control_summary: {e}")
    try:
        integrity = integrity_utils.aggregate_integrity()
    except Exception as e:
        integrity = {}
        errors.append(f"integrity: {e}")
    try:
        drift = drift_utils.aggregate_drift()
    except Exception as e:
        drift = {}
        errors.append(f"drift: {e}")
    try:
        portfolio = portfolio_utils.aggregate_portfolio()
    except Exception as e:
        portfolio = {}
        errors.append(f"portfolio: {e}")
    try:
        forecast = forecast_utils.get_operator_forecast()
    except Exception as e:
        forecast = {}
        errors.append(f"forecast: {e}")
    # Matrix logic
    matrix_status = 'quiet'
    top_issue = 'none'
    why_it_matters = ''
    recommended_paths = []
    stabilizing_signals = []
    worsening_signals = []
    first_surface = ''
    second_surface = ''
    third_surface = ''
    summary = 'No urgent operator inspection required.'
    recommendation = 'Monitor dashboard as usual.'
    # Example logic: escalate if forecast, drift, or integrity signals are not ok
    if not forecast.get('ok', True) or not drift.get('ok', True) or not integrity.get('ok', True):
        matrix_status = 'guided'
        top_issue = 'Signal anomaly detected'
        why_it_matters = 'One or more core signals indicate possible risk or anomaly.'
        summary = 'Operator guidance recommended.'
        recommendation = 'Inspect surfaces in recommended order.'
        # Example path
        recommended_paths.append({
            'issue': 'Signal anomaly',
            'why': why_it_matters,
            'inspect_first': 'control-summary',
            'inspect_next': 'integrity',
            'trend': 'worsening' if not forecast.get('ok', True) else 'uncertain'
        })
        first_surface = 'control-summary'
        second_surface = 'integrity'
        third_surface = 'drift'
        worsening_signals.append('Signal anomaly present')
    # If portfolio risk band is not stable
    elif portfolio.get('risk_band') and portfolio['risk_band'] != 'stable':
        matrix_status = 'urgent'
        top_issue = f"Portfolio risk: {portfolio['risk_band']}"
        why_it_matters = 'Portfolio risk band is elevated.'
        summary = 'Urgent operator inspection recommended.'
        recommendation = 'Start with portfolio, then control-summary, then drift.'
        recommended_paths.append({
            'issue': top_issue,
            'why': why_it_matters,
            'inspect_first': 'portfolio',
            'inspect_next': 'control-summary',
            'trend': 'worsening'
        })
        first_surface = 'portfolio'
        second_surface = 'control-summary'
        third_surface = 'drift'
        worsening_signals.append(f"Portfolio risk: {portfolio['risk_band']}")
    else:
        matrix_status = 'quiet'
        top_issue = 'none'
        why_it_matters = 'No material risk detected.'
        summary = 'No urgent operator inspection required.'
        recommendation = 'Monitor dashboard as usual.'
        recommended_paths.append({
            'issue': 'none',
            'why': why_it_matters,
            'inspect_first': 'portfolio',
            'inspect_next': 'control-summary',
            'trend': 'stable'
        })
        first_surface = 'portfolio'
        second_surface = 'control-summary'
        third_surface = 'drift'
        stabilizing_signals.append('All core signals stable')
    # Deterministic ordering
    recommended_paths = sorted(recommended_paths, key=lambda x: x['issue'])
    stabilizing_signals = sorted(set(stabilizing_signals))
    worsening_signals = sorted(set(worsening_signals))
    return {
        'ok': True,
        'timestamp': now,
        'matrix_status': matrix_status,
        'top_issue': top_issue,
        'why_it_matters': why_it_matters,
        'recommended_paths': recommended_paths,
        'stabilizing_signals': stabilizing_signals,
        'worsening_signals': worsening_signals,
        'first_surface': first_surface,
        'second_surface': second_surface,
        'third_surface': third_surface,
        'summary': summary,
        'recommendation': recommendation,
        'errors': errors
    }
