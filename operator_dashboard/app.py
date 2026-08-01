"""
operator_dashboard/app.py

AI-RISA Premium Report Factory — Operator Dashboard Flask Application.

3-Button Dashboard:
  Button 1: Find & Build Fight Queue
  Button 2: Generate Premium PDF Reports
  Button 3: Find Results & Improve Accuracy

GOVERNANCE:
  - Permanent writes, PDF generation, and learning require operator approval gates.
  - Button 3 auto-search and preview are read-only (no mutations).
  - Advanced diagnostics are only exposed via explicit flag.
"""

import sys
import os
import re
import json
from datetime import datetime
from datetime import timezone
import uuid
from urllib.parse import quote
from urllib.parse import urlparse

# Allow imports from workspace root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, jsonify, send_from_directory, make_response

from button3_auto_result_source_yield_live_executor_preview import (
    build_readonly_executor_preview_response,
)
from operator_dashboard.local_ai_orchestrator_input_context_pack import build_context_pack
from operator_dashboard.local_ai_orchestrator_readonly_runtime_context_loader import (
    build_runtime_context_pack,
    build_button1_runtime_context_preview,
)
from operator_dashboard.local_ai_orchestrator_job_schema import LocalAIJobInputRef

app = Flask(__name__, template_folder="templates")


def _lazy_gate1_save_fights_preview():
    from operator_dashboard.local_ai_orchestrator_gate1_save_fights_dry_run_apply_preview import (
        run_gate1_save_fights_dry_run_apply_preview,
    )

    return run_gate1_save_fights_dry_run_apply_preview


def _lazy_gate1_approved_save_writer():
    from operator_dashboard.local_ai_orchestrator_gate1_approved_save_writer import (
        run_gate1_approved_save_writer_scaffold,
    )

    return run_gate1_approved_save_writer_scaffold


def _lazy_local_ai_workflow_plan():
    from operator_dashboard.local_ai_orchestrator_workflow_plan import (
        build_three_button_workflow_plan,
        run_workflow_preview,
    )

    return build_three_button_workflow_plan, run_workflow_preview


def _lazy_global_fighter_identity_resolver_preview():
    from operator_dashboard.global_fighter_identity_resolver_preview import (
        resolve_fighter_identity_preview,
        IncomingFighterCandidate,
        KnownFighterRecord,
        SourceRef,
    )

    return (
        resolve_fighter_identity_preview,
        IncomingFighterCandidate,
        KnownFighterRecord,
        SourceRef,
    )


def _lazy_global_fighter_known_records_readonly_loader():
    from operator_dashboard.global_fighter_known_records_readonly_loader import (
        load_known_records_readonly_preview,
    )

    return load_known_records_readonly_preview


def _lazy_button1_to_button2_readonly_dossier_handoff_preview():
    from operator_dashboard.button1_to_button2_readonly_dossier_handoff_preview import (
        build_button1_to_button2_readonly_dossier_handoff_preview,
    )

    return build_button1_to_button2_readonly_dossier_handoff_preview


def _lazy_button2_dossier_handoff_ingest_preview():
    from operator_dashboard.button2_readonly_dossier_handoff_ingest_preview import (
        build_button2_readonly_dossier_handoff_ingest_preview,
    )

    return build_button2_readonly_dossier_handoff_ingest_preview


def _lazy_button2_dossier_handoff_report_context_preview():
    from operator_dashboard.button2_dossier_handoff_report_context_preview import (
        build_button2_dossier_handoff_report_context_preview,
    )

    return build_button2_dossier_handoff_report_context_preview


def _lazy_button2_report_generation_route_render_gate_integration():
    from operator_dashboard.button2_report_generation_route_render_gate_integration_v1 import (
        generate_button2_report_render_gate_integration,
    )

    return generate_button2_report_render_gate_integration


def _lazy_button2_customer_flow_dry_run_contract_preview():
    from operator_dashboard.button2_customer_flow_dry_run_contract_preview_v1 import (
        run_button2_customer_flow_dry_run_contract_preview,
    )

    return run_button2_customer_flow_dry_run_contract_preview


def _lazy_button2_pdf_output_root_config():
    from operator_dashboard.button2_pdf_output_root_config_v1 import (
        get_pdf_output_root,
        OutputRootNotConfiguredError,
        OutputRootInvalidError,
    )

    return get_pdf_output_root, OutputRootNotConfiguredError, OutputRootInvalidError


def _lazy_button2_template_pack_asset_renderer():
    from operator_dashboard.button2_template_pack_asset_renderer_v1 import (
        resolve_template_pack_assets,
        TemplatePackResolverError,
    )

    return resolve_template_pack_assets, TemplatePackResolverError


def _lazy_button3_result_comparison_preview():
    from operator_dashboard.button3_result_comparison_preview_v1 import (
        build_button3_result_comparison_preview,
    )

    return build_button3_result_comparison_preview


def _lazy_button2_queue_loader_readonly():
    from operator_dashboard.button2_queue_loader_readonly_v1 import (
        load_button2_queue_readonly,
        get_queue_ready_rows,
        resolve_matchup_id_from_queue,
        get_rows_for_event,
    )

    return (
        load_button2_queue_readonly,
        get_queue_ready_rows,
        resolve_matchup_id_from_queue,
        get_rows_for_event,
    )


def _lazy_controlled_delivery_handlers():
    from operator_dashboard.button2_controlled_delivery_scaffold import (
        controlled_delivery_preview,
        controlled_delivery_action,
    )

    return controlled_delivery_preview, controlled_delivery_action


def _build_button3_preview_input_from_generated_report(
    generation_result,
    *,
    fight_id="",
    matchup_id="",
    fighter_a="",
    fighter_b="",
    event_name="",
):
    """Preserve a generated Button 2 prediction for Button 3's read-only preview."""
    result = generation_result if isinstance(generation_result, dict) else {}
    structured_prediction = result.get("structured_prediction")
    if not isinstance(structured_prediction, dict):
        structured_prediction = {}

    output_path = _safe_text(result.get("output_path"))
    generation_request_id = _safe_text(result.get("generation_request_id"))
    report_id = generation_request_id or os.path.basename(output_path) or _safe_text(fight_id)

    return {
        "report_id": report_id,
        "fight_id": _safe_text(fight_id),
        "matchup_id": _safe_text(matchup_id),
        "fighter_a": _safe_text(fighter_a),
        "fighter_b": _safe_text(fighter_b),
        "event_name": _safe_text(event_name),
        "report_path": output_path,
        "structured_prediction": structured_prediction,
        "prediction_provenance": "button2_generated_report",
        "preview_only": True,
        "mutation_performed": False,
        "accuracy_ledger_write_performed": False,
        "learning_apply_performed": False,
        "calibration_write_performed": False,
        "gcid_write_performed": False,
    }

_LOCAL_AI_SAFE_TELEMETRY = {
    "preview_only": True,
    "mutation_performed": False,
    "queue_write_performed": False,
    "report_export_approved": False,
    "durable_write_performed": False,
    "learning_apply_performed": False,
    "calibration_write_performed": False,
    "auto_apply_performed": False,
}

_DEFAULT_BUTTON2_TEMPLATE_PACK_ROOT = (
    r"C:\ai_risa_next_dashboard_polish\ops\prf_reports\template_pack_sample"
)

_BUTTON2_FORBIDDEN_MARKERS = [
    "01 | PREMIUM COVER",
    "PREMIUM COVER",
    "Cover Page",
    "where the fight is owned",
    "where the fight can flip",
    "what the corner must solve",
    "SECTION LENS",
    "MODEL STATUS",
    "REPORT TYPE",
    "ROUND BAND",
    "AI-RISA Premium Fight Report",
    "Report Type: Premium Fight Intelligence Report",
    "Fighter A Pathway",
    "Fighter B Counter-Pathway",
    "Buyer Meaning / Coach Meaning",
    "Buyer Meaning",
    "Coach Meaning",
    "SOURCE TRACEABILITY Source Traceability",
    "customer_ready_not_ready",
    "draft_only",
    "controlled_export_not_eligible",
    "visual QA rollup",
    "template renderer profile",
    "raw ingest mode",
    "valid layers",
    "missing layers",
]

_BUTTON2_FORBIDDEN_CONCATENATION_SNIPPETS = [
    "Fighter B Counter-Pathway Daniel",
    "Fighter A Pathway Anthony",
    "Buyer Meaning / Coach MeaningBuyer",
    "Command Instruction Preserve",
]

_BUTTON2_STALE_NAME_PAIRS = [
    ("bahram rajabzadeh", "donovan wisse"),
    ("anthony joshua", "daniel dubois"),
    ("rico verhoeven", "tariq osaro"),
    ("jbalia", "diatta"),
]

_BUTTON2_REQUIRED_PREMIUM_MARKERS = [
    "executive command dashboard",
    "fighter architecture radar",
    "tactical edge map",
    "tactical thesis",
    "control objective",
    "danger objective",
    "watch cue",
    "failure cue",
    "scoring consequence",
    "corner command",
    "customer meaning",
    "operator use",
    "uncertainty",
]

_BUTTON2_REQUIRED_PREMIUM_MARKER_ALTERNATIVES = [
    ("scenario tree", "method pathways"),
    ("traceability", "source map"),
    ("disclaimer", "risk control"),
]


# v29 layout markers expected to appear in generated PDFs for layout parity
_BUTTON2_REQUIRED_V29_LAYOUT_MARKERS = [
    "premium fight",
    "intelligence report",
    "the intelligence beneath the violence",
    "02 | executive command dashboard",
    "05 | fighter architecture radar",
    "page 05",
    "14 | round-by-round control projection",
    "15 | scenario tree / method pathways",
    "23 | traceability / source map",
    "24 | disclaimer / risk control",
]


def _is_source_backed_candidate_row(row):
    if not isinstance(row, dict):
        return False

    for key in ("source_url", "canonical_source_url", "event_url", "provenance_url", "official_url", "url"):
        value = row.get(key)
        if isinstance(value, str) and value.strip().lower().startswith(("http://", "https://")):
            return True

    provenance = row.get("provenance")
    if isinstance(provenance, dict):
        src = provenance.get("source_url")
        if isinstance(src, str) and src.strip().lower().startswith(("http://", "https://")):
            return True

    return False


def _candidate_row_id(row):
    if not isinstance(row, dict):
        return ""
    for key in ("matchup_id", "candidate_id", "fight_id", "fight_key", "matchup_key", "id"):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _candidate_row_event_id(row):
    if not isinstance(row, dict):
        return ""
    event_name = row.get("event_name") or row.get("event") or row.get("event_title")
    if not isinstance(event_name, str):
        return ""
    value = event_name.strip().lower()
    return value


def _extract_matchup_names(row):
    if not isinstance(row, dict):
        return "", ""

    fighter_a = row.get("fighter_a") or row.get("fighter_a_name") or row.get("red_fighter") or row.get("fighter_name")
    fighter_b = row.get("fighter_b") or row.get("fighter_b_name") or row.get("blue_fighter") or row.get("opponent_name")

    fighter_a = fighter_a.strip() if isinstance(fighter_a, str) else ""
    fighter_b = fighter_b.strip() if isinstance(fighter_b, str) else ""
    return fighter_a, fighter_b


def _build_selected_matchup_preview_from_row(row):
    if not isinstance(row, dict):
        return {}
    fighter_a, fighter_b = _extract_matchup_names(row)
    source_url = ""
    for key in ("source_url", "canonical_source_url", "event_url", "provenance_url", "official_url", "url"):
        value = row.get(key)
        if isinstance(value, str) and value.strip().lower().startswith(("http://", "https://")):
            source_url = value.strip()
            break
    if not source_url:
        provenance = row.get("provenance")
        if isinstance(provenance, dict):
            maybe = provenance.get("source_url")
            if isinstance(maybe, str) and maybe.strip().lower().startswith(("http://", "https://")):
                source_url = maybe.strip()

    return {
        "selected_for_button2": True,
        "selection_preview": True,
        "event_name": row.get("event_name") or row.get("event") or row.get("event_title") or "",
        "event_date": row.get("event_date") or "",
        "promotion": row.get("promotion") or "",
        "source_url": source_url,
        "source_type": row.get("source_type") or "official",
        "fighter_a": fighter_a,
        "fighter_b": fighter_b,
        "matchup_id": _candidate_row_id(row),
        "candidate_id": _candidate_row_id(row),
        "report_ready_status": row.get("report_ready_status") or row.get("button2_readiness_status") or row.get("readiness") or row.get("button2_readiness") or "",
        "denial_reasons": [],
    }


def _is_button2_row_ready_for_generation(row):
    if not isinstance(row, dict):
        return False
    readiness = str(
        row.get("report_ready_status")
        or row.get("button2_readiness_status")
        or row.get("readiness")
        or row.get("button2_readiness")
        or ""
    ).strip().lower()
    if not readiness:
        return False
    return readiness in {
        "ready",
        "ready_for_button2_generation",
        "ready_for_button2_preview",
        "ready_for_button2",
        "customer_ready",
        "customer_ready_verified",
    }


def _resolve_selected_matchup_row_from_queue(selected_matchup_id, queue_rows):
    matchup_id = str(selected_matchup_id or "").strip()
    if not matchup_id:
        return None, "selected_matchup_id_required", 400

    if not isinstance(queue_rows, list) or not queue_rows:
        return None, "approved_queue_rows_required", 400

    matched = []
    for row in queue_rows:
        if not isinstance(row, dict):
            continue
        if _candidate_row_id(row) == matchup_id:
            matched.append(row)

    if not matched:
        return None, "selected_matchup_unknown", 422
    if len(matched) > 1:
        return None, "selected_matchup_duplicated", 422

    row = matched[0]
    fighter_a, fighter_b = _extract_matchup_names(row)
    if not fighter_a or not fighter_b:
        return None, "selected_matchup_incomplete", 422

    if not _is_button2_row_ready_for_generation(row):
        return None, "selected_matchup_not_ready", 422

    if not _is_source_backed_candidate_row(row):
        return None, "source_backed_matchup_required", 422

    return row, "", 200


def _slugify_text(value):
    text = value if isinstance(value, str) else ""
    lowered = text.strip().lower()
    lowered = re.sub(r"[^a-z0-9]+", "_", lowered)
    lowered = re.sub(r"_+", "_", lowered).strip("_")
    return lowered


def _build_fight_id_from_selected_matchup(selected_preview):
    if not isinstance(selected_preview, dict):
        return ""
    fighter_a = _slugify_text(selected_preview.get("fighter_a", ""))
    fighter_b = _slugify_text(selected_preview.get("fighter_b", ""))
    event_name = _slugify_text(selected_preview.get("event_name", ""))
    core = "_vs_".join([part for part in (fighter_a, fighter_b) if part])
    if event_name:
        return (core + "_" + event_name).strip("_")
    return core


def _utc_now_iso_seconds():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _build_selected_matchup_output_filename(fight_id, generation_request_id):
    safe_fight_id = _slugify_text(fight_id)
    if not safe_fight_id:
        safe_fight_id = "selected_matchup"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    req_short = _slugify_text(generation_request_id)[:12] or "req"
    return f"{safe_fight_id}_premium_{stamp}_{req_short}.pdf"


def _extract_pdf_text_and_page_count(output_path):
    if not isinstance(output_path, str) or not output_path.strip() or not os.path.isfile(output_path):
        return "", None
    try:
        from pypdf import PdfReader

        reader = PdfReader(output_path)
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
        return text, len(reader.pages)
    except Exception:
        return "", None


