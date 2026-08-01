"""Read-only Button 2 destination inspection at the private capability boundary."""

from __future__ import annotations

import hashlib
import os
import re
import stat
import sys
from pathlib import Path
from typing import Any, Mapping

COMPOSITE_VERSION = "button2-governed-internal-pdf-archive-destination-private-inspection-capability-v1"
ROOT_VERSION = "button2-governed-internal-pdf-archive-root-private-capability-v1"
FILESYSTEM_VERSION = "button2-governed-internal-pdf-archive-destination-filesystem-object-inspection-capability-v1"
IDENTITY_VERSION = "button2-governed-internal-pdf-windows-file-identity-v1"
PARSER_CAPABILITY_VERSION = "button2-governed-internal-pdf-archive-destination-parser-result-capability-v1"
REQUEST_VERSION = "button2-governed-internal-pdf-archive-destination-parser-request-v1"
RESULT_VERSION = "button2-governed-internal-pdf-archive-destination-parser-result-v1"
METADATA_VERSION = "button2-governed-internal-pdf-archive-destination-trusted-metadata-v1"
RESOURCE_POLICY = "button2-governed-internal-pdf-archive-destination-resource-policy-v1"
DESTINATION_VERSION = "button2-governed-internal-pdf-destination-evidence-v1"

MAX_FILE_SIZE = 104857600
SIGNATURE_BYTES = 1024
HASH_CHUNK = 1048576
MAX_PAGES = 10000
PARSER_TIMEOUT = 10
PARSER_MEMORY = 268435456

