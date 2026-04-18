"""
AI-RISA Coverage Readiness Workflow
Consumes event_decomposition output, classifies bout coverage, emits fighter gap candidates, and produces a deterministic readiness summary.
"""

def classify_bout_coverage(bout):
    """Return 'complete' if both fighters present/non-blank, else 'incomplete'."""
    a = bout.get("fighter_a")
    b = bout.get("fighter_b")
    if a and b:
        return "complete"
    return "incomplete"

def make_gap_candidate(event_name, bout_index, side, bout):
    fighter_id = bout.get(f"fighter_{side}")
    return {
        "task_type": "fighter_gap_real_grounding",
        "fighter_id": fighter_id or f"missing_{side}_{event_name}_{bout_index}",
        "source_event_name": event_name,
        "source_bout_index": bout_index,
        "missing_side": side,
        "reason": "missing_or_blank_fighter"
    }

def coverage_readiness(event_artifact):
    event_name = event_artifact.get("event_name")
    bouts = event_artifact.get("discovered_bout_slots", [])
    total_bouts = len(bouts)
    complete_bout_indices = []
    incomplete_bout_indices = []
    fighter_gap_candidates = []
    for idx, bout in enumerate(bouts):
        coverage = classify_bout_coverage(bout)
        if coverage == "complete":
            complete_bout_indices.append(idx)
        else:
            incomplete_bout_indices.append(idx)
            # Emit only one deterministic gap candidate per incomplete bout
            if not bout.get("fighter_a"):
                fighter_gap_candidates.append(make_gap_candidate(event_name, idx, "a", bout))
            elif not bout.get("fighter_b"):
                fighter_gap_candidates.append(make_gap_candidate(event_name, idx, "b", bout))
    complete_bouts = len(complete_bout_indices)
    incomplete_bouts = len(incomplete_bout_indices)
    if complete_bouts == total_bouts and total_bouts > 0:
        readiness_status = "ready"
    elif complete_bouts > 0:
        readiness_status = "partial"
    else:
        readiness_status = "blocked"
    result = {
        "event_name": event_name,
        "readiness_status": readiness_status,
        "total_bouts": total_bouts,
        "complete_bouts": complete_bouts,
        "incomplete_bouts": incomplete_bouts,
        "fighter_gap_candidate_count": len(fighter_gap_candidates),
        "fighter_gap_candidates": fighter_gap_candidates,
        "complete_bout_indices": complete_bout_indices,
        "incomplete_bout_indices": incomplete_bout_indices,
        "readiness_summary": {
            "event_name": event_name,
            "readiness_status": readiness_status,
            "total_bouts": total_bouts,
            "complete_bouts": complete_bouts,
            "incomplete_bouts": incomplete_bouts,
            "fighter_gap_candidate_count": len(fighter_gap_candidates)
        }
    }
    return result