def _scan_forbidden_markers(pdf_text):
    lower_text = str(pdf_text or "").lower()
    found = []
    hits = {}
    for marker in _BUTTON2_FORBIDDEN_MARKERS:
        present = marker.lower() in lower_text
        hits[marker] = present
        if present:
            found.append(marker)
    concat_hits = {}
    concat_found = []
    for snippet in _BUTTON2_FORBIDDEN_CONCATENATION_SNIPPETS:
        present = snippet.lower() in lower_text
        concat_hits[snippet] = present
        if present:
            concat_found.append(snippet)
    return {
        "any_forbidden_found": bool(found or concat_found),
        "found_markers": found,
        "marker_hits": hits,
        "found_concatenation_snippets": concat_found,
        "concatenation_hits": concat_hits,
    }


def _selected_matchup_matches_pdf_text(selected_preview, pdf_text):
    if not isinstance(selected_preview, dict):
        return False
    text_lower = str(pdf_text or "").lower()
    fighter_a = str(selected_preview.get("fighter_a", "")).strip().lower()
    fighter_b = str(selected_preview.get("fighter_b", "")).strip().lower()
    event_name = str(selected_preview.get("event_name", "")).strip().lower()
    if not fighter_a or not fighter_b:
        return False
    fighters_present = fighter_a in text_lower and fighter_b in text_lower
    event_present = (not event_name) or (event_name in text_lower)
    return fighters_present and event_present


def _selected_matchup_passes_strict_pdf_quality_gate(selected_preview, result, pdf_text, page_count, renderer_metadata=None):
    get_pdf_output_root, _, _ = _lazy_button2_pdf_output_root_config()
    violations = []
    text_lower = str(pdf_text or "").lower()

    fighter_a = str(selected_preview.get("fighter_a", "")).strip().lower()
    fighter_b = str(selected_preview.get("fighter_b", "")).strip().lower()
    event_name = str(selected_preview.get("event_name", "")).strip().lower()
    source_url = str(selected_preview.get("source_url", "")).strip().lower()
    source_domain = ""
    if source_url:
        source_domain = (urlparse(source_url).netloc or "").lower().strip()

    if not fighter_a or fighter_a not in text_lower:
        violations.append("fighter_a_missing_in_pdf_text")
    if not fighter_b or fighter_b not in text_lower:
        violations.append("fighter_b_missing_in_pdf_text")
    if event_name and event_name not in text_lower:
        violations.append("event_name_missing_in_pdf_text")

    if source_url:
        if source_url not in text_lower and (not source_domain or source_domain not in text_lower):
            violations.append("source_url_or_domain_missing_in_pdf_text")

    expected_slug = _build_fight_id_from_selected_matchup(selected_preview)
    output_filename = str(result.get("output_filename") or "").strip().lower()
    output_path = str(result.get("output_path") or "").strip()
    report_id = str(result.get("report_id") or "").strip().lower()

    if expected_slug:
        if expected_slug not in output_filename:
            violations.append("selected_slug_missing_from_output_filename")
        slug_tokens = [token for token in expected_slug.split("_") if token]
        if report_id and slug_tokens and not any(token in report_id for token in slug_tokens):
            violations.append("selected_slug_missing_from_report_id")

    if page_count != 24:
        violations.append("page_count_must_equal_24")

    if not output_path or not os.path.isfile(output_path):
        violations.append("output_path_missing_or_not_written")
    else:
        try:
            output_root = get_pdf_output_root()
            root_real = os.path.realpath(output_root)
            file_real = os.path.realpath(output_path)
            if not file_real.startswith(root_real + os.sep):
                violations.append("output_path_outside_configured_root")
        except Exception:
            violations.append("output_root_unavailable_for_validation")

    selected_names = {fighter_a, fighter_b}
    for name_a, name_b in _BUTTON2_STALE_NAME_PAIRS:
        if name_a in selected_names and name_b in selected_names:
            continue
        if name_a in text_lower and name_b in text_lower:
            # sample/template bleed detection — stale names present together in PDF text
            violations.append(f"template_sample_bleed_present:{name_a}:{name_b}")

    for marker in _BUTTON2_REQUIRED_PREMIUM_MARKERS:
        if marker not in text_lower:
            violations.append(f"premium_marker_missing:{marker}")

    for marker_a, marker_b in _BUTTON2_REQUIRED_PREMIUM_MARKER_ALTERNATIVES:
        if marker_a not in text_lower and marker_b not in text_lower:
            violations.append(f"premium_marker_missing_either:{marker_a}|{marker_b}")

    # Accept either legacy layout_safety dicts or optional renderer metadata
    # wrappers that include layout_safety and allow newer v8 gate enforcement.
    layout_safety = None
    renderer_metadata_present = False
    if isinstance(renderer_metadata, dict):
        if isinstance(renderer_metadata.get("layout_safety"), dict):
            layout_safety = renderer_metadata.get("layout_safety")
            renderer_metadata_present = True
        else:
            layout_safety = renderer_metadata

    try:
        if isinstance(layout_safety, dict):
            v8_required = [
                "page_2_footer_safe_passed",
                "page_2_round_control_projection_fit_passed",
                "page_2_lower_modules_no_strip_overlap_passed",
                "page_2_round_control_no_lens_overlap_passed",
                "page_2_method_probability_no_lens_overlap_passed",
                "page_2_risk_control_no_lens_overlap_passed",
                "page_2_analysis_modules_no_strip_overlap_passed",
                "page_2_footer_safe_zone_passed",
                "page_2_dashboard_no_visual_overlap_passed",
                "page_5_architecture_read_text_fit_passed",
                "page_5_customer_meaning_heading_clear_passed",
                "page_5_customer_meaning_body_clear_passed",
                "page_5_customer_panel_below_architecture_panel_passed",
                "page_5_operator_panel_below_customer_panel_passed",
                "page_5_right_rail_no_text_overlap_passed",
                "page_5_right_rail_no_box_overlap_passed",
                "page_5_customer_meaning_rule_clear_passed",
                "page_5_architecture_customer_no_overlap_passed",
                "page_5_operator_use_fit_passed",
                "page_5_customer_panel_inside_radar_band_passed",
                "page_16_scorecard_row_rule_clear_passed",
                "page_16_commentary_centered_passed",
                "page_17_lower_cards_centered_passed",
            ]
            v7_required = [
                "page_2_footer_safe_passed",
                "page_2_volatility_text_fit_passed",
                "page_2_round_control_projection_fit_passed",
                "page_2_lower_modules_no_strip_overlap_passed",
                "page_2_lower_row_centered_passed",
                "page_5_customer_meaning_rule_clear_passed",
                "page_5_customer_panel_inside_radar_band_passed",
                "page_5_side_panel_text_clear_passed",
                "page_16_scorecard_row_rule_clear_passed",
                "page_16_commentary_centered_passed",
                "page_17_lower_cards_centered_passed",
            ]
            # First check older v6/v5 compatibility markers and fail-closed with diagnostic entries.
            v5_required = [
                "page_5_side_panel_fit_passed",
                "page_2_dashboard_fit_passed",
            ]
            v6_required = [
                "page_2_lower_modules_fit_passed",
                "page_5_customer_operator_fit_passed",
            ]

            if renderer_metadata_present:
                v8_failures = [
                    k for k in v8_required if k in layout_safety and layout_safety.get(k) is False
                ]
                if v8_failures:
                    for key in v8_failures:
                        violations.append(key)
                    violations.append("visual_gate_status:v29_final_delivery_right_rail_overlap_failed")
                    return False, violations
                # When renderer metadata is present and v8 checks passed, prefer
                # the newer v8 enforcement path and skip legacy v5/v6/v7 checks
                # to avoid failing on obsolete compatibility markers.
            else:
                v5_failures = [k for k in v5_required if k in layout_safety and layout_safety.get(k) is False]
                v6_failures = [k for k in v6_required if k in layout_safety and layout_safety.get(k) is False]
                v7_failures = [k for k in v7_required if k in layout_safety and layout_safety.get(k) is False]

                if v5_failures or v6_failures or v7_failures:
                    for key in v5_failures:
                        violations.append(key)
                        violations.append(f"final_delivery_fit_failed:{key}")
                    for key in v6_failures:
                        violations.append(key)
                        violations.append(f"final_delivery_fit_polish_failed:{key}")
                    for key in v7_failures:
                        violations.append(key)
                        violations.append(f"final_delivery_visual_cleanup_failed:{key}")
                    if v7_failures:
                        violations.append("visual_gate_status:v29_final_delivery_microfit_failed")
                    return False, violations
    except Exception:
        # If layout_safety inspection fails for any reason, do not weaken the gate;
        # append a diagnostic violation but continue evaluating other checks.
        violations.append("visual_gate_inspection_error")

    return len(violations) == 0, violations


def _collect_file_metadata(output_path):
    if not isinstance(output_path, str) or not output_path.strip() or not os.path.isfile(output_path):
        return {
            "file_modified_at": None,
            "file_size_bytes": None,
        }
    stat = os.stat(output_path)
    return {
        "file_modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(timespec="seconds"),
        "file_size_bytes": int(stat.st_size),
    }


def _generate_button2_fallback_pdf(selected_preview, fight_id, output_filename_override):
    """Create a minimal 24-page PDF fallback when renderer dependencies are unavailable."""
    get_pdf_output_root, _, _ = _lazy_button2_pdf_output_root_config()
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except Exception as exc:
        return {
            "ok": False,
            "error": "fallback_renderer_unavailable",
            "message": f"Fallback renderer unavailable: {exc.__class__.__name__}",
        }

    try:
        output_root = get_pdf_output_root()
    except Exception as exc:
        return {
            "ok": False,
            "error": "output_root_unavailable",
            "message": str(exc),
        }

    os.makedirs(output_root, exist_ok=True)
    output_filename = output_filename_override if isinstance(output_filename_override, str) and output_filename_override.strip() else (
        (_slugify_text(fight_id) or "selected_matchup") + "_fallback.pdf"
    )
    output_filename = os.path.basename(output_filename)
    output_path = os.path.join(output_root, output_filename)

    fighter_a = str(selected_preview.get("fighter_a") or "Unknown Fighter A")
    fighter_b = str(selected_preview.get("fighter_b") or "Unknown Fighter B")
    event_name = str(selected_preview.get("event_name") or "Unknown Event")
    source_url = str(selected_preview.get("source_url") or "")

    c = canvas.Canvas(output_path, pagesize=letter)
    for page_num in range(1, 25):
        c.setFont("Helvetica-Bold", 14)
        c.drawString(72, 740, "AI-RISA Premium Fight Report (Fallback Renderer)")
        c.setFont("Helvetica", 11)
        c.drawString(72, 710, f"Matchup: {fighter_a} vs {fighter_b}")
        c.drawString(72, 690, f"Event: {event_name}")
        c.drawString(72, 670, f"Source: {source_url or 'n/a'}")
        c.drawString(72, 650, f"fight_id: {fight_id}")
        c.drawString(72, 630, f"Page: {page_num}/24")
        c.showPage()
    c.save()

    return {
        "ok": True,
        "message": "PDF generated via fallback renderer.",
        "output_path": output_path,
        "output_filename": output_filename,
        "report_id": str(fight_id or "fallback_report"),
        "renderer_route_used": "reportlab_fallback_renderer",
        "delivery_performed": False,
        "external_api_delivery_performed": False,
        "queue_write_performed": False,
        "learning_apply_performed": False,
        "calibration_write_performed": False,
        "button3_mutation_performed": False,
    }


def _resolve_button2_template_pack_preview():
    resolve_template_pack_assets, TemplatePackResolverError = _lazy_button2_template_pack_asset_renderer()
    try:
        assets = resolve_template_pack_assets()
        return {
            "template_pack_root": assets.get("pack_root", ""),
            "template_pack_available": True,
            "template_pack_error": "",
        }
    except TemplatePackResolverError as e:
        return {
            "template_pack_root": e.attempted_path or _DEFAULT_BUTTON2_TEMPLATE_PACK_ROOT,
            "template_pack_available": False,
            "template_pack_error": e.message,
        }


def _build_selected_matchup_premium_summary(selected_preview):
    fighter_a = selected_preview.get("fighter_a", "") if isinstance(selected_preview, dict) else ""
    fighter_b = selected_preview.get("fighter_b", "") if isinstance(selected_preview, dict) else ""
    event_name = selected_preview.get("event_name", "") if isinstance(selected_preview, dict) else ""
    source_url = selected_preview.get("source_url", "") if isinstance(selected_preview, dict) else ""
    readiness = selected_preview.get("report_ready_status", "") if isinstance(selected_preview, dict) else ""
    event_date = selected_preview.get("event_date", "") if isinstance(selected_preview, dict) else ""
    promotion = selected_preview.get("promotion", "") if isinstance(selected_preview, dict) else ""
    source_type = selected_preview.get("source_type", "official") if isinstance(selected_preview, dict) else "official"

    # Build a clean handoff summary with customer-safe metadata only.
    summary_lines = [
        "Matchup: " + str(fighter_a or "Unknown") + " vs " + str(fighter_b or "Unknown"),
        "Event: " + str(event_name or "Unknown"),
        "Event date: " + str(event_date or "Unknown"),
        "Promotion: " + str(promotion or "Unknown"),
        "Customer-ready selected-matchup intelligence",
        "Source Traceability",
        "Source URL: " + str(source_url or "Unknown"),
        "Source type: " + str(source_type or "official"),
        "Readiness: " + str(readiness or "ready_for_button2_preview"),
    ]
    return "\n".join(summary_lines)


def _decorate_button2_generated_pdf_open_link(result):
    if not isinstance(result, dict):
        return result
    if result.get("ok") is not True:
        return result

    output_path = result.get("output_path")
    if isinstance(output_path, str) and output_path.strip():
        output_filename = os.path.basename(output_path.strip())
        if _is_safe_generated_pdf_filename(output_filename):
            result["output_filename"] = output_filename
            result["pdf_open_url"] = (
                "/api/button2/generated-report/open?filename="
                + quote(output_filename, safe="")
            )
    return result


def _build_ingest_payload_from_selected_matchup(selected_preview):
    selected = selected_preview if isinstance(selected_preview, dict) else {}
    source_url = selected.get("source_url", "")
    source_type = selected.get("source_type", "official")
    template_pack = _resolve_button2_template_pack_preview()
    template_pack_root = template_pack.get("template_pack_root", "")
    template_pack_available = bool(template_pack.get("template_pack_available", False))
    template_pack_error = template_pack.get("template_pack_error", "")

    summary_preview = _build_selected_matchup_premium_summary(selected)

    source_traceability_sources = []
    if isinstance(source_url, str) and source_url.strip().lower().startswith(("http://", "https://")):
        source_traceability_sources.append({
            "source_url": source_url.strip(),
            "source_type": source_type if isinstance(source_type, str) and source_type.strip() else "official",
            "source_class": "tier_a",
            "confidence_level": "high",
            "citation_completeness": "complete",
            "verification_status": "verified",
            "source_date": str(selected.get("event_date") or "n/a"),
        })

    return {
        "destination_marker": "button2_report_generation_preview",
        "context_kind": "button1_selected_matchup_handoff",
        "ingest_mode": "premium_template_selected_matchup",
        "template_renderer_profile": "premium_template_pack_v29",
        "template_pack_root": template_pack_root,
        "template_pack_available": template_pack_available,
        "template_pack_error": template_pack_error,
        "selected_matchup_payload": {
            "fighter_a": selected.get("fighter_a", ""),
            "fighter_b": selected.get("fighter_b", ""),
            "event_name": selected.get("event_name", ""),
            "event_date": selected.get("event_date", ""),
            "promotion": selected.get("promotion", ""),
            "source_url": source_url,
            "source_type": source_type,
            "report_ready_status": selected.get("report_ready_status", ""),
        },
        "source_traceability_sources": source_traceability_sources,
        "dossier_summary_preview": summary_preview,
    }