REQUEST_FIELDS = frozenset({
    "contract_version", "requested_action", "fixture_id", "report_id", "report_version",
    "expected_filename", "expected_sha256", "expected_file_size_bytes", "expected_page_count",
    "source_boundary_id", "archive_root_id", "archive_root_version", "archive_policy_id",
    "archive_boundary_id", "destination_relative_id", "request_id", "idempotency_key",
})
SOURCE_FIELDS = frozenset({
    "inspection_contract_version", "inspection_completed", "artifact_state", "fixture_id",
    "report_id", "report_version", "expected_filename", "observed_filename", "sha256",
    "file_size_bytes", "page_count", "pdf_signature_valid", "pdf_parse_valid", "identity_valid",
    "classification_valid", "internal_warning_valid", "source_boundary_id", "source_identity",
    "source_artifact_version_token", "customer_ready_possible", "customer_release_authorized",
    "queue_write_performed", "pdf_generation_performed", "artifact_archived", "artifact_removed",
    "artifact_overwritten", "permanent_mutation_performed", "action_performed",
})
SOURCE_REQUIRED_FIELDS = SOURCE_FIELDS
CAPABILITY_FIELDS = frozenset({
    "capability_contract_version", "capability_id", "archive_root_id", "archive_root_version",
    "archive_policy_id", "archive_boundary_id", "platform", "filesystem_policy_id",
    "sanitization_policy_id", "configured", "enabled", "server_controlled", "customer_isolated",
    "source_isolated", "action_performed", "internal_test_only", "fixture_only", "production_capable",
    "capability_source_id", "capability_source_version", "expiry_or_validity_evidence",
    "root_configuration_fingerprint", "root_identity", "root_target", "root_observer",
    "filesystem_observer", "identity_observer", "parser_capability", "safety_flags",
})
CAPABILITY_REQUIRED_FIELDS = CAPABILITY_FIELDS
PARSER_CAPABILITY_FIELDS = frozenset({
    "capability_contract_version", "capability_source_id", "capability_source_version",
    "enabled", "supported", "internal_test_only", "fixture_only", "production_capable",
    "action_performed", "parser", "trusted_metadata", "resource_policy_id", "safety_flags",
})
PARSER_RESULT_FIELDS = frozenset({
    "contract_version", "ok", "status", "inspection_completed", "parser_source_id",
    "parser_source_version", "parser_policy_id", "resource_policy_id", "fixture_id",
    "report_id", "report_version", "expected_filename", "destination_relative_id",
    "destination_identity_version_token", "pdf_signature_valid", "pdf_parse_valid",
    "observed_page_count", "encrypted_or_protected", "embedded_files_detected",
    "javascript_detected", "external_resource_request_detected", "rendering_performed",
    "network_access_performed", "filesystem_write_performed", "process_isolation_claimed",
    "timeout_enforced", "memory_limit_enforced", "timeout_occurred", "memory_limit_exceeded",
    "resource_limit_exceeded", "blocked_reason", "evidence_version_token", "evaluated_at",
    "request_id", "idempotency_key", "action_performed", "safety_flags",
})
METADATA_FIELDS = frozenset({
    "contract_version", "evidence_completed", "metadata_source_type", "metadata_source_id",
    "metadata_source_version", "metadata_integrity_token", "fixture_id", "report_id",
    "report_version", "filename", "sha256", "file_size_bytes", "page_count", "classification",
    "internal_warning", "provenance_source_type", "provenance_source_id", "provenance_verified",
    "provenance_fixture_bound", "archive_root_id", "archive_root_version", "archive_policy_id",
    "archive_boundary_id", "destination_relative_id", "destination_evidence_version_token",
    "evaluated_at", "request_id", "idempotency_key", "action_performed",
})
SAFETY_FLAGS = (
    "customer_ready_possible", "customer_release_authorized", "queue_write_performed",
    "pdf_generation_performed", "learning_applied", "calibration_applied",
    "accuracy_ledger_written", "gcid_written", "model_weights_changed", "fighter_ratings_changed",
    "prediction_logic_changed", "artifact_archived", "artifact_removed", "artifact_overwritten",
    "permanent_mutation_performed", "action_performed",
)
STATUSES = frozenset({
    "DESTINATION_INSPECTION_COMPLETE", "DESTINATION_INSPECTION_BLOCKED",
    "DESTINATION_INSPECTION_UNAVAILABLE", "DESTINATION_INSPECTION_UNSUPPORTED_PLATFORM",
})
CLASSIFICATIONS = frozenset({
    "DESTINATION_ABSENT", "IDENTICAL_ARCHIVE_PRESENT", "CONFLICTING_ARCHIVE_PRESENT",
    "DESTINATION_NON_REGULAR", "DESTINATION_LINK_OR_REPARSE", "DESTINATION_DIRECTORY_COLLISION",
    "DESTINATION_OUTSIDE_APPROVED_ROOT", "SOURCE_DESTINATION_SAME", "IDENTITY_NORMALIZATION_COLLISION",
})
REASONS = frozenset({
    "invalid_destination_inspection_contract", "unexpected_destination_inspection_fields",
    "unsupported_contract_version", "source_artifact_evidence_invalid", "source_artifact_state_not_eligible",
    "source_artifact_identity_mismatch", "archive_root_missing", "archive_root_disabled", "archive_root_invalid",
    "archive_root_not_directory", "archive_root_link_or_reparse", "archive_root_identity_mismatch",
    "archive_policy_mismatch", "archive_boundary_mismatch", "unsupported_platform", "invalid_destination_relative_id",
    "invalid_path_component", "reserved_path_component", "non_ascii_path_component", "path_component_too_long",
    "relative_identifier_too_long", "identity_normalization_collision", "destination_outside_approved_root",
    "parent_missing", "parent_non_directory", "parent_link_or_reparse", "parent_access_denied",
    "parent_inspection_failed", "destination_link_or_reparse", "destination_non_regular",
    "destination_directory_collision", "destination_access_denied", "destination_inspection_failed",
    "source_destination_same", "source_destination_identity_unavailable", "destination_identity_mismatch",
    "pdf_signature_validation_failed", "pdf_parse_validation_failed", "sha256_mismatch", "file_size_mismatch",
    "page_count_mismatch", "classification_evidence_missing", "classification_mismatch", "warning_evidence_missing",
    "warning_mismatch", "trusted_metadata_invalid", "trusted_metadata_stale", "trusted_metadata_identity_mismatch",
    "trusted_metadata_integrity_invalid", "trusted_metadata_request_mismatch", "trusted_metadata_idempotency_mismatch",
    "provenance_evidence_missing", "provenance_invalid", "provenance_fixture_binding_failed", "resource_limit_exceeded",
    "invalid_parser_request_contract", "unexpected_parser_request_fields", "unsupported_parser_request_version",
    "invalid_parser_result_contract", "unexpected_parser_result_fields", "unsupported_parser_result_version",
    "parser_capability_missing", "parser_capability_disabled", "parser_capability_unsupported",
    "parser_capability_invalid", "parser_result_missing", "parser_result_invalid", "parser_result_stale",
    "parser_result_identity_mismatch", "parser_result_request_mismatch", "parser_result_idempotency_mismatch",
    "parser_result_target_mismatch", "parser_timeout", "parser_memory_limit_exceeded", "encrypted_pdf_unsupported",
    "embedded_content_unsupported", "javascript_detected", "external_resource_request_blocked",
    "parser_isolation_not_enforced", "parser_network_access_detected", "parser_filesystem_write_detected",
    "parser_rendering_detected", "parser_internal_failure",
})

