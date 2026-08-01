"""Single-write renderer for one governed fictional Button 2 PDF artifact."""

from __future__ import annotations

import copy
import hashlib
import html
from pathlib import Path
from typing import Any, Mapping

from operator_dashboard.button2_governed_internal_pdf_preflight_adapter_v1 import (
    INTERNAL_ARTIFACT_CLASSIFICATION,
)
from operator_dashboard.button2_pdf_render_gate_v1 import render_button2_pdf


def _blocked(reason: str) -> dict[str, Any]:
    return {
        "ok": False,
        "status": "blocked",
        "blocked_reason": reason,
        "pdf_generation_performed": False,
        "pdf_generation_count": 0,
        "customer_release_authorized": False,
        "queue_write_performed": False,
        "artifact_overwritten": False,
        "permanent_mutation_performed": False,
    }


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _internal_html(row: Mapping[str, Any], plan: Mapping[str, Any]) -> str:
    prediction = row["structured_prediction"]
    fields = {
        "fixture_id": plan["fixture_id"],
        "report_id": plan["report_id"],
        "report_version": plan["report_version"],
        "event": plan["event"]["name"],
        "fighter_a": plan["fighter_a"],
        "fighter_b": plan["fighter_b"],
        "predicted_winner": prediction.get("predicted_winner", ""),
        "predicted_method": prediction.get("predicted_method", ""),
        "predicted_round": prediction.get("predicted_round", ""),
        "prediction_schema": plan["prediction_schema_version"],
        "source_provenance": plan["source_provenance"],
        "report_provenance": plan["report_provenance"],
    }
    lines = "".join(f"<p><strong>{html.escape(key)}:</strong> {html.escape(str(value))}</p>" for key, value in fields.items())
    return f"""<!doctype html><html><head><meta charset='utf-8'><title>AI-RISA Internal Test Fixture</title>
<style>body{{font-family:Arial,sans-serif;margin:48px;color:#17202a}}h1{{color:#173b57}}.warning{{border:2px solid #b42318;padding:14px;font-weight:bold}}</style>
</head><body><h1>AI-RISA Premium Report Factory</h1><p>Advanced Intelligence: Ring Intelligence Systems Architecture</p>
<div class='warning'>INTERNAL TEST FIXTURE<br>NOT FOR CUSTOMER RELEASE</div>
<h2>Governed Internal Artifact</h2>{lines}
<p><strong>classification:</strong> {INTERNAL_ARTIFACT_CLASSIFICATION}</p>
<p><strong>preview-only:</strong> true</p><p><strong>customer release authorized:</strong> false</p>
</body></html>"""


def render_button2_governed_internal_pdf_v1(
    preflight_plan: Mapping[str, Any],
    report_row: Mapping[str, Any],
) -> dict[str, Any]:
    """Render exactly one preflight-approved fictional internal PDF."""
    if not isinstance(preflight_plan, Mapping) or preflight_plan.get("ok") is not True:
        return _blocked("preflight_required")
    if preflight_plan.get("preflight_only") is not True:
        return _blocked("preflight_only_required")
    if preflight_plan.get("artifact_classification") != INTERNAL_ARTIFACT_CLASSIFICATION:
        return _blocked("invalid_internal_artifact_classification")
    if not isinstance(report_row, Mapping):
        return _blocked("report_row_must_be_mapping")

    row = copy.deepcopy(dict(report_row))
    for key in ("fixture_id", "matchup_id", "report_id", "report_version"):
        if _text(row.get(key)) != _text(preflight_plan.get(key)):
            return _blocked("preflight_report_identity_mismatch")
    if preflight_plan.get("customer_ready_possible") is not False or preflight_plan.get("customer_release_authorized") is not False:
        return _blocked("customer_release_boundary_invalid")
    if preflight_plan.get("overwrite_allowed") is not False:
        return _blocked("overwrite_not_authorized")
    if not isinstance(row.get("structured_prediction"), Mapping):
        return _blocked("structured_prediction_missing")
    if not _text(preflight_plan.get("source_provenance")) or not _text(preflight_plan.get("report_provenance")):
        return _blocked("provenance_missing")

    output_path = Path(_text(preflight_plan.get("proposed_output_path"))).resolve()
    root = Path(_text(preflight_plan.get("proposed_output_directory"))).resolve()
    if not _text(preflight_plan.get("proposed_filename")) or output_path.name != preflight_plan["proposed_filename"]:
        return _blocked("preflight_output_path_mismatch")
    try:
        output_path.relative_to(root)
    except ValueError:
        return _blocked("output_path_escapes_preflight_root")
    if output_path.exists() or not root.is_dir():
        return _blocked("approved_target_missing_or_exists")

    try:
        render_result = render_button2_pdf(_internal_html(row, preflight_plan))
        pdf_bytes = render_result.get("pdf_bytes") if isinstance(render_result, Mapping) else None
        if not isinstance(pdf_bytes, bytes) or len(pdf_bytes) < 256 or not pdf_bytes.startswith(b"%PDF-"):
            return _blocked("renderer_returned_invalid_pdf")
        output_path.write_bytes(pdf_bytes)
        if not output_path.is_file():
            return _blocked("controlled_write_not_confirmed")
    except Exception:
        if output_path.exists():
            output_path.unlink()
        return _blocked("renderer_or_controlled_write_failed")

    digest = hashlib.sha256(pdf_bytes).hexdigest()
    return {
        "ok": True,
        "status": "generated_internal_test_pdf",
        "fixture_id": preflight_plan["fixture_id"], "matchup_id": preflight_plan["matchup_id"],
        "report_id": preflight_plan["report_id"], "report_version": preflight_plan["report_version"],
        "artifact_classification": INTERNAL_ARTIFACT_CLASSIFICATION,
        "internal_only": True, "test_fixture_only": True, "customer_ready_possible": False,
        "customer_release_authorized": False, "queue_write_performed": False,
        "pdf_generation_performed": True, "pdf_generation_count": 1,
        "output_directory_created": False, "artifact_overwritten": False,
        "permanent_mutation_performed": False, "controlled_artifact_write_performed": True,
        "output_path": str(output_path), "filename": output_path.name, "file_exists": True,
        "file_size_bytes": len(pdf_bytes), "sha256": digest,
        "pdf_signature_valid": True, "source_provenance": preflight_plan["source_provenance"],
        "report_provenance": preflight_plan["report_provenance"],
        "safety_flags": {"preview_only": True, "not_for_customer_release": True, "overwrite_allowed": False},
    }