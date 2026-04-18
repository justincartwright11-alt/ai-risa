"""
AI-RISA Scouting Input Pack Workflow
Consumes report_candidate_pack output and emits deterministic per-bout scouting input bundles for downstream report generation.
"""

def scouting_input_pack(report_candidate_pack_result):
    event_name = report_candidate_pack_result.get("event_name")
    ready_candidates = report_candidate_pack_result.get("ready_report_candidates", [])
    blocked_candidates = report_candidate_pack_result.get("blocked_report_candidates", [])
    ready_bout_indices = report_candidate_pack_result.get("ready_bout_indices", [])
    blocked_bout_indices = report_candidate_pack_result.get("blocked_bout_indices", [])
    blocker_summary = report_candidate_pack_result.get("blocker_summary", [])
    pack_summary = report_candidate_pack_result.get("report_candidate_pack_summary", {})
    total_candidates = len(ready_candidates) + len(blocked_candidates)
    ready_scouting_candidates = []
    blocked_scouting_candidates = []
    # Ready scouting bundles
    for candidate in ready_candidates:
        bundle = {
            "event_name": event_name,
            "bout_index": candidate.get("bout_index"),
            "scouting_status": "ready",
            "fighter_a": candidate.get("fighter_a"),
            "fighter_b": candidate.get("fighter_b"),
            "weight_class": candidate.get("weight_class"),
            "scheduled_rounds": candidate.get("scheduled_rounds"),
            "is_title_fight": candidate.get("is_title_fight"),
            "source_summary": pack_summary,
            "report_candidate_snapshot": candidate
        }
        ready_scouting_candidates.append(bundle)
    # Blocked scouting bundles
    for candidate in blocked_candidates:
        idx = candidate.get("bout_index")
        blocker_reason = None
        for b in blocker_summary:
            if b.get("bout_index") == idx:
                blocker_reason = b.get("blocker_reasons")
                break
        bundle = {
            "event_name": event_name,
            "bout_index": idx,
            "scouting_status": "blocked",
            "blocker_reason": blocker_reason,
            "report_candidate_snapshot": candidate
        }
        blocked_scouting_candidates.append(bundle)
    # Scouting pack status
    if len(ready_scouting_candidates) == total_candidates and total_candidates > 0:
        scouting_pack_status = "ready"
    elif len(ready_scouting_candidates) > 0:
        scouting_pack_status = "partial"
    else:
        scouting_pack_status = "blocked"
    result = {
        "event_name": event_name,
        "scouting_pack_status": scouting_pack_status,
        "total_candidates": total_candidates,
        "ready_scouting_candidates": ready_scouting_candidates,
        "blocked_scouting_candidates": blocked_scouting_candidates,
        "ready_bout_indices": ready_bout_indices,
        "blocked_bout_indices": blocked_bout_indices,
        "blocker_summary": blocker_summary,
        "scouting_input_pack_summary": {
            "event_name": event_name,
            "scouting_pack_status": scouting_pack_status,
            "total_candidates": total_candidates,
            "ready_candidates": len(ready_scouting_candidates),
            "blocked_candidates": len(blocked_scouting_candidates),
            "has_ready_candidates": len(ready_scouting_candidates) > 0,
            "has_blocked_candidates": len(blocked_scouting_candidates) > 0,
            "ready_bout_indices": ready_bout_indices,
            "blocked_bout_indices": blocked_bout_indices,
            "blocker_summary": blocker_summary
        }
    }
    return result
