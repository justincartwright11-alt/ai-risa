"""
AI-RISA Draft Report Pack Workflow
Consumes report_skeleton_pack output and emits deterministic per-bout draft report inputs and an event-level draft readiness summary for downstream final report generation.
"""

def draft_report_pack(report_skeleton_pack_result):
    event_name = report_skeleton_pack_result.get("event_name")
    ready_report_skeletons = report_skeleton_pack_result.get("ready_report_skeletons", [])
    blocked_report_skeletons = report_skeleton_pack_result.get("blocked_report_skeletons", [])
    ready_bout_indices = report_skeleton_pack_result.get("ready_bout_indices", [])
    blocked_bout_indices = report_skeleton_pack_result.get("blocked_bout_indices", [])
    blocker_summary = report_skeleton_pack_result.get("blocker_summary", [])
    report_skeleton_pack_summary = report_skeleton_pack_result.get("report_skeleton_pack_summary", {})

    ready_draft_reports = []
    blocked_draft_reports = []

    # Ready draft reports
    for skeleton in ready_report_skeletons:
        bundle = {
            "event_name": event_name,
            "bout_index": skeleton.get("bout_index"),
            "draft_report_status": "ready",
            "fighter_a": skeleton.get("fighter_a"),
            "fighter_b": skeleton.get("fighter_b"),
            "weight_class": skeleton.get("weight_class"),
            "scheduled_rounds": skeleton.get("scheduled_rounds"),
            "is_title_fight": skeleton.get("is_title_fight"),
            "draft_sections": {
                "headline": None,
                "matchup_summary": None,
                "fighter_a_section": None,
                "fighter_b_section": None,
                "tactical_section": None,
                "risk_flags": None,
                "readiness_notes": None
            },
            "report_skeleton_snapshot": skeleton,
            "narrative_snapshot": skeleton.get("narrative_snapshot")
        }
        ready_draft_reports.append(bundle)

    # Blocked draft reports
    for skeleton in blocked_report_skeletons:
        blocker_reason = skeleton.get("blocker_reason")
        if isinstance(blocker_reason, list):
            blocker_reason = blocker_reason[0] if blocker_reason else None
        bundle = {
            "event_name": event_name,
            "bout_index": skeleton.get("bout_index"),
            "draft_report_status": "blocked",
            "blocker_reason": blocker_reason,
            "report_skeleton_snapshot": skeleton
        }
        blocked_draft_reports.append(bundle)

    total_bouts = len(ready_draft_reports) + len(blocked_draft_reports)
    # Draft readiness
    if len(ready_draft_reports) == total_bouts and total_bouts > 0:
        draft_report_pack_status = "ready"
    elif len(ready_draft_reports) > 0:
        draft_report_pack_status = "partial"
    else:
        draft_report_pack_status = "blocked"

    result = {
        "event_name": event_name,
        "draft_report_pack_status": draft_report_pack_status,
        "total_bouts": total_bouts,
        "ready_draft_reports": ready_draft_reports,
        "blocked_draft_reports": blocked_draft_reports,
        "ready_bout_indices": ready_bout_indices,
        "blocked_bout_indices": blocked_bout_indices,
        "blocker_summary": blocker_summary,
        "draft_report_pack_summary": {
            "event_name": event_name,
            "draft_report_pack_status": draft_report_pack_status,
            "total_bouts": total_bouts,
            "ready_draft_reports": len(ready_draft_reports),
            "blocked_draft_reports": len(blocked_draft_reports),
            "has_ready_draft_reports": len(ready_draft_reports) > 0,
            "has_blocked_draft_reports": len(blocked_draft_reports) > 0,
            "ready_bout_indices": ready_bout_indices,
            "blocked_bout_indices": blocked_bout_indices,
            "blocker_summary": blocker_summary
        }
    }
    return result
