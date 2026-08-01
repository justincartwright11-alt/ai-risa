from __future__ import annotations

import ast
import copy

from operator_dashboard.button2_governed_internal_pdf_archive_plan_adapter_v1 import (
    ARCHIVE_ROOT_CONTRACT_VERSION,
    AUDIT_CONTRACT_VERSION,
    AUTHORIZATION_CONTRACT_VERSION,
    CONCURRENCY_CONTRACT_VERSION,
    DESTINATION_CONTRACT_VERSION,
    INSPECTION_CONTRACT_VERSION,
    PLANNER_CONTRACT_VERSION,
    SAFETY_FLAGS,
    build_button2_governed_internal_pdf_archive_plan_v1,
)


def _objects():
    request = {"contract_version": PLANNER_CONTRACT_VERSION, "requested_action": "plan_internal_pdf_archive", "fixture_id": "closed_loop_governed_local_fixture_v1", "report_id": "internal_fixture_report_closed_loop_v1", "report_version": "DRAFT_INTERNAL_FIXTURE_v1", "expected_artifact_state": "ACTIVE_INTERNAL_TEST_ARTIFACT", "expected_filename": "internal_fixture_report_closed_loop_v1.pdf", "expected_sha256": "a" * 64, "expected_file_size_bytes": 1234, "expected_page_count": 4, "archive_root_id": "internal-archive", "archive_root_version": "v1", "archive_policy_id": "retain-internal-test-v1", "request_id": "request-1", "idempotency_key": "idem-1", "approval_id": "approval-1"}
    row = {"fixture_id": request["fixture_id"], "fixture_only": True, "internal_only": True, "test_fixture_only": True, "report_id": request["report_id"], "report_version": request["report_version"], "classification": "governed_internal_test_pdf", "internal_warning": "INTERNAL TEST FIXTURE NOT FOR CUSTOMER RELEASE", "customer_ready": False, "customer_release_authorized": False, "queue_write_authorized": False, "schema_version": "schema-v1", "provenance_source_type": "test_fixture", "provenance_source_id": "fixture-source-1", "provenance_verified": True, "provenance_fixture_bound": True}
    artifact = {"inspection_contract_version": INSPECTION_CONTRACT_VERSION, "inspection_completed": True, "artifact_state": "ACTIVE_INTERNAL_TEST_ARTIFACT", "fixture_id": request["fixture_id"], "report_id": request["report_id"], "report_version": request["report_version"], "expected_filename": request["expected_filename"], "observed_filename": request["expected_filename"], "sha256": request["expected_sha256"], "file_size_bytes": 1234, "page_count": 4, "pdf_signature_valid": True, "pdf_parse_valid": True, "identity_valid": True, "classification_valid": True, "internal_warning_valid": True, "source_boundary_id": "source-boundary-1", "customer_ready_possible": False, "customer_release_authorized": False, "queue_write_performed": False, "pdf_generation_performed": False, "artifact_archived": False, "artifact_removed": False, "artifact_overwritten": False, "permanent_mutation_performed": False}
    root = {"capability_contract_version": ARCHIVE_ROOT_CONTRACT_VERSION, "archive_root_id": request["archive_root_id"], "archive_root_version": request["archive_root_version"], "archive_policy_id": request["archive_policy_id"], "configured": True, "enabled": True, "absolute_validated": True, "server_controlled": True, "customer_isolated": True, "source_isolated": True, "link_safe": True, "platform": "windows", "filesystem_policy_id": "windows-safe-v1", "sanitization_policy_id": "ascii-reject-v1", "archive_boundary_id": "archive-boundary-1"}
    destination = {"destination_evidence_contract_version": DESTINATION_CONTRACT_VERSION, "archive_root_id": request["archive_root_id"], "archive_root_version": request["archive_root_version"], "archive_policy_id": request["archive_policy_id"], "destination_relative_id": "", "destination_status": "DESTINATION_ABSENT", "collision_classification": "NONE", "destination_regular_file": False, "destination_link_or_reparse": False, "destination_inside_approved_root": True, "source_destination_distinct": True, "identity_match": False, "sha256_match": False, "file_size_match": False, "page_count_match": False, "classification_match": False, "warning_match": False, "evidence_completed": True, "action_performed": False}
    auth = {"authorization_contract_version": AUTHORIZATION_CONTRACT_VERSION, "authorization_status": "PLANNING_APPROVED", "requested_action": request["requested_action"], "fixture_id": request["fixture_id"], "report_id": request["report_id"], "report_version": request["report_version"], "operator_id": "operator-1", "operator_role": "internal_operator", "approval_id": request["approval_id"], "request_id": request["request_id"], "idempotency_key": request["idempotency_key"], "planning_authorized": True, "execution_authorized": False, "authorization_expires_at": "2099-01-01T00:00:00Z", "blocked_reason": "", "evidence_completed": True}
    audit = {"audit_capability_contract_version": AUDIT_CONTRACT_VERSION, "audit_sink_id": "audit-1", "audit_sink_available": True, "schema_supported": True, "planning_event_supported": True, "persistence_authorized": True, "action_performed": False}
    concurrency = {"concurrency_contract_version": CONCURRENCY_CONTRACT_VERSION, "artifact_action_active": False, "conflicting_action": False, "artifact_version_token": "artifact-version-1", "source_evidence_current": True, "destination_evidence_current": True, "evaluated_at": "2099-01-01T00:00:00Z", "evidence_completed": True}
    return [row, artifact, root, destination, auth, audit, concurrency, request]


def _plan(objects):
    return build_button2_governed_internal_pdf_archive_plan_v1(*objects)


