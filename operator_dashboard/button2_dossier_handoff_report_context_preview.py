import html

from operator_dashboard.button2_visual_intelligence_overlap_offpage_proof_instrumentation_v1 import run_geometry_proof

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

    source_ingest_mode_val = _safe_text(
        ingest_context.get("ingest_mode", "preview_only"),
        "preview_only",
    )

    template_renderer_profile_val = _safe_text(
        ingest_context.get("template_renderer_profile", "button2_html_composition_entry_point_v1"),
        "button2_html_composition_entry_point_v1",
    )

    template_pack_root_val = _safe_text(
        ingest_context.get("template_pack_root", ""),
        "",
    )
    template_pack_available = bool(ingest_context.get("template_pack_available", False))

    selected_matchup = ingest_context.get("selected_matchup_payload", {})
    if not isinstance(selected_matchup, dict):
        selected_matchup = {}

    selected_source_url = _safe_text(selected_matchup.get("source_url", ""), "")
    selected_event_name = _safe_text(selected_matchup.get("event_name", ""), "Unknown Event")
    selected_event_date = _safe_text(selected_matchup.get("event_date", ""), "n/a")
    selected_fighter_a = _safe_text(selected_matchup.get("fighter_a", ""), "Unknown Fighter A")
    selected_fighter_b = _safe_text(selected_matchup.get("fighter_b", ""), "Unknown Fighter B")

    source_type_raw = selected_matchup.get("source_type", "official")
    source_type_value = "official"
    if isinstance(source_type_raw, str):
        normalized = source_type_raw.strip().lower()
        if normalized in {"official", "research", "operator"}:
            source_type_value = normalized

    source_traceability_rows = []
    if selected_source_url:
        source_traceability_rows.append({
            "id": "SRC-001",
            "type": source_type_value,
            "url": selected_source_url,
            "date": selected_event_date,
        })
    else:
        source_traceability_rows.append({
            "id": "SRC-CTX",
            "type": source_context_kind_val,
            "url": "n/a",
            "date": "n/a",
        })

    source_traceability_metadata = {
        "schema_version": "button2.source_traceability.v1",
        "validation_status": "valid" if selected_source_url else "missing",
        "validation_issues": [] if selected_source_url else ["missing_selected_source_url"],
        "total_sources": len(source_traceability_rows),
        "official_sources_count": 1 if selected_source_url and source_type_value == "official" else 0,
        "research_sources_count": 1 if selected_source_url and source_type_value == "research" else 0,
        "operator_sources_count": 1 if selected_source_url and source_type_value == "operator" else 0,
        "average_confidence_level": "high" if selected_source_url else "uncertain",
        "corroboration_coverage": 1.0 if selected_source_url else 0.0,
        "sources": [
            {
                "source_type": source_type_value,
                "source_class": "tier_a",
                "confidence_level": "high" if selected_source_url else "uncertain",
                "citation_completeness": "complete" if selected_source_url else "minimal",
                "verification_status": "verified" if selected_source_url else "unverified",
                "source_url": selected_source_url or "n/a",
                "source_date": selected_event_date,
            }
        ],
        "lineage_graph": {
            "input_kind": source_context_kind_val,
            "template_renderer_profile": template_renderer_profile_val,
            "template_pack_root": template_pack_root_val,
            "template_pack_available": template_pack_available,
            "selected_matchup": {
                "fighter_a": selected_fighter_a,
                "fighter_b": selected_fighter_b,
                "event_name": selected_event_name,
            },
        },
    }

    # --- Visual QA metadata markers (preview-level, not certified) ---
    report_context_preview = {
        "destination_marker": _EXPECTED_DESTINATION_MARKER,
        "report_context_kind": "dossier_handoff_report_context_preview",
        "source_context_kind": source_context_kind_val,
        "source_ingest_mode": source_ingest_mode_val,
        "template_renderer_profile": template_renderer_profile_val,
        "template_pack_root": template_pack_root_val,
        "template_pack_available": template_pack_available,
        "selected_matchup": {
            "fighter_a": selected_fighter_a,
            "fighter_b": selected_fighter_b,
            "event_name": selected_event_name,
            "event_date": selected_event_date,
            "source_url": selected_source_url,
        },
        "handoff_summary_preview": handoff_summary_preview,
        # --- Metadata markers (all preview/unavailable/not_certified) ---
        "page_block_boundaries": [
            {"id": "block-1", "type": "summary", "bounds": [0, 0, 400, 100], "page_index": 0}
        ],
        "hierarchy_markers": [
            {"block": "executive_summary", "order": 0},
            {"block": "dossier_handoff_report_context_preview", "order": 1}
        ],
        "source_traceability": source_traceability_rows,
        "source_traceability_metadata": source_traceability_metadata,
        "overlap_proof": "unavailable",
        "off_page_text_proof": "unavailable",
        "visual_certification_status": "not_certified",
    }

    # Optional: run real geometry proof if caller provides geometry_data in the ingest context.
    # No layout changes, no PDF writes, no certification without operator_approval=True.
    geometry_data = ingest_context.get("geometry_data")
    if geometry_data is not None:
        proof = run_geometry_proof(geometry_data)
        report_context_preview["overlap_proof"] = proof["overlap_proof"]
        report_context_preview["off_page_text_proof"] = proof["off_page_text_proof"]
        report_context_preview["visual_certification_status"] = proof["visual_certification_status"]

    return {
        "ok": True,
        "destination_marker": _EXPECTED_DESTINATION_MARKER,
        "report_context_preview": report_context_preview,
        **_base_flags(True),
    }
