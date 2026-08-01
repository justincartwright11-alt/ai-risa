"""Non-writing preflight contract for one governed internal Button 2 fixture."""

from __future__ import annotations

import copy
import os
import re
from pathlib import Path
from typing import Any, Mapping


INTERNAL_ARTIFACT_CLASSIFICATION = "governed_internal_test_pdf"
_SAFE_IDENTITY = re.compile(r"^[A-Za-z0-9_-]+$")
_PATH_SEPARATORS = ("/", "\\")


def _blocked(reason: str) -> dict[str, Any]:
    return {
        "ok": False,
        "status": "blocked",
        "preflight_only": True,
        "blocked_reason": reason,
        "pdf_generation_performed": False,
        "queue_write_performed": False,
        "customer_release_authorized": False,
        "permanent_mutation_performed": False,
    }


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _safe_identity(value: Any) -> str | None:
    text = _text(value)
    if not text or any(separator in text for separator in _PATH_SEPARATORS):
        return None
    if ".." in text:
        return None
    return text


def _safe_filename_identity(value: Any) -> str | None:
    text = _safe_identity(value)
    return text if text and _SAFE_IDENTITY.fullmatch(text) else None


def _root_path(value: Any) -> Path | None:
    try:
        text = os.fspath(value)
    except TypeError:
        text = ""
    text = _text(text)
    if not text or not os.path.isabs(text) or ".." in Path(text).parts:
        return None
    root = Path(text).expanduser().resolve()
    if root.exists() and not root.is_dir():
        return None
    return root


def _build_button2_governed_internal_pdf_plan_v1(
    report_row: Mapping[str, Any],
    approved_internal_output_root: str | os.PathLike[str],
    *,
    fixture_mode: bool,
    generation_timestamp: str | None = None,
    reject_existing_target: bool,
    status: str,
) -> dict[str, Any]:
    """Validate a governed fixture and propose, but never create, an internal PDF path."""
    if not fixture_mode:
        return _blocked("local_fixture_mode_required")
    if not isinstance(report_row, Mapping):
        return _blocked("report_row_must_be_mapping")

    row = copy.deepcopy(dict(report_row))
    if any(row.get(key) is not True for key in ("fixture_only", "internal_test_only", "read_only")):
        return _blocked("governed_fixture_metadata_invalid")
    if any(row.get(key) is not False for key in (
        "customer_ready_possible", "customer_release_authorized", "queue_write_performed",
        "pdf_generation_performed", "permanent_mutation_performed",
    )):
        return _blocked("governed_fixture_authority_flags_invalid")
    if row.get("overwrite_requested") is True:
        return _blocked("overwrite_not_authorized")

    identity_fields = ("fixture_id", "matchup_id", "fighter_a", "fighter_b", "report_id", "report_version")
    identities = {field: _safe_identity(row.get(field)) for field in identity_fields}
    if any(value is None for value in identities.values()):
        return _blocked("fixture_identity_incomplete_or_unsafe")
    if any(_safe_filename_identity(row.get(field)) is None for field in ("report_id", "report_version")):
        return _blocked("fixture_identity_incomplete_or_unsafe")
    if not all(_text(row.get(key)) for key in ("event_name", "event_date", "promotion")):
        return _blocked("event_metadata_incomplete")

    prediction = row.get("structured_prediction")
    schema_version = _text(row.get("prediction_schema_version"))
    if not isinstance(prediction, Mapping) or not schema_version:
        return _blocked("structured_prediction_contract_missing")
    if _text(prediction.get("contract_version")) != schema_version:
        return _blocked("structured_prediction_schema_mismatch")
    source_provenance = _text(row.get("source_provenance"))
    report_provenance = _text(row.get("prediction_provenance"))
    if not source_provenance or not report_provenance:
        return _blocked("provenance_missing")

    root = _root_path(approved_internal_output_root)
    if root is None:
        return _blocked("approved_internal_output_root_invalid")
    filename = f"{identities['report_id']}__{identities['report_version']}.pdf"
    proposed = (root / filename).resolve()
    try:
        proposed.relative_to(root)
    except ValueError:
        return _blocked("proposed_output_path_escapes_root")
    artifact_exists = proposed.exists()
    if reject_existing_target and artifact_exists:
        return _blocked("proposed_output_target_exists")
    if generation_timestamp is not None and not _text(generation_timestamp):
        return _blocked("generation_timestamp_invalid")

    return {
        "ok": True,
        "status": status,
        "preflight_only": True,
        "fixture_id": identities["fixture_id"], "matchup_id": identities["matchup_id"],
        "report_id": identities["report_id"], "report_version": identities["report_version"],
        "fighter_a": identities["fighter_a"], "fighter_b": identities["fighter_b"],
        "event": {"name": row["event_name"].strip(), "date": row["event_date"].strip(), "promotion": row["promotion"].strip()},
        "structured_prediction_present": True, "prediction_schema_version": schema_version,
        "source_provenance": source_provenance, "report_provenance": report_provenance,
        "artifact_classification": INTERNAL_ARTIFACT_CLASSIFICATION,
        "artifact_labels": ["INTERNAL TEST FIXTURE", "NOT FOR CUSTOMER RELEASE"],
        "internal_only": True, "test_fixture_only": True, "read_only_source": True,
        "customer_ready_possible": False, "customer_release_authorized": False,
        "queue_write_performed": False, "pdf_generation_performed": False,
        "output_directory_created": False, "artifact_overwritten": False,
        "permanent_mutation_performed": False,
        "proposed_output_directory": str(root), "proposed_filename": filename,
        "proposed_output_path": str(proposed), "overwrite_allowed": False,
        "artifact_exists_at_plan_time": artifact_exists,
        "validation_reasons": ["governed fixture validated", "output path proposed without filesystem mutation"],
    }


def build_button2_governed_internal_pdf_preflight_v1(
    report_row: Mapping[str, Any],
    approved_internal_output_root: str | os.PathLike[str],
    *,
    fixture_mode: bool,
    generation_timestamp: str | None = None,
) -> dict[str, Any]:
    """Validate a governed fixture and reject an existing generation target."""
    return _build_button2_governed_internal_pdf_plan_v1(
        report_row,
        approved_internal_output_root,
        fixture_mode=fixture_mode,
        generation_timestamp=generation_timestamp,
        reject_existing_target=True,
        status="preflight_valid",
    )


def build_button2_governed_internal_pdf_inspection_plan_v1(
    row: Mapping[str, Any],
    output_root: str | os.PathLike[str],
    *,
    fixture_mode: bool = False,
) -> dict[str, Any]:
    """Build a pure read-only inspection plan without collision authority."""
    plan = _build_button2_governed_internal_pdf_plan_v1(
        row,
        output_root,
        fixture_mode=fixture_mode,
        reject_existing_target=False,
        status="inspection_plan_ready",
    )
    if plan.get("ok") is True:
        plan.update(
            plan_purpose="governed_internal_pdf_read_only_inspection",
            artifact_archived=False,
            artifact_removed=False,
            artifact_overwritten=False,
        )
    return plan