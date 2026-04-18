def publication_control_pack(release_audit_pack_result):
    """
    Consumes release_audit_pack_result and emits a deterministic publication control bundle for operator-controlled publish decisions.
    Contract is strictly deterministic: no randomness, stable ordering, no timestamps.
    """
    event_name = release_audit_pack_result["event_name"]
    release_audit_status = release_audit_pack_result["release_audit_status"]
    auditable_releases = release_audit_pack_result["auditable_releases"]
    blocked_audits = release_audit_pack_result["blocked_audits"]
    ready_bout_indices = release_audit_pack_result["ready_bout_indices"]
    blocked_bout_indices = release_audit_pack_result["blocked_bout_indices"]
    blocker_summary = release_audit_pack_result["blocker_summary"]

    # Compose approved_publications
    approved_publications = []
    audit_checks_summary = {}
    for audit in sorted(auditable_releases, key=lambda r: (r.get("publication_order", 0), r.get("bout_index", 0))):
        audit_checks_summary[audit.get("bout_index")] = audit.get("audit_checks", {})
        approved_publications.append({
            "bout_index": audit.get("bout_index"),
            "delivery_key": audit.get("delivery_key"),
            "publication_label": audit.get("publication_label"),
            "publication_order": audit.get("publication_order"),
            "fighter_a": audit.get("fighter_a"),
            "fighter_b": audit.get("fighter_b"),
            "execution_action": audit.get("execution_action"),
            "audit_checks": audit.get("audit_checks", {}),
            "audit_snapshot": audit
        })

    # Compose blocked_publications
    blocked_publications = []
    for blocked in sorted(blocked_audits, key=lambda r: r.get("bout_index", 0)):
        blocked_publications.append({
            "bout_index": blocked.get("bout_index"),
            "blocker_reason": blocked.get("blocker_reason"),
            "audit_snapshot": blocked
        })

    # Compose publication_control_status
    if len(approved_publications) == 0:
        publication_control_status = "blocked"
    elif len(blocked_publications) == 0:
        publication_control_status = "ready"
    else:
        publication_control_status = "partial"

    # Compose publication_control_summary
    publication_control_summary = {
        "event_name": event_name,
        "publication_control_status": publication_control_status,
        "approved_count": len(approved_publications),
        "blocked_count": len(blocked_publications)
    }

    return {
        "event_name": event_name,
        "publication_control_status": publication_control_status,
        "approved_publications": approved_publications,
        "blocked_publications": blocked_publications,
        "ready_bout_indices": ready_bout_indices,
        "blocked_bout_indices": blocked_bout_indices,
        "blocker_summary": blocker_summary,
        "audit_checks_summary": audit_checks_summary,
        "publication_control_summary": publication_control_summary
    }