_HEX = re.compile(r"^[0-9a-f]{64}$")
_RESERVED = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}


def _flags() -> dict[str, bool]:
    return {name: False for name in SAFETY_FLAGS}


def _strict_false_flags(value: Any) -> bool:
    return isinstance(value, Mapping) and set(value) == set(SAFETY_FLAGS) and all(item is False for item in value.values())


def _identity_valid(value: Any) -> bool:
    return isinstance(value, Mapping) and value.get("identity_completed") is True and value.get("identity_supported") is True and isinstance(value.get("volume_identifier"), str) and isinstance(value.get("file_identifier"), str)


def _source_valid(source: Any) -> bool:
    if not isinstance(source, Mapping) or set(source) != SOURCE_REQUIRED_FIELDS:
        return False
    if source.get("inspection_contract_version") != "button2-governed-internal-pdf-artifact-inspection-v1":
        return False
    if source.get("inspection_completed") is not True or source.get("artifact_state") != "ACTIVE_INTERNAL_TEST_ARTIFACT":
        return False
    if not _HEX.fullmatch(source.get("sha256", "")) or type(source.get("file_size_bytes")) is not int or source["file_size_bytes"] < 0 or type(source.get("page_count")) is not int or not 1 <= source["page_count"] <= MAX_PAGES:
        return False
    if not all(source.get(key) is True for key in ("pdf_signature_valid", "pdf_parse_valid", "identity_valid", "classification_valid", "internal_warning_valid")):
        return False
    if not all(source.get(key) is False for key in ("customer_ready_possible", "customer_release_authorized", "queue_write_performed", "pdf_generation_performed", "artifact_archived", "artifact_removed", "artifact_overwritten", "permanent_mutation_performed", "action_performed")):
        return False
    return _identity_valid(source.get("source_identity"))


def _capability_valid(capability: Any) -> bool:
    if not isinstance(capability, Mapping) or set(capability) != CAPABILITY_REQUIRED_FIELDS:
        return False
    if capability.get("capability_contract_version") != COMPOSITE_VERSION:
        return False
    if not all(capability.get(key) is True for key in ("configured", "enabled", "server_controlled", "customer_isolated", "source_isolated", "internal_test_only", "fixture_only")):
        return False
    if capability.get("production_capable") is not False or capability.get("action_performed") is not False:
        return False
    if not _strict_false_flags(capability.get("safety_flags")) or not _identity_valid(capability.get("root_identity")):
        return False
    if not isinstance(capability.get("root_target"), (str, os.PathLike)):
        return False
    return all(callable(capability.get(key)) for key in ("root_observer", "filesystem_observer", "identity_observer"))


def _parser_capability_valid(value: Any) -> bool:
    return isinstance(value, Mapping) and set(value) == PARSER_CAPABILITY_FIELDS and value.get("capability_contract_version") == PARSER_CAPABILITY_VERSION and value.get("enabled") is True and value.get("supported") is True and value.get("internal_test_only") is True and value.get("fixture_only") is True and value.get("production_capable") is False and value.get("action_performed") is False and callable(value.get("parser")) and isinstance(value.get("trusted_metadata"), Mapping) and value.get("resource_policy_id") == RESOURCE_POLICY and _strict_false_flags(value.get("safety_flags"))


def _metadata_schema_valid(value: Any) -> bool:
    return isinstance(value, Mapping) and set(value) == METADATA_FIELDS and value.get("contract_version") == METADATA_VERSION and value.get("evidence_completed") is True and value.get("action_performed") is False and value.get("metadata_source_type") in {"governed_internal_fixture_metadata", "server_controlled_immutable_sidecar_metadata", "previously_verified_archive_metadata_record"} and isinstance(value.get("metadata_integrity_token"), str) and bool(value["metadata_integrity_token"]) and value.get("provenance_verified") is True and value.get("provenance_fixture_bound") is True


