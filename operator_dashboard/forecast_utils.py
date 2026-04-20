# forecast_utils.py
"""
Forecast aggregation logic for AI-RISA Build 22.
Synthesizes read-only forecast/early-warning from existing backend signals.
"""
import time
from . import (
    queue_utils, evidence_utils, comparison_utils, timeline_utils, anomaly_utils,
    watchlist_utils, digest_utils, escalation_utils, review_queue_utils, briefing_utils,
    casefile_utils, portfolio_utils, control_summary_utils, integrity_utils, drift_utils, action_ledger_utils
)

def get_operator_forecast():
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
    # Projected risk bands (simple deterministic logic)
    risk_bands = []
    forecast_status = 'stable'
    early_warning_items = []
    escalation_risk = 'none'
    artifact_risk = 'none'
    blocker_risk = 'none'
    stale_surface_risk = 'none'
    urgent_event_forecast = []
    summary = 'No material risk detected.'
    recommendation = 'No operator action required.'
    # Example: escalate if any drift, integrity, or control summary signals are not ok
    if not control_summary.get('ok', True) or not integrity.get('ok', True) or not drift.get('ok', True):
        forecast_status = 'watch'
        summary = 'Operator attention may be required soon.'
        recommendation = 'Monitor dashboard for changes.'
        if not control_summary.get('ok', True):
            early_warning_items.append('Control summary not ok')
        if not integrity.get('ok', True):
            early_warning_items.append('Integrity not ok')
        if not drift.get('ok', True):
            early_warning_items.append('Drift detected')
    # Portfolio risk band example
    if portfolio.get('risk_band'):
        risk_bands.append(portfolio['risk_band'])
        if portfolio['risk_band'] != 'stable':
            forecast_status = 'elevated'
            summary = 'Elevated risk detected in portfolio.'
            recommendation = 'Review portfolio and related signals.'
            early_warning_items.append(f"Portfolio risk: {portfolio['risk_band']}")
    # Escalation risk example
    if drift.get('escalation_drift'):
        escalation_risk = 'possible'
        early_warning_items.append('Escalation drift present')
    # Artifact risk example
    if integrity.get('artifact_issues'):
        artifact_risk = 'possible'
        early_warning_items.append('Artifact issues detected')
    # Blocker risk example
    if drift.get('blocker_drift'):
        blocker_risk = 'possible'
        early_warning_items.append('Blocker drift present')
    # Stale surface risk example
    if drift.get('stale_surface_drift'):
        stale_surface_risk = 'possible'
        early_warning_items.append('Stale surface drift present')
    # Urgent event forecast (stub: use urgent_event_delta from drift)
    if drift.get('urgent_event_delta'):
        urgent_event_forecast = drift['urgent_event_delta']
    # Deterministic ordering
    early_warning_items = sorted(set(early_warning_items))
    urgent_event_forecast = sorted(urgent_event_forecast)
    return {
        'ok': True,
        'timestamp': now,
        'forecast_status': forecast_status,
        'projected_risk_bands': risk_bands,
        'early_warning_items': early_warning_items,
        'escalation_risk': escalation_risk,
        'artifact_risk': artifact_risk,
        'blocker_risk': blocker_risk,
        'stale_surface_risk': stale_surface_risk,
        'urgent_event_forecast': urgent_event_forecast,
        'summary': summary,
        'recommendation': recommendation,
        'errors': errors
    }
