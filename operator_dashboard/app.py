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

# Allow imports from workspace root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, jsonify

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
    return render_template("index.html")


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


# ─── Button 2 API ─────────────────────────────────────────────────────────────

@app.route("/api/operator/button2/generate-report", methods=["POST"])
def generate_report():
    """
    [OPERATOR GATE] Generate a premium PDF report.
    Requires explicit operator approval.
    """
    data = request.get_json(silent=True) or {}
    approved = data.get("operator_approved", False)
    if not approved:
        return jsonify({
            "ok": False,
            "error": "operator_approval_required",
            "message": "PDF generation must be approved by operator."
        }), 403
    return jsonify({"ok": True, "message": "gate_passed_no_fight_selected"})


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


if __name__ == "__main__":
    app.run(debug=True, port=5050)