def _response(request: Any, *, status: str = "DESTINATION_INSPECTION_BLOCKED", reason: str = "invalid_destination_inspection_contract", **values: Any) -> dict[str, Any]:
    req = request if isinstance(request, Mapping) else {}
    result = {
        "contract_version": DESTINATION_VERSION, "ok": False, "status": status,
        "requested_action": req.get("requested_action", ""), "inspection_completed": False,
        "fixture_id": req.get("fixture_id", ""), "report_id": req.get("report_id", ""),
        "report_version": req.get("report_version", ""), "expected_filename": req.get("expected_filename", ""),
        "expected_sha256": req.get("expected_sha256", ""), "expected_file_size_bytes": req.get("expected_file_size_bytes", 0),
        "expected_page_count": req.get("expected_page_count", 0), "source_boundary_id": req.get("source_boundary_id", ""),
        "archive_root_id": req.get("archive_root_id", ""), "archive_root_version": req.get("archive_root_version", ""),
        "archive_policy_id": req.get("archive_policy_id", ""), "archive_boundary_id": req.get("archive_boundary_id", ""),
        "destination_relative_id": req.get("destination_relative_id", ""), "destination_status": "",
        "collision_classification": "", "destination_exists": False, "destination_regular_file": False,
        "destination_link_or_reparse": False, "destination_inside_approved_root": False,
        "source_destination_distinct": False, "identity_match": False, "sha256_match": False,
        "file_size_match": False, "page_count_match": False, "classification_match": False,
        "warning_match": False, "pdf_signature_valid": False, "pdf_parse_valid": False,
        "evidence_version_token": "", "evaluated_at": "", "request_id": req.get("request_id", ""),
        "idempotency_key": req.get("idempotency_key", ""), "blocked_reason": reason if reason == "" or reason in REASONS else "invalid_destination_inspection_contract",
        "action_performed": False, "safety_flags": _flags(),
    }
    result.update(values)
    return result


def _string(value: Any, limit: int) -> bool:
    return isinstance(value, str) and bool(value) and len(value) <= limit and value == value.strip() and value.isascii() and "\x00" not in value and not any(ord(c) < 32 or ord(c) == 127 for c in value)


def _component(value: Any, limit: int, alphabet: str) -> str | None:
    if not _string(value, limit):
        if isinstance(value, str) and not value.isascii():
            return "non_ascii_path_component"
        if isinstance(value, str) and len(value) > limit:
            return "path_component_too_long"
        return "invalid_path_component"
    if value in {".", ".."} or value.endswith(".") or any(c in value for c in "/\\:") or not all(c in alphabet for c in value):
        return "invalid_path_component"
    if value.upper().split(".", 1)[0] in _RESERVED:
        return "reserved_path_component"
    return None


def _regular_identity(observer: Any, target: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        raw = observer(target) if callable(observer) else None
    except OSError:
        return None, "destination_inspection_failed"
    if raw is None:
        try:
            info = os.stat(target, follow_symlinks=False)
            raw = {"identity_completed": True, "identity_supported": True, "volume_identifier": str(getattr(info, "st_dev", "")), "file_identifier": str(getattr(info, "st_ino", "")), "object_type": "regular"}
        except OSError:
            return None, "source_destination_identity_unavailable"
    if not isinstance(raw, Mapping) or raw.get("identity_completed") is not True or raw.get("identity_supported") is not True:
        return None, "source_destination_identity_unavailable"
    return dict(raw), None


def _reparse(observer: Any, path: Path) -> bool | None:
    if callable(observer):
        value = observer(path)
        return value if isinstance(value, bool) else None
    try:
        info = os.lstat(path)
        return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400)
    except OSError:
        return None


def _metadata_valid(metadata: Any, req: Mapping[str, Any], source: Mapping[str, Any], digest: str, size: int, pages: int, root: Mapping[str, Any]) -> tuple[bool, str]:
    if not isinstance(metadata, Mapping):
        return False, "classification_evidence_missing"
    if not _metadata_schema_valid(metadata):
        return False, "trusted_metadata_invalid"
    if metadata.get("action_performed") is not False:
        return False, "trusted_metadata_invalid"
    metadata_bindings = (("fixture_id", "fixture_id"), ("report_id", "report_id"), ("report_version", "report_version"), ("filename", "expected_filename"), ("sha256", "expected_sha256"), ("file_size_bytes", "expected_file_size_bytes"), ("page_count", "expected_page_count"), ("request_id", "request_id"), ("idempotency_key", "idempotency_key"))
    if any(metadata.get(metadata_key) != req.get(request_key) for metadata_key, request_key in metadata_bindings):
        return False, "trusted_metadata_request_mismatch"
    if metadata.get("sha256") != digest or metadata.get("file_size_bytes") != size or metadata.get("page_count") != pages:
        return False, "trusted_metadata_identity_mismatch"
    if metadata.get("classification") != "governed_internal_test_pdf":
        return False, "classification_mismatch"
    if metadata.get("internal_warning") != "INTERNAL TEST FIXTURE NOT FOR CUSTOMER RELEASE":
        return False, "warning_mismatch"
    if metadata.get("provenance_verified") is not True or metadata.get("provenance_fixture_bound") is not True:
        return False, "provenance_invalid"
    if metadata.get("archive_root_id") != root.get("archive_root_id") or metadata.get("archive_root_version") != root.get("archive_root_version"):
        return False, "trusted_metadata_identity_mismatch"
    return True, ""


