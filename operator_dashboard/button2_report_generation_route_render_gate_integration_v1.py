"""
Button 2 Report Generation Route Integration (v1)
--------------------------------------------------
Integrates the operator-approved PDF generation route:
  1. Gate 2 operator approval guard (non-negotiable)
  2. Fight key validation
  3. Report composition entry point
  4. Guarded render gate
  5. Server-controlled output path resolution
  6. PDF file write

GOVERNANCE:
  - Operator approval required first
  - Fight selection validated
  - HTML from composition pipeline only
  - Output path server-derived only
  - No file write on failed composition/render/path resolution
  - Visual QA disabled by default
"""

import os

from operator_dashboard.button2_readonly_dossier_handoff_ingest_preview import (
    build_button2_readonly_dossier_handoff_ingest_preview,
)
from operator_dashboard.button2_dossier_handoff_report_context_preview import (
    build_button2_dossier_handoff_report_context_preview,
)
from operator_dashboard.button2_html_composition_entry_point_v1 import (
    build_button2_report_html,
)
from operator_dashboard.button2_pdf_render_gate_v1 import render_button2_pdf
from operator_dashboard.button2_pdf_output_root_config_v1 import (
    resolve_pdf_output_path,
    OutputRootNotConfiguredError,
    OutputRootInvalidError,
    FightKeyInvalidError,
    PathTraversalError,
)
from operator_dashboard.button2_visual_intelligence_overlap_offpage_proof_instrumentation_v1 import (
    run_geometry_proof,
)


def _base_telemetry():
    """Base telemetry flags for all routes."""
    return {
        "preview_only": False,
        "gate2_approval_required": True,
        "gate2_bypass_performed": False,
        "pdf_generation_performed": False,
        "file_write_performed": False,
        "export_performed": False,
        "delivery_performed": False,
        "report_write_performed": False,
        "visual_qa_enabled": False,
        "visual_qa_operator_approval": False,
        "profile_create_update_merge": False,
        "database_ranking_writes": False,
        "result_report_learning_calibration": False,
    }