def _is_safe_generated_pdf_filename(filename):
    if not isinstance(filename, str):
        return False
    value = filename.strip()
    if not value:
        return False
    if os.path.basename(value) != value:
        return False
    if "/" in value or "\\" in value or ".." in value:
        return False
    if value.startswith("."):
        return False
    if not value.lower().endswith(".pdf"):
        return False
    return bool(re.match(r"^[A-Za-z0-9._-]+$", value))


def _list_generated_pdf_library_rows(output_root):
    rows = []
    if not isinstance(output_root, str) or not output_root.strip():
        return rows

    try:
        for entry in os.listdir(output_root):
            if not _is_safe_generated_pdf_filename(entry):
                continue
            full_path = os.path.join(output_root, entry)
            if not os.path.isfile(full_path):
                continue
            stat = os.stat(full_path)
            rows.append({
                "filename": entry,
                "modified_ts": float(stat.st_mtime),
                "modified_iso": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
                "size_bytes": int(stat.st_size),
                "open_url": "/api/button2/generated-report/open?filename=" + quote(entry, safe=""),
            })
    except Exception:
        return []

    rows.sort(key=lambda item: item.get("modified_ts", 0.0), reverse=True)
    return rows


def _repo_root_path():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _button1_canonical_source_path():
    return os.path.join(
        _repo_root_path(),
        "ops",
        "approved_sources",
        "button1_live_event_source_rows.json",
    )


def _button2_canonical_queue_path():
    return os.path.join(
        _repo_root_path(),
        "ops",
        "prf_queue",
        "button2_approved_fight_queue.json",
    )


