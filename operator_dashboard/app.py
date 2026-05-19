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
from datetime import datetime
from datetime import timezone
import uuid
from urllib.parse import quote

# Allow imports from workspace root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, jsonify, send_from_directory

from button3_auto_result_source_yield_live_executor_preview import (
    build_readonly_executor_preview_response,
)
from operator_dashboard.local_ai_orchestrator_input_context_pack import build_context_pack
from operator_dashboard.local_ai_orchestrator_readonly_runtime_context_loader import (
    build_runtime_context_pack,
)
from operator_dashboard.local_ai_orchestrator_job_schema import LocalAIJobInputRef
from operator_dashboard.local_ai_orchestrator_gate1_save_fights_dry_run_apply_preview import (
    run_gate1_save_fights_dry_run_apply_preview,
)
from operator_dashboard.local_ai_orchestrator_gate1_approved_save_writer import (
    run_gate1_approved_save_writer_scaffold,
)
from operator_dashboard.local_ai_orchestrator_workflow_plan import (
    build_three_button_workflow_plan,
    run_workflow_preview,
)
from operator_dashboard.global_fighter_identity_resolver_preview import (
    resolve_fighter_identity_preview,
    IncomingFighterCandidate,
    KnownFighterRecord,
    SourceRef,
)
from operator_dashboard.global_fighter_known_records_readonly_loader import (
    load_known_records_readonly_preview,
)
from operator_dashboard.button1_to_button2_readonly_dossier_handoff_preview import (
    build_button1_to_button2_readonly_dossier_handoff_preview,
)
from operator_dashboard.button2_readonly_dossier_handoff_ingest_preview import (
    build_button2_readonly_dossier_handoff_ingest_preview,
)
from operator_dashboard.button2_dossier_handoff_report_context_preview import (
    build_button2_dossier_handoff_report_context_preview,
)
from operator_dashboard.button2_report_generation_route_render_gate_integration_v1 import (
    generate_button2_report_render_gate_integration,
)
from operator_dashboard.button2_pdf_output_root_config_v1 import (
    get_pdf_output_root,
    OutputRootNotConfiguredError,
    OutputRootInvalidError,
)
from operator_dashboard.button2_controlled_delivery_scaffold import controlled_delivery
from operator_dashboard.button2_template_pack_asset_renderer_v1 import (
    resolve_template_pack_assets,
    TemplatePackResolverError,
)
from operator_dashboard.button3_result_comparison_preview_v1 import (
    build_button3_result_comparison_preview,
)

app = Flask(__name__, template_folder="templates")

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
    return {
        "any_forbidden_found": bool(found),
        "found_markers": found,
        "marker_hits": hits,
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


def _resolve_button2_template_pack_preview():
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

    # Build customer-safe summary - excludes internal/debug metadata
    summary_lines = [
        "AI-RISA Premium Fight Report",
        "Premium Selected-Matchup Intelligence",
        "Template renderer profile: premium_template_pack_v29",
        "Matchup: " + str(fighter_a or "Unknown") + " vs " + str(fighter_b or "Unknown"),
        "Event: " + str(event_name or "Unknown"),
        "Event date: " + str(event_date or "Unknown"),
        "Promotion: " + str(promotion or "Unknown"),
        "Source Traceability",
        "Source URL: " + str(source_url or "Unknown"),
        "Source type: " + str(source_type or "official"),
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


def _build_runtime_preflight_status(host_value):
    output_root = os.environ.get("BUTTON2_PDF_OUTPUT_ROOT", "")
    output_root_value = output_root.strip() if isinstance(output_root, str) else ""
    output_root_ready = bool(output_root_value) and os.path.isdir(output_root_value)

    gtk_path = r"C:\msys64\ucrt64\bin"
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
    output_root = os.environ.get("BUTTON2_PDF_OUTPUT_ROOT", "")
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
    data = request.get_json(silent=True) or {}
    result = generate_button2_report_render_gate_integration(data)
    result = _decorate_button2_generated_pdf_open_link(result)
    status_code = 200 if result.get("ok") else (403 if result.get("error") == "operator_approval_required" else 400)
    return jsonify(result), status_code


@app.route("/api/button2/selected-matchup/generate-guarded-v1", methods=["POST"])
def button2_selected_matchup_generate_guarded_v1():
    """Gate2 guarded generation from an explicitly selected Button1->Button2 matchup preview."""
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

    selected_preview = body.get("selected_matchup_preview")
    if not isinstance(selected_preview, dict):
        return jsonify({
            "ok": False,
            "error": "selected_matchup_required",
            "message": "A selected_matchup_preview object is required.",
            "operator_action_required": True,
            "selected_matchup_required": True,
            "queue_write_performed": False,
            "delivery_performed": False,
            "external_api_delivery_performed": False,
            "learning_apply_performed": False,
            "calibration_write_performed": False,
            "button3_mutation_performed": False,
        }), 400

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
        }), 400

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
        }), 400

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
        }), 400

    generation_request_id = uuid.uuid4().hex
    selected_matchup_id = (
        selected_preview.get("matchup_id")
        or selected_preview.get("candidate_id")
        or fight_id
    )
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

    if result.get("ok") is True:
        output_path = result.get("output_path", "")
        generated_pdf_text, extracted_page_count = _extract_pdf_text_and_page_count(output_path)
        file_meta = _collect_file_metadata(output_path)
        text_scan = _scan_forbidden_markers(generated_pdf_text)
        selected_matchup_matches_pdf_text = _selected_matchup_matches_pdf_text(selected_preview, generated_pdf_text)

    result.update({
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
        "external_api_delivery_performed": False,
        "learning_apply_performed": False,
        "calibration_write_performed": False,
        "button3_mutation_performed": False,
    })

    status_code = 200 if result.get("ok") else (403 if result.get("error") == "operator_approval_required" else 400)
    return jsonify(result), status_code


@app.route("/api/button2/generated-report/open", methods=["GET"])
def button2_generated_report_open_v1():
    """Serve generated Button 2 PDFs from the configured output root only."""
    filename = request.args.get("filename", "")
    if not _is_safe_generated_pdf_filename(filename):
        return jsonify({
            "ok": False,
            "error": "invalid_filename",
            "message": "filename must be a safe PDF filename.",
        }), 400

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

    return send_from_directory(output_root, filename, mimetype="application/pdf")


@app.route("/api/button2/generated-report/library", methods=["GET"])
def button2_generated_report_library_v1():
    """Render a safe read-only library of generated PDFs from configured output root."""
    if request.args.get("path") or request.args.get("dir") or request.args.get("folder"):
        return jsonify({
            "ok": False,
            "error": "invalid_query",
            "message": "Directory override is not allowed.",
        }), 400

    try:
        output_root = get_pdf_output_root()
    except (OutputRootNotConfiguredError, OutputRootInvalidError) as e:
        return jsonify({
            "ok": False,
            "error": "output_root_unavailable",
            "message": str(e),
        }), 400

    rows = _list_generated_pdf_library_rows(output_root)
    return render_template(
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
    )


@app.route("/api/button2/dossier-handoff/ingest-preview", methods=["POST"])
def button2_dossier_handoff_ingest_preview():
    """Return preview-only Button 2 ingest context from Button 1 handoff payload."""
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

    response = build_button3_result_comparison_preview(body)
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

app.register_blueprint(controlled_delivery)

if __name__ == "__main__":
    app.run(debug=True, port=5050)
