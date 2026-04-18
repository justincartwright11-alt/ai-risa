def publication_execution_pack(release_audit_pack_result):
    """
    Consumes release_audit_pack_result and emits a deterministic publication execution bundle for controlled publish actions.
    Contract is strictly deterministic: no randomness, stable ordering, no timestamps.
    """
    event_name = release_audit_pack_result["event_name"]
    release_audit_status = release_audit_pack_result["release_audit_status"]
    auditable_releases = release_audit_pack_result["auditable_releases"]
    blocked_audits = release_audit_pack_result["blocked_audits"]
    ready_bout_indices = release_audit_pack_result["release_ready_bout_indices"]
    blocked_bout_indices = release_audit_pack_result["blocked_bout_indices"]
    blocker_summary = release_audit_pack_result["blocker_summary"]

    # Compose executable_publications
    executable_publications = []
    for audit in sorted(auditable_releases, key=lambda r: (r.get("publication_order", 0), r["bout_index"])):
        executable_publications.append({
            "event_name": audit["event_name"],
            "bout_index": audit["bout_index"],
            "execution_status": "executable",
            "delivery_key": audit["delivery_key"],
            "publication_label": audit["publication_label"],
            "publication_order": audit.get("publication_order", 0),
            "execution_action": "publish_ready",  # deterministic placeholder
            "audit_snapshot": audit,
            "release_snapshot": audit.get("release_snapshot")
        })

    # Compose blocked_publications
    blocked_publications = []
    for blocked in sorted(blocked_audits, key=lambda r: r["bout_index"]):
        blocked_publications.append({
            "event_name": blocked["event_name"],
            "bout_index": blocked["bout_index"],
            "execution_status": "blocked",
            "blocker_reason": blocked.get("blocker_reason"),
            "audit_snapshot": blocked
        })

    # Compose publication_execution_status
    if len(executable_publications) == 0:
        publication_execution_status = "blocked"
    elif len(blocked_publications) == 0:
        publication_execution_status = "ready"
    else:
        publication_execution_status = "partial"

    # Compose publication_execution_summary
    publication_execution_summary = {
        "event_name": event_name,
        "publication_execution_status": publication_execution_status,
        "executable_count": len(executable_publications),
        "blocked_count": len(blocked_publications)
    }

    return {
        "event_name": event_name,
        "publication_execution_status": publication_execution_status,
        "executable_publications": executable_publications,
        "blocked_publications": blocked_publications,
        "ready_bout_indices": ready_bout_indices,
        "blocked_bout_indices": blocked_bout_indices,
        "blocker_summary": blocker_summary,
        "publication_execution_summary": publication_execution_summary
    }
