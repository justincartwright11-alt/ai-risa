"""Pure, bounded planning for governed internal PDF archive operations."""

from __future__ import annotations

import re
from typing import Any

PLANNER_CONTRACT_VERSION = "button2-governed-internal-pdf-archive-planner-v1"
INSPECTION_CONTRACT_VERSION = "button2-governed-internal-pdf-artifact-inspection-v1"
ARCHIVE_ROOT_CONTRACT_VERSION = "button2-governed-internal-pdf-archive-root-capability-v1"
DESTINATION_CONTRACT_VERSION = "button2-governed-internal-pdf-destination-evidence-v1"
AUTHORIZATION_CONTRACT_VERSION = "button2-governed-internal-pdf-authorization-v1"
AUDIT_CONTRACT_VERSION = "button2-governed-internal-pdf-audit-capability-v1"
CONCURRENCY_CONTRACT_VERSION = "button2-governed-internal-pdf-concurrency-v1"

REQUEST_FIELDS = frozenset(("contract_version", "requested_action", "fixture_id", "report_id", "report_version", "expected_artifact_state", "expected_filename", "expected_sha256", "expected_file_size_bytes", "expected_page_count", "archive_root_id", "archive_root_version", "archive_policy_id", "request_id", "idempotency_key", "approval_id", "requested_at", "correlation_id"))
ROW_FIELDS = frozenset(("fixture_id", "fixture_only", "internal_only", "test_fixture_only", "report_id", "report_version", "classification", "internal_warning", "customer_ready", "customer_release_authorized", "queue_write_authorized", "schema_version", "provenance_source_type", "provenance_source_id", "provenance_verified", "provenance_fixture_bound"))
ARTIFACT_FIELDS = frozenset(("inspection_contract_version", "inspection_completed", "artifact_state", "fixture_id", "report_id", "report_version", "expected_filename", "observed_filename", "sha256", "file_size_bytes", "page_count", "pdf_signature_valid", "pdf_parse_valid", "identity_valid", "classification_valid", "internal_warning_valid", "source_boundary_id", "customer_ready_possible", "customer_release_authorized", "queue_write_performed", "pdf_generation_performed", "artifact_archived", "artifact_removed", "artifact_overwritten", "permanent_mutation_performed"))
ROOT_FIELDS = frozenset(("capability_contract_version", "archive_root_id", "archive_root_version", "archive_policy_id", "configured", "enabled", "absolute_validated", "server_controlled", "customer_isolated", "source_isolated", "link_safe", "platform", "filesystem_policy_id", "sanitization_policy_id", "archive_boundary_id"))
DESTINATION_FIELDS = frozenset(("destination_evidence_contract_version", "archive_root_id", "archive_root_version", "archive_policy_id", "destination_relative_id", "destination_status", "collision_classification", "destination_regular_file", "destination_link_or_reparse", "destination_inside_approved_root", "source_destination_distinct", "identity_match", "sha256_match", "file_size_match", "page_count_match", "classification_match", "warning_match", "evidence_completed", "action_performed"))
AUTH_FIELDS = frozenset(("authorization_contract_version", "authorization_status", "requested_action", "fixture_id", "report_id", "report_version", "operator_id", "operator_role", "approval_id", "request_id", "idempotency_key", "planning_authorized", "execution_authorized", "authorization_expires_at", "blocked_reason", "evidence_completed"))
AUDIT_FIELDS = frozenset(("audit_capability_contract_version", "audit_sink_id", "audit_sink_available", "schema_supported", "planning_event_supported", "persistence_authorized", "action_performed"))
CONCURRENCY_FIELDS = frozenset(("concurrency_contract_version", "artifact_action_active", "conflicting_action", "artifact_version_token", "source_evidence_current", "destination_evidence_current", "evaluated_at", "evidence_completed"))
SAFETY_FLAGS = ("customer_ready_possible", "customer_release_authorized", "queue_write_performed", "pdf_generation_performed", "learning_applied", "calibration_applied", "accuracy_ledger_written", "gcid_written", "model_weights_changed", "fighter_ratings_changed", "prediction_logic_changed", "artifact_archived", "artifact_removed", "artifact_overwritten", "permanent_mutation_performed")
STATUSES = frozenset(("ARCHIVE_PLAN_READY", "ARCHIVE_PLAN_BLOCKED", "ARCHIVE_ALREADY_SATISFIED", "ARCHIVE_PLAN_REQUIRES_DESTINATION_INSPECTION", "ARCHIVE_PLAN_REQUIRES_AUTHORIZATION", "ARCHIVE_PLAN_REQUIRES_AUDIT_CAPABILITY", "ARCHIVE_PLAN_REQUIRES_CURRENT_CONCURRENCY_EVIDENCE"))
BLOCKED_REASONS = frozenset(("invalid_plan_contract", "unexpected_plan_fields", "unsupported_contract_version", "fixture_governance_blocked", "governed_row_identity_mismatch", "artifact_state_not_archive_eligible", "artifact_identity_mismatch", "filename_mismatch", "sha256_mismatch", "file_size_mismatch", "page_count_mismatch", "signature_validation_failed", "parse_validation_failed", "classification_mismatch", "internal_warning_missing", "forbidden_release_claim_present", "archive_root_missing", "archive_root_disabled", "archive_root_invalid", "archive_root_identity_mismatch", "archive_policy_missing", "sanitization_policy_mismatch", "invalid_path_component", "non_ascii_path_component", "reserved_path_component", "path_component_too_long", "relative_identifier_too_long", "identity_case_collision", "destination_evidence_missing", "destination_evidence_stale", "source_destination_same", "archive_destination_collision", "destination_link_or_reparse", "destination_non_regular", "destination_outside_approved_root", "authorization_not_satisfied", "approval_not_satisfied", "authorization_evidence_stale", "audit_capability_unavailable", "audit_schema_unsupported", "concurrency_evidence_missing", "concurrency_evidence_stale", "concurrency_conflict", "idempotency_conflict", "planning_not_authorized"))

