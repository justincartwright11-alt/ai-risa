"""
AI-RISA Final Report Pack Workflow
Consumes draft_report_pack output and emits deterministic per-bout final report bundles and an event-level final-report readiness summary for downstream final report generation.
"""

def final_report_pack(draft_report_pack_result):
    event_name = draft_report_pack_result.get("event_name")
    ready_draft_reports = draft_report_pack_result.get("ready_draft_reports", [])
    blocked_draft_reports = draft_report_pack_result.get("blocked_draft_reports", [])
    ready_bout_indices = draft_report_pack_result.get("ready_bout_indices", [])
    blocked_bout_indices = draft_report_pack_result.get("blocked_bout_indices", [])
    blocker_summary = draft_report_pack_result.get("blocker_summary", [])
    draft_report_pack_summary = draft_report_pack_result.get("draft_report_pack_summary", {})

    ready_final_reports = []
    blocked_final_reports = []

    # Ready final reports
    for draft in ready_draft_reports:
        bundle = {
            "event_name": event_name,
            "bout_index": draft.get("bout_index"),
            "final_report_status": "ready",
            "fighter_a": draft.get("fighter_a"),
            "fighter_b": draft.get("fighter_b"),
            "weight_class": draft.get("weight_class"),
            "scheduled_rounds": draft.get("scheduled_rounds"),
            "is_title_fight": draft.get("is_title_fight"),
            "final_report_sections": {
                "headline": None,
                "executive_summary": None,
                "fighter_a_analysis": None,
                "fighter_b_analysis": None,
                "matchup_dynamics": None,
                "risk_flags": None,
                "final_readiness_notes": None
            },
            "draft_report_snapshot": draft,
            "report_skeleton_snapshot": draft.get("report_skeleton_snapshot")
        }
        ready_final_reports.append(bundle)

    # Blocked final reports
    for draft in blocked_draft_reports:
        blocker_reason = draft.get("blocker_reason")
        if isinstance(blocker_reason, list):
            blocker_reason = blocker_reason[0] if blocker_reason else None
        bundle = {
            "event_name": event_name,
            "bout_index": draft.get("bout_index"),
            "final_report_status": "blocked",
            "blocker_reason": blocker_reason,
            "draft_report_snapshot": draft
        }
        blocked_final_reports.append(bundle)

    total_bouts = len(ready_final_reports) + len(blocked_final_reports)
    # Final report readiness
    if len(ready_final_reports) == total_bouts and total_bouts > 0:
        final_report_pack_status = "ready"
    elif len(ready_final_reports) > 0:
        final_report_pack_status = "partial"
    else:
        final_report_pack_status = "blocked"

    result = {
        "event_name": event_name,
        "final_report_pack_status": final_report_pack_status,
        "total_bouts": total_bouts,
        "ready_final_reports": ready_final_reports,
        "blocked_final_reports": blocked_final_reports,
        "ready_bout_indices": ready_bout_indices,
        "blocked_bout_indices": blocked_bout_indices,
        "blocker_summary": blocker_summary,
        "final_report_pack_summary": {
            "event_name": event_name,
            "final_report_pack_status": final_report_pack_status,
            "total_bouts": total_bouts,
            "ready_final_reports": len(ready_final_reports),
            "blocked_final_reports": len(blocked_final_reports),
            "has_ready_final_reports": len(ready_final_reports) > 0,
            "has_blocked_final_reports": len(blocked_final_reports) > 0,
            "ready_bout_indices": ready_bout_indices,
            "blocked_bout_indices": blocked_bout_indices,
            "blocker_summary": blocker_summary
        }
    }
    return result