def test_ready_is_deterministic_immutable_and_bounded():
    objects = _objects()
    before = copy.deepcopy(objects)
    first = _plan(objects)
    second = _plan(objects)
    assert first == second
    assert first["status"] == "ARCHIVE_PLAN_READY"
    assert first["destination_relative_id"] == "closed_loop_governed_local_fixture_v1/internal_fixture_report_closed_loop_v1/DRAFT_INTERNAL_FIXTURE_v1/internal_fixture_report_closed_loop_v1.pdf"
    assert objects == before
    assert all(first["safety_flags"].get(flag) is False for flag in SAFETY_FLAGS)
    assert first["execution_authorized"] is False and first["action_performed"] is False
    assert not any("\\" in str(value) or (isinstance(value, str) and len(value) > 512) for value in first.values())


def test_destination_outcomes_and_gates():
    objects = _objects()
    ready = _plan(objects)
    objects[3]["destination_relative_id"] = ready["destination_relative_id"]
    objects[3]["destination_status"] = "IDENTICAL_ARCHIVE_PRESENT"
    for key in ("identity_match", "sha256_match", "file_size_match", "page_count_match", "classification_match", "warning_match"):
        objects[3][key] = True
    assert _plan(objects)["status"] == "ARCHIVE_ALREADY_SATISFIED"
    objects[3]["destination_status"] = "DESTINATION_EVIDENCE_NOT_EVALUATED"
    assert _plan(objects)["status"] == "ARCHIVE_PLAN_REQUIRES_DESTINATION_INSPECTION"
    objects[3]["destination_status"] = "CONFLICTING_ARCHIVE_PRESENT"
    assert _plan(objects)["blocked_reason"] == "archive_destination_collision"
    objects[3]["destination_status"] = "SOURCE_DESTINATION_SAME"
    assert _plan(objects)["blocked_reason"] == "source_destination_same"


def test_validation_matrix():
    cases = ((7, "unsupported_contract_version"), ("new_field", "unexpected_plan_fields"), ("expected_file_size_bytes", "invalid_plan_contract"), ("expected_page_count", "invalid_plan_contract"), ("expected_sha256", "invalid_plan_contract"), ("report_id", "governed_row_identity_mismatch"), ("artifact_state", "artifact_state_not_archive_eligible"), ("pdf_signature_valid", "signature_validation_failed"), ("pdf_parse_valid", "parse_validation_failed"), ("sha256", "sha256_mismatch"), ("file_size_bytes", "file_size_mismatch"), ("page_count", "page_count_mismatch"), ("configured", "archive_root_missing"), ("enabled", "archive_root_disabled"), ("archive_root_id", "archive_root_identity_mismatch"), ("planning_authorized", "planning_not_authorized"), ("audit_sink_available", "audit_capability_unavailable"), ("conflicting_action", "concurrency_conflict"), ("source_evidence_current", "concurrency_evidence_stale"))
    for field, reason in cases:
        objects = _objects()
        target = objects[7] if field in (7, "expected_file_size_bytes", "expected_page_count", "expected_sha256", "new_field") else objects[0] if field == "report_id" else objects[1] if field in ("artifact_state", "pdf_signature_valid", "pdf_parse_valid", "sha256", "file_size_bytes", "page_count") else objects[2] if field in ("configured", "enabled", "archive_root_id") else objects[4] if field == "planning_authorized" else objects[5] if field == "audit_sink_available" else objects[6]
        if field == 7: target["contract_version"] = "unsupported"
        elif field == "new_field": target[field] = True
        elif field == "expected_file_size_bytes": target[field] = True
        elif field == "expected_page_count": target[field] = 0
        elif field == "expected_sha256": target[field] = "A" * 64
        elif field == "report_id": target[field] = "different"
        elif field == "archive_root_id": target[field] = "different"
        elif field == "planning_authorized": target[field] = False
        elif field == "audit_sink_available": target[field] = False
        elif field == "source_evidence_current": target[field] = False
        elif field == "conflicting_action": target[field] = True
        elif field == "configured": target[field] = False
        elif field == "enabled": target[field] = False
        elif field == "artifact_state": target[field] = "ABSENT"
        elif field in ("pdf_signature_valid", "pdf_parse_valid"): target[field] = False
        elif field == "sha256": target[field] = "b" * 64
        elif field == "file_size_bytes": target[field] = 999
        elif field == "page_count": target[field] = 3
        assert _plan(objects)["blocked_reason"] == reason, field


def test_path_policy_and_reserved_names():
    for bad in ("../escape", "a/b", "a\\b", "a:b", "C:drive", "\\\\server", "éclair", "CON.pdf"):
        objects = _objects()
        objects[7]["report_id"] = bad
        objects[0]["report_id"] = bad
        objects[1]["report_id"] = bad
        result = _plan(objects)
        assert result["blocked_reason"] in {"invalid_plan_contract", "invalid_path_component", "non_ascii_path_component", "reserved_path_component"}


def test_static_authority_and_no_runtime_side_effect_surface():
    source = open(__file__.replace("test_button2_governed_internal_pdf_archive_plan_adapter_v1.py", "button2_governed_internal_pdf_archive_plan_adapter_v1.py"), encoding="utf-8").read()
    tree = ast.parse(source)
    prohibited = {"os", "pathlib", "shutil", "tempfile", "subprocess", "flask", "requests", "socket", "sqlite3", "datetime", "random", "uuid"}
    assert not any(isinstance(node, ast.Import) and any(alias.name.split(".")[0] in prohibited for alias in node.names) for node in tree.body)
    assert not any(isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] in prohibited for node in tree.body)
    assert not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"open", "exec", "eval"} for node in ast.walk(tree))