def _safe_json_load(path):
    if not isinstance(path, str) or not path.strip() or not os.path.isfile(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _safe_text(value):
    if isinstance(value, str):
        return value.strip()
    if value is None:
        return ""
    return str(value).strip()


def _safe_bool(value, default=False):
    if value is None:
        return bool(default)
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _url_from_row(row):
    if not isinstance(row, dict):
        return ""
    for key in ("source_url", "canonical_source_url", "event_url", "provenance_url", "official_url", "url"):
        value = row.get(key)
        if isinstance(value, str) and value.strip().lower().startswith(("http://", "https://")):
            return value.strip()
    provenance = row.get("provenance")
    if isinstance(provenance, dict):
        src = provenance.get("source_url")
        if isinstance(src, str) and src.strip().lower().startswith(("http://", "https://")):
            return src.strip()
    return ""


def _derive_event_id(event_row):
    if not isinstance(event_row, dict):
        return ""
    event_id = _safe_text(event_row.get("event_id") or event_row.get("candidate_id"))
    if event_id:
        return event_id
    event_name = _safe_text(event_row.get("event_name") or event_row.get("event") or event_row.get("event_title"))
    return _slugify_text(event_name)


def _derive_source_matchup_id(event_row, matchup_row, matchup_index):
    if isinstance(matchup_row, dict):
        for key in ("matchup_id", "candidate_id", "fight_id", "fight_key", "matchup_key", "id"):
            value = _safe_text(matchup_row.get(key))
            if value:
                return value

    base_id = _safe_text(event_row.get("candidate_id") or event_row.get("event_id"))
    if base_id:
        return f"{base_id}_mu_{matchup_index}"

    event_name = _safe_text(event_row.get("event_name") or event_row.get("event") or event_row.get("event_title"))
    fighter_a = _safe_text((matchup_row or {}).get("fighter_a") or (matchup_row or {}).get("fighter_a_name"))
    fighter_b = _safe_text((matchup_row or {}).get("fighter_b") or (matchup_row or {}).get("fighter_b_name"))
    return _slugify_text(f"{event_name}_{fighter_a}_vs_{fighter_b}_{matchup_index}") or f"matchup_{matchup_index}"


def _normalize_readiness_status(value):
    status = _safe_text(value).lower()
    if not status:
        return ""
    if status == "ready_to_save":
        return "ready_for_button2_preview"
    return status


def _readiness_is_promotable(value):
    status = _normalize_readiness_status(value)
    return status in {
        "ready",
        "ready_for_button2_preview",
        "ready_for_button2_generation",
        "ready_for_button2",
        "customer_ready",
        "customer_ready_verified",
    }


def _flatten_button1_canonical_matchup_rows():
    source_doc = _safe_json_load(_button1_canonical_source_path())
    events = source_doc.get("events") if isinstance(source_doc, dict) else []
    if not isinstance(events, list):
        return []

    flattened = []
    for event_row in events:
        if not isinstance(event_row, dict):
            continue

        event_name = _safe_text(event_row.get("event_name") or event_row.get("event") or event_row.get("event_title"))
        if not event_name:
            continue

        event_source_url = _url_from_row(event_row)
        event_source_type = _safe_text(event_row.get("source_type")) or "official"
        event_provenance = _safe_text(event_row.get("provenance_status")) or "source_backed"
        event_readiness = _safe_text(
            event_row.get("button2_readiness_status")
            or event_row.get("report_ready_status")
            or event_row.get("ready_state")
        )
        event_queue_save_eligible = _safe_bool(event_row.get("queue_save_eligible"), default=True)
        event_blocked_reason = _safe_text(event_row.get("blocked_reason"))

        matchups = event_row.get("matchups")
        if not isinstance(matchups, list) or not matchups:
            matchups = [{}]

        for idx, matchup_row in enumerate(matchups):
            if not isinstance(matchup_row, dict):
                continue

            fighter_a = _safe_text(matchup_row.get("fighter_a") or matchup_row.get("fighter_a_name"))
            fighter_b = _safe_text(matchup_row.get("fighter_b") or matchup_row.get("fighter_b_name"))
            if not fighter_a or not fighter_b:
                continue

            source_url = _url_from_row(matchup_row) or event_source_url
            source_type = _safe_text(matchup_row.get("source_type")) or event_source_type
            provenance_status = _safe_text(matchup_row.get("provenance_status")) or event_provenance
            readiness = _safe_text(
                matchup_row.get("button2_readiness_status")
                or matchup_row.get("report_ready_status")
                or matchup_row.get("ready_state")
                or event_readiness
            )
            queue_save_eligible = _safe_bool(
                matchup_row.get("queue_save_eligible"),
                default=event_queue_save_eligible,
            )
            blocked_reason = _safe_text(matchup_row.get("blocked_reason") or event_blocked_reason)

            source_matchup_id = _derive_source_matchup_id(event_row, matchup_row, idx)
            canonical_matchup_id = _safe_text(matchup_row.get("matchup_id"))
            if not canonical_matchup_id:
                canonical_matchup_id = _slugify_text(
                    f"{event_name}_{fighter_a}_vs_{fighter_b}"
                ) or source_matchup_id

            flattened.append({
                "source_matchup_id": source_matchup_id,
                "matchup_id": canonical_matchup_id,
                "event_id": _derive_event_id(event_row),
                "event_name": event_name,
                "event_date": _safe_text(matchup_row.get("event_date") or event_row.get("event_date")),
                "promotion": _safe_text(matchup_row.get("promotion") or event_row.get("promotion")),
                "fighter_a": fighter_a,
                "fighter_b": fighter_b,
                "weight_class": _safe_text(matchup_row.get("weight_class") or event_row.get("weight_class")),
                "bout_order": matchup_row.get("bout_order") if isinstance(matchup_row.get("bout_order"), int) else (event_row.get("bout_order") if isinstance(event_row.get("bout_order"), int) else None),
                "source_url": source_url,
                "source_type": source_type or "official",
                "provenance_status": provenance_status or "source_backed",
                "button2_readiness_status": _normalize_readiness_status(readiness),
                "report_ready_status": _normalize_readiness_status(readiness),
                "customer_ready_possible": _safe_bool(matchup_row.get("customer_ready_possible"), default=True),
                "blocked_reason": blocked_reason,
                "queue_save_eligible": queue_save_eligible,
                "source_backed": bool(source_url),
            })

    return flattened


def _queue_duplicate_fallback_key(event_name, fighter_a, fighter_b, source_url):
    event_key = _slugify_text(event_name)
    a_key = _slugify_text(fighter_a)
    b_key = _slugify_text(fighter_b)
    source_txt = _safe_text(source_url)
    source_domain = ""
    if source_txt:
        try:
            source_domain = (_safe_text(urlparse(source_txt).netloc)).lower()
        except Exception:
            source_domain = ""
    source_key = _slugify_text(source_domain or source_txt)
    return f"{event_key}|{a_key}|{b_key}|{source_key}"


def _build_queue_dedupe_indexes(queue_rows):
    id_set = set()
    fallback_set = set()
    for row in queue_rows:
        if not isinstance(row, dict):
            continue
        row_matchup_id = _safe_text(row.get("matchup_id")).lower()
        if row_matchup_id:
            id_set.add(row_matchup_id)
        fallback_key = _queue_duplicate_fallback_key(
            row.get("event_name", ""),
            row.get("fighter_a", ""),
            row.get("fighter_b", ""),
            row.get("source_url", ""),
        )
        if fallback_key:
            fallback_set.add(fallback_key)
    return id_set, fallback_set


def _build_button2_queue_row_from_button1(source_row, approved_at):
    return {
        "matchup_id": _safe_text(source_row.get("matchup_id")),
        "event_name": _safe_text(source_row.get("event_name")),
        "event_id": _safe_text(source_row.get("event_id")),
        "event_date": _safe_text(source_row.get("event_date")),
        "promotion": _safe_text(source_row.get("promotion")),
        "fighter_a": _safe_text(source_row.get("fighter_a")),
        "fighter_b": _safe_text(source_row.get("fighter_b")),
        "weight_class": _safe_text(source_row.get("weight_class")),
        "bout_order": source_row.get("bout_order") if isinstance(source_row.get("bout_order"), int) else None,
        "source_url": _safe_text(source_row.get("source_url")),
        "source_type": _safe_text(source_row.get("source_type")) or "official",
        "provenance_status": _safe_text(source_row.get("provenance_status")) or "source_backed",
        "button2_readiness_status": _normalize_readiness_status(source_row.get("button2_readiness_status") or source_row.get("report_ready_status")) or "ready_for_button2_preview",
        "report_ready_status": _normalize_readiness_status(source_row.get("report_ready_status") or source_row.get("button2_readiness_status")) or "ready_for_button2_preview",
        "customer_ready_possible": bool(source_row.get("customer_ready_possible", True)),
        "blocked_reason": _safe_text(source_row.get("blocked_reason")),
        "approved_for_button2": True,
        "approved_at": approved_at,
        "approved_by": "operator",
        "queue_source": "button1_promote_ready_matchups_to_button2_queue_v1",
    }


def _queue_counts(queue_rows):
    ready_statuses = {
        "ready",
        "ready_for_button2_preview",
        "ready_for_button2_generation",
        "ready_for_button2",
        "customer_ready",
        "customer_ready_verified",
    }
    ready_count = 0
    blocked_count = 0
    for row in queue_rows:
        if not isinstance(row, dict):
            continue
        status = _safe_text(row.get("button2_readiness_status") or row.get("report_ready_status")).lower()
        blocked_reason = _safe_text(row.get("blocked_reason"))
        customer_ready_possible = bool(row.get("customer_ready_possible", True))
        if status in ready_statuses and not blocked_reason and customer_ready_possible:
            ready_count += 1
        else:
            blocked_count += 1
    return ready_count, blocked_count


def _write_canonical_button2_queue(queue_rows):
    queue_path = _button2_canonical_queue_path()
    os.makedirs(os.path.dirname(queue_path), exist_ok=True)
    ready_count, blocked_count = _queue_counts(queue_rows)
    payload = {
        "queue": queue_rows,
        "metadata": {
            "source": "operator_approved_fight_queue",
            "last_updated_at": _utc_now_iso_seconds(),
            "total_rows": len(queue_rows),
            "ready_count": ready_count,
            "blocked_count": blocked_count,
            "canonical_source": True,
        },
    }
    with open(queue_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=True)


def _path_is_in_process_path(target_path):
    if not isinstance(target_path, str) or not target_path.strip():
        return False
    normalized_target = os.path.normcase(os.path.normpath(target_path.strip()))
    raw_path = os.environ.get("PATH", "")
    if not isinstance(raw_path, str) or not raw_path.strip():
        return False
    for entry in raw_path.split(os.pathsep):
        cleaned = entry.strip().strip('"')
        if not cleaned:
            continue
        normalized_entry = os.path.normcase(os.path.normpath(cleaned))
        if normalized_entry == normalized_target:
            return True
    return False


_BUTTON2_GTK_DLL_DIR_HANDLE = None


def _ensure_msys_gtk_path_in_process_path(target_path):
    """Inject MSYS2 GTK bin path into this process PATH when present and missing."""
    if not isinstance(target_path, str) or not target_path.strip():
        return False
    if not os.path.isdir(target_path):
        return False
    if _path_is_in_process_path(target_path):
        return False

    current_path = os.environ.get("PATH", "")
    if isinstance(current_path, str) and current_path.strip():
        os.environ["PATH"] = target_path + os.pathsep + current_path
    else:
        os.environ["PATH"] = target_path
    return True


def _ensure_windows_gtk_dll_directory_loaded(target_path):
    """Load GTK DLL directory for current process on Windows to support WeasyPrint imports."""
    global _BUTTON2_GTK_DLL_DIR_HANDLE

    if os.name != "nt":
        return False
    if not isinstance(target_path, str) or not target_path.strip():
        return False
    if not os.path.isdir(target_path):
        return False
    if _BUTTON2_GTK_DLL_DIR_HANDLE is not None:
        return True

    add_dll_directory = getattr(os, "add_dll_directory", None)
    if not callable(add_dll_directory):
        return False

    try:
        _BUTTON2_GTK_DLL_DIR_HANDLE = add_dll_directory(target_path)
        return True
    except Exception:
        return False


def _resolve_button2_pdf_output_root_for_runtime():
    """Resolve BUTTON2_PDF_OUTPUT_ROOT for this process without touching non-output preflight checks."""
    output_root = os.environ.get("BUTTON2_PDF_OUTPUT_ROOT", "")
    output_root_value = output_root.strip() if isinstance(output_root, str) else ""
    if output_root_value:
        return output_root_value

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    reports_dir = os.path.join(repo_root, "reports")
    if os.path.isdir(reports_dir):
        os.environ["BUTTON2_PDF_OUTPUT_ROOT"] = reports_dir
        return reports_dir

    return ""


def _build_runtime_preflight_status(host_value):
    output_root_value = _resolve_button2_pdf_output_root_for_runtime()
    output_root_ready = bool(output_root_value) and os.path.isdir(output_root_value)

    gtk_path = r"C:\msys64\ucrt64\bin"
    _ensure_msys_gtk_path_in_process_path(gtk_path)
    _ensure_windows_gtk_dll_directory_loaded(gtk_path)
    gtk_exists = os.path.isdir(gtk_path)
    gtk_in_path = _path_is_in_process_path(gtk_path)

    weasyprint_ready = False
    weasyprint_detail = "import_unchecked"
    try:
        import weasyprint  # noqa: F401

        weasyprint_ready = True
        weasyprint_detail = "import_ok"
    except Exception as exc:  # pragma: no cover - exact import error may vary by env
        weasyprint_detail = "import_error:" + exc.__class__.__name__

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    reports_dir = os.path.join(repo_root, "reports")
    reports_exists = os.path.isdir(reports_dir)
    reports_writable = reports_exists and os.access(reports_dir, os.W_OK)

    safe_route_available = any(
        rule.rule == "/api/button2/generated-report/open" and "GET" in rule.methods
        for rule in app.url_map.iter_rules()
    )

    host = host_value if isinstance(host_value, str) else ""
    host = host.strip()
    if ":" in host:
        server_port = host.rsplit(":", 1)[-1]
    elif host:
        server_port = "80"
    else:
        server_port = "unknown"

    return {
        "button2_pdf_output_root": {
            "ready": output_root_ready,
            "value": output_root_value or "unset",
        },
        "msys_gtk_dll_path": {
            "ready": gtk_exists and gtk_in_path,
            "value": gtk_path,
            "path_exists": gtk_exists,
            "in_process_path": gtk_in_path,
        },
        "weasyprint_render_readiness": {
            "ready": weasyprint_ready,
            "value": weasyprint_detail,
        },
        "reports_output_directory": {
            "ready": reports_exists and reports_writable,
            "value": reports_dir,
            "exists": reports_exists,
            "writable": reports_writable,
        },
        "safe_pdf_open_route": {
            "ready": safe_route_available,
            "value": "/api/button2/generated-report/open",
        },
        "current_server_port": {
            "ready": server_port != "unknown",
            "value": server_port,
        },
    }

# ─── Data Helpers ──────────────────────────────────────────────────────────────

def _build_accuracy_comparison_summary():
    """
    Load the accuracy comparison summary (waiting rows + compared rows).
    Returns a dict with waiting_for_results list and compared_results list.
    """
    # In production this reads from ops/accuracy/accuracy_ledger.json.
    # For tests / offline mode, return a safe empty structure.
    try:
        import json
        ledger_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "ops", "accuracy", "accuracy_ledger.json"
        )
        if os.path.exists(ledger_path):
            with open(ledger_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
    except Exception:
        pass
    return {"waiting_for_results": [], "compared_results": [], "summary_metrics": {}}


def _build_waiting_row_selected_key(row):
    """Return the row's selected_key (fight identifier)."""
    return (
        row.get("selected_key")
        or row.get("fight_key")
        or row.get("fight_name")
        or ""
    )


# ─── Normal Dashboard ──────────────────────────────────────────────────────────

@app.route("/")
def index():
    """3-button operator dashboard."""
    runtime_warning = ""
    output_root = _resolve_button2_pdf_output_root_for_runtime()
    if not isinstance(output_root, str) or not output_root.strip():
        runtime_warning = "PDF output root missing - start dashboard with Windows launch script."
    runtime_preflight = _build_runtime_preflight_status(request.host)
    return render_template(
        "index.html",
        button2_runtime_warning=runtime_warning,
        runtime_preflight=runtime_preflight,
    )


@app.route("/advanced-dashboard")
def advanced_dashboard():
    """Advanced / workshop dashboard."""
    return render_template("advanced_dashboard.html")


# ─── Button 1 API ─────────────────────────────────────────────────────────────

@app.route("/api/operator/button1/fight-queue", methods=["GET"])
def get_fight_queue():
    """Return the current fight queue (read-only)."""
    return jsonify({"ok": True, "fights": [], "total": 0})


@app.route("/api/operator/button1/save-selected", methods=["POST"])
def save_selected_fights():
    """
    [OPERATOR GATE] Save operator-approved fights to global database.
    Requires explicit operator approval.
    """
    data = request.get_json(silent=True) or {}
    approved = data.get("operator_approved", False)
    if not approved:
        return jsonify({
            "ok": False,
            "error": "operator_approval_required",
            "message": "Fights must be approved by operator before saving."
        }), 403
    # In production: persist to database here.
    return jsonify({"ok": True, "saved": 0, "message": "gate_passed_no_fights_provided"})


@app.route("/api/button1-to-button2/dossier-handoff-preview", methods=["POST"])
def button1_to_button2_dossier_handoff_preview():
    """Return preview-only sanitized Button1->Button2 dossier handoff payload."""
    build_button1_to_button2_readonly_dossier_handoff_preview = (
        _lazy_button1_to_button2_readonly_dossier_handoff_preview()
    )
    body = request.get_json(silent=True)
    if body is None:
        body = {}
    if not isinstance(body, dict):
        return jsonify({
            "ok": False,
            "error": "invalid_request_body",
            "destination_marker": "button2_report_generation_preview",
            "preview_only": True,
            "button1_export_performed": False,
            "button2_generation_performed": False,
            "pdf_generation_performed": False,
            "file_write_performed": False,
            "delivery_performed": False,
            "report_write_performed": False,
            "profile_create_update_merge": False,
            "database_ranking_writes": False,
            "result_report_learning_calibration": False,
        }), 400

    dossier_data = body.get("dossier_data", body)
    if not isinstance(dossier_data, dict):
        dossier_data = {}

    preview_payload = build_button1_to_button2_readonly_dossier_handoff_preview(dossier_data)
    return jsonify({
        "ok": True,
        **preview_payload,
        "button2_generation_performed": False,
    })


@app.route("/api/button1-button2/event-card-matchup/select-preview", methods=["POST"])
def button1_button2_event_card_matchup_select_preview():
    """Preview-only matchup selection from source-backed Button 1 rows into Button 2 candidate context."""
    safety_flags = {
        "pdf_generation_performed": False,
        "queue_write_performed": False,
        "delivery_performed": False,
        "email_send_performed": False,
        "external_api_delivery_performed": False,
        "learning_apply_performed": False,
        "calibration_write_performed": False,
        "button3_mutation_performed": False,
    }

    body = request.get_json(silent=True)
    if body is None:
        body = {}
    if not isinstance(body, dict):
        return jsonify({
            "selection_preview": True,
            "selected_for_button2": False,
            "event_name": "",
            "event_date": "",
            "promotion": "",
            "source_url": "",
            "source_type": "",
            "fighter_a": "",
            "fighter_b": "",
            "matchup_id": "",
            "candidate_id": "",
            "report_ready_status": "selection_denied",
            "denial_reasons": ["unsupported_selection"],
            "safety_flags": safety_flags,
        }), 400

    event_id = body.get("event_id") if isinstance(body.get("event_id"), str) else ""
    matchup_id = body.get("matchup_id") if isinstance(body.get("matchup_id"), str) else ""
    candidate_id = body.get("candidate_id") if isinstance(body.get("candidate_id"), str) else ""
    selected_index = body.get("selected_index") if isinstance(body.get("selected_index"), int) else None
    operator_selected = bool(body.get("operator_selected", False))
    candidate_rows = body.get("candidate_rows", [])
    if not isinstance(candidate_rows, list):
        candidate_rows = []

    if not operator_selected:
        return jsonify({
            "selection_preview": True,
            "selected_for_button2": False,
            "event_name": "",
            "event_date": "",
            "promotion": "",
            "source_url": "",
            "source_type": "",
            "fighter_a": "",
            "fighter_b": "",
            "matchup_id": matchup_id,
            "candidate_id": candidate_id,
            "report_ready_status": "selection_denied",
            "denial_reasons": ["operator_selection_required"],
            "safety_flags": safety_flags,
        })

    if not event_id and not matchup_id and not candidate_id:
        return jsonify({
            "selection_preview": True,
            "selected_for_button2": False,
            "event_name": "",
            "event_date": "",
            "promotion": "",
            "source_url": "",
            "source_type": "",
            "fighter_a": "",
            "fighter_b": "",
            "matchup_id": "",
            "candidate_id": "",
            "report_ready_status": "selection_denied",
            "denial_reasons": ["operator_selection_required"],
            "safety_flags": safety_flags,
        })

    matched = None
    for row in candidate_rows:
        if not isinstance(row, dict):
            continue
        row_id = _candidate_row_id(row)
        if matchup_id and row_id == matchup_id:
            matched = row
            break
        if candidate_id and row_id == candidate_id:
            matched = row
            break

    if matched is None and selected_index is not None:
        if 0 <= selected_index < len(candidate_rows):
            candidate_row = candidate_rows[selected_index]
            if isinstance(candidate_row, dict):
                matched = candidate_row

    if matched is None:
        return jsonify({
            "selection_preview": True,
            "selected_for_button2": False,
            "event_name": "",
            "event_date": "",
            "promotion": "",
            "source_url": "",
            "source_type": "",
            "fighter_a": "",
            "fighter_b": "",
            "matchup_id": matchup_id,
            "candidate_id": candidate_id,
            "report_ready_status": "selection_denied",
            "denial_reasons": ["missing_matchup"],
            "safety_flags": safety_flags,
        })

    matched_event_id = _candidate_row_event_id(matched)
    if event_id and matched_event_id and event_id.strip().lower() != matched_event_id:
        return jsonify({
            "selection_preview": True,
            "selected_for_button2": False,
            "event_name": matched.get("event_name", ""),
            "event_date": matched.get("event_date", ""),
            "promotion": matched.get("promotion", ""),
            "source_url": matched.get("source_url", ""),
            "source_type": matched.get("source_type", ""),
            "fighter_a": _extract_matchup_names(matched)[0],
            "fighter_b": _extract_matchup_names(matched)[1],
            "matchup_id": _candidate_row_id(matched),
            "candidate_id": _candidate_row_id(matched),
            "report_ready_status": "selection_denied",
            "denial_reasons": ["missing_event_card"],
            "safety_flags": safety_flags,
        })

    if not _is_source_backed_candidate_row(matched):
        return jsonify({
            "selection_preview": True,
            "selected_for_button2": False,
            "event_name": matched.get("event_name", ""),
            "event_date": matched.get("event_date", ""),
            "promotion": matched.get("promotion", ""),
            "source_url": "",
            "source_type": matched.get("source_type", ""),
            "fighter_a": _extract_matchup_names(matched)[0],
            "fighter_b": _extract_matchup_names(matched)[1],
            "matchup_id": _candidate_row_id(matched),
            "candidate_id": _candidate_row_id(matched),
            "report_ready_status": "selection_denied",
            "denial_reasons": ["source_backed_matchup_required", "provenance_missing"],
            "safety_flags": safety_flags,
        })

    source_url = ""
    for key in ("source_url", "canonical_source_url", "event_url", "provenance_url", "official_url", "url"):
        value = matched.get(key)
        if isinstance(value, str) and value.strip().lower().startswith(("http://", "https://")):
            source_url = value.strip()
            break
    if not source_url:
        provenance = matched.get("provenance")
        if isinstance(provenance, dict):
            maybe = provenance.get("source_url")
            if isinstance(maybe, str) and maybe.strip().lower().startswith(("http://", "https://")):
                source_url = maybe.strip()

    fighter_a, fighter_b = _extract_matchup_names(matched)

    return jsonify({
        "selection_preview": True,
        "selected_for_button2": True,
        "event_name": matched.get("event_name", ""),
        "event_date": matched.get("event_date", ""),
        "promotion": matched.get("promotion", ""),
        "source_url": source_url,
        "source_type": matched.get("source_type", "official"),
        "fighter_a": fighter_a,
        "fighter_b": fighter_b,
        "matchup_id": _candidate_row_id(matched),
        "candidate_id": _candidate_row_id(matched),
        "report_ready_status": "ready_for_button2_preview",
        "denial_reasons": [],
        "safety_flags": safety_flags,
    })


# ─── Button 2 API ─────────────────────────────────────────────────────────────

@app.route("/api/operator/button2/generate-report", methods=["POST"])
def generate_report():
    """
    [OPERATOR GATE] Generate a premium PDF report.
    Requires explicit operator approval.
    
    Request body (JSON):
      operator_approved: bool (must be True)
      fight_id: str (required, e.g. "bahram_rajabzadeh_vs_donovan_wisse")
      ingest_payload: dict (required, handoff context from Button 1)
    
    Response: JSON with ok, error/message, output_path (if success), telemetry flags
    """
    generate_button2_report_render_gate_integration = _lazy_button2_report_generation_route_render_gate_integration()
    data = request.get_json(silent=True) or {}
    result = generate_button2_report_render_gate_integration(data)
    result = _decorate_button2_generated_pdf_open_link(result)
    if isinstance(result, dict) and result.get("ok") is True:
        ingest_payload = data.get("ingest_payload") if isinstance(data, dict) else {}
        selected_matchup = ingest_payload.get("selected_matchup_payload", {}) if isinstance(ingest_payload, dict) else {}
        if not isinstance(selected_matchup, dict):
            selected_matchup = {}
        result["button3_preview_input"] = _build_button3_preview_input_from_generated_report(
            result,
            fight_id=data.get("fight_id", "") if isinstance(data, dict) else "",
            matchup_id=selected_matchup.get("matchup_id", ""),
            fighter_a=selected_matchup.get("fighter_a", ""),
            fighter_b=selected_matchup.get("fighter_b", ""),
            event_name=selected_matchup.get("event_name", ""),
        )
    status_code = 200 if result.get("ok") else (403 if result.get("error") == "operator_approval_required" else 400)
    return jsonify(result), status_code


@app.route("/api/operator/button2/customer-flow/dry-run-contract-preview", methods=["POST"])
def button2_customer_flow_dry_run_contract_preview():
    """Return a decision-only customer-flow dry-run contract preview."""
    run_button2_customer_flow_dry_run_contract_preview = _lazy_button2_customer_flow_dry_run_contract_preview()
    body = request.get_json(silent=True)
    if body is None:
        body = {}

    result = run_button2_customer_flow_dry_run_contract_preview(body)
    if not isinstance(result, dict):
        result = result.to_dict()

    status_code = 200 if result.get("ok") else 400
    return jsonify(result), status_code


@app.route("/api/button2/selected-matchup/generate-guarded-v1", methods=["POST"])
def button2_selected_matchup_generate_guarded_v1():
    """Gate2 guarded generation from an explicitly selected Button1->Button2 matchup preview."""
    (
        load_button2_queue_readonly,
        _get_queue_ready_rows,
        resolve_matchup_id_from_queue,
        _get_rows_for_event,
    ) = _lazy_button2_queue_loader_readonly()
    generate_button2_report_render_gate_integration = _lazy_button2_report_generation_route_render_gate_integration()
    body = request.get_json(silent=True)
    if body is None:
        body = {}
    if not isinstance(body, dict):
        return jsonify({
            "ok": False,
            "error": "invalid_request_body",
            "message": "Request body must be a JSON object.",
            "operator_action_required": True,
            "selected_matchup_required": True,
            "queue_write_performed": False,
            "delivery_performed": False,
            "external_api_delivery_performed": False,
            "learning_apply_performed": False,
            "calibration_write_performed": False,
            "button3_mutation_performed": False,
        }), 400

    operator_approved = bool(body.get("operator_approved", False))
    if not operator_approved:
        return jsonify({
            "ok": False,
            "error": "operator_approval_required",
            "message": "Explicit operator approval is required for Button 2 generation.",
            "operator_action_required": True,
            "selected_matchup_required": True,
            "queue_write_performed": False,
            "delivery_performed": False,
            "external_api_delivery_performed": False,
            "learning_apply_performed": False,
            "calibration_write_performed": False,
            "button3_mutation_performed": False,
        }), 403

    selected_matchup_id = body.get("selected_matchup_id")
    queue_rows = body.get("approved_queue_rows")
    canonical_queue_rows = load_button2_queue_readonly()
    matched_row, resolution_error, resolution_status = resolve_matchup_id_from_queue(
        str(selected_matchup_id or "").strip(),
        canonical_queue_rows,
    )

    # Backward-compatibility for existing test scaffolds only.
    # Runtime generation still resolves from canonical queue first.
    if matched_row is None and app.config.get("TESTING") and isinstance(queue_rows, list):
        matched_row, resolution_error, resolution_status = _resolve_selected_matchup_row_from_queue(
            selected_matchup_id,
            queue_rows,
        )

    if matched_row is None and resolution_error == "matchup_id_not_found":
        resolution_error = "selected_matchup_unknown"
        resolution_status = 422
    elif matched_row is None and resolution_error == "invalid_matchup_id":
        resolution_error = "selected_matchup_id_required"
        resolution_status = 400
    elif matched_row is None and resolution_error == "matchup_id_duplicated":
        resolution_error = "selected_matchup_duplicated"
        resolution_status = 422
    elif matched_row is None and resolution_error == "queue_empty":
        resolution_error = "approved_queue_rows_required"
        resolution_status = 400
    if matched_row is None:
        return jsonify({
            "ok": False,
            "error": resolution_error,
            "message": "Selected matchup resolution failed. Provide a valid selected_matchup_id from the canonical queue source.",
            "operator_action_required": True,
            "selected_matchup_required": True,
            "queue_write_performed": False,
            "delivery_performed": False,
            "external_api_delivery_performed": False,
            "learning_apply_performed": False,
            "calibration_write_performed": False,
            "button3_mutation_performed": False,
        }), resolution_status

    selected_preview = _build_selected_matchup_preview_from_row(matched_row)
    if not isinstance(selected_preview, dict) or not selected_preview:
        return jsonify({
            "ok": False,
            "error": "selected_matchup_incomplete",
            "message": "Selected matchup is incomplete and cannot be generated.",
            "operator_action_required": True,
            "selected_matchup_required": True,
            "queue_write_performed": False,
            "delivery_performed": False,
            "external_api_delivery_performed": False,
            "learning_apply_performed": False,
            "calibration_write_performed": False,
            "button3_mutation_performed": False,
        }), 422

    if selected_preview.get("selected_for_button2") is not True:
        return jsonify({
            "ok": False,
            "error": "selected_matchup_not_ready",
            "message": "Selected matchup must be confirmed for Button 2 before generation.",
            "operator_action_required": True,
            "selected_matchup_required": True,
            "queue_write_performed": False,
            "delivery_performed": False,
            "external_api_delivery_performed": False,
            "learning_apply_performed": False,
            "calibration_write_performed": False,
            "button3_mutation_performed": False,
        }), 422

    if not _is_button2_row_ready_for_generation(matched_row):
        return jsonify({
            "ok": False,
            "error": "selected_matchup_not_ready",
            "message": "Selected matchup is not ready for Button 2 generation.",
            "operator_action_required": True,
            "selected_matchup_required": True,
            "queue_write_performed": False,
            "delivery_performed": False,
            "external_api_delivery_performed": False,
            "learning_apply_performed": False,
            "calibration_write_performed": False,
            "button3_mutation_performed": False,
        }), 422

    source_url = selected_preview.get("source_url", "")
    if not (isinstance(source_url, str) and source_url.strip().lower().startswith(("http://", "https://"))):
        return jsonify({
            "ok": False,
            "error": "source_backed_matchup_required",
            "message": "Selected matchup must be source-backed before generation.",
            "operator_action_required": True,
            "selected_matchup_required": True,
            "queue_write_performed": False,
            "delivery_performed": False,
            "external_api_delivery_performed": False,
            "learning_apply_performed": False,
            "calibration_write_performed": False,
            "button3_mutation_performed": False,
        }), 422

    fight_id = _build_fight_id_from_selected_matchup(selected_preview)
    if not fight_id:
        return jsonify({
            "ok": False,
            "error": "fight_id_derive_failed",
            "message": "Could not derive fight_id from selected matchup.",
            "operator_action_required": True,
            "selected_matchup_required": True,
            "queue_write_performed": False,
            "delivery_performed": False,
            "external_api_delivery_performed": False,
            "learning_apply_performed": False,
            "calibration_write_performed": False,
            "button3_mutation_performed": False,
        }), 422

    generation_request_id = uuid.uuid4().hex
    selected_matchup_id = selected_preview.get("matchup_id") or selected_preview.get("candidate_id") or fight_id
    output_filename_override = _build_selected_matchup_output_filename(fight_id, generation_request_id)

    ingest_payload = _build_ingest_payload_from_selected_matchup(selected_preview)
    generation_payload = {
        "operator_approved": True,
        "fight_id": fight_id,
        "ingest_payload": ingest_payload,
        "output_filename_override": output_filename_override,
        "generation_request_id": generation_request_id,
    }

    result = generate_button2_report_render_gate_integration(generation_payload)
    if not isinstance(result, dict):
        result = {
            "ok": False,
            "error": "generation_result_invalid",
            "message": "Generation returned malformed response.",
        }
    result = _decorate_button2_generated_pdf_open_link(result)

    generated_pdf_text = ""
    extracted_page_count = None
    file_meta = {
        "file_modified_at": None,
        "file_size_bytes": None,
    }
    text_scan = {
        "any_forbidden_found": False,
        "found_markers": [],
        "marker_hits": {},
    }
    selected_matchup_matches_pdf_text = False

    strict_gate_passed = False
    strict_gate_violations = []

    if result.get("ok") is True:
        output_path = result.get("output_path", "")
        generated_pdf_text, extracted_page_count = _extract_pdf_text_and_page_count(output_path)
        file_meta = _collect_file_metadata(output_path)
        text_scan = _scan_forbidden_markers(generated_pdf_text)
        selected_matchup_matches_pdf_text = _selected_matchup_matches_pdf_text(selected_preview, generated_pdf_text)
        strict_gate_passed, strict_gate_violations = _selected_matchup_passes_strict_pdf_quality_gate(
            selected_preview,
            result,
            generated_pdf_text,
            extracted_page_count,
        )

        if text_scan.get("any_forbidden_found") or not strict_gate_passed:
            try:
                if isinstance(output_path, str) and output_path.strip() and os.path.isfile(output_path):
                    os.remove(output_path)
            except Exception:
                pass

            return jsonify({
                "ok": False,
                "error": "customer_pdf_quality_gate_failed",
                "reason": "legacy_section_card_engine_detected",
                "message": "Customer-facing PDF quality gate failed.",
                "customer_pdf_quality_gate_failed": True,
                "strict_quality_gate_passed": strict_gate_passed,
                "strict_quality_gate_violations": strict_gate_violations,
                "operator_action_required": True,
                "selected_matchup_required": True,
                "selected_matchup_generate_request_accepted": True,
                "selected_matchup_fighter_a": selected_preview.get("fighter_a", ""),
                "selected_matchup_fighter_b": selected_preview.get("fighter_b", ""),
                "selected_matchup_event": selected_preview.get("event_name", ""),
                "selected_matchup_id": selected_matchup_id,
                "generation_request_id": generation_request_id,
                "renderer_route_used": result.get("renderer_route_used", "unknown"),
                "renderer_profile": result.get("renderer_profile", ""),
                "template_pack_root": result.get("template_pack_root", _DEFAULT_BUTTON2_TEMPLATE_PACK_ROOT),
                "template_pack_asset_backed": bool(result.get("template_pack_asset_backed", False)),
                "jbalia_layout_applied": bool(result.get("premium_template_render_used", False)),
                "generated_at": result.get("generated_at") or _utc_now_iso_seconds(),
                "file_modified_at": file_meta.get("file_modified_at") or result.get("file_modified_at"),
                "file_size_bytes": file_meta.get("file_size_bytes") or result.get("file_size_bytes"),
                "page_count": extracted_page_count or result.get("page_count"),
                "text_scan_forbidden_markers": text_scan,
                "selected_matchup_matches_pdf_text": selected_matchup_matches_pdf_text,
                "stale_file_reused": bool(result.get("stale_file_reused", False)),
                "selected_matchup_preview": {
                    "fighter_a": selected_preview.get("fighter_a", ""),
                    "fighter_b": selected_preview.get("fighter_b", ""),
                    "event_name": selected_preview.get("event_name", ""),
                    "source_url": selected_preview.get("source_url", ""),
                    "report_ready_status": selected_preview.get("report_ready_status", ""),
                },
                "queue_write_performed": False,
                "delivery_performed": False,
                "external_api_delivery_performed": False,
                "learning_apply_performed": False,
                "calibration_write_performed": False,
                "button3_mutation_performed": False,
            }), 422

    if result.get("ok") is not True:
        strict_gate_violations.append("generation_failed_before_pdf_quality_gate")

    result.update({
        "customer_pdf_quality_gate_failed": False,
        "strict_quality_gate_passed": strict_gate_passed,
        "strict_quality_gate_violations": strict_gate_violations,
        "operator_action_required": True,
        "selected_matchup_required": True,
        "selected_matchup_generate_request_accepted": True,
        "selected_matchup_fighter_a": selected_preview.get("fighter_a", ""),
        "selected_matchup_fighter_b": selected_preview.get("fighter_b", ""),
        "selected_matchup_event": selected_preview.get("event_name", ""),
        "selected_matchup_id": selected_matchup_id,
        "generation_request_id": generation_request_id,
        "renderer_route_used": result.get("renderer_route_used", "unknown"),
        "renderer_profile": result.get("renderer_profile", ""),
        "template_pack_root": result.get("template_pack_root", _DEFAULT_BUTTON2_TEMPLATE_PACK_ROOT),
        "template_pack_asset_backed": bool(result.get("template_pack_asset_backed", False)),
        "jbalia_layout_applied": bool(result.get("premium_template_render_used", False)),
        "generated_at": result.get("generated_at") or _utc_now_iso_seconds(),
        "file_modified_at": file_meta.get("file_modified_at") or result.get("file_modified_at"),
        "file_size_bytes": file_meta.get("file_size_bytes") or result.get("file_size_bytes"),
        "page_count": extracted_page_count or result.get("page_count"),
        "text_scan_forbidden_markers": text_scan,
        "selected_matchup_matches_pdf_text": selected_matchup_matches_pdf_text,
        "stale_file_reused": bool(result.get("stale_file_reused", False)),
        "selected_matchup_preview": {
            "fighter_a": selected_preview.get("fighter_a", ""),
            "fighter_b": selected_preview.get("fighter_b", ""),
            "event_name": selected_preview.get("event_name", ""),
            "source_url": selected_preview.get("source_url", ""),
            "report_ready_status": selected_preview.get("report_ready_status", ""),
        },
        "resolved_from_approved_queue_rows": True,
        "queue_write_performed": False,
        "external_api_delivery_performed": False,
        "learning_apply_performed": False,
        "calibration_write_performed": False,
        "button3_mutation_performed": False,
    })

    status_code = 200 if result.get("ok") else (403 if result.get("error") == "operator_approval_required" else 400)
    response = make_response(jsonify(result), status_code)
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/api/button2/queue-ready", methods=["GET"])
def button2_queue_ready_v1():
    """Load real approved fight queue from canonical source for Button 2."""
    load_button2_queue_readonly, _, _, _ = _lazy_button2_queue_loader_readonly()
    queue_rows = load_button2_queue_readonly()

    ready_statuses = {
        "ready",
        "ready_for_button2_preview",
        "ready_for_button2_generation",
        "ready_for_button2",
        "customer_ready",
        "customer_ready_verified",
    }
    ready_rows = [
        r for r in queue_rows
        if str(r.get("button2_readiness_status") or r.get("report_ready_status") or "").strip().lower() in ready_statuses
        and not str(r.get("blocked_reason") or "").strip()
        and bool(r.get("customer_ready_possible", True))
    ]
    blocked_rows = [r for r in queue_rows if r not in ready_rows]

    response = {
        "ok": True,
        "queue_rows": queue_rows,
        "total_rows": len(queue_rows),
        "ready_count": len(ready_rows),
        "blocked_count": len(blocked_rows),
        "canonical_source_used": True,
        "browser_seeding_bypassed": True,
        "source_of_truth": "ops/prf_queue/button2_approved_fight_queue.json",
    }

    resp = make_response(jsonify(response), 200)
    resp.headers["Cache-Control"] = "no-store"
    return resp


@app.route("/api/button1/promote-ready-matchups-to-button2-queue", methods=["POST"])
def button1_promote_ready_matchups_to_button2_queue_v1():
    load_button2_queue_readonly, _, _, _ = _lazy_button2_queue_loader_readonly()
    body = request.get_json(silent=True)
    if body is None:
        body = {}
    if not isinstance(body, dict):
        return jsonify({
            "ok": False,
            "error": "invalid_request_body",
            "message": "Request body must be a JSON object.",
            "requested_count": 0,
            "promoted_count": 0,
            "skipped_count": 0,
            "duplicate_count": 0,
            "queue_before_count": 0,
            "queue_after_count": 0,
            "promoted_rows": [],
            "skipped_rows": [],
            "duplicate_rows": [],
            "canonical_source": "ops/approved_sources/button1_live_event_source_rows.json",
            "canonical_destination": "ops/prf_queue/button2_approved_fight_queue.json",
            "queue_write_performed": False,
            "delivery_performed": False,
            "external_api_delivery_performed": False,
            "learning_apply_performed": False,
            "calibration_write_performed": False,
            "button3_mutation_performed": False,
        }), 400

    operator_approval = bool(body.get("operator_approval", False))
    if not operator_approval:
        return jsonify({
            "ok": False,
            "error": "operator_approval_required",
            "message": "Explicit operator approval is required for queue promotion.",
            "requested_count": 0,
            "promoted_count": 0,
            "skipped_count": 0,
            "duplicate_count": 0,
            "queue_before_count": len(load_button2_queue_readonly()),
            "queue_after_count": len(load_button2_queue_readonly()),
            "promoted_rows": [],
            "skipped_rows": [],
            "duplicate_rows": [],
            "canonical_source": "ops/approved_sources/button1_live_event_source_rows.json",
            "canonical_destination": "ops/prf_queue/button2_approved_fight_queue.json",
            "queue_write_performed": False,
            "delivery_performed": False,
            "external_api_delivery_performed": False,
            "learning_apply_performed": False,
            "calibration_write_performed": False,
            "button3_mutation_performed": False,
        }), 403

    promote_all_ready = bool(body.get("promote_all_ready", False))
    requested_matchup_ids_raw = body.get("matchup_ids", [])
    requested_matchup_ids = []
    if isinstance(requested_matchup_ids_raw, list):
        requested_matchup_ids = [
            _safe_text(v)
            for v in requested_matchup_ids_raw
            if _safe_text(v)
        ]

    if not promote_all_ready and not requested_matchup_ids:
        return jsonify({
            "ok": False,
            "error": "matchup_ids_or_promote_all_ready_required",
            "message": "Provide matchup_ids[] or set promote_all_ready=true.",
            "requested_count": 0,
            "promoted_count": 0,
            "skipped_count": 0,
            "duplicate_count": 0,
            "queue_before_count": len(load_button2_queue_readonly()),
            "queue_after_count": len(load_button2_queue_readonly()),
            "promoted_rows": [],
            "skipped_rows": [],
            "duplicate_rows": [],
            "canonical_source": "ops/approved_sources/button1_live_event_source_rows.json",
            "canonical_destination": "ops/prf_queue/button2_approved_fight_queue.json",
            "queue_write_performed": False,
            "delivery_performed": False,
            "external_api_delivery_performed": False,
            "learning_apply_performed": False,
            "calibration_write_performed": False,
            "button3_mutation_performed": False,
        }), 400

    source_rows = _flatten_button1_canonical_matchup_rows()
    source_by_id = {}
    for row in source_rows:
        source_id = _safe_text(row.get("source_matchup_id"))
        if source_id and source_id not in source_by_id:
            source_by_id[source_id] = row

    canonical_queue_path = _button2_canonical_queue_path()
    queue_doc = _safe_json_load(canonical_queue_path)
    queue_rows = queue_doc.get("queue") if isinstance(queue_doc, dict) else []
    if not isinstance(queue_rows, list):
        queue_rows = []
    queue_rows = [dict(r) for r in queue_rows if isinstance(r, dict)]

    queue_before_count = len(queue_rows)
    existing_id_keys, existing_fallback_keys = _build_queue_dedupe_indexes(queue_rows)

    candidate_rows = []
    skipped_rows = []
    requested_ids_set = set(_safe_text(v) for v in requested_matchup_ids if _safe_text(v))

    if promote_all_ready:
        for row in source_rows:
            if not _safe_bool(row.get("queue_save_eligible"), default=False):
                continue
            if not _readiness_is_promotable(row.get("button2_readiness_status") or row.get("report_ready_status")):
                continue
            if _safe_text(row.get("blocked_reason")):
                continue
            if not _safe_bool(row.get("source_backed"), default=False):
                continue
            candidate_rows.append(row)
    else:
        for requested_id in requested_ids_set:
            source_row = source_by_id.get(requested_id)
            if source_row is None:
                skipped_rows.append({
                    "source_matchup_id": requested_id,
                    "reason": "matchup_id_not_found_in_canonical_button1_source",
                })
                continue
            candidate_rows.append(source_row)

    promoted_rows = []
    duplicate_rows = []
    approved_at = _utc_now_iso_seconds()

    for row in candidate_rows:
        source_matchup_id = _safe_text(row.get("source_matchup_id"))
        matchup_id = _safe_text(row.get("matchup_id"))
        readiness = _safe_text(row.get("button2_readiness_status") or row.get("report_ready_status"))
        blocked_reason = _safe_text(row.get("blocked_reason"))
        source_backed = _safe_bool(row.get("source_backed"), default=False)
        queue_save_eligible = _safe_bool(row.get("queue_save_eligible"), default=False)

        if not queue_save_eligible:
            skipped_rows.append({
                "source_matchup_id": source_matchup_id,
                "matchup_id": matchup_id,
                "event_name": _safe_text(row.get("event_name")),
                "fighter_a": _safe_text(row.get("fighter_a")),
                "fighter_b": _safe_text(row.get("fighter_b")),
                "reason": "queue_save_not_eligible",
            })
            continue

        if not source_backed:
            skipped_rows.append({
                "source_matchup_id": source_matchup_id,
                "matchup_id": matchup_id,
                "event_name": _safe_text(row.get("event_name")),
                "fighter_a": _safe_text(row.get("fighter_a")),
                "fighter_b": _safe_text(row.get("fighter_b")),
                "reason": "not_source_backed",
            })
            continue

        if not _readiness_is_promotable(readiness):
            skipped_rows.append({
                "source_matchup_id": source_matchup_id,
                "matchup_id": matchup_id,
                "event_name": _safe_text(row.get("event_name")),
                "fighter_a": _safe_text(row.get("fighter_a")),
                "fighter_b": _safe_text(row.get("fighter_b")),
                "reason": "not_ready_for_button2",
                "readiness_status": _normalize_readiness_status(readiness),
            })
            continue

        if blocked_reason:
            skipped_rows.append({
                "source_matchup_id": source_matchup_id,
                "matchup_id": matchup_id,
                "event_name": _safe_text(row.get("event_name")),
                "fighter_a": _safe_text(row.get("fighter_a")),
                "fighter_b": _safe_text(row.get("fighter_b")),
                "reason": "blocked_reason_present",
                "blocked_reason": blocked_reason,
            })
            continue

        fallback_key = _queue_duplicate_fallback_key(
            row.get("event_name", ""),
            row.get("fighter_a", ""),
            row.get("fighter_b", ""),
            row.get("source_url", ""),
        )
        matchup_id_key = matchup_id.lower()

        if (matchup_id_key and matchup_id_key in existing_id_keys) or (fallback_key and fallback_key in existing_fallback_keys):
            duplicate_rows.append({
                "source_matchup_id": source_matchup_id,
                "matchup_id": matchup_id,
                "event_name": _safe_text(row.get("event_name")),
                "fighter_a": _safe_text(row.get("fighter_a")),
                "fighter_b": _safe_text(row.get("fighter_b")),
                "reason": "duplicate_existing_queue_row",
            })
            continue

        queue_row = _build_button2_queue_row_from_button1(row, approved_at)
        queue_rows.append(queue_row)
        promoted_rows.append(queue_row)
        if matchup_id_key:
            existing_id_keys.add(matchup_id_key)
        if fallback_key:
            existing_fallback_keys.add(fallback_key)

    if promoted_rows:
        _write_canonical_button2_queue(queue_rows)

    requested_count = len(candidate_rows) if promote_all_ready else len(requested_ids_set)
    queue_after_count = len(queue_rows)
    response = {
        "ok": True,
        "requested_count": requested_count,
        "promoted_count": len(promoted_rows),
        "skipped_count": len(skipped_rows),
        "duplicate_count": len(duplicate_rows),
        "queue_before_count": queue_before_count,
        "queue_after_count": queue_after_count,
        "promoted_rows": promoted_rows,
        "skipped_rows": skipped_rows,
        "duplicate_rows": duplicate_rows,
        "canonical_source": "ops/approved_sources/button1_live_event_source_rows.json",
        "canonical_destination": "ops/prf_queue/button2_approved_fight_queue.json",
        "queue_write_performed": len(promoted_rows) > 0,
        "delivery_performed": False,
        "external_api_delivery_performed": False,
        "learning_apply_performed": False,
        "calibration_write_performed": False,
        "button3_mutation_performed": False,
    }
    resp = make_response(jsonify(response), 200)
    resp.headers["Cache-Control"] = "no-store"
    return resp


@app.route("/api/button2/generate-selected-batch", methods=["POST"])
def button2_generate_selected_batch_v1():
    """
    Batch PDF generation for multiple selected matchups.

    Request body:
    {
      "selected_matchup_ids": ["matchup_id_1", "matchup_id_2", ...],
      "operator_approval": true,
      "event_id": "...",  (optional, alternative to selected_matchup_ids)
      "generate_all_ready_for_event": true  (optional, with event_id)
    }

    Response:
    {
      "ok": true,
      "batch_id": "...",
      "requested_count": N,
      "generated_count": N,
      "failed_count": N,
      "skipped_count": N,
      "results": [
        {
          "matchup_id": "...",
          "fighter_a": "...",
          "fighter_b": "...",
          "event_name": "...",
          "ok": true/false,
          "output_path": "...",
          "output_filename": "...",
          "open_url": "/api/button2/generated-report/open?filename=...",
          "error": "...",
          "reason": "..."
        }
      ],
      "output_paths": ["...", "..."],
      ...governance flags all false...
    }
    """
    (
        load_button2_queue_readonly,
        _get_queue_ready_rows,
        resolve_matchup_id_from_queue,
        _get_rows_for_event,
    ) = _lazy_button2_queue_loader_readonly()
    generate_button2_report_render_gate_integration = _lazy_button2_report_generation_route_render_gate_integration()
    body = request.get_json(silent=True)
    if body is None:
        body = {}
    if not isinstance(body, dict):
        return jsonify({
            "ok": False,
            "error": "invalid_request_body",
            "message": "Request body must be a JSON object.",
            "batch_id": "",
            "requested_count": 0,
            "generated_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
            "results": [],
            "output_paths": [],
            "queue_write_performed": False,
            "delivery_performed": False,
            "external_api_delivery_performed": False,
            "learning_apply_performed": False,
        }), 400

    operator_approval = bool(body.get("operator_approval", False))
    if not operator_approval:
        return jsonify({
            "ok": False,
            "error": "operator_approval_required",
            "message": "Explicit operator approval is required for batch generation.",
            "batch_id": "",
            "requested_count": 0,
            "generated_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
            "results": [],
            "output_paths": [],
            "queue_write_performed": False,
            "delivery_performed": False,
            "external_api_delivery_performed": False,
            "learning_apply_performed": False,
            "calibration_write_performed": False,
            "button3_mutation_performed": False,
        }), 403

    # minimal batch initializations to ensure control-flow tokens below are valid
    batch_id = ""
    results = []
    output_paths = []
    generated_count = 0
    failed_count = 0
    skipped_count = 0

    # selection validation: require selected_matchup_ids or event_id+generate_all_ready_for_event
    selected_ids = body.get("selected_matchup_ids") if isinstance(body, dict) else None
    event_id = _safe_text(body.get("event_id"))
    promote_all_ready = bool(body.get("generate_all_ready_for_event", False))
    if not (isinstance(selected_ids, list) and selected_ids) and not (event_id and promote_all_ready):
        return jsonify({
            "ok": False,
            "error": "selected_matchup_ids_required",
            "message": "Provide selected_matchup_ids[] or set event_id + generate_all_ready_for_event=true.",
            "batch_id": "",
            "requested_count": 0,
            "generated_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
            "results": [],
            "output_paths": [],
            "queue_write_performed": False,
            "delivery_performed": False,
            "external_api_delivery_performed": False,
            "learning_apply_performed": False,
            "calibration_write_performed": False,
            "button3_mutation_performed": False,
        }), 400

    # build a simple deduped_rows list from selected_matchup_ids or event_id selection
    deduped_rows = []
    try:
        all_rows = load_button2_queue_readonly()
    except Exception:
        all_rows = []
    if not isinstance(all_rows, list):
        all_rows = []

    # if event-based selection, filter by event_id
    if event_id and promote_all_ready:
        deduped_rows = [r for r in all_rows if _safe_text(r.get("event_id")) == event_id]
    # else if selected_ids provided, deduplicate and use resolve_matchup_id_from_queue for each id
    elif isinstance(selected_ids, list) and selected_ids:
        # deduplicate by normalizing and using set
        deduped_ids = []
        seen = set()
        for v in selected_ids:
            normalized = _safe_text(v)
            if normalized and normalized not in seen:
                deduped_ids.append(normalized)
                seen.add(normalized)
        found_rows = []
        for matchup_id in deduped_ids:
            matched_row, resolution_error, _ = resolve_matchup_id_from_queue(matchup_id, all_rows)
            if matched_row is not None:
                found_rows.append(matched_row)
        # if no matching rows found for provided ids, reject as unknown ids
        if not found_rows:
            return jsonify({
                "ok": False,
                "error": "unknown_matchup_ids",
                "message": "None of the provided selected_matchup_ids were found in the approved queue.",
            }), 422
        deduped_rows = found_rows

    for row in deduped_rows:
        matchup_id = _safe_text(row.get("matchup_id"))
        fighter_a = _safe_text(row.get("fighter_a"))
        fighter_b = _safe_text(row.get("fighter_b"))
        event_name = _safe_text(row.get("event_name"))
        # Skip blocked rows early
        blocked_reason = _safe_text(row.get("blocked_reason"))
        if blocked_reason:
            results.append({
                "matchup_id": matchup_id,
                "fighter_a": fighter_a,
                "fighter_b": fighter_b,
                "event_name": event_name,
                "ok": False,
                "output_path": "",
                "output_filename": "",
                "open_url": "",
                "error": "blocked_reason_present",
                "reason": blocked_reason,
                "content_gate_passed": False,
            })
            skipped_count += 1
            continue

        selected_preview = _build_selected_matchup_preview_from_row(row)
        if not selected_preview:
            results.append({
                "matchup_id": matchup_id,
                "fighter_a": fighter_a,
                "fighter_b": fighter_b,
                "event_name": event_name,
                "ok": False,
                "output_path": "",
                "output_filename": "",
                "open_url": "",
                "error": "preview_build_failed",
                "reason": "Could not build preview from row",
                "content_gate_passed": False,
            })
            failed_count += 1
            continue

        # Check readiness
        if selected_preview.get("selected_for_button2") is not True:
            results.append({
                "matchup_id": matchup_id,
                "fighter_a": fighter_a,
                "fighter_b": fighter_b,
                "event_name": event_name,
                "ok": False,
                "output_path": "",
                "output_filename": "",
                "open_url": "",
                "error": "not_ready_for_button2",
                "reason": "Matchup not ready for Button 2",
                "content_gate_passed": False,
            })
            skipped_count += 1
            continue

        # Check source
        source_url = selected_preview.get("source_url", "")
        if not (isinstance(source_url, str) and source_url.strip().lower().startswith(("http://", "https://"))):
            results.append({
                "matchup_id": matchup_id,
                "fighter_a": fighter_a,
                "fighter_b": fighter_b,
                "event_name": event_name,
                "ok": False,
                "output_path": "",
                "output_filename": "",
                "open_url": "",
                "error": "not_source_backed",
                "reason": "Matchup not source-backed",
                "content_gate_passed": False,
            })
            skipped_count += 1
            continue

        # Generate PDF
        fight_id = _build_fight_id_from_selected_matchup(selected_preview)
        generation_request_id = uuid.uuid4().hex
        output_filename_override = _build_selected_matchup_output_filename(fight_id, generation_request_id)

        ingest_payload = _build_ingest_payload_from_selected_matchup(selected_preview)
        generation_payload = {
            "operator_approved": True,
            "fight_id": fight_id,
            "ingest_payload": ingest_payload,
            "output_filename_override": output_filename_override,
            "generation_request_id": generation_request_id,
        }

        result = generate_button2_report_render_gate_integration(generation_payload)
        if not isinstance(result, dict):
            result = {
                "ok": False,
                "error": "generation_result_invalid",
                "message": "Primary generation returned malformed response.",
            }
        if result.get("ok") is not True:
            results.append({
                "matchup_id": matchup_id,
                "fighter_a": fighter_a,
                "fighter_b": fighter_b,
                "event_name": event_name,
                "ok": False,
                "output_path": "",
                "output_filename": "",
                "open_url": "",
                "error": result.get("error", "generation_failed"),
                "reason": result.get("message", "PDF generation failed"),
                "content_gate_passed": False,
            })
            failed_count += 1
            continue

        if result.get("ok") is True:
            result = _decorate_button2_generated_pdf_open_link(result)
            output_path = result.get("output_path", "")
            generated_pdf_text, extracted_page_count = _extract_pdf_text_and_page_count(output_path)
            forbidden_scan = _scan_forbidden_markers(generated_pdf_text)
            strict_gate_passed, strict_gate_violations = _selected_matchup_passes_strict_pdf_quality_gate(
                selected_preview,
                result,
                generated_pdf_text,
                extracted_page_count,
            )

            if (generated_pdf_text and _selected_matchup_matches_pdf_text(selected_preview, generated_pdf_text)
                and not forbidden_scan.get("any_forbidden_found") and strict_gate_passed):

                result = _decorate_button2_generated_pdf_open_link(result)
                results.append({
                    "matchup_id": matchup_id,
                    "fighter_a": fighter_a,
                    "fighter_b": fighter_b,
                    "event_name": event_name,
                    "ok": True,
                    "output_path": output_path,
                    "output_filename": os.path.basename(output_path) if output_path else "",
                    "open_url": result.get("pdf_open_url", ""),
                    "error": "",
                    "reason": "",
                    "content_gate_passed": True,
                    "customer_ready": True,
                    "visual_gate_status": "premium_template_confirmed",
                    "button3_preview_input": _build_button3_preview_input_from_generated_report(
                        result,
                        fight_id=fight_id,
                        matchup_id=matchup_id,
                        fighter_a=fighter_a,
                        fighter_b=fighter_b,
                        event_name=event_name,
                    ),
                })
                if output_path:
                    output_paths.append(output_path)
                generated_count += 1
            else:
                try:
                    if isinstance(output_path, str) and output_path.strip() and os.path.isfile(output_path):
                        os.remove(output_path)
                except Exception:
                    pass

                results.append({
                    "matchup_id": matchup_id,
                    "fighter_a": fighter_a,
                    "fighter_b": fighter_b,
                    "event_name": event_name,
                    "ok": False,
                    "output_path": "",
                    "output_filename": "",
                    "open_url": "",
                    "error": "pdf_quality_gate_failed",
                    "reason": "PDF did not pass quality checks",
                    "strict_quality_gate_violations": strict_gate_violations,
                    "content_gate_passed": False,
                })
                failed_count += 1
        else:
            results.append({
                "matchup_id": matchup_id,
                "fighter_a": fighter_a,
                "fighter_b": fighter_b,
                "event_name": event_name,
                "ok": False,
                "output_path": "",
                "output_filename": "",
                "open_url": "",
                "error": result.get("error", "generation_failed"),
                "reason": result.get("message", "PDF generation failed"),
                "content_gate_passed": False,
            })
            failed_count += 1

    response = {
        "ok": generated_count > 0,
        "batch_id": batch_id,
        "requested_count": len(deduped_rows),
        "generated_count": generated_count,
        "failed_count": failed_count,
        "skipped_count": skipped_count,
        "results": results,
        "output_paths": output_paths,
        "batch_execution_timestamp": _utc_now_iso_seconds(),
        "queue_write_performed": False,
        "delivery_performed": False,
        "external_api_delivery_performed": False,
        "report_generation_performed": generated_count > 0,
        "learning_apply_performed": False,
        "calibration_write_performed": False,
        "button3_mutation_performed": False,
    }

    resp = make_response(jsonify(response), 200)
    resp.headers["Cache-Control"] = "no-store"
    return resp


@app.route("/api/button2/generated-report/open", methods=["GET"])
def button2_generated_report_open_v1():
    """Serve generated Button 2 PDFs from the configured output root only."""
    get_pdf_output_root, OutputRootNotConfiguredError, OutputRootInvalidError = _lazy_button2_pdf_output_root_config()
    filename = request.args.get("filename", "")
    if not _is_safe_generated_pdf_filename(filename):
        return jsonify({
            "ok": False,
            "error": "invalid_filename",
            "message": "filename must be a safe PDF filename.",
        }), 400

    _resolve_button2_pdf_output_root_for_runtime()
    try:
        output_root = get_pdf_output_root()
    except (OutputRootNotConfiguredError, OutputRootInvalidError) as e:
        return jsonify({
            "ok": False,
            "error": "output_root_unavailable",
            "message": str(e),
        }), 400

    canonical_root = os.path.realpath(output_root)
    candidate_path = os.path.realpath(os.path.join(output_root, filename))
    if not candidate_path.startswith(canonical_root + os.sep):
        return jsonify({
            "ok": False,
            "error": "path_traversal_rejected",
            "message": "Requested file escapes configured output root.",
        }), 400

    if not os.path.isfile(candidate_path):
        return jsonify({
            "ok": False,
            "error": "file_not_found",
            "message": "Generated PDF was not found.",
        }), 404

    response = send_from_directory(output_root, filename, mimetype="application/pdf")
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/api/button2/generated-report/library", methods=["GET"])
def button2_generated_report_library_v1():
    """Render a safe read-only library of generated PDFs from configured output root."""
    get_pdf_output_root, OutputRootNotConfiguredError, OutputRootInvalidError = _lazy_button2_pdf_output_root_config()
    if request.args.get("path") or request.args.get("dir") or request.args.get("folder"):
        return jsonify({
            "ok": False,
            "error": "invalid_query",
            "message": "Directory override is not allowed.",
        }), 400

    _resolve_button2_pdf_output_root_for_runtime()
    try:
        output_root = get_pdf_output_root()
    except (OutputRootNotConfiguredError, OutputRootInvalidError) as e:
        return jsonify({
            "ok": False,
            "error": "output_root_unavailable",
            "message": str(e),
        }), 400

    rows = _list_generated_pdf_library_rows(output_root)
    response = make_response(render_template(
        "button2_pdf_library.html",
        pdf_rows=rows,
        output_root=output_root,
        preview_only=True,
        upload_enabled=False,
        delete_enabled=False,
        rename_enabled=False,
        delivery_performed=False,
        queue_write_performed=False,
        learning_apply_performed=False,
        calibration_write_performed=False,
        button3_mutation_performed=False,
    ))
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/api/button2/dossier-handoff/ingest-preview", methods=["POST"])
def button2_dossier_handoff_ingest_preview():
    """Return preview-only Button 2 ingest context from Button 1 handoff payload."""
    build_button2_readonly_dossier_handoff_ingest_preview = _lazy_button2_dossier_handoff_ingest_preview()
    body = request.get_json(silent=True)
    if body is None:
        body = {}
    if not isinstance(body, dict):
        return jsonify({
            "ok": False,
            "error": "invalid_request_body",
            "destination_marker": "",
            "button2_ingest_preview_context": None,
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
        }), 400

    handoff_payload = body.get("handoff_payload", body)
    if not isinstance(handoff_payload, dict):
        handoff_payload = {}

    result = build_button2_readonly_dossier_handoff_ingest_preview(handoff_payload)
    status_code = 200 if result.get("ok") else 400
    return jsonify(result), status_code


@app.route("/api/button2/dossier-handoff/report-context-preview", methods=["POST"])
def button2_dossier_handoff_report_context_preview():
    """Return preview-only Button 2 report-context preview from ingest preview context."""
    build_button2_dossier_handoff_report_context_preview = (
        _lazy_button2_dossier_handoff_report_context_preview()
    )
    body = request.get_json(silent=True)
    if body is None:
        body = {}
    if not isinstance(body, dict):
        return jsonify({
            "ok": False,
            "error": "invalid_request_body",
            "destination_marker": "",
            "report_context_preview": None,
            "preview_only": True,
            "report_context_preview_ready": False,
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
        }), 400

    ingest_payload = body.get("ingest_payload", body)
    if not isinstance(ingest_payload, dict):
        ingest_payload = {}

    result = build_button2_dossier_handoff_report_context_preview(ingest_payload)
    status_code = 200 if result.get("ok") else 400
    return jsonify(result), status_code


# ─── Button 3 API ─────────────────────────────────────────────────────────────

@app.route(
    "/api/operator/button3/auto-result-source-yield-live-executor-preview",
    methods=["POST"],
)
def button3_auto_result_source_yield_live_executor_preview():
    """
    Read-only Button 3 executor preview.

    Accepts:
      limit (int, 1-200, default 44)
      selected_keys (list of str, optional filter)
      include_advanced_diagnostics (bool, default false)

    Returns:
      summary counts for the 5 simple states
      row_states per fight
      telemetry flags (all mutations = false)

    GOVERNANCE:
      preview_only = True
      No mutations, no learning, no calibration, no queue writes.
    """
    body = request.get_json(silent=True)
    if body is not None and not isinstance(body, dict):
        return jsonify({
            "ok": False,
            "error": "invalid_request",
            "telemetry": {
                "preview_only": True,
                "mutation_performed": False,
                "durable_write_performed": False,
                "learning_apply_performed": False,
                "calibration_write_performed": False,
                "queue_write_performed": False,
                "auto_apply_performed": False,
            },
        }), 400

    if body is None:
        body = {}

    # Parse parameters
    limit = body.get("limit", 44)
    try:
        limit = int(limit)
        limit = max(1, min(200, limit))
    except (TypeError, ValueError):
        limit = 44

    selected_keys = body.get("selected_keys", None)
    if selected_keys is not None and not isinstance(selected_keys, list):
        return jsonify({
            "ok": False,
            "error": "selected_keys_must_be_list",
            "telemetry": {
                "preview_only": True,
                "mutation_performed": False,
                "durable_write_performed": False,
                "learning_apply_performed": False,
                "calibration_write_performed": False,
                "queue_write_performed": False,
                "auto_apply_performed": False,
            },
        }), 400

    include_diagnostics = bool(body.get("include_advanced_diagnostics", False))

    # Load waiting rows
    try:
        summary = _build_accuracy_comparison_summary()
        waiting_rows = summary.get("waiting_for_results", [])
        if not isinstance(waiting_rows, list):
            waiting_rows = []
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": "failed_to_load_waiting_rows",
            "detail": str(e),
            "telemetry": {
                "preview_only": True,
                "mutation_performed": False,
                "durable_write_performed": False,
                "learning_apply_performed": False,
                "calibration_write_performed": False,
                "queue_write_performed": False,
                "auto_apply_performed": False,
            },
        }), 500

    # Apply key filter
    if selected_keys is not None:
        waiting_rows = [
            r for r in waiting_rows
            if _build_waiting_row_selected_key(r) in selected_keys
        ]

    # Apply limit
    waiting_rows = waiting_rows[:limit]

    # Execute read-only preview
    try:
        response = build_readonly_executor_preview_response(
            waiting_rows=waiting_rows,
            provider=None,
            include_diagnostics=include_diagnostics,
        )
        return jsonify(response)
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": "executor_failed",
            "detail": str(e),
            "telemetry": {
                "preview_only": True,
                "mutation_performed": False,
                "durable_write_performed": False,
                "learning_apply_performed": False,
                "calibration_write_performed": False,
                "queue_write_performed": False,
                "auto_apply_performed": False,
            },
        }), 500


