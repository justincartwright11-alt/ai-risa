import html


_EXPECTED_DESTINATION_MARKER = "button2_report_generation_preview"


def _safe_text(value, fallback=""):
    if value is None:
        return fallback
    text = str(value).strip()
    if not text:
        return fallback
    return html.escape(text)


def _base_flags():
    return {
        "preview_only": True,
        "button2_generation_performed": False,
        "pdf_generation_performed": False,
        "file_write_performed": False,
        "export_performed": False,
        "delivery_performed": False,
        "report_write_performed": False,
        "gate2_approval_required": True,
        "profile_create_update_merge": False,
        "database_ranking_writes": False,
        "result_report_learning_calibration": False,
    }


def build_button2_readonly_dossier_handoff_ingest_preview(handoff_payload):
    """Build a preview-only Button 2 ingest context from Button 1 handoff payload."""
    payload = handoff_payload if isinstance(handoff_payload, dict) else {}

    destination_marker = _safe_text(payload.get("destination_marker", ""))
    if destination_marker != _EXPECTED_DESTINATION_MARKER:
        return {
            "ok": False,
            "error": "invalid_destination_marker",
            "destination_marker": destination_marker or "",
            "button2_ingest_preview_context": None,
            **_base_flags(),
        }

    summary_preview = _safe_text(payload.get("dossier_summary_preview", ""), "No dossier summary preview provided.")

    # Build read-only ingest context only; no report generation side effects.
    ingest_context = {
        "destination_marker": _EXPECTED_DESTINATION_MARKER,
        "ingest_mode": "preview_only",
        "context_kind": "button1_dossier_handoff",
        "dossier_summary_preview": summary_preview,
    }

    return {
        "ok": True,
        "destination_marker": _EXPECTED_DESTINATION_MARKER,
        "button2_ingest_preview_context": ingest_context,
        **_base_flags(),
    }
