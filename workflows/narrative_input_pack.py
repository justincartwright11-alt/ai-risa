"""
AI-RISA Narrative Input Pack Workflow
Consumes report_brief_pack output and emits deterministic per-bout narrative/report input bundles and an event-level narrative readiness summary for downstream report generation.
"""

def narrative_input_pack(report_brief_pack_result):
    event_name = report_brief_pack_result.get("event_name")
    ready_briefs = report_brief_pack_result.get("ready_bout_briefs", [])
    blocked_briefs = report_brief_pack_result.get("blocked_bout_briefs", [])
    ready_bout_indices = report_brief_pack_result.get("ready_bout_indices", [])
    blocked_bout_indices = report_brief_pack_result.get("blocked_bout_indices", [])
    blocker_summary = report_brief_pack_result.get("blocker_summary", [])
    pack_summary = report_brief_pack_result.get("report_brief_pack_summary", {})
    total_bouts = len(ready_briefs) + len(blocked_briefs)
    ready_narrative_inputs = []
    blocked_narrative_inputs = []
    # Ready narrative bundles
    for brief in ready_briefs:
        dossier = brief.get("dossier_snapshot", {})
        bundle = {
            "event_name": event_name,
            "bout_index": brief.get("bout_index"),
            "narrative_status": "ready",
            "fighter_a": brief.get("fighter_a"),
            "fighter_b": brief.get("fighter_b"),
            "weight_class": brief.get("weight_class"),
            "scheduled_rounds": brief.get("scheduled_rounds"),
            "is_title_fight": brief.get("is_title_fight"),
            "brief_summary": pack_summary,
            "dossier_snapshot": dossier,
            "report_brief_snapshot": brief
        }
        ready_narrative_inputs.append(bundle)
    # Blocked narrative bundles
    for brief in blocked_briefs:
        bundle = {
            "event_name": event_name,
            "bout_index": brief.get("bout_index"),
            "narrative_status": "blocked",
            "blocker_reason": brief.get("blocker_reason"),
            "report_brief_snapshot": brief
        }
        blocked_narrative_inputs.append(bundle)
    # Narrative pack status
    if len(ready_narrative_inputs) == total_bouts and total_bouts > 0:
        narrative_pack_status = "ready"
    elif len(ready_narrative_inputs) > 0:
        narrative_pack_status = "partial"
    else:
        narrative_pack_status = "blocked"
    result = {
        "event_name": event_name,
        "narrative_pack_status": narrative_pack_status,
        "total_bouts": total_bouts,
        "ready_narrative_inputs": ready_narrative_inputs,
        "blocked_narrative_inputs": blocked_narrative_inputs,
        "ready_bout_indices": ready_bout_indices,
        "blocked_bout_indices": blocked_bout_indices,
        "blocker_summary": blocker_summary,
        "narrative_input_pack_summary": {
            "event_name": event_name,
            "narrative_pack_status": narrative_pack_status,
            "total_bouts": total_bouts,
            "ready_narrative_inputs": len(ready_narrative_inputs),
            "blocked_narrative_inputs": len(blocked_narrative_inputs),
            "has_ready_narrative_inputs": len(ready_narrative_inputs) > 0,
            "has_blocked_narrative_inputs": len(blocked_narrative_inputs) > 0,
            "ready_bout_indices": ready_bout_indices,
            "blocked_bout_indices": blocked_bout_indices,
            "blocker_summary": blocker_summary
        }
    }
    return result
