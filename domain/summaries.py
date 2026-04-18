from .normalization import stable_sorted

def decomposition_summary(raw_bouts, normalized_bouts, bout_errors, event_metadata):
    title_fight_count = sum(1 for b in normalized_bouts if b.get("is_title_fight") is True)
    weight_classes_seen = sorted({b.get("weight_class") for b in normalized_bouts if b.get("weight_class")})
    # Build normalization_actions: one entry per input bout
    error_map = {e["index"]: e["error"] for e in bout_errors if "index" in e and "error" in e}
    norm_bout_map = {b["bout_index"]: b for b in normalized_bouts if "bout_index" in b}
    normalization_actions = []
    for idx in range(len(raw_bouts)):
        if idx in norm_bout_map:
            notes = norm_bout_map[idx].get("normalization_notes", [])
            normalization_actions.append({"bout_index": idx, "notes": notes})
        elif idx in error_map:
            normalization_actions.append({"bout_index": idx, "notes": [error_map[idx]]})
        else:
            normalization_actions.append({"bout_index": idx, "notes": ["unknown"]})
    return {
        "input_bout_count": len(raw_bouts),
        "input_bouts": len(raw_bouts),
        "normalized_bout_count": len(normalized_bouts),
        "normalized_bouts": len(normalized_bouts),
        "invalid_bout_count": len(bout_errors),
        "bout_errors": bout_errors,
        "title_fight_count": title_fight_count,
        "weight_classes_seen": weight_classes_seen,
        "normalization_actions": normalization_actions,
        "event_fields": sorted(list(event_metadata.keys())),
        "status": "ok" if normalized_bouts else "no_valid_bouts"
    }

def intake_summary(input_entry_count, normalized_batch_entries, accepted_count, skipped_count, promotions_seen, normalization_actions):
    return {
        "input_entry_count": input_entry_count,
        "normalized_entry_count": len(normalized_batch_entries),
        "accepted_count": accepted_count,
        "skipped_count": skipped_count,
        "promotions_seen": stable_sorted(promotions_seen),
        "normalization_actions": normalization_actions
    }

def enrichment_summary(fields_present_count, fields_missing_count, fields_enriched_count, coverage_status, enrichment_actions):
    return {
        "fields_present_count": fields_present_count,
        "fields_missing_count": fields_missing_count,
        "fields_enriched_count": fields_enriched_count,
        "coverage_status": coverage_status,
        "enrichment_actions": enrichment_actions
    }
