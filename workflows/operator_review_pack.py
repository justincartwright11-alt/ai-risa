def operator_review_pack(export_bundle_pack_result):
    """
    Consumes export_bundle_pack_result and emits a deterministic operator review bundle for human review before publication.
    Contract is strictly deterministic: no randomness, stable ordering, no timestamps.
    """
    event_name = export_bundle_pack_result["event_name"]
    export_bundle_status = export_bundle_pack_result["export_bundle_status"]
    deliverable_exports = export_bundle_pack_result["deliverable_exports"]
    blocked_exports = export_bundle_pack_result["blocked_exports"]
    blocker_summary = export_bundle_pack_result["blocker_summary"]

    # Compose reviewable_exports
    reviewable_exports = []
    for export in sorted(deliverable_exports, key=lambda r: (r["publication_order"], r["bout_index"])):
        reviewable_exports.append({
            "event_name": export["event_name"],
            "bout_index": export["bout_index"],
            "review_status": "reviewable",
            "delivery_key": export["delivery_key"],
            "publication_label": export["publication_label"],
            "fighter_a": export.get("fighter_a"),
            "fighter_b": export.get("fighter_b"),
            "review_notes": [],
            "export_snapshot": export
        })

    # Compose blocked_exports
    blocked_review_exports = []
    for blocked in sorted(blocked_exports, key=lambda r: r["bout_index"]):
        blocked_review_exports.append({
            "event_name": blocked["event_name"],
            "bout_index": blocked["bout_index"],
            "review_status": "blocked",
            "blocker_reason": blocked.get("blocker_reason"),
            "export_snapshot": blocked
        })

    # Compose review_flags
    review_flags = {}
    for r in reviewable_exports:
        # Deterministic: no flags by default, but structure is present
        review_flags[r["bout_index"]] = []
    for b in blocked_review_exports:
        review_flags[b["bout_index"]] = [b.get("blocker_reason")] if b.get("blocker_reason") else []

    # Compose operator_review_status
    if len(reviewable_exports) == 0:
        operator_review_status = "blocked"
    elif len(blocked_review_exports) == 0:
        operator_review_status = "ready"
    else:
        operator_review_status = "partial"

    # Compose operator_review_summary
    operator_review_summary = {
        "event_name": event_name,
        "operator_review_status": operator_review_status,
        "reviewable_count": len(reviewable_exports),
        "blocked_count": len(blocked_review_exports)
    }

    return {
        "event_name": event_name,
        "operator_review_status": operator_review_status,
        "reviewable_exports": reviewable_exports,
        "blocked_exports": blocked_review_exports,
        "review_flags": review_flags,
        "blocker_summary": blocker_summary,
        "operator_review_summary": operator_review_summary
    }