def _result_valid(result: Any, request: Mapping[str, Any], target_token: str) -> tuple[bool, str]:
    if not isinstance(result, Mapping):
        return False, "parser_result_invalid"
    if set(result) != PARSER_RESULT_FIELDS:
        return False, "unexpected_parser_result_fields"
    if result.get("contract_version") != RESULT_VERSION:
        return False, "unsupported_parser_result_version"
    if not all(isinstance(result.get(key), bool) for key in ("ok", "inspection_completed", "pdf_signature_valid", "pdf_parse_valid", "encrypted_or_protected", "embedded_files_detected", "javascript_detected", "external_resource_request_detected", "rendering_performed", "network_access_performed", "filesystem_write_performed", "process_isolation_claimed", "timeout_enforced", "memory_limit_enforced", "timeout_occurred", "memory_limit_exceeded", "resource_limit_exceeded", "action_performed")):
        return False, "invalid_parser_result_contract"
    if not all(isinstance(result.get(key), str) and result.get(key) for key in ("parser_source_id", "parser_source_version", "parser_policy_id", "resource_policy_id", "evidence_version_token", "evaluated_at")):
        return False, "parser_result_missing"
    if result.get("resource_policy_id") != RESOURCE_POLICY or result.get("status") not in {"PARSER_RESULT_COMPLETE", "PARSER_RESULT_BLOCKED", "PARSER_RESULT_UNAVAILABLE", "PARSER_RESULT_TIMED_OUT", "PARSER_RESULT_RESOURCE_LIMITED", "PARSER_RESULT_UNSUPPORTED"}:
        return False, "invalid_parser_result_contract"
    if any(result.get(k) != request.get(k) for k in ("fixture_id", "report_id", "report_version", "expected_filename", "destination_relative_id", "request_id", "idempotency_key")):
        return False, "parser_result_request_mismatch"
    if result.get("destination_identity_version_token") != target_token:
        return False, "parser_result_identity_mismatch"
    if result.get("action_performed") is not False or not _strict_false_flags(result.get("safety_flags")):
        return False, "parser_result_invalid"
    if any(result.get(k) is not False for k in ("network_access_performed", "filesystem_write_performed", "rendering_performed")):
        return False, "parser_network_access_detected" if result.get("network_access_performed") else "parser_filesystem_write_detected" if result.get("filesystem_write_performed") else "parser_rendering_detected"
    if result.get("timeout_occurred") and result.get("status") != "PARSER_RESULT_TIMED_OUT":
        return False, "parser_timeout"
    if result.get("memory_limit_exceeded") and result.get("status") != "PARSER_RESULT_RESOURCE_LIMITED":
        return False, "parser_memory_limit_exceeded"
    return True, ""


