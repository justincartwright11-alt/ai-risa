"""
AI-RISA Bout Dossier Pack Workflow
Consumes scouting_input_pack output and emits deterministic per-bout dossier bundles for downstream report writing.
"""

def bout_dossier_pack(scouting_input_pack_result):
    event_name = scouting_input_pack_result.get("event_name")
    scouting_pack_status = scouting_input_pack_result.get("scouting_pack_status")
    ready_scouting_candidates = scouting_input_pack_result.get("ready_scouting_candidates", [])
    blocked_scouting_candidates = scouting_input_pack_result.get("blocked_scouting_candidates", [])
    ready_bout_indices = scouting_input_pack_result.get("ready_bout_indices", [])
    blocked_bout_indices = scouting_input_pack_result.get("blocked_bout_indices", [])
    blocker_summary = scouting_input_pack_result.get("blocker_summary", [])
    total_bouts = len(ready_scouting_candidates) + len(blocked_scouting_candidates)
    ready_bout_dossiers = []
    blocked_bout_dossiers = []
    # Ready dossiers
    for bundle in ready_scouting_candidates:
        dossier = {
            "event_name": event_name,
            "bout_index": bundle.get("bout_index"),
            "dossier_status": "ready",
            "fighter_a": bundle.get("fighter_a"),
            "fighter_b": bundle.get("fighter_b"),
            "weight_class": bundle.get("weight_class"),
            "scheduled_rounds": bundle.get("scheduled_rounds"),
            "is_title_fight": bundle.get("is_title_fight"),
            "scouting_bundle_snapshot": bundle,
            "source_summary": scouting_input_pack_result.get("scouting_input_pack_summary", {})
        }
        ready_bout_dossiers.append(dossier)
    # Blocked dossiers
    for bundle in blocked_scouting_candidates:
        dossier = {
            "event_name": event_name,
            "bout_index": bundle.get("bout_index"),
            "dossier_status": "blocked",
            "blocker_reason": bundle.get("blocker_reason"),
            "scouting_bundle_snapshot": bundle,
            "source_summary": scouting_input_pack_result.get("scouting_input_pack_summary", {})
        }
        blocked_bout_dossiers.append(dossier)
    # Dossier pack status
    if len(ready_bout_dossiers) == total_bouts and total_bouts > 0:
        dossier_pack_status = "ready"
    elif len(ready_bout_dossiers) > 0:
        dossier_pack_status = "partial"
    else:
        dossier_pack_status = "blocked"
    result = {
        "event_name": event_name,
        "scouting_pack_status": scouting_pack_status,
        "dossier_pack_status": dossier_pack_status,
        "total_bouts": total_bouts,
        "ready_bout_dossiers": ready_bout_dossiers,
        "blocked_bout_dossiers": blocked_bout_dossiers,
        "ready_bout_indices": ready_bout_indices,
        "blocked_bout_indices": blocked_bout_indices,
        "blocker_summary": blocker_summary,
        "bout_dossier_pack_summary": {
            "event_name": event_name,
            "dossier_pack_status": dossier_pack_status,
            "total_bouts": total_bouts,
            "ready_bout_dossiers": len(ready_bout_dossiers),
            "blocked_bout_dossiers": len(blocked_bout_dossiers),
            "has_ready_bout_dossiers": len(ready_bout_dossiers) > 0,
            "has_blocked_bout_dossiers": len(blocked_bout_dossiers) > 0,
            "ready_bout_indices": ready_bout_indices,
            "blocked_bout_indices": blocked_bout_indices,
            "blocker_summary": blocker_summary
        }
    }
    return result
