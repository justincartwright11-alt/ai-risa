"""
AI-RISA Report Brief Pack Workflow
Consumes bout_dossier_pack output and emits deterministic event-level and per-bout report briefs for downstream report writing.
"""

def report_brief_pack(bout_dossier_pack_result):
    event_name = bout_dossier_pack_result.get("event_name")
    dossiers_ready = bout_dossier_pack_result.get("ready_bout_dossiers", [])
    dossiers_blocked = bout_dossier_pack_result.get("blocked_bout_dossiers", [])
    ready_bout_indices = bout_dossier_pack_result.get("ready_bout_indices", [])
    blocked_bout_indices = bout_dossier_pack_result.get("blocked_bout_indices", [])
    blocker_summary = bout_dossier_pack_result.get("blocker_summary", [])
    total_bouts = len(dossiers_ready) + len(dossiers_blocked)
    ready_bout_briefs = []
    blocked_bout_briefs = []
    # Ready briefs
    for dossier in dossiers_ready:
        brief = {
            "event_name": event_name,
            "bout_index": dossier.get("bout_index"),
            "brief_status": "ready",
            "fighter_a": dossier.get("fighter_a"),
            "fighter_b": dossier.get("fighter_b"),
            "weight_class": dossier.get("weight_class"),
            "scheduled_rounds": dossier.get("scheduled_rounds"),
            "is_title_fight": dossier.get("is_title_fight"),
            "dossier_snapshot": dossier
        }
        ready_bout_briefs.append(brief)
    # Blocked briefs
    for dossier in dossiers_blocked:
        brief = {
            "event_name": event_name,
            "bout_index": dossier.get("bout_index"),
            "brief_status": "blocked",
            "blocker_reason": dossier.get("blocker_reason"),
            "dossier_snapshot": dossier
        }
        blocked_bout_briefs.append(brief)
    # Brief pack status
    if len(ready_bout_briefs) == total_bouts and total_bouts > 0:
        report_brief_status = "ready"
    elif len(ready_bout_briefs) > 0:
        report_brief_status = "partial"
    else:
        report_brief_status = "blocked"
    result = {
        "event_name": event_name,
        "report_brief_status": report_brief_status,
        "ready_bout_briefs": ready_bout_briefs,
        "blocked_bout_briefs": blocked_bout_briefs,
        "ready_bout_indices": ready_bout_indices,
        "blocked_bout_indices": blocked_bout_indices,
        "blocker_summary": blocker_summary,
        "report_brief_pack_summary": {
            "event_name": event_name,
            "report_brief_status": report_brief_status,
            "total_bouts": total_bouts,
            "ready_bout_briefs": len(ready_bout_briefs),
            "blocked_bout_briefs": len(blocked_bout_briefs),
            "has_ready_bout_briefs": len(ready_bout_briefs) > 0,
            "has_blocked_bout_briefs": len(blocked_bout_briefs) > 0,
            "ready_bout_indices": ready_bout_indices,
            "blocked_bout_indices": blocked_bout_indices,
            "blocker_summary": blocker_summary
        }
    }
    return result
