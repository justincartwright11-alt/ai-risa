def export_bundle_pack(delivery_bundle_pack_result):
    """
    Consumes delivery_bundle_pack_result and emits a deterministic event-level export bundle for downstream publishing or operator review.
    Contract is strictly deterministic: no timestamps, no randomness, stable ordering by publication_order then bout_index.
    """
    event_name = delivery_bundle_pack_result["event_name"]
    delivery_bundle_status = delivery_bundle_pack_result["delivery_bundle_status"]
    deliverable_reports = delivery_bundle_pack_result["deliverable_reports"]
    blocked_deliverables = delivery_bundle_pack_result["blocked_deliverables"]
    deliverable_bout_indices = delivery_bundle_pack_result["deliverable_bout_indices"]
    blocked_bout_indices = delivery_bundle_pack_result["blocked_bout_indices"]
    blocker_summary = delivery_bundle_pack_result["blocker_summary"]
    delivery_bundle_summary = delivery_bundle_pack_result["delivery_bundle_summary"]

    # Compose deliverable_exports
    deliverable_exports = []
    for report in sorted(deliverable_reports, key=lambda r: (r["publication_order"], r["bout_index"])):
        export_payload = {
            "metadata": {
                "event_name": report["event_name"],
                "bout_index": report["bout_index"],
                "publication_label": report["publication_label"],
                "delivery_key": report["delivery_key"]
            },
            "release_sections": report.get("release_snapshot", {}).get("sections", {}),
            "audit_summary": report.get("manifest_snapshot", {}).get("audit_summary", {})
        }
        deliverable_exports.append({
            "event_name": report["event_name"],
            "bout_index": report["bout_index"],
            "export_status": "deliverable",
            "delivery_key": report["delivery_key"],
            "publication_label": report["publication_label"],
            "publication_order": report["publication_order"],
            "fighter_a": report.get("fighter_a"),
            "fighter_b": report.get("fighter_b"),
            "weight_class": report.get("weight_class"),
            "scheduled_rounds": report.get("scheduled_rounds"),
            "is_title_fight": report.get("is_title_fight"),
            "export_payload": export_payload,
            "delivery_snapshot": report.get("release_snapshot")
        })

    # Compose blocked_exports
    blocked_exports = []
    for blocked in sorted(blocked_deliverables, key=lambda r: r["bout_index"]):
        blocked_exports.append({
            "event_name": blocked["event_name"],
            "bout_index": blocked["bout_index"],
            "export_status": "blocked",
            "blocker_reason": blocked.get("blocker_reason"),
            "delivery_snapshot": blocked.get("release_snapshot")
        })

    # Compose export_manifest
    export_manifest = {
        "event_name": event_name,
        "deliverable_count": len(deliverable_exports),
        "blocked_count": len(blocked_exports),
        "deliverable_bout_indices": deliverable_bout_indices,
        "blocked_bout_indices": blocked_bout_indices,
        "publication_labels": [d["publication_label"] for d in deliverable_exports],
        "delivery_keys": [d["delivery_key"] for d in deliverable_exports]
    }

    # Compose export_bundle_status
    if len(deliverable_exports) == 0:
        export_bundle_status = "blocked"
    elif len(blocked_exports) == 0:
        export_bundle_status = "ready"
    else:
        export_bundle_status = "partial"

    # Compose export_bundle_summary
    export_bundle_summary = {
        "event_name": event_name,
        "export_bundle_status": export_bundle_status,
        "deliverable_count": len(deliverable_exports),
        "blocked_count": len(blocked_exports)
    }

    return {
        "event_name": event_name,
        "export_bundle_status": export_bundle_status,
        "total_bouts": len(deliverable_exports) + len(blocked_exports),
        "deliverable_exports": deliverable_exports,
        "blocked_exports": blocked_exports,
        "deliverable_bout_indices": deliverable_bout_indices,
        "blocked_bout_indices": blocked_bout_indices,
        "blocker_summary": blocker_summary,
        "export_manifest": export_manifest,
        "export_bundle_summary": export_bundle_summary
    }
