def release_audit_pack(publication_release_pack_result):
    """
    Consumes publication_release_pack_result and emits a deterministic release audit bundle for traceability before publishing.
    Contract is strictly deterministic: no randomness, stable ordering, no timestamps.
    """
    event_name = publication_release_pack_result["event_name"]
    publication_release_status = publication_release_pack_result["publication_release_status"]
    release_ready_exports = publication_release_pack_result["release_ready_exports"]
    blocked_releases = publication_release_pack_result["blocked_releases"]
    release_ready_bout_indices = publication_release_pack_result["release_ready_bout_indices"]
    blocked_bout_indices = publication_release_pack_result["blocked_bout_indices"]
    review_flags = publication_release_pack_result["review_flags"]
    blocker_summary = publication_release_pack_result["blocker_summary"]
    
    # Compose auditable_releases
    auditable_releases = []
    for export in sorted(release_ready_exports, key=lambda r: (r.get("publication_order", 0), r["bout_index"])):
        audit_checks = {
            "delivery_key_present": bool(export.get("delivery_key")),
            "publication_label_present": bool(export.get("publication_label")),
            "publication_order_present": export.get("publication_order") is not None,
            "fighter_fields_present": bool(export.get("fighter_a")) and bool(export.get("fighter_b")),
            "release_status_valid": export.get("release_status") == "release_ready"
        }
        auditable_releases.append({
            "event_name": export["event_name"],
            "bout_index": export["bout_index"],
            "audit_status": "auditable",
            "delivery_key": export["delivery_key"],
            "publication_label": export["publication_label"],
            "publication_order": export.get("publication_order", 0),
            "fighter_a": export.get("fighter_a"),
            "fighter_b": export.get("fighter_b"),
            "audit_checks": audit_checks,
            "release_snapshot": export,
            "operator_review_snapshot": export.get("operator_review_snapshot")
        })
    
    # Compose blocked_audits
    blocked_audits = []
    for blocked in sorted(blocked_releases, key=lambda r: r["bout_index"]):
        blocked_audits.append({
            "event_name": blocked["event_name"],
            "bout_index": blocked["bout_index"],
            "audit_status": "blocked",
            "blocker_reason": blocked.get("blocker_reason"),
            "release_snapshot": blocked.get("operator_review_snapshot") or blocked
        })
    
    # Compose release_audit_status
    if len(auditable_releases) == 0:
        release_audit_status = "blocked"
    elif len(blocked_audits) == 0:
        release_audit_status = "ready"
    else:
        release_audit_status = "partial"
    
    # Compose release_audit_summary
    release_audit_summary = {
        "event_name": event_name,
        "release_audit_status": release_audit_status,
        "auditable_count": len(auditable_releases),
        "blocked_count": len(blocked_audits)
    }
    
    return {
        "event_name": event_name,
        "release_audit_status": release_audit_status,
        "auditable_releases": auditable_releases,
        "blocked_audits": blocked_audits,
        "release_ready_bout_indices": release_ready_bout_indices,
        "blocked_bout_indices": blocked_bout_indices,
        "review_flags": review_flags,
        "blocker_summary": blocker_summary,
        "release_audit_summary": release_audit_summary
    }
