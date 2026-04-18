"""
AI-RISA Report Candidate Pack Workflow
Consumes event_decomposition and report_readiness outputs, assembles deterministic report candidate bundles for downstream report generation.
"""

def report_candidate_pack(event_decomposition, report_readiness_result):
    event_name = report_readiness_result.get("event_name") or event_decomposition.get("event_name")
    total_bouts = report_readiness_result.get("total_bouts")
    ready_indices = report_readiness_result.get("report_ready_indices", [])
    blocked_indices = report_readiness_result.get("report_blocked_indices", [])
    bouts = event_decomposition.get("discovered_bout_slots", [])
    blocker_summary = []
    ready_report_candidates = []
    blocked_report_candidates = []
    for idx, bout in enumerate(bouts):
        candidate = {
            "event_name": event_name,
            "bout_index": idx,
            "fighter_a": bout.get("fighter_a"),
            "fighter_b": bout.get("fighter_b"),
            "weight_class": bout.get("weight_class"),
            "scheduled_rounds": bout.get("scheduled_rounds"),
            "is_title_fight": bout.get("is_title_fight"),
        }
        if idx in ready_indices:
            ready_report_candidates.append(candidate)
        elif idx in blocked_indices:
            blocked_report_candidates.append(candidate)
            notes = bout.get("normalization_notes") or []
            blocker_summary.append({"bout_index": idx, "blocker_reasons": notes})
    reportability_status = report_readiness_result.get("reportability_status")
    pack_summary = {
        "event_name": event_name,
        "reportability_status": reportability_status,
        "total_bouts": total_bouts,
        "ready_report_candidates": len(ready_report_candidates),
        "blocked_report_candidates": len(blocked_report_candidates),
        "ready_bout_indices": ready_indices,
        "blocked_bout_indices": blocked_indices,
        "blocker_summary": blocker_summary,
        "report_candidate_pack_summary": {
            "event_name": event_name,
            "reportability_status": reportability_status,
            "total_bouts": total_bouts,
            "ready_report_candidates": len(ready_report_candidates),
            "blocked_report_candidates": len(blocked_report_candidates),
            "ready_bout_indices": ready_indices,
            "blocked_bout_indices": blocked_indices,
            "blocker_summary": blocker_summary
        }
    }
    return pack_summary, ready_report_candidates, blocked_report_candidates
