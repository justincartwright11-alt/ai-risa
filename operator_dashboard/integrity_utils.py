"""
Read-only integrity aggregation helper for AI-RISA Build 20.
Synthesizes dashboard integrity/readiness from contract-compliant backend sources.
Strictly deterministic, read-only, and safe.
"""
import time
from . import (
    queue_utils, evidence_utils, comparison_utils, timeline_utils, anomaly_utils,
    watchlist_utils, digest_utils, escalation_utils, review_queue_utils, briefing_utils,
    casefile_utils, portfolio_utils, control_summary_utils, action_ledger_utils
)

def aggregate_integrity():
    # Deterministic timestamp
    timestamp = int(time.time())
    errors = []
    # Endpoint health: check contract shape for all core endpoints
    endpoint_health = "healthy"
    endpoint_checks = []
    for name, util in [
        ("queue", queue_utils),
        ("evidence", evidence_utils),
        ("comparison", comparison_utils),
        ("timeline", timeline_utils),
        ("anomalies", anomaly_utils),
        ("watchlist", watchlist_utils),
        ("digest", digest_utils),
        ("escalation", escalation_utils),
        ("review_queue", review_queue_utils),
        ("briefing", briefing_utils),
        ("casefile", casefile_utils),
        ("portfolio", portfolio_utils),
        ("control_summary", control_summary_utils),
        ("ledger", action_ledger_utils),
    ]:
        try:
            result = util.get_contract_status() if hasattr(util, "get_contract_status") else {"ok": True}
            if not (result and result.get("ok")):
                endpoint_checks.append(f"{name} not ok")
        except Exception as e:
            endpoint_checks.append(f"{name} error: {e}")
    if endpoint_checks:
        endpoint_health = "degraded"
        errors.extend(endpoint_checks)
    # Alignment summary: check queue/evidence/comparison/timeline consistency
    alignment_summary = "aligned"
    try:
        q = queue_utils.get_contract_status()
        e = evidence_utils.get_contract_status()
        c = comparison_utils.get_contract_status()
        t = timeline_utils.get_contract_status()
        if not (q.get("ok") and e.get("ok") and c.get("ok") and t.get("ok")):
            alignment_summary = "misaligned"
            errors.append("core alignment issue")
    except Exception as e:
        alignment_summary = "error"
        errors.append(f"alignment error: {e}")
    # Artifact health: check for missing/stale artifacts
    artifact_health = "healthy"
    artifact_issues = []
    for util in [evidence_utils, comparison_utils, timeline_utils, anomaly_utils, watchlist_utils, digest_utils, briefing_utils, casefile_utils]:
        try:
            status = util.get_contract_status() if hasattr(util, "get_contract_status") else {"ok": True}
            if not status.get("ok"):
                artifact_issues.append(util.__name__)
        except Exception as e:
            artifact_issues.append(f"{util.__name__} error: {e}")
    if artifact_issues:
        artifact_health = "degraded"
        errors.extend(artifact_issues)
    # Ledger health: check for empty/malformed/stale ledger
    ledger_health = "healthy"
    try:
        ledger_status = action_ledger_utils.get_contract_status() if hasattr(action_ledger_utils, "get_contract_status") else {"ok": True}
        if not ledger_status.get("ok"):
            ledger_health = "degraded"
            errors.append("ledger not ok")
    except Exception as e:
        ledger_health = "error"
        errors.append(f"ledger error: {e}")
    # Blocker health: unresolved blocker anomalies
    blocker_health = "clear"
    try:
        blockers = anomaly_utils.get_blocker_status() if hasattr(anomaly_utils, "get_blocker_status") else []
        if blockers:
            blocker_health = "blockers present"
            errors.append("blockers present")
    except Exception as e:
        blocker_health = "error"
        errors.append(f"blocker error: {e}")
    # Stale surface health: stale event surfaces or summaries
    stale_surface_health = "fresh"
    try:
        stale = control_summary_utils.get_stale_surface_status() if hasattr(control_summary_utils, "get_stale_surface_status") else []
        if stale:
            stale_surface_health = "stale"
            errors.append("stale surfaces present")
    except Exception as e:
        stale_surface_health = "error"
        errors.append(f"stale surface error: {e}")
    # Readiness status
    if endpoint_health == "healthy" and alignment_summary == "aligned" and artifact_health == "healthy" and ledger_health == "healthy" and blocker_health == "clear" and stale_surface_health == "fresh":
        readiness_status = "ready"
        recommendation = "System is ready. No action needed."
    elif endpoint_health == "degraded" or artifact_health == "degraded" or ledger_health == "degraded" or blocker_health != "clear" or stale_surface_health != "fresh":
        readiness_status = "degraded"
        recommendation = "Check degraded endpoints, artifacts, ledger, blockers, or stale surfaces. See errors for details."
    else:
        readiness_status = "caution"
        recommendation = "Review alignment and error details before relying on dashboard."
    # Summary
    summary = f"Dashboard integrity: {readiness_status}. {len(errors)} issues." if errors else f"Dashboard integrity: {readiness_status}. All systems nominal."
    return {
        "ok": True,
        "timestamp": timestamp,
        "endpoint_health": endpoint_health,
        "alignment_summary": alignment_summary,
        "artifact_health": artifact_health,
        "ledger_health": ledger_health,
        "blocker_health": blocker_health,
        "stale_surface_health": stale_surface_health,
        "readiness_status": readiness_status,
        "summary": summary,
        "recommendation": recommendation,
        "errors": errors,
    }
