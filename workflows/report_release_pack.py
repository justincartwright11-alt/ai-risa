"""
AI-RISA Report Release Pack Workflow
Consumes final_report_pack output and emits deterministic per-bout release-ready report bundles and an event-level release-readiness summary for downstream release.
"""

def report_release_pack(final_report_pack_result):
    event_name = final_report_pack_result.get("event_name")
    ready_final_reports = final_report_pack_result.get("ready_final_reports", [])
    blocked_final_reports = final_report_pack_result.get("blocked_final_reports", [])
    ready_bout_indices = final_report_pack_result.get("ready_bout_indices", [])
    blocked_bout_indices = final_report_pack_result.get("blocked_bout_indices", [])
    blocker_summary = final_report_pack_result.get("blocker_summary", [])
    final_report_pack_summary = final_report_pack_result.get("final_report_pack_summary", {})

    ready_release_reports = []
    blocked_release_reports = []

    # Ready release reports
    for final in ready_final_reports:
        bundle = {
            "event_name": event_name,
            "bout_index": final.get("bout_index"),
            "report_release_status": "ready",
            "fighter_a": final.get("fighter_a"),
            "fighter_b": final.get("fighter_b"),
            "weight_class": final.get("weight_class"),
            "scheduled_rounds": final.get("scheduled_rounds"),
            "is_title_fight": final.get("is_title_fight"),
            "release_sections": {
                "headline": None,
                "release_summary": None,
                "fighter_a_release": None,
                "fighter_b_release": None,
                "matchup_release": None,
                "risk_flags": None,
                "release_notes": None
            },
            "final_report_snapshot": final,
            "draft_report_snapshot": final.get("draft_report_snapshot")
        }
        ready_release_reports.append(bundle)

    # Blocked release reports
    for final in blocked_final_reports:
        blocker_reason = final.get("blocker_reason")
        if isinstance(blocker_reason, list):
            blocker_reason = blocker_reason[0] if blocker_reason else None
        bundle = {
            "event_name": event_name,
            "bout_index": final.get("bout_index"),
            "report_release_status": "blocked",
            "blocker_reason": blocker_reason,
            "final_report_snapshot": final
        }
        blocked_release_reports.append(bundle)

    total_bouts = len(ready_release_reports) + len(blocked_release_reports)
    # Release readiness
    if len(ready_release_reports) == total_bouts and total_bouts > 0:
        report_release_pack_status = "ready"
    elif len(ready_release_reports) > 0:
        report_release_pack_status = "partial"
    else:
        report_release_pack_status = "blocked"

    result = {
        "event_name": event_name,
        "report_release_pack_status": report_release_pack_status,
        "total_bouts": total_bouts,
        "ready_release_reports": ready_release_reports,
        "blocked_release_reports": blocked_release_reports,
        "ready_bout_indices": ready_bout_indices,
        "blocked_bout_indices": blocked_bout_indices,
        "blocker_summary": blocker_summary,
        "report_release_pack_summary": {
            "event_name": event_name,
            "report_release_pack_status": report_release_pack_status,
            "total_bouts": total_bouts,
            "ready_release_reports": len(ready_release_reports),
            "blocked_release_reports": len(blocked_release_reports),
            "has_ready_release_reports": len(ready_release_reports) > 0,
            "has_blocked_release_reports": len(blocked_release_reports) > 0,
            "ready_bout_indices": ready_bout_indices,
            "blocked_bout_indices": blocked_bout_indices,
            "blocker_summary": blocker_summary
        }
    }
    return result