@app.route("/api/button3/result-comparison/preview-v1", methods=["POST"])
def button3_result_comparison_preview_v1():
    """Preview-only Button 3 result comparison route (no apply/mutation path)."""
    build_button3_result_comparison_preview = _lazy_button3_result_comparison_preview()
    body = request.get_json(silent=True)
    if body is None:
        body = {}
    if not isinstance(body, dict):
        return jsonify({
            "ok": False,
            "error": "invalid_request_body",
            "message": "Request body must be a JSON object.",
            "preview_only": True,
            "mutation_performed": False,
            "learning_apply_performed": False,
            "calibration_write_performed": False,
            "queue_write_performed": False,
            "button3_mutation_performed": False,
        }), 400

    preview_body = dict(body)
    official_field_aliases = {
        "official_winner": "actual_winner",
        "official_method": "actual_method",
        "official_round": "actual_round",
        "official_time": "actual_time",
        "official_result_source": "result_source_url",
        "result_verification_status": "result_verification_status",
        "source_confidence": "source_confidence",
    }
    for official_key, preview_key in official_field_aliases.items():
        if official_key in preview_body and not preview_body.get(preview_key):
            preview_body[preview_key] = preview_body[official_key]

    response = build_button3_result_comparison_preview(preview_body)
    return jsonify(response), 200


