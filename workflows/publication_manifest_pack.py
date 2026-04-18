"""
AI-RISA Publication Manifest Pack Workflow
Consumes report_release_pack output and emits a deterministic event-level publication manifest for external delivery/readout.
"""

def publication_manifest_pack(report_release_pack_result):
    event_name = report_release_pack_result.get("event_name")
    ready_release_reports = report_release_pack_result.get("ready_release_reports", [])
    blocked_release_reports = report_release_pack_result.get("blocked_release_reports", [])
    ready_bout_indices = report_release_pack_result.get("ready_bout_indices", [])
    blocked_bout_indices = report_release_pack_result.get("blocked_bout_indices", [])
    blocker_summary = report_release_pack_result.get("blocker_summary", [])
    report_release_pack_summary = report_release_pack_result.get("report_release_pack_summary", {})

    publishable_reports = []
    blocked_reports = []

    # Deterministic ordering by bout_index
    ready_release_reports_sorted = sorted(ready_release_reports, key=lambda x: x.get("bout_index", 0))
    blocked_release_reports_sorted = sorted(blocked_release_reports, key=lambda x: x.get("bout_index", 0))

    # Publishable manifest bundles
    for order, release in enumerate(ready_release_reports_sorted):
        bundle = {
            "event_name": event_name,
            "bout_index": release.get("bout_index"),
            "publication_status": "publishable",
            "fighter_a": release.get("fighter_a"),
            "fighter_b": release.get("fighter_b"),
            "weight_class": release.get("weight_class"),
            "scheduled_rounds": release.get("scheduled_rounds"),
            "is_title_fight": release.get("is_title_fight"),
            "release_snapshot": release,
            "publication_label": f"{event_name}_bout_{release.get('bout_index')}",
            "publication_order": order
        }
        publishable_reports.append(bundle)

    # Blocked manifest bundles
    for release in blocked_release_reports_sorted:
        blocker_reason = release.get("blocker_reason")
        if isinstance(blocker_reason, list):
            blocker_reason = blocker_reason[0] if blocker_reason else None
        bundle = {
            "event_name": event_name,
            "bout_index": release.get("bout_index"),
            "publication_status": "blocked",
            "blocker_reason": blocker_reason,
            "release_snapshot": release
        }
        blocked_reports.append(bundle)

    total_bouts = len(publishable_reports) + len(blocked_reports)
    # Manifest status
    if len(publishable_reports) == total_bouts and total_bouts > 0:
        publication_manifest_status = "ready"
    elif len(publishable_reports) > 0:
        publication_manifest_status = "partial"
    else:
        publication_manifest_status = "blocked"

    result = {
        "event_name": event_name,
        "publication_manifest_status": publication_manifest_status,
        "total_bouts": total_bouts,
        "publishable_reports": publishable_reports,
        "blocked_reports": blocked_reports,
        "publishable_bout_indices": ready_bout_indices,
        "blocked_bout_indices": blocked_bout_indices,
        "blocker_summary": blocker_summary,
        "publication_manifest_summary": {
            "event_name": event_name,
            "publication_manifest_status": publication_manifest_status,
            "total_bouts": total_bouts,
            "publishable_reports": len(publishable_reports),
            "blocked_reports": len(blocked_reports),
            "has_publishable_reports": len(publishable_reports) > 0,
            "has_blocked_reports": len(blocked_reports) > 0,
            "publishable_bout_indices": ready_bout_indices,
            "blocked_bout_indices": blocked_bout_indices,
            "blocker_summary": blocker_summary
        }
    }
    return result