def inspect_button2_governed_internal_pdf_archive_destination_v1(private_inspection_capability, source_artifact_evidence, destination_request):
    """Inspect one deterministic destination using only a private composite capability."""
    request = destination_request if isinstance(destination_request, Mapping) else {}
    if not isinstance(destination_request, Mapping) or request.get("contract_version") != "button2-governed-internal-pdf-destination-inspection-v1" or request.get("requested_action") != "inspect_internal_pdf_archive_destination":
        return _response(request, reason="unsupported_contract_version" if isinstance(request, Mapping) and request.get("contract_version") else "invalid_destination_inspection_contract")
    if set(request) != REQUEST_FIELDS:
        return _response(request, reason="unexpected_destination_inspection_fields")
    if any(not _string(request.get(k), n) for k, n in (("fixture_id", 64), ("report_id", 96), ("report_version", 32), ("expected_filename", 160), ("source_boundary_id", 96), ("archive_root_id", 96), ("archive_root_version", 96), ("archive_policy_id", 96), ("archive_boundary_id", 96), ("destination_relative_id", 512), ("request_id", 128), ("idempotency_key", 128))) or not _HEX.fullmatch(request.get("expected_sha256", "")) or type(request.get("expected_file_size_bytes")) is not int or request["expected_file_size_bytes"] < 0 or type(request.get("expected_page_count")) is not int or not 1 <= request["expected_page_count"] <= MAX_PAGES:
        return _response(request, reason="invalid_destination_inspection_contract")
    if not _source_valid(source_artifact_evidence):
        return _response(request, reason="source_artifact_evidence_invalid")
    source = source_artifact_evidence
    if source.get("artifact_state") != "ACTIVE_INTERNAL_TEST_ARTIFACT" or source.get("inspection_completed") is not True:
        return _response(request, reason="source_artifact_state_not_eligible")
    for key in ("fixture_id", "report_id", "report_version"):
        if source.get(key) != request.get(key):
            return _response(request, reason="source_artifact_identity_mismatch")
    if source.get("observed_filename") != request.get("expected_filename") or source.get("expected_filename") != request.get("expected_filename"):
        return _response(request, reason="source_artifact_identity_mismatch")
    if source.get("pdf_signature_valid") is not True or source.get("pdf_parse_valid") is not True or source.get("identity_valid") is not True or source.get("classification_valid") is not True or source.get("internal_warning_valid") is not True:
        return _response(request, reason="source_artifact_evidence_invalid")
    if any(source.get(k) is not False for k in ("customer_ready_possible", "customer_release_authorized", "queue_write_performed", "pdf_generation_performed", "artifact_archived", "artifact_removed", "artifact_overwritten", "permanent_mutation_performed", "action_performed")):
        return _response(request, reason="source_artifact_evidence_invalid")
    if source.get("source_boundary_id") != request.get("source_boundary_id"):
        return _response(request, reason="source_artifact_identity_mismatch")
    if not _capability_valid(private_inspection_capability):
        return _response(request, reason="invalid_destination_inspection_contract")
    capability = private_inspection_capability
    if capability.get("capability_contract_version") != COMPOSITE_VERSION:
        return _response(request, reason="unsupported_contract_version")
    if not all(capability.get(k) is True for k in ("configured", "enabled", "server_controlled", "customer_isolated", "source_isolated")) or capability.get("action_performed") is not False:
        return _response(request, reason="archive_root_disabled" if capability.get("enabled") is not True else "archive_root_invalid")
    if capability.get("archive_root_id") != request["archive_root_id"] or capability.get("archive_root_version") != request["archive_root_version"] or capability.get("archive_policy_id") != request["archive_policy_id"] or capability.get("archive_boundary_id") != request["archive_boundary_id"]:
        return _response(request, reason="archive_root_identity_mismatch")
    if capability.get("platform") != "windows":
        return _response(request, status="DESTINATION_INSPECTION_UNSUPPORTED_PLATFORM", reason="unsupported_platform")
    if capability.get("internal_test_only") is not True or capability.get("fixture_only") is not True or capability.get("production_capable") is not False:
        return _response(request, reason="archive_root_invalid")
    if source.get("source_identity") is None:
        return _response(request, reason="source_destination_identity_unavailable")
    components = (("fixture_id", 64, "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-"), ("report_id", 96, "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-"), ("report_version", 32, "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_.-"), ("expected_filename", 160, "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_.-"))
    for key, limit, alphabet in components:
        reason = _component(request[key], limit, alphabet)
        if reason:
            return _response(request, reason=reason)
    if not request["expected_filename"].lower().endswith(".pdf"):
        return _response(request, reason="invalid_path_component")
    logical_id = "/".join(request[k] for k, _, _ in components)
    if request["destination_relative_id"] != logical_id:
        return _response(request, reason="invalid_destination_relative_id")
    root_target = capability.get("root_target")
    if not isinstance(root_target, (str, os.PathLike)):
        return _response(request, reason="archive_root_missing")
    root = Path(root_target)
    if not root.is_absolute() or root.drive == "" or any(part in {".", ".."} for part in root.parts):
        return _response(request, reason="archive_root_invalid")
    root_reparse = _reparse(capability.get("root_observer"), root)
    if root_reparse is None:
        return _response(request, reason="archive_root_missing")
    if root_reparse:
        return _response(request, reason="archive_root_link_or_reparse")
    try:
        root_stat = os.stat(root, follow_symlinks=False)
    except FileNotFoundError:
        return _response(request, reason="archive_root_missing")
    except PermissionError:
        return _response(request, reason="archive_root_invalid")
    except OSError:
        return _response(request, reason="archive_root_invalid")
    if not stat.S_ISDIR(root_stat.st_mode):
        return _response(request, reason="archive_root_not_directory")
    target = root.joinpath(*[request[k] for k, _, _ in components])
    try:
        target.relative_to(root)
    except ValueError:
        return _response(request, reason="destination_outside_approved_root")
    parents = [root / request["fixture_id"], root / request["fixture_id"] / request["report_id"], root / request["fixture_id"] / request["report_id"] / request["report_version"]]
    for parent in parents:
        try:
            info = os.stat(parent, follow_symlinks=False)
        except FileNotFoundError:
            return _response(request, status="DESTINATION_INSPECTION_UNAVAILABLE", reason="parent_missing")
        except PermissionError:
            return _response(request, reason="parent_access_denied")
        except OSError:
            return _response(request, reason="parent_inspection_failed")
        reparse = _reparse(capability.get("filesystem_observer"), parent)
        if reparse:
            return _response(request, reason="parent_link_or_reparse")
        if not stat.S_ISDIR(info.st_mode):
            return _response(request, reason="parent_non_directory")
    try:
        target_info = os.lstat(target)
    except FileNotFoundError:
        return _response(request, status="DESTINATION_INSPECTION_COMPLETE", reason="", ok=True, inspection_completed=True, destination_status="DESTINATION_ABSENT", collision_classification="NONE", destination_inside_approved_root=True, source_destination_distinct=True)
    except PermissionError:
        return _response(request, reason="destination_access_denied")
    except OSError:
        return _response(request, reason="destination_inspection_failed")
    target_reparse = _reparse(capability.get("filesystem_observer"), target)
    if target_reparse:
        return _response(request, reason="destination_link_or_reparse", destination_exists=True, destination_link_or_reparse=True)
    if stat.S_ISDIR(target_info.st_mode):
        return _response(request, reason="destination_directory_collision", destination_exists=True, destination_status="DESTINATION_DIRECTORY_COLLISION")
    if not stat.S_ISREG(target_info.st_mode):
        return _response(request, reason="destination_non_regular", destination_exists=True, destination_status="DESTINATION_NON_REGULAR")
    destination_identity, identity_reason = _regular_identity(capability.get("identity_observer"), target)
    if identity_reason:
        return _response(request, reason=identity_reason, destination_exists=True, destination_regular_file=True)
    source_identity = source["source_identity"]
    if destination_identity.get("volume_identifier") == source_identity.get("volume_identifier") and destination_identity.get("file_identifier") == source_identity.get("file_identifier"):
        return _response(request, reason="source_destination_same", destination_exists=True, destination_regular_file=True, destination_status="SOURCE_DESTINATION_SAME")
    try:
        size = target.stat().st_size
    except OSError:
        return _response(request, reason="destination_inspection_failed", destination_exists=True)
    if size > MAX_FILE_SIZE:
        return _response(request, reason="resource_limit_exceeded", destination_exists=True, destination_regular_file=True)
    try:
        with target.open("rb") as handle:
            signature = handle.read(SIGNATURE_BYTES)
    except OSError:
        return _response(request, reason="destination_access_denied", destination_exists=True)
    if not signature.startswith(b"%PDF-"):
        return _response(request, reason="pdf_signature_validation_failed", destination_exists=True, destination_regular_file=True)
    target_token = str(capability.get("identity_observer")(target).get("identity_version_token", "")) if callable(capability.get("identity_observer")) else f"{destination_identity.get('volume_identifier')}:{destination_identity.get('file_identifier')}"
    parser_capability = capability.get("parser_capability")
    if not isinstance(parser_capability, Mapping):
        return _response(request, reason="parser_capability_missing", destination_exists=True, destination_regular_file=True)
    if parser_capability.get("capability_contract_version") != PARSER_CAPABILITY_VERSION:
        return _response(request, reason="unsupported_contract_version", destination_exists=True, destination_regular_file=True)
    if parser_capability.get("enabled") is not True:
        return _response(request, reason="parser_capability_disabled", destination_exists=True, destination_regular_file=True)
    if parser_capability.get("supported") is not True:
        return _response(request, reason="parser_capability_unsupported", destination_exists=True, destination_regular_file=True)
    if not _parser_capability_valid(parser_capability):
        return _response(request, reason="parser_capability_invalid", destination_exists=True, destination_regular_file=True)
    parser = parser_capability.get("parser")
    if not callable(parser) or parser_capability.get("internal_test_only") is not True or parser_capability.get("fixture_only") is not True or parser_capability.get("production_capable") is not False:
        return _response(request, reason="parser_capability_invalid", destination_exists=True, destination_regular_file=True)
    parser_request = {"contract_version": REQUEST_VERSION, "requested_action": "inspect_validated_internal_pdf_destination", "fixture_id": request["fixture_id"], "report_id": request["report_id"], "report_version": request["report_version"], "expected_filename": request["expected_filename"], "expected_sha256": request["expected_sha256"], "expected_file_size_bytes": request["expected_file_size_bytes"], "expected_page_count": request["expected_page_count"], "destination_relative_id": logical_id, "destination_identity_version_token": target_token, "resource_policy_id": RESOURCE_POLICY, "maximum_file_size_bytes": MAX_FILE_SIZE, "maximum_page_count": MAX_PAGES, "parser_timeout_seconds": PARSER_TIMEOUT, "parser_memory_limit_bytes": PARSER_MEMORY, "request_id": request["request_id"], "idempotency_key": request["idempotency_key"]}
    try:
        parser_result = parser(target, parser_request)
    except Exception:
        return _response(request, reason="parser_internal_failure", destination_exists=True, destination_regular_file=True)
    valid, parser_reason = _result_valid(parser_result, parser_request, target_token)
    if not valid:
        return _response(request, reason=parser_reason, destination_exists=True, destination_regular_file=True)
    if parser_result.get("status") != "PARSER_RESULT_COMPLETE" or parser_result.get("ok") is not True:
        reason = parser_result.get("blocked_reason") or "parser_internal_failure"
        if reason not in REASONS:
            reason = "parser_internal_failure"
        return _response(request, reason=reason, destination_exists=True, destination_regular_file=True)
    page_count = parser_result.get("observed_page_count")
    if type(page_count) is not int or not 1 <= page_count <= MAX_PAGES:
        return _response(request, reason="resource_limit_exceeded" if isinstance(page_count, int) and page_count > MAX_PAGES else "page_count_mismatch", destination_exists=True, destination_regular_file=True)
    if page_count != request["expected_page_count"]:
        return _response(request, reason="page_count_mismatch", destination_exists=True, destination_regular_file=True)
    digest_hash = hashlib.sha256()
    try:
        with target.open("rb") as handle:
            while True:
                chunk = handle.read(HASH_CHUNK)
                if not chunk:
                    break
                digest_hash.update(chunk)
    except OSError:
        return _response(request, reason="destination_access_denied", destination_exists=True, destination_regular_file=True)
    digest = digest_hash.hexdigest()
    if digest != request["expected_sha256"]:
        return _response(request, reason="sha256_mismatch", destination_exists=True, destination_regular_file=True)
    metadata = parser_capability.get("trusted_metadata")
    valid_metadata, metadata_reason = _metadata_valid(metadata, request, source, digest, size, page_count, capability)
    if not valid_metadata:
        return _response(request, reason=metadata_reason, destination_exists=True, destination_regular_file=True)
    identical = source.get("sha256") == digest and source.get("file_size_bytes") == size and source.get("page_count") == page_count
    status = "DESTINATION_INSPECTION_COMPLETE"
    classification = "IDENTICAL_ARCHIVE_PRESENT" if identical else "CONFLICTING_ARCHIVE_PRESENT"
    return _response(request, status=status, reason="", ok=True, inspection_completed=True, destination_status=classification, collision_classification=classification, destination_exists=True, destination_regular_file=True, destination_inside_approved_root=True, source_destination_distinct=True, identity_match=identical, sha256_match=identical, file_size_match=source.get("file_size_bytes") == size, page_count_match=source.get("page_count") == page_count, classification_match=True, warning_match=True, pdf_signature_valid=True, pdf_parse_valid=True, evidence_version_token=metadata.get("destination_evidence_version_token", ""), evaluated_at=metadata.get("evaluated_at", ""), blocked_reason="", action_performed=False)
