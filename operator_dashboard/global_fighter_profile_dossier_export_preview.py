import html

def build_dossier_preview(dossier_data):
    """
    Build a read-only preview of the fighter intelligence dossier.

    Args:
        dossier_data (dict): Sanitized dossier data.

    Returns:
        dict: Preview summary with metadata.
    """
    # Sanitize input fields to escape HTML/XSS payloads
    fighter_name = html.escape(dossier_data.get("fighter_name", "Unknown Fighter"))
    promotion = html.escape(dossier_data.get("promotion", "Unknown Promotion"))
    division = html.escape(dossier_data.get("division", "Unknown Division"))
    record = html.escape(dossier_data.get("record", "0W-0L-0D"))
    confidence = html.escape(dossier_data.get("confidence", "Unknown"))
    source = html.escape(dossier_data.get("source", "Unknown Source"))

    preview_text = (
        f"Fighter Intelligence Dossier Preview\n"
        f"Fighter: {fighter_name}\n"
        f"Promotion: {promotion}\n"
        f"Division: {division}\n"
        f"Record: {record}\n"
        f"Confidence: {confidence}\n"
        f"Source: {source}\n\n"
        "Read-only preview. No profile create, update, merge, ranking, database, learning, or calibration action was performed."
    )

    return {
        "preview": preview_text,
        "preview_only": True,
        "export_performed": False,
        "file_write_performed": False,
        "profile_create_update_merge": False,
        "database_ranking_writes": False,
        "result_report_learning_calibration": False,
    }