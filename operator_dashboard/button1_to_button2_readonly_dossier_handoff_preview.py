import html


_ALLOWED_SUMMARY_FIELDS = (
    "fighter_name",
    "promotion",
    "division",
    "record",
    "confidence",
    "source",
)


def _safe_text(value, fallback):
    """Return escaped text for preview-only rendering."""
    if value is None:
        return fallback
    text = str(value).strip()
    if not text:
        return fallback
    return html.escape(text)


def build_button1_to_button2_readonly_dossier_handoff_preview(dossier_data):
    """Build a preview-only read-only handoff object from Button 1 to Button 2."""
    payload = dossier_data if isinstance(dossier_data, dict) else {}

    # Only include explicitly allowed safe summary fields.
    safe_values = {
        key: _safe_text(payload.get(key), "")
        for key in _ALLOWED_SUMMARY_FIELDS
    }

    fighter_name = safe_values["fighter_name"] or "Unknown Fighter"
    promotion = safe_values["promotion"] or "Unknown Promotion"
    division = safe_values["division"] or "Unknown Division"
    record = safe_values["record"] or "0W-0L-0D"
    confidence = safe_values["confidence"] or "Unknown"
    source = safe_values["source"] or "Unknown Source"

    dossier_summary_preview = (
        "Button1 Read-Only Dossier Handoff Preview\n"
        f"Fighter: {fighter_name}\n"
        f"Promotion: {promotion}\n"
        f"Division: {division}\n"
        f"Record: {record}\n"
        f"Confidence: {confidence}\n"
        f"Source: {source}\n\n"
        "Read-only handoff preview for Button 2 context. No export, PDF, delivery, or mutation action was performed from Button 1."
    )

    return {
        "destination_marker": "button2_report_generation_preview",
        "dossier_summary_preview": dossier_summary_preview,
        "preview_only": True,
        "button1_export_performed": False,
        "pdf_generation_performed": False,
        "file_write_performed": False,
        "delivery_performed": False,
        "report_write_performed": False,
        "profile_create_update_merge": False,
        "database_ranking_writes": False,
        "result_report_learning_calibration": False,
    }
