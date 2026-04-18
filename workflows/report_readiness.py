"""
AI-RISA Coverage-to-Report Readiness Bridge
Consumes coverage_readiness output and produces a deterministic downstream summary for scouting/report generation.
"""

def report_readiness(coverage_result):
    event_name = coverage_result.get("event_name")
    total_bouts = coverage_result.get("total_bouts", 0)
    complete_indices = coverage_result.get("complete_bout_indices", [])
    incomplete_indices = coverage_result.get("incomplete_bout_indices", [])
    gap_candidates = coverage_result.get("fighter_gap_candidates", [])
    gap_count = coverage_result.get("fighter_gap_candidate_count", 0)
    report_ready_indices = list(complete_indices)
    report_blocked_indices = list(incomplete_indices)
    report_ready_bouts = len(report_ready_indices)
    report_blocked_bouts = len(report_blocked_indices)
    if report_ready_bouts == total_bouts and total_bouts > 0:
        reportability_status = "ready"
    elif report_ready_bouts > 0:
        reportability_status = "partial"
    else:
        reportability_status = "blocked"
    result = {
        "event_name": event_name,
        "reportability_status": reportability_status,
        "total_bouts": total_bouts,
        "report_ready_bouts": report_ready_bouts,
        "report_blocked_bouts": report_blocked_bouts,
        "report_ready_indices": report_ready_indices,
        "report_blocked_indices": report_blocked_indices,
        "fighter_gap_candidate_count": gap_count,
        "fighter_gap_candidates": gap_candidates,
        "report_readiness_summary": {
            "event_name": event_name,
            "reportability_status": reportability_status,
            "total_bouts": total_bouts,
            "report_ready_bouts": report_ready_bouts,
            "report_blocked_bouts": report_blocked_bouts,
            "fighter_gap_candidate_count": gap_count,
            "has_blocked_bouts": report_blocked_bouts > 0,
            "has_ready_bouts": report_ready_bouts > 0
        }
    }
    return result
