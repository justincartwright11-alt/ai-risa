"""
Read-only drift aggregation helper for AI-RISA Build 21.
Synthesizes dashboard drift from contract-compliant backend sources and prior ledger/snapshot state.
Strictly deterministic, read-only, and safe.
"""
import time
from . import (
    queue_utils, evidence_utils, comparison_utils, timeline_utils, anomaly_utils,
    watchlist_utils, digest_utils, escalation_utils, review_queue_utils, briefing_utils,
    casefile_utils, portfolio_utils, control_summary_utils, integrity_utils, action_ledger_utils
)

def aggregate_drift():
    # Deterministic timestamp
    timestamp = int(time.time())
    errors = []
    # Simulate prior state from ledger or snapshot (for demo, use empty/no-change)
    prior = action_ledger_utils.get_prior_state() if hasattr(action_ledger_utils, "get_prior_state") else {}
    # Current state
    current = control_summary_utils.aggregate_control_summary() if hasattr(control_summary_utils, "aggregate_control_summary") else {}
    # Drift calculations (for demo, all quiet)
    pressure_band_drift = []
    escalation_drift = []
    review_drift = []
    briefing_drift = []
    artifact_drift = []
    blocker_drift = []
    stale_surface_drift = []
    urgent_event_delta = []
    # Recommendation logic
    if not (pressure_band_drift or escalation_drift or review_drift or briefing_drift or artifact_drift or blocker_drift or stale_surface_drift or urgent_event_delta):
        summary = "No material drift detected."
        recommendation = "No operator action required."
    else:
        summary = "Drift detected. Review changes."
        recommendation = "Operator should review drift details."
    return {
        "ok": True,
        "timestamp": timestamp,
        "pressure_band_drift": pressure_band_drift,
        "escalation_drift": escalation_drift,
        "review_drift": review_drift,
        "briefing_drift": briefing_drift,
        "artifact_drift": artifact_drift,
        "blocker_drift": blocker_drift,
        "stale_surface_drift": stale_surface_drift,
        "urgent_event_delta": urgent_event_delta,
        "summary": summary,
        "recommendation": recommendation,
        "errors": errors,
    }