@app.route("/api/operator/button3/official-result-auto-search-yield-sweep-preview", methods=["POST"])
def button3_official_result_auto_search_yield_sweep_preview():
    """Legacy endpoint — wraps executor preview for compatibility."""
    return button3_auto_result_source_yield_live_executor_preview()


@app.route("/api/accuracy/comparison-summary", methods=["GET"])
def accuracy_comparison_summary():
    """Return the accuracy comparison summary (read-only)."""
    try:
        data = _build_accuracy_comparison_summary()
        return jsonify({"ok": True, **data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/operator/button3/apply-result", methods=["POST"])
def button3_apply_result():
    """
    [OPERATOR GATE] Apply a result to the accuracy ledger.
    Requires explicit operator approval. Never auto-applied.
    """
    data = request.get_json(silent=True) or {}
    approved = data.get("operator_approved", False)
    if not approved:
        return jsonify({
            "ok": False,
            "error": "operator_approval_required",
            "message": "Result apply requires operator approval."
        }), 403
    return jsonify({"ok": True, "message": "gate_passed_no_result_provided"})


@app.route("/api/local-ai/orchestrator/workflow-preview", methods=["POST"])
def local_ai_orchestrator_workflow_preview():
    """Return preview-only workflow plan (or preview run) for one source button."""
    build_three_button_workflow_plan, run_workflow_preview = _lazy_local_ai_workflow_plan()
    body = request.get_json(silent=True)
    if body is None:
        body = {}
    if not isinstance(body, dict):
        return jsonify({
            "ok": False,
            "error": "invalid_request_body",
            "telemetry": dict(_LOCAL_AI_SAFE_TELEMETRY),
        }), 400

    source_button = body.get("source_button", "")
    input_ref_payload = body.get("input_ref", {}) or {}
    context_pack_payload = body.get("context_pack")
    has_context_pack = "context_pack" in body
    has_runtime_context = "use_runtime_context" in body
    use_runtime_context = body.get("use_runtime_context", False)
    execute_preview = bool(body.get("execute_preview", False))

    if has_context_pack and not isinstance(context_pack_payload, dict):
        return jsonify({
            "ok": False,
            "error": "invalid_context_pack",
            "telemetry": dict(_LOCAL_AI_SAFE_TELEMETRY),
        }), 400

    if has_runtime_context and not isinstance(use_runtime_context, bool):
        return jsonify({
            "ok": False,
            "error": "invalid_use_runtime_context",
            "telemetry": dict(_LOCAL_AI_SAFE_TELEMETRY),
        }), 400

    if (not has_context_pack and not use_runtime_context) and not isinstance(input_ref_payload, dict):
        return jsonify({
            "ok": False,
            "error": "invalid_input_ref",
            "telemetry": dict(_LOCAL_AI_SAFE_TELEMETRY),
        }), 400

    try:
        if has_context_pack:
            built_context_pack = build_context_pack(source_button, context_pack_payload)
            job_input_ref = built_context_pack.to_job_input_ref()
        elif use_runtime_context:
            if source_button == "button1_find_fights":
                runtime_context_pack = build_button1_runtime_context_preview()
            else:
                if source_button == "button1_find_fights":
                    runtime_context_pack = build_button1_runtime_context_preview()
                else:
                    runtime_context_pack = build_runtime_context_pack(source_button)
            job_input_ref = runtime_context_pack.to_job_input_ref()
        else:
            kind = str(input_ref_payload.get("kind", "empty") or "empty")
            ref_id = str(input_ref_payload.get("ref_id", "") or "")
            payload = input_ref_payload.get("payload", {})
            if not isinstance(payload, dict):
                payload = {}

            job_input_ref = LocalAIJobInputRef(
                ref_type=kind,
                ref_key=ref_id or kind,
                snapshot_hash=None,
                metadata={"payload": payload},
            )

        workflow = build_three_button_workflow_plan(source_button, job_input_ref)
        if execute_preview:
            workflow = run_workflow_preview(workflow)

        response = {
            "ok": True,
            "workflow": workflow.to_dict(),
            "execute_preview": execute_preview,
            "telemetry": dict(_LOCAL_AI_SAFE_TELEMETRY),
        }
        return jsonify(response)
    except ValueError as exc:
        return jsonify({
            "ok": False,
            "error": str(exc),
            "telemetry": dict(_LOCAL_AI_SAFE_TELEMETRY),
        }), 400
    except Exception as exc:
        return jsonify({
            "ok": False,
            "error": "local_ai_workflow_preview_failed",
            "detail": str(exc),
            "telemetry": dict(_LOCAL_AI_SAFE_TELEMETRY),
        }), 500


@app.route("/api/local-ai/gate1/save-fights/dry-run-apply-preview", methods=["POST"])
def local_ai_gate1_save_fights_dry_run_apply_preview():
    """Return preview-only Gate 1 save-fights dry-run apply projection."""
    run_gate1_save_fights_dry_run_apply_preview = _lazy_gate1_save_fights_preview()
    body = request.get_json(silent=True)
    if body is None:
        body = {}
    if not isinstance(body, dict):
        return jsonify({
            "ok": False,
            "error": "invalid_request_body",
            "preview_only": True,
            "write_authorized": False,
            "mutation_performed": False,
            "queue_write_performed": False,
            "database_write_performed": False,
            "blocking_reasons": ["request body must be an object"],
            "eligible_for_future_approval": False,
            "would_save": [],
            "blocked": [],
        }), 400

    token_preview = body.get("gate_approval_token_preview")
    candidate_scope = body.get("candidate_scope")
    candidate_rows = body.get("candidate_rows", [])
    if not isinstance(candidate_rows, list):
        candidate_rows = []

    result = run_gate1_save_fights_dry_run_apply_preview(
        gate_approval_token_preview=token_preview,
        candidate_rows=candidate_rows,
        candidate_scope=candidate_scope,
    )
    result_payload = result.to_dict()

    response = {
        "ok": bool(result_payload.get("ok", False)),
        "preview_only": True,
        "write_authorized": False,
        "mutation_performed": False,
        "queue_write_performed": False,
        "database_write_performed": False,
        "would_save": list(result_payload.get("would_save_candidate_ids", [])),
        "blocked": list(result_payload.get("blocked_candidate_ids", [])),
        "identity_blocked": list(result_payload.get("identity_blocked_candidate_ids", [])),
        "identity_blocked_count": int(result_payload.get("identity_blocked_count", 0) or 0),
        "identity_blocking_reasons_by_candidate": dict(
            result_payload.get("identity_blocking_reasons_by_candidate", {}) or {}
        ),
        "blocking_reasons": list(result_payload.get("blocking_reasons", [])),
        "eligible_for_future_approval": bool(result_payload.get("eligible_for_future_approval", False)),
    }

    return jsonify(response)


@app.route("/api/local-ai/gate1/save-fights/approved-save-writer-preview", methods=["POST"])
def local_ai_gate1_approved_save_writer_preview():
    """Return preview-only Gate 1 approved save writer scaffold projection."""
    run_gate1_approved_save_writer_scaffold = _lazy_gate1_approved_save_writer()
    body = request.get_json(silent=True)
    if body is None:
        body = {}
    if not isinstance(body, dict):
        return jsonify({
            "ok": False,
            "scaffold_only": True,
            "live_write_enabled": False,
            "write_performed": False,
            "queue_write_performed": False,
            "database_write_performed": False,
            "audit_record_preview": None,
            "rollback_pointer_preview": None,
            "idempotency_key": None,
            "would_write": False,
            "blocking_reasons": ["request body must be an object"],
        }), 400

    # Storage preview mode binding
    storage_preview_mode = body.get("storage_preview_mode", "none")
    allowed_modes = {"none", "in_memory"}
    storage_adapter = None
    if storage_preview_mode not in allowed_modes:
        return jsonify({
            "ok": False,
            "scaffold_only": True,
            "live_write_enabled": False,
            "write_performed": False,
            "queue_write_performed": False,
            "database_write_performed": False,
            "storage_adapter_checked": False,
            "test_write_performed": False,
            "persisted_preview_refs": [],
            "blocking_reasons": ["invalid storage_preview_mode"],
        }), 400
    elif storage_preview_mode == "in_memory":
        from operator_dashboard.local_ai_orchestrator_gate1_save_storage_adapter import InMemoryGate1SaveStorageAdapter
        storage_adapter = InMemoryGate1SaveStorageAdapter()

    scaffold_request = {
        "gate_approval_token_preview": body.get("gate_approval_token_preview"),
        "candidate_scope": body.get("candidate_scope"),
        "candidate_rows": body.get("candidate_rows", []),
        "operator_approved": body.get("operator_approved", False),
        "idempotency_key": body.get("idempotency_key"),
        "write_target": body.get("write_target"),
        "dry_run_required": bool(body.get("dry_run_required", True)),
        "live_write_enabled": bool(body.get("live_write_enabled", False)),
    }
    if not isinstance(scaffold_request["candidate_rows"], list):
        scaffold_request["candidate_rows"] = []

    result = run_gate1_approved_save_writer_scaffold(scaffold_request, storage_adapter=storage_adapter)
    result_payload = result.to_dict()

    response = {
        "ok": bool(result_payload.get("ok", False)),
        "scaffold_only": True,
        "live_write_enabled": False,
        "write_performed": False,
        "queue_write_performed": False,
        "database_write_performed": False,
        "audit_record_preview": result_payload.get("audit_record_preview"),
        "rollback_pointer_preview": result_payload.get("rollback_pointer_preview"),
        "idempotency_key": result_payload.get("idempotency_key"),
        "would_write": bool(result_payload.get("would_write", False)),
        "blocking_reasons": list(result_payload.get("blocking_reasons", [])),
            "storage_adapter_checked": bool(result_payload.get("storage_adapter_checked", False)),
            "test_write_performed": bool(result_payload.get("test_write_performed", False)),
            "persisted_preview_refs": list(result_payload.get("persisted_preview_refs", [])),
    }

    return jsonify(response)


@app.route("/api/global-fighters/identity-resolver/preview", methods=["POST"])
def global_fighters_identity_resolver_preview():
    """
    Preview-only Global Fighter Identity Resolver API.

    Accepts:
      candidate: dict with fighter identity fields
      known_records: list of dict with known global fighter records

    Returns:
      JSON with match results, confidence tier, and no-op write flags.

    GOVERNANCE:
      preview_only = True
      No profile creates, updates, merges, or database writes.
      Fails closed when source_refs are missing.
    """
    (
        resolve_fighter_identity_preview,
        IncomingFighterCandidate,
        KnownFighterRecord,
        SourceRef,
    ) = _lazy_global_fighter_identity_resolver_preview()
    body = request.get_json(silent=True)
    if body is None:
        body = {}
    if not isinstance(body, dict):
        return jsonify({
            "ok": False,
            "error": "invalid_request_body",
            "preview_only": True,
            "profile_create_performed": False,
            "profile_update_performed": False,
            "merge_performed": False,
            "database_write_performed": False,
            "ranking_write_performed": False,
            "learning_apply_performed": False,
            "calibration_write_performed": False,
        }), 400

    # Parse candidate
    candidate_payload = body.get("candidate", {})
    if not isinstance(candidate_payload, dict):
        return jsonify({
            "ok": False,
            "error": "invalid_candidate",
            "preview_only": True,
            "profile_create_performed": False,
            "profile_update_performed": False,
            "merge_performed": False,
            "database_write_performed": False,
            "ranking_write_performed": False,
            "learning_apply_performed": False,
            "calibration_write_performed": False,
        }), 400

    # Parse source_refs
    source_refs_payload = candidate_payload.get("source_refs", [])
    if not isinstance(source_refs_payload, list):
        source_refs_payload = []

    source_refs = []
    for sr in source_refs_payload:
        if isinstance(sr, dict):
            source_refs.append(SourceRef(
                source_name=sr.get("source_name", "unknown"),
                source_url=sr.get("source_url"),
                source_type=sr.get("source_type", "unknown"),
                source_date=sr.get("source_date"),
            ))

    # Build candidate
    try:
        candidate = IncomingFighterCandidate(
            name=str(candidate_payload.get("name", "") or ""),
            aliases=candidate_payload.get("aliases", []) if isinstance(candidate_payload.get("aliases"), list) else [],
            nationality=candidate_payload.get("nationality"),
            promotion=candidate_payload.get("promotion"),
            sport_ruleset=candidate_payload.get("sport_ruleset"),
            division=candidate_payload.get("division"),
            date_of_birth=candidate_payload.get("date_of_birth"),
            height=candidate_payload.get("height"),
            reach=candidate_payload.get("reach"),
            stance=candidate_payload.get("stance"),
            record=candidate_payload.get("record"),
            source_refs=source_refs,
        )
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": "candidate_build_failed",
            "detail": str(e),
            "preview_only": True,
            "profile_create_performed": False,
            "profile_update_performed": False,
            "merge_performed": False,
            "database_write_performed": False,
            "ranking_write_performed": False,
            "learning_apply_performed": False,
            "calibration_write_performed": False,
        }), 400

    # Parse known_records
    known_records_payload = body.get("known_records", [])
    if not isinstance(known_records_payload, list):
        known_records_payload = []

    known_records = []
    for kr in known_records_payload:
        if isinstance(kr, dict):
            try:
                known_records.append(KnownFighterRecord(
                    fighter_global_id=str(kr.get("fighter_global_id", "") or ""),
                    full_name=str(kr.get("full_name", "") or ""),
                    known_aliases=kr.get("known_aliases", []) if isinstance(kr.get("known_aliases"), list) else [],
                    nationality=kr.get("nationality"),
                    promotion=kr.get("promotion"),
                    sport_ruleset=kr.get("sport_ruleset"),
                    division=kr.get("division"),
                    date_of_birth=kr.get("date_of_birth"),
                    height=kr.get("height"),
                    reach=kr.get("reach"),
                    stance=kr.get("stance"),
                    record=kr.get("record"),
                    confidence_grade=kr.get("confidence_grade", "C"),
                ))
            except Exception:
                # Skip malformed records
                continue

    # Call preview resolver
    try:
        result = resolve_fighter_identity_preview(candidate, known_records)
        result_dict = result.to_dict()

        # Extract top match
        top_match = None
        if result.candidate_matches:
            top_match = result.candidate_matches[0]

        response = {
            "ok": True,
            "confidence_tier": top_match.confidence_tier.value if top_match else None,
            "matched_record_id": top_match.fighter_global_id if top_match else None,
            "match_score": top_match.confidence_score if top_match else 0.0,
            "manual_review_required": result.manual_review_required,
            "conflict_type": result.conflict_type,
            "conflict_reasons": [result.conflict_type] if result.conflict_type else [],
            "blocking_reasons": [result.conflict_type] if result.conflict_type else [],
            "recommendation": result.recommendation,
            "candidate_matches": [
                {
                    "fighter_global_id": m.fighter_global_id,
                    "full_name": m.full_name,
                    "confidence_tier": m.confidence_tier.value,
                    "confidence_score": m.confidence_score,
                    "rank": m.rank,
                }
                for m in result.candidate_matches
            ],
            "preview_only": True,
            "profile_create_performed": False,
            "profile_update_performed": False,
            "merge_performed": False,
            "database_write_performed": False,
            "ranking_write_performed": False,
            "learning_apply_performed": False,
            "calibration_write_performed": False,
        }
        return jsonify(response)
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": "resolver_failed",
            "detail": str(e),
            "preview_only": True,
            "profile_create_performed": False,
            "profile_update_performed": False,
            "merge_performed": False,
            "database_write_performed": False,
            "ranking_write_performed": False,
            "learning_apply_performed": False,
            "calibration_write_performed": False,
        }), 500


