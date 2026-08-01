"""Read-only inspection for one governed internal Button 2 PDF target."""

from __future__ import annotations

import copy
import hashlib
import os
import stat
from io import BytesIO
from pathlib import Path
from typing import Any, Mapping

from pypdf import PdfReader

from operator_dashboard.button2_governed_internal_pdf_preflight_adapter_v1 import (
    INTERNAL_ARTIFACT_CLASSIFICATION,
)


_SAFETY_FLAGS = {
    "customer_ready_possible": False,
    "customer_release_authorized": False,
    "queue_write_performed": False,
    "pdf_generation_performed": False,
    "learning_applied": False,
    "calibration_applied": False,
    "accuracy_ledger_written": False,
    "gcid_written": False,
    "model_weights_changed": False,
    "fighter_ratings_changed": False,
    "prediction_logic_changed": False,
    "artifact_archived": False,
    "artifact_removed": False,
    "artifact_overwritten": False,
    "permanent_mutation_performed": False,
}


def _blocked(
    reason: str,
    *,
    artifact_exists: bool = False,
    inspection_performed: bool = False,
    **metadata: Any,
) -> dict[str, Any]:
    result = {
        "ok": False,
        "status": "blocked",
        "blocked_reason": reason,
        "artifact_exists": artifact_exists,
        "inspection_performed": inspection_performed,
        **_SAFETY_FLAGS,
    }
    result.update(metadata)
    return result


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _required_plan_values(plan: Mapping[str, Any]) -> tuple[Path, Path, Path, Path, str] | None:
    required = (
        "proposed_output_directory",
        "proposed_output_path",
        "proposed_filename",
        "fixture_id",
        "report_id",
        "report_version",
        "artifact_classification",
    )
    if any(not _text(plan.get(key)) for key in required):
        return None
    if plan.get("ok") is not True or plan.get("preflight_only") is not True:
        return None
    if plan.get("customer_ready_possible") is not False:
        return None
    if plan.get("customer_release_authorized") is not False:
        return None
    if plan.get("overwrite_allowed") is not False:
        return None
    if plan.get("pdf_generation_performed") is not False:
        return None
    if plan.get("artifact_classification") != INTERNAL_ARTIFACT_CLASSIFICATION:
        return None

    root_text = _text(plan["proposed_output_directory"])
    target_text = _text(plan["proposed_output_path"])
    if not os.path.isabs(root_text) or not os.path.isabs(target_text):
        return None
    if any(part == ".." for part in Path(root_text).parts + Path(target_text).parts):
        return None
    root_input = Path(root_text)
    target_input = Path(target_text)
    root = root_input.resolve(strict=False)
    target = target_input.resolve(strict=False)
    if target == root:
        return None
    return root_input, root, target_input, target, _text(plan["proposed_filename"])


def _has_reparse_or_link(path: Path) -> bool:
    try:
        current = path
        while True:
            info = os.lstat(current)
            if stat.S_ISLNK(info.st_mode):
                return True
            attributes = getattr(info, "st_file_attributes", 0)
            if attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400):
                return True
            if current.parent == current:
                return False
            current = current.parent
    except (OSError, ValueError):
        return False


def _expected_row_matches_plan(expected_row: Mapping[str, Any], plan: Mapping[str, Any]) -> bool:
    for key in ("fixture_id", "report_id", "report_version", "fighter_a", "fighter_b"):
        if _text(expected_row.get(key)) != _text(plan.get(key)):
            return False
    if any(expected_row.get(key) is not True for key in ("fixture_only", "internal_test_only", "read_only")):
        return False
    if expected_row.get("customer_ready_possible") is not False or expected_row.get("customer_release_authorized") is not False:
        return False
    return bool(_text(expected_row.get("source_provenance")) and _text(expected_row.get("prediction_provenance")))


