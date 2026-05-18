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

    context_kind = _safe_text(payload.get("context_kind", "button1_dossier_handoff"), "button1_dossier_handoff")
    ingest_mode = _safe_text(payload.get("ingest_mode", "preview_only"), "preview_only")
    template_renderer_profile = _safe_text(
        payload.get("template_renderer_profile", "button2_html_composition_entry_point_v1"),
        "button2_html_composition_entry_point_v1",
    )
    template_pack_root = _safe_text(payload.get("template_pack_root", ""), "")
    template_pack_available = bool(payload.get("template_pack_available", False))

    selected_matchup_payload = payload.get("selected_matchup_payload", {})
    if not isinstance(selected_matchup_payload, dict):
        selected_matchup_payload = {}

    source_traceability_sources = payload.get("source_traceability_sources", [])
    if not isinstance(source_traceability_sources, list):
        source_traceability_sources = []

    # Build read-only ingest context only; no report generation side effects.
    ingest_context = {
        "destination_marker": _EXPECTED_DESTINATION_MARKER,
        "ingest_mode": ingest_mode,
        "context_kind": context_kind,
        "template_renderer_profile": template_renderer_profile,
        "template_pack_root": template_pack_root,
        "template_pack_available": template_pack_available,
        "selected_matchup_payload": selected_matchup_payload,
        "source_traceability_sources": source_traceability_sources,
        "dossier_summary_preview": summary_preview,
    }

    return {
        "ok": True,
        "destination_marker": _EXPECTED_DESTINATION_MARKER,
        "button2_ingest_preview_context": ingest_context,
        **_base_flags(),
    }
