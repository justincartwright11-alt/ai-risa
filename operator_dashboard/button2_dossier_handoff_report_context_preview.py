import html


_EXPECTED_DESTINATION_MARKER = "button2_report_generation_preview"


def _safe_text(value, fallback=""):
    if value is None:
        return fallback
    text = str(value).strip()
    if not text:
        return fallback
    return html.escape(text)


def _base_flags(report_context_preview_ready):
    return {
        "preview_only": True,
        "report_context_preview_ready": bool(report_context_preview_ready),
        "button2_generation_performed": False,
        "pdf_generation_performed": False,
        "file_write_performed": False,
        "export_performed": False,
        "delivery_performed": False,
        "report_write_performed": False,
        "gate2_approval_required": True,
        "gate2_bypass_performed": False,
        "profile_create_update_merge": False,
        "database_ranking_writes": False,
        "result_report_learning_calibration": False,
    }


def build_button2_dossier_handoff_report_context_preview(ingest_payload):
    """Build preview-only Button 2 report-context data from ingest preview context."""
    payload = ingest_payload if isinstance(ingest_payload, dict) else {}
    ingest_context = payload.get("button2_ingest_preview_context", payload)
    if not isinstance(ingest_context, dict):
        ingest_context = {}

    destination_marker = _safe_text(ingest_context.get("destination_marker", ""))
    if destination_marker != _EXPECTED_DESTINATION_MARKER:
        return {
            "ok": False,
            "error": "invalid_destination_marker",
            "destination_marker": destination_marker,
            "report_context_preview": None,
            **_base_flags(False),
        }

    handoff_summary_preview = _safe_text(
        ingest_context.get("dossier_summary_preview", ""),
        "No dossier summary preview provided.",
    )

    # Extracted before dict literal so source_traceability can reference it correctly
    source_context_kind_val = _safe_text(
        ingest_context.get("context_kind", "button1_dossier_handoff"),
        "button1_dossier_handoff",
    )

    # --- Visual QA metadata markers (preview-level, not certified) ---
    report_context_preview = {
        "destination_marker": _EXPECTED_DESTINATION_MARKER,
        "report_context_kind": "dossier_handoff_report_context_preview",
        "source_context_kind": source_context_kind_val,
        "source_ingest_mode": _safe_text(
            ingest_context.get("ingest_mode", "preview_only"),
            "preview_only",
        ),
        "handoff_summary_preview": handoff_summary_preview,
        # --- Metadata markers (all preview/unavailable/not_certified) ---
        "page_block_boundaries": [
            {"id": "block-1", "type": "summary", "bounds": [0, 0, 400, 100], "page_index": 0}
        ],
        "hierarchy_markers": [
            {"block": "executive_summary", "order": 0},
            {"block": "dossier_handoff_report_context_preview", "order": 1}
        ],
        "source_traceability": [
            {"id": "SRC-CTX", "type": source_context_kind_val, "date": "n/a"}
        ],
        "overlap_proof": "unavailable",
        "off_page_text_proof": "unavailable",
        "visual_certification_status": "not_certified",
    }

    return {
        "ok": True,
        "destination_marker": _EXPECTED_DESTINATION_MARKER,
        "report_context_preview": report_context_preview,
        **_base_flags(True),
    }