_DESTINATION_STATES = frozenset(("DESTINATION_EVIDENCE_NOT_EVALUATED", "DESTINATION_ABSENT", "IDENTICAL_ARCHIVE_PRESENT", "CONFLICTING_ARCHIVE_PRESENT", "DESTINATION_NON_REGULAR", "DESTINATION_LINK_OR_REPARSE", "DESTINATION_DIRECTORY_COLLISION", "DESTINATION_OUTSIDE_APPROVED_ROOT", "SOURCE_DESTINATION_SAME", "IDENTITY_NORMALIZATION_COLLISION", "IDEMPOTENCY_CONFLICT"))
_RESERVED = frozenset(("CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))))
_HEX = re.compile(r"^[0-9a-f]{64}$")


def _base(req: Any, artifact: Any = None, root: Any = None, destination: Any = None, auth: Any = None) -> dict[str, Any]:
    req = req if isinstance(req, dict) else {}
    artifact = artifact if isinstance(artifact, dict) else {}
    root = root if isinstance(root, dict) else {}
    destination = destination if isinstance(destination, dict) else {}
    auth = auth if isinstance(auth, dict) else {}
    result = {"contract_version": PLANNER_CONTRACT_VERSION, "ok": False, "status": "ARCHIVE_PLAN_BLOCKED", "requested_action": req.get("requested_action", ""), "fixture_id": req.get("fixture_id", ""), "report_id": req.get("report_id", ""), "report_version": req.get("report_version", ""), "current_artifact_state": artifact.get("artifact_state", ""), "proposed_state": "ARCHIVE_PLANNED", "filename": req.get("expected_filename", ""), "expected_sha256": req.get("expected_sha256", ""), "expected_file_size_bytes": req.get("expected_file_size_bytes", 0), "expected_page_count": req.get("expected_page_count", 0), "source_boundary_id": artifact.get("source_boundary_id", ""), "archive_boundary_id": root.get("archive_boundary_id", ""), "archive_root_id": root.get("archive_root_id", req.get("archive_root_id", "")), "archive_root_version": root.get("archive_root_version", req.get("archive_root_version", "")), "archive_policy_id": root.get("archive_policy_id", req.get("archive_policy_id", "")), "destination_relative_id": destination.get("destination_relative_id", ""), "destination_status": destination.get("destination_status", ""), "collision_classification": destination.get("collision_classification", ""), "source_destination_distinct": destination.get("source_destination_distinct", False), "authorization_status": auth.get("authorization_status", ""), "audit_sink_available": False, "concurrency_status": "", "planning_authorized": auth.get("planning_authorized", False), "execution_authorized": False, "action_performed": False, "request_id": req.get("request_id", ""), "idempotency_key": req.get("idempotency_key", ""), "approval_id": req.get("approval_id", ""), "blocked_reason": "invalid_plan_contract", "safety_flags": {name: False for name in SAFETY_FLAGS}}
    return result


def _fail(result: dict[str, Any], reason: str, status: str = "ARCHIVE_PLAN_BLOCKED") -> dict[str, Any]:
    result["status"] = status if status in STATUSES else "ARCHIVE_PLAN_BLOCKED"
    result["blocked_reason"] = reason if reason in BLOCKED_REASONS else "invalid_plan_contract"
    return result


def _string(value: Any, limit: int, *, ascii_only: bool = True) -> bool:
    return isinstance(value, str) and bool(value) and len(value) <= limit and "\x00" not in value and not any(ord(c) < 32 or ord(c) == 127 for c in value) and (not ascii_only or value.isascii())


def _component(value: Any, limit: int, alphabet: str) -> str | None:
    if not _string(value, limit):
        return "non_ascii_path_component" if isinstance(value, str) and not value.isascii() else ("path_component_too_long" if isinstance(value, str) and len(value) > limit else "invalid_path_component")
    if value in (".", "..") or value != value.strip() or value.endswith(".") or any(c in value for c in "/\\:") or not all(c in alphabet for c in value):
        return "invalid_path_component"
    if value.upper().split(".", 1)[0] in _RESERVED:
        return "reserved_path_component"
    return None


def _fields(value: Any, allowed: frozenset[str]) -> bool:
    return isinstance(value, dict) and set(value) <= allowed


def _versions(req: Any, artifact: Any, root: Any, destination: Any, auth: Any, audit: Any, concurrency: Any) -> bool:
    return (isinstance(req, dict) and req.get("contract_version") == PLANNER_CONTRACT_VERSION and isinstance(artifact, dict) and artifact.get("inspection_contract_version") == INSPECTION_CONTRACT_VERSION and isinstance(root, dict) and root.get("capability_contract_version") == ARCHIVE_ROOT_CONTRACT_VERSION and isinstance(destination, dict) and destination.get("destination_evidence_contract_version") == DESTINATION_CONTRACT_VERSION and isinstance(auth, dict) and auth.get("authorization_contract_version") == AUTHORIZATION_CONTRACT_VERSION and isinstance(audit, dict) and audit.get("audit_capability_contract_version") == AUDIT_CONTRACT_VERSION and isinstance(concurrency, dict) and concurrency.get("concurrency_contract_version") == CONCURRENCY_CONTRACT_VERSION)


def build_button2_governed_internal_pdf_archive_plan_v1(governed_row, artifact_evidence, archive_root_capability, destination_evidence, authorization_evidence, audit_capability, concurrency_evidence, request_envelope):
    result = _base(request_envelope, artifact_evidence, archive_root_capability, destination_evidence, authorization_evidence)
    objects = (governed_row, artifact_evidence, archive_root_capability, destination_evidence, authorization_evidence, audit_capability, concurrency_evidence, request_envelope)
    if not _versions(request_envelope, artifact_evidence, archive_root_capability, destination_evidence, authorization_evidence, audit_capability, concurrency_evidence):
        return _fail(result, "unsupported_contract_version")
    if not _fields(request_envelope, REQUEST_FIELDS) or any(not _fields(obj, fields) for obj, fields in zip(objects, (ROW_FIELDS, ARTIFACT_FIELDS, ROOT_FIELDS, DESTINATION_FIELDS, AUTH_FIELDS, AUDIT_FIELDS, CONCURRENCY_FIELDS, REQUEST_FIELDS))):
        return _fail(result, "unexpected_plan_fields")
    req = request_envelope
    required_strings = (("fixture_id", 64), ("report_id", 96), ("report_version", 32), ("expected_filename", 160), ("archive_root_id", 96), ("archive_root_version", 96), ("archive_policy_id", 96), ("request_id", 128), ("idempotency_key", 128))
    if req.get("requested_action") != "plan_internal_pdf_archive" or req.get("expected_artifact_state") != "ACTIVE_INTERNAL_TEST_ARTIFACT" or any(not _string(req.get(k), n) for k, n in required_strings) or not _HEX.fullmatch(req.get("expected_sha256", "")) or type(req.get("expected_file_size_bytes")) is not int or not 0 <= req["expected_file_size_bytes"] <= 2**63 - 1 or type(req.get("expected_page_count")) is not int or not 0 < req["expected_page_count"] <= 10000 or any(k in req for k in ("source_path", "absolute_source_path", "archive_path", "destination_path", "archive_root_path", "temporary_path", "customer_path", "arbitrary_filename", "arbitrary_directory", "wildcard", "glob", "recursive", "overwrite", "force", "skip_validation", "skip_authorization", "skip_audit", "raw_pdf_bytes", "arbitrary_report_content")):
        return _fail(result, "invalid_plan_contract")
    row = governed_row
    if not all(row.get(k) is True for k in ("fixture_only", "internal_only", "test_fixture_only", "provenance_verified", "provenance_fixture_bound")) or row.get("customer_ready") is not False or row.get("customer_release_authorized") is not False or row.get("queue_write_authorized") is not False or row.get("classification") != "governed_internal_test_pdf" or row.get("internal_warning") != "INTERNAL TEST FIXTURE NOT FOR CUSTOMER RELEASE" or not all(_string(row.get(k), 128) for k in ("schema_version", "provenance_source_type", "provenance_source_id")):
        return _fail(result, "fixture_governance_blocked")
    if any(row.get(k) != req.get(k) for k in ("fixture_id", "report_id", "report_version")) or any(artifact_evidence.get(k) != req.get(k) for k in ("fixture_id", "report_id", "report_version", "expected_filename")):
        return _fail(result, "governed_row_identity_mismatch")
    artifact = artifact_evidence
    if artifact.get("artifact_state") != "ACTIVE_INTERNAL_TEST_ARTIFACT":
        return _fail(result, "artifact_state_not_archive_eligible")
    checks = ("inspection_completed", "pdf_signature_valid", "pdf_parse_valid", "identity_valid", "classification_valid", "internal_warning_valid")
    if any(artifact.get(k) is not True for k in checks):
        reason = "signature_validation_failed" if artifact.get("pdf_signature_valid") is not True else "parse_validation_failed" if artifact.get("pdf_parse_valid") is not True else "classification_mismatch" if artifact.get("classification_valid") is not True else "internal_warning_missing"
        return _fail(result, reason)
    if artifact.get("observed_filename") != req["expected_filename"]: return _fail(result, "filename_mismatch")
    if artifact.get("sha256") != req["expected_sha256"]: return _fail(result, "sha256_mismatch")
    if artifact.get("file_size_bytes") != req["expected_file_size_bytes"]: return _fail(result, "file_size_mismatch")
    if artifact.get("page_count") != req["expected_page_count"]: return _fail(result, "page_count_mismatch")
    if any(artifact.get(k) is not False for k in ("customer_ready_possible", "customer_release_authorized", "queue_write_performed", "pdf_generation_performed", "artifact_archived", "artifact_removed", "artifact_overwritten", "permanent_mutation_performed")): return _fail(result, "forbidden_release_claim_present")
    root = archive_root_capability
    if not all(root.get(k) is True for k in ("configured", "enabled", "absolute_validated", "server_controlled", "customer_isolated", "source_isolated", "link_safe")): return _fail(result, "archive_root_missing" if root.get("configured") is not True else "archive_root_disabled" if root.get("enabled") is not True else "archive_root_invalid")
    if any(root.get(k) != req.get(k) for k in ("archive_root_id", "archive_root_version", "archive_policy_id")): return _fail(result, "archive_root_identity_mismatch")
    if not _string(root.get("archive_boundary_id"), 96) or not _string(artifact.get("source_boundary_id"), 96) or root["archive_boundary_id"] == artifact["source_boundary_id"]: return _fail(result, "archive_root_invalid")
    if root.get("filesystem_policy_id") != "windows-safe-v1" or root.get("sanitization_policy_id") != "ascii-reject-v1": return _fail(result, "sanitization_policy_mismatch")
    for key, limit, alphabet in (("fixture_id", 64, "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"), ("report_id", 96, "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"), ("report_version", 32, "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-"), ("expected_filename", 160, "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-")):
        reason = _component(req[key], limit, alphabet)
        if reason: return _fail(result, reason)
    if not req["expected_filename"].lower().endswith(".pdf"): return _fail(result, "invalid_path_component")
    destination_id = "/".join((req["fixture_id"], req["report_id"], req["report_version"], req["expected_filename"]))
    if len(destination_id) > 512: return _fail(result, "relative_identifier_too_long")
    result["destination_relative_id"] = destination_id
    destination = destination_evidence
    if destination.get("destination_relative_id") not in ("", destination_id) or destination.get("archive_root_id") != req["archive_root_id"] or destination.get("archive_root_version") != req["archive_root_version"] or destination.get("archive_policy_id") != req["archive_policy_id"] or destination.get("action_performed") is not False: return _fail(result, "destination_evidence_missing")
    if destination.get("evidence_completed") is not True or destination.get("destination_status") == "DESTINATION_EVIDENCE_NOT_EVALUATED": return _fail(result, "destination_evidence_missing", "ARCHIVE_PLAN_REQUIRES_DESTINATION_INSPECTION")
    state = destination.get("destination_status")
    if state not in _DESTINATION_STATES: return _fail(result, "destination_evidence_missing")
    if state == "DESTINATION_ABSENT":
        if destination.get("source_destination_distinct") is not True: return _fail(result, "source_destination_same")
    elif state == "IDENTICAL_ARCHIVE_PRESENT":
        if not all(destination.get(k) is True for k in ("identity_match", "sha256_match", "file_size_match", "page_count_match", "classification_match", "warning_match")): return _fail(result, "idempotency_conflict")
    else:
        reason = {"SOURCE_DESTINATION_SAME":"source_destination_same", "DESTINATION_LINK_OR_REPARSE":"destination_link_or_reparse", "DESTINATION_NON_REGULAR":"destination_non_regular", "DESTINATION_OUTSIDE_APPROVED_ROOT":"destination_outside_approved_root", "IDENTITY_NORMALIZATION_COLLISION":"identity_case_collision", "IDEMPOTENCY_CONFLICT":"idempotency_conflict"}.get(state, "archive_destination_collision")
        return _fail(result, reason)
    auth = authorization_evidence
    if auth.get("requested_action") != req["requested_action"] or any(auth.get(k) != req.get(k) for k in ("fixture_id", "report_id", "report_version", "request_id", "idempotency_key")): return _fail(result, "authorization_not_satisfied")
    if auth.get("evidence_completed") is not True or auth.get("planning_authorized") is not True or auth.get("execution_authorized") is not False: return _fail(result, "planning_not_authorized", "ARCHIVE_PLAN_REQUIRES_AUTHORIZATION")
    audit = audit_capability
    result["audit_sink_available"] = audit.get("audit_sink_available") is True
    if not all(audit.get(k) is True for k in ("audit_sink_available", "schema_supported", "planning_event_supported", "persistence_authorized")) or audit.get("action_performed") is not False: return _fail(result, "audit_schema_unsupported" if audit.get("audit_sink_available") is True else "audit_capability_unavailable", "ARCHIVE_PLAN_REQUIRES_AUDIT_CAPABILITY")
    concurrency = concurrency_evidence
    result["concurrency_status"] = "CURRENT"
    if concurrency.get("evidence_completed") is not True: return _fail(result, "concurrency_evidence_missing", "ARCHIVE_PLAN_REQUIRES_CURRENT_CONCURRENCY_EVIDENCE")
    if concurrency.get("artifact_action_active") is True or concurrency.get("conflicting_action") is not False: return _fail(result, "concurrency_conflict")
    if concurrency.get("source_evidence_current") is not True or concurrency.get("destination_evidence_current") is not True: return _fail(result, "concurrency_evidence_stale", "ARCHIVE_PLAN_REQUIRES_CURRENT_CONCURRENCY_EVIDENCE")
    if not _string(concurrency.get("artifact_version_token"), 128) or not _string(concurrency.get("evaluated_at"), 64): return _fail(result, "concurrency_evidence_missing")
    if destination.get("destination_status") == "IDEMPOTENCY_CONFLICT": return _fail(result, "idempotency_conflict")
    result["ok"] = True
    result["status"] = "ARCHIVE_ALREADY_SATISFIED" if state == "IDENTICAL_ARCHIVE_PRESENT" else "ARCHIVE_PLAN_READY"
    result["blocked_reason"] = ""
    result["authorization_status"] = auth.get("authorization_status", "")
    result["planning_authorized"] = True
    return result
