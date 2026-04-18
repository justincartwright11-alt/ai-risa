"""
AI-RISA Report Skeleton Pack Workflow
Consumes narrative_input_pack output and emits deterministic per-bout report skeletons and an event-level draft-readiness summary for downstream final report generation.
"""

def report_skeleton_pack(narrative_input_pack_result):
    event_name = narrative_input_pack_result.get("event_name")
    narrative_pack_status = narrative_input_pack_result.get("narrative_pack_status")
    ready_narrative_inputs = narrative_input_pack_result.get("ready_narrative_inputs", [])
    blocked_narrative_inputs = narrative_input_pack_result.get("blocked_narrative_inputs", [])
    ready_bout_indices = narrative_input_pack_result.get("ready_bout_indices", [])
    blocked_bout_indices = narrative_input_pack_result.get("blocked_bout_indices", [])
    blocker_summary = narrative_input_pack_result.get("blocker_summary", [])
    narrative_input_pack_summary = narrative_input_pack_result.get("narrative_input_pack_summary", {})

    ready_report_skeletons = []
    blocked_report_skeletons = []

    # Ready skeletons
    for bundle in ready_narrative_inputs:
        skeleton = {
            "event_name": event_name,
            "bout_index": bundle.get("bout_index"),
            "report_skeleton_status": "ready",
            "fighter_a": bundle.get("fighter_a"),
            "fighter_b": bundle.get("fighter_b"),
            "weight_class": bundle.get("weight_class"),
            "scheduled_rounds": bundle.get("scheduled_rounds"),
            "is_title_fight": bundle.get("is_title_fight"),
            "skeleton_sections": {
                "matchup_overview": None,
                "fighter_a_profile": None,
                "fighter_b_profile": None,
                "tactical_themes": None,
                "readiness_notes": None
            },
            "narrative_snapshot": bundle,
            "report_brief_snapshot": bundle.get("report_brief_snapshot")
        }
        ready_report_skeletons.append(skeleton)

    # Blocked skeletons
    for bundle in blocked_narrative_inputs:
        blocker_reason = bundle.get("blocker_reason")
        # Deterministically carry forward as a string
        if isinstance(blocker_reason, list):
            blocker_reason = blocker_reason[0] if blocker_reason else None
        skeleton = {
            "event_name": event_name,
            "bout_index": bundle.get("bout_index"),
            "report_skeleton_status": "blocked",
            "blocker_reason": blocker_reason,
            "narrative_snapshot": bundle
        }
        blocked_report_skeletons.append(skeleton)

    total_bouts = len(ready_report_skeletons) + len(blocked_report_skeletons)
    # Draft readiness
    if len(ready_report_skeletons) == total_bouts and total_bouts > 0:
        report_skeleton_pack_status = "ready"
    elif len(ready_report_skeletons) > 0:
        report_skeleton_pack_status = "partial"
    else:
        report_skeleton_pack_status = "blocked"

    result = {
        "event_name": event_name,
        "report_skeleton_pack_status": report_skeleton_pack_status,
        "total_bouts": total_bouts,
        "ready_report_skeletons": ready_report_skeletons,
        "blocked_report_skeletons": blocked_report_skeletons,
        "ready_bout_indices": ready_bout_indices,
        "blocked_bout_indices": blocked_bout_indices,
        "blocker_summary": blocker_summary,
        "report_skeleton_pack_summary": {
            "event_name": event_name,
            "report_skeleton_pack_status": report_skeleton_pack_status,
            "total_bouts": total_bouts,
            "ready_report_skeletons": len(ready_report_skeletons),
            "blocked_report_skeletons": len(blocked_report_skeletons),
            "has_ready_report_skeletons": len(ready_report_skeletons) > 0,
            "has_blocked_report_skeletons": len(blocked_report_skeletons) > 0,
            "ready_bout_indices": ready_bout_indices,
            "blocked_bout_indices": blocked_bout_indices,
            "blocker_summary": blocker_summary
        }
    }
    return result