def _text_validation(text: str, plan: Mapping[str, Any]) -> tuple[str | None, dict[str, bool]]:
    checks = {
        "internal_warning_present": "INTERNAL TEST FIXTURE" in text,
        "release_warning_present": "NOT FOR CUSTOMER RELEASE" in text,
        "ai_risa_present": "AI-RISA" in text,
        "fixture_identity_present": _text(plan["fixture_id"]) in text,
        "report_id_present": _text(plan["report_id"]) in text,
        "report_version_present": _text(plan["report_version"]) in text,
        "fighter_a_present": _text(plan.get("fighter_a")) in text,
        "fighter_b_present": _text(plan.get("fighter_b")) in text,
        "classification_present": INTERNAL_ARTIFACT_CLASSIFICATION in text,
    }
    if not checks["internal_warning_present"] or not checks["release_warning_present"]:
        return "internal_warning_missing", checks
    forbidden_claims = (
        "customer ready: true",
        "customer-ready: true",
        "customer release authorized: true",
        "customer-release: true",
        "customer released",
        "production approved",
        "official commercial report",
    )
    if any(claim in text.lower() for claim in forbidden_claims):
        return "forbidden_release_claim_present", checks
    if not all(checks.values()):
        return "artifact_identity_mismatch", checks
    return None, checks


def inspect_button2_governed_internal_pdf_artifact_v1(
    preflight_plan: Mapping[str, Any],
    expected_row: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Inspect only the deterministic target from an approved preflight plan."""
    if not isinstance(preflight_plan, Mapping):
        return _blocked("invalid_preflight_plan")
    values = _required_plan_values(preflight_plan)
    if values is None:
        return _blocked("invalid_preflight_plan")
    root_input, root, target_input, target, filename = values
    if expected_row is not None:
        if not isinstance(expected_row, Mapping) or not _expected_row_matches_plan(expected_row, preflight_plan):
            return _blocked("artifact_identity_mismatch", inspection_performed=False)

    try:
        if _has_reparse_or_link(root_input) or _has_reparse_or_link(target_input):
            return _blocked("target_link_or_reparse_point_rejected", inspection_performed=True)
        if target.name != filename:
            return _blocked("target_filename_mismatch", inspection_performed=True)
        target.relative_to(root)
    except ValueError:
        return _blocked("target_outside_approved_root", inspection_performed=True)
    except OSError:
        return _blocked("target_link_or_reparse_point_rejected", inspection_performed=True)

    try:
        target_stat = os.lstat(target)
    except FileNotFoundError:
        return {
            "ok": True,
            "status": "absent",
            "artifact_exists": False,
            "artifact_state": "ABSENT",
            "inspection_performed": True,
            "expected_filename": filename,
            "fixture_id": preflight_plan["fixture_id"],
            "report_id": preflight_plan["report_id"],
            "report_version": preflight_plan["report_version"],
            "artifact_classification": INTERNAL_ARTIFACT_CLASSIFICATION,
            **_SAFETY_FLAGS,
        }
    except OSError:
        return _blocked("target_outside_approved_root", inspection_performed=True)

    if not stat.S_ISREG(target_stat.st_mode):
        return _blocked("target_is_not_regular_file", artifact_exists=True, inspection_performed=True)
    try:
        content = target.read_bytes()
    except OSError:
        return _blocked("pdf_parse_failed", artifact_exists=True, inspection_performed=True)
    if not content.startswith(b"%PDF-"):
        return _blocked("pdf_signature_invalid", artifact_exists=True, inspection_performed=True)
    if len(content) == 0:
        return _blocked("pdf_page_count_invalid", artifact_exists=True, inspection_performed=True)
    try:
        reader = PdfReader(BytesIO(content))
        page_count = len(reader.pages)
        if page_count < 1:
            return _blocked("pdf_page_count_invalid", artifact_exists=True, inspection_performed=True)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        return _blocked("pdf_parse_failed", artifact_exists=True, inspection_performed=True)

    text_reason, text_checks = _text_validation(text, preflight_plan)
    if text_reason:
        return _blocked(
            text_reason,
            artifact_exists=True,
            inspection_performed=True,
            text_validation=text_checks,
        )
    return {
        "ok": True,
        "status": "present_valid",
        "artifact_exists": True,
        "artifact_state": "ACTIVE_INTERNAL_TEST_ARTIFACT",
        "inspection_performed": True,
        "regular_file": True,
        "path_contained": True,
        "filename_matches": True,
        "pdf_signature_valid": True,
        "file_size_bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
        "page_count": page_count,
        "fixture_id": preflight_plan["fixture_id"],
        "report_id": preflight_plan["report_id"],
        "report_version": preflight_plan["report_version"],
        "artifact_classification": INTERNAL_ARTIFACT_CLASSIFICATION,
        "internal_only": True,
        "test_fixture_only": True,
        "customer_ready_possible": False,
        "customer_release_authorized": False,
        "text_validation": text_checks,
        **_SAFETY_FLAGS,
    }