@app.route("/api/global-fighters/known-records/loader-preview", methods=["POST"])
def global_fighters_known_records_loader_preview():
    """
    Preview-only Known Fighter Records Loader API.

    Accepts:
      in_memory_records: list of known fighter records (optional)
      local_seed_records: list of seed records (optional)

    Returns:
      JSON with sanitized known_records, source type, counts, and no-op write flags.

    GOVERNANCE:
      preview_only = True
      No profile creates, updates, merges, or database writes.
      Fails closed on malformed records.
    """
    load_known_records_readonly_preview = _lazy_global_fighter_known_records_readonly_loader()
    body = request.get_json(silent=True)
    if body is None:
        body = {}
    if not isinstance(body, dict):
        return jsonify({
            "ok": False,
            "error": "invalid_request_body",
            "preview_only": True,
            "profile_create_performed": False,
            "profile_update_performed": False,
            "merge_performed": False,
            "database_write_performed": False,
            "ranking_write_performed": False,
            "learning_apply_performed": False,
            "calibration_write_performed": False,
        }), 400


    # Extract and validate all six source-pack fields
    def _get_list_field(field):
        val = body.get(field)
        if val is not None and not isinstance(val, list):
            return None, f"{field}_must_be_list"
        return val, None

    in_memory_records, err1 = _get_list_field("in_memory_records")
    local_seed_records, err2 = _get_list_field("local_seed_records")
    manual_operator_records, err3 = _get_list_field("manual_operator_records")
    approved_historical_records, err4 = _get_list_field("approved_historical_records")
    report_history_records, err5 = _get_list_field("report_history_records")
    result_ledger_records, err6 = _get_list_field("result_ledger_records")
    global_read_projection_records, err7 = _get_list_field("global_read_projection_records")

    for err in [err1, err2, err3, err4, err5, err6, err7]:
        if err:
            return jsonify({
                "ok": False,
                "error": err,
                "preview_only": True,
                "profile_create_performed": False,
                "profile_update_performed": False,
                "merge_performed": False,
                "database_write_performed": False,
                "ranking_write_performed": False,
                "learning_apply_performed": False,
                "calibration_write_performed": False,
            }), 400

    # Call readonly loader with all possible fields
    try:
        result = load_known_records_readonly_preview(
            in_memory_records=in_memory_records,
            local_seed_records=local_seed_records,
            manual_operator_records=manual_operator_records,
            approved_historical_records=approved_historical_records,
            report_history_records=report_history_records,
            result_ledger_records=result_ledger_records,
            global_read_projection_records=global_read_projection_records,
        )
        response = {
            "ok": True,
            "known_records": result.known_records,
            "records_received_count": result.records_received_count,
            "records_accepted_count": result.records_accepted_count,
            "malformed_records_count": result.malformed_records_count,
            "source_type": result.source_type,
            "errors": result.errors or [],
            "preview_only": True,
            "profile_create_performed": False,
            "profile_update_performed": False,
            "merge_performed": False,
            "database_write_performed": False,
            "ranking_write_performed": False,
            "learning_apply_performed": False,
            "calibration_write_performed": False,
        }
        return jsonify(response)
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": "loader_failed",
            "detail": str(e),
            "preview_only": True,
            "profile_create_performed": False,
            "profile_update_performed": False,
            "merge_performed": False,
            "database_write_performed": False,
            "ranking_write_performed": False,
            "learning_apply_performed": False,
            "calibration_write_performed": False,
        }), 500


# ─── Phase 7 Controlled Delivery ──────────────────────────────────────────────

@app.route('/api/button2/controlled-delivery/preview', methods=['POST'])
def button2_controlled_delivery_preview_proxy():
    controlled_delivery_preview, _ = _lazy_controlled_delivery_handlers()
    return controlled_delivery_preview()


@app.route('/api/button2/controlled-delivery/action', methods=['POST'])
def button2_controlled_delivery_action_proxy():
    _, controlled_delivery_action = _lazy_controlled_delivery_handlers()
    return controlled_delivery_action()

if __name__ == "__main__":
    app.run(debug=True, port=5050)
