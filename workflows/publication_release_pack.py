def publication_release_pack(operator_review_pack_result):
    """
    Consumes operator_review_pack_result and emits a deterministic publication release bundle for controlled release actions.
    Contract is strictly deterministic: no randomness, stable ordering, no timestamps.
    """
    event_name = operator_review_pack_result["event_name"]
    operator_review_status = operator_review_pack_result["operator_review_status"]
    reviewable_exports = operator_review_pack_result["reviewable_exports"]
    blocked_exports = operator_review_pack_result["blocked_exports"]
    review_flags = operator_review_pack_result["review_flags"]
    blocker_summary = operator_review_pack_result["blocker_summary"]

    # Compose release_ready_exports
    release_ready_exports = []
    release_ready_bout_indices = []
    for export in sorted(reviewable_exports, key=lambda r: (r.get("publication_order", 0), r["bout_index"])):
        release_ready_bout_indices.append(export["bout_index"])
        release_ready_exports.append({
            "event_name": export["event_name"],
            "bout_index": export["bout_index"],
            "release_status": "release_ready",
            "delivery_key": export["delivery_key"],
            "publication_label": export["publication_label"],
            "publication_order": export.get("publication_order", 0),
            "fighter_a": export.get("fighter_a"),
            "fighter_b": export.get("fighter_b"),
            "release_notes": [],
            "operator_review_snapshot": export
        })

    # Compose blocked_releases
    blocked_releases = []
    blocked_bout_indices = []
    for blocked in sorted(blocked_exports, key=lambda r: r["bout_index"]):
        blocked_bout_indices.append(blocked["bout_index"])
        blocked_releases.append({
            "event_name": blocked["event_name"],
            "bout_index": blocked["bout_index"],
            "release_status": "blocked",
            "blocker_reason": blocked.get("blocker_reason"),
            "operator_review_snapshot": blocked
        })

    # Compose publication_release_status
    if len(release_ready_exports) == 0:
        publication_release_status = "blocked"
    elif len(blocked_releases) == 0:
        publication_release_status = "ready"
    else:
        publication_release_status = "partial"

    # Compose publication_release_summary
    publication_release_summary = {
        "event_name": event_name,
        "publication_release_status": publication_release_status,
        "release_ready_count": len(release_ready_exports),
        "blocked_count": len(blocked_releases)
    }

    return {
        "event_name": event_name,
        "publication_release_status": publication_release_status,
        "release_ready_exports": release_ready_exports,
        "blocked_releases": blocked_releases,
        "release_ready_bout_indices": release_ready_bout_indices,
        "blocked_bout_indices": blocked_bout_indices,
        "review_flags": review_flags,
        "blocker_summary": blocker_summary,
        "publication_release_summary": publication_release_summary
    }
