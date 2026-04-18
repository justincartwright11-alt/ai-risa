"""
AI-RISA Delivery Bundle Pack Workflow
Consumes publication_manifest_pack output and emits a deterministic event-level delivery bundle for consumer-facing delivery.
"""

def delivery_bundle_pack(publication_manifest_pack_result):
    event_name = publication_manifest_pack_result.get("event_name")
    publishable_reports = publication_manifest_pack_result.get("publishable_reports", [])
    blocked_reports = publication_manifest_pack_result.get("blocked_reports", [])
    publishable_bout_indices = publication_manifest_pack_result.get("publishable_bout_indices", [])
    blocked_bout_indices = publication_manifest_pack_result.get("blocked_bout_indices", [])
    blocker_summary = publication_manifest_pack_result.get("blocker_summary", [])
    publication_manifest_summary = publication_manifest_pack_result.get("publication_manifest_summary", {})

    deliverable_reports = []
    blocked_deliverables = []

    # Deterministic ordering by publication_order
    publishable_reports_sorted = sorted(publishable_reports, key=lambda x: x.get("publication_order", 0))
    blocked_reports_sorted = sorted(blocked_reports, key=lambda x: x.get("bout_index", 0))

    # Deliverable bundles
    for report in publishable_reports_sorted:
        delivery_key = f"{event_name}_delivery_{report.get('bout_index')}"
        bundle = {
            "event_name": event_name,
            "bout_index": report.get("bout_index"),
            "delivery_status": "deliverable",
            "fighter_a": report.get("fighter_a"),
            "fighter_b": report.get("fighter_b"),
            "weight_class": report.get("weight_class"),
            "scheduled_rounds": report.get("scheduled_rounds"),
            "is_title_fight": report.get("is_title_fight"),
            "publication_label": report.get("publication_label"),
            "publication_order": report.get("publication_order"),
            "delivery_key": delivery_key,
            "release_snapshot": report.get("release_snapshot"),
            "manifest_snapshot": report
        }
        deliverable_reports.append(bundle)

    # Blocked bundles
    for report in blocked_reports_sorted:
        blocker_reason = report.get("blocker_reason")
        if isinstance(blocker_reason, list):
            blocker_reason = blocker_reason[0] if blocker_reason else None
        bundle = {
            "event_name": event_name,
            "bout_index": report.get("bout_index"),
            "delivery_status": "blocked",
            "blocker_reason": blocker_reason,
            "release_snapshot": report.get("release_snapshot"),
            "manifest_snapshot": report
        }
        blocked_deliverables.append(bundle)

    total_bouts = len(deliverable_reports) + len(blocked_deliverables)
    # Delivery bundle status
    if len(deliverable_reports) == total_bouts and total_bouts > 0:
        delivery_bundle_status = "ready"
    elif len(deliverable_reports) > 0:
        delivery_bundle_status = "partial"
    else:
        delivery_bundle_status = "blocked"

    result = {
        "event_name": event_name,
        "delivery_bundle_status": delivery_bundle_status,
        "total_bouts": total_bouts,
        "deliverable_reports": deliverable_reports,
        "blocked_deliverables": blocked_deliverables,
        "deliverable_bout_indices": publishable_bout_indices,
        "blocked_bout_indices": blocked_bout_indices,
        "blocker_summary": blocker_summary,
        "delivery_bundle_summary": {
            "event_name": event_name,
            "delivery_bundle_status": delivery_bundle_status,
            "total_bouts": total_bouts,
            "deliverable_reports": len(deliverable_reports),
            "blocked_deliverables": len(blocked_deliverables),
            "has_deliverable_reports": len(deliverable_reports) > 0,
            "has_blocked_deliverables": len(blocked_deliverables) > 0,
            "deliverable_bout_indices": publishable_bout_indices,
            "blocked_bout_indices": blocked_bout_indices,
            "blocker_summary": blocker_summary
        }
    }
    return result