def generate_button2_report_render_gate_integration(request_data):
    """
    Operator-approved Button 2 PDF generation flow.

    This is the core implementation of /api/operator/button2/generate-report,
    integrated behind the approval gate.

    Parameters
    ----------
    request_data : dict
        POST request body containing:
          - operator_approved : bool (required, must be True)
          - fight_id : str (required, e.g. "bahram_rajabzadeh_vs_donovan_wisse")
          - ingest_payload : dict (required, handoff context from Button 1)

    Returns
    -------
    dict
        Response with keys:
          ok : bool
          error : str (if ok=False)
          message : str (if ok=True)
          output_path : str (if file written successfully)
          qa_summary : dict or None (if visual QA enabled)
          ... (telemetry flags)
    """
    telemetry = _base_telemetry()

    # Handle None request_data
    if request_data is None or not isinstance(request_data, dict):
        return {
            "ok": False,
            "error": "invalid_request_data",
            "message": "Request data must be a dict.",
            **telemetry,
        }

    # ─── Gate 2: Operator Approval (Non-Negotiable, First Check) ──────────────
    approved = request_data.get("operator_approved", False)
    if not approved:
        return {
            "ok": False,
            "error": "operator_approval_required",
            "message": "PDF generation requires explicit operator approval.",
            **telemetry,
        }

    # ─── Fight Selection: Required and Validated ──────────────────────────────
    fight_id = request_data.get("fight_id")
    if not fight_id or not isinstance(fight_id, str):
        return {
            "ok": False,
            "error": "fight_id_required",
            "message": "fight_id must be a non-empty string.",
            **telemetry,
        }

    # ─── Ingest Payload: Required ─────────────────────────────────────────────
    ingest_payload = request_data.get("ingest_payload")
    if not ingest_payload or not isinstance(ingest_payload, dict):
        return {
            "ok": False,
            "error": "ingest_payload_required",
            "message": "ingest_payload must be a non-empty dict.",
            **telemetry,
        }

    # ─── Report Composition: Build Report Context ─────────────────────────────
    try:
        ingest_result = build_button2_readonly_dossier_handoff_ingest_preview(ingest_payload)
    except Exception as e:
        return {
            "ok": False,
            "error": "ingest_composition_exception",
            "message": f"Ingest composition failed: {str(e)}",
            **telemetry,
        }
    if not ingest_result.get("ok"):
        return {
            "ok": False,
            "error": "ingest_context_invalid",
            "message": f"Failed to build ingest context: {ingest_result.get('error', 'unknown')}",
            **telemetry,
        }

    # Extract ingest context from result
    ingest_context = ingest_result.get("button2_ingest_preview_context")
    if not ingest_context or not isinstance(ingest_context, dict):
        return {
            "ok": False,
            "error": "ingest_context_invalid",
            "message": "Ingest context is missing or malformed.",
            **telemetry,
        }

    # Build report context
    try:
        context_result = build_button2_dossier_handoff_report_context_preview({"button2_ingest_preview_context": ingest_context})
    except Exception as e:
        return {
            "ok": False,
            "error": "report_context_composition_exception",
            "message": f"Report context composition failed: {str(e)}",
            **telemetry,
        }
    if not context_result.get("ok"):
        return {
            "ok": False,
            "error": "report_context_invalid",
            "message": f"Failed to build report context: {context_result.get('error', 'unknown')}",
            **telemetry,
        }

    report_context_preview = context_result.get("report_context_preview")
    if not report_context_preview or not isinstance(report_context_preview, dict):
        return {
            "ok": False,
            "error": "report_context_invalid",
            "message": "Report context is missing or malformed.",
            **telemetry,
        }

    # ─── HTML Composition: Build Safe HTML Input ──────────────────────────────
    try:
        html_result = build_button2_report_html(report_context_preview)
    except Exception as e:
        return {
            "ok": False,
            "error": "html_composition_exception",
            "message": f"HTML composition failed: {str(e)}",
            **telemetry,
        }
    if not html_result.get("ok"):
        return {
            "ok": False,
            "error": "html_composition_failed",
            "message": f"Failed to build HTML: {html_result.get('error', 'unknown')}",
            **telemetry,
        }

    html_content = html_result.get("html_content")
    if not html_content or not isinstance(html_content, str):
        return {
            "ok": False,
            "error": "html_composition_failed",
            "message": "HTML content is missing or malformed.",
            **telemetry,
        }

    # ─── Render Gate: Call Guarded PDF Renderer ──────────────────────────────
    try:
        render_result = render_button2_pdf(html_content)
        pdf_bytes = render_result.get("pdf_bytes")
        geometry_data = render_result.get("geometry_data")
        if not pdf_bytes or not isinstance(pdf_bytes, bytes):
            return {
                "ok": False,
                "error": "pdf_render_failed",
                "message": "PDF render returned no content.",
                **telemetry,
            }
    except Exception as e:
        return {
            "ok": False,
            "error": "pdf_render_exception",
            "message": f"PDF render failed: {str(e)}",
            **telemetry,
        }

    # Mark PDF generation
    telemetry["pdf_generation_performed"] = True

    # ─── Output Path Resolution: Server-Controlled Only ──────────────────────
    try:
        output_path = resolve_pdf_output_path(fight_id)
    except (OutputRootNotConfiguredError, OutputRootInvalidError, FightKeyInvalidError, PathTraversalError) as e:
        return {
            "ok": False,
            "error": "output_path_invalid",
            "message": f"Failed to resolve output path: {str(e)}",
            **telemetry,
        }

    # ─── File Write: No Write Without Approval + Composition + Render + Path ─
    output_dir = os.path.dirname(output_path)
    try:
        # Ensure output directory exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # Write PDF file
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)
    except Exception as e:
        return {
            "ok": False,
            "error": "file_write_failed",
            "message": f"Failed to write PDF file: {str(e)}",
            **telemetry,
        }

    # Mark file write
    telemetry["file_write_performed"] = True

    # ─── Visual QA Results: Side-Channel Only, Preview Mode ──────────────────
    qa_summary = None
    visual_qa_enabled = os.environ.get("BUTTON2_VISUAL_QA", "0").strip() == "1"
    telemetry["visual_qa_enabled"] = visual_qa_enabled

    if geometry_data is not None and visual_qa_enabled:
        try:
            proof = run_geometry_proof(geometry_data)
            qa_summary = {
                "overlap_proof": proof.get("overlap_proof"),
                "off_page_text_proof": proof.get("off_page_text_proof"),
                "visual_certification_status": proof.get("visual_certification_status"),
            }
        except Exception:
            # QA is best-effort; do not fail the entire report generation
            pass

    return {
        "ok": True,
        "message": "PDF generated and saved successfully.",
        "output_path": output_path,
        "qa_summary": qa_summary,
        **telemetry,
    }
