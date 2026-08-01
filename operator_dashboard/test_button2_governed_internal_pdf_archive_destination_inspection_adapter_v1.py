from __future__ import annotations

import ast
import copy
import hashlib
from pathlib import Path

from operator_dashboard.button2_governed_internal_pdf_archive_destination_inspection_adapter_v1 import (
    COMPOSITE_VERSION,
    DESTINATION_VERSION,
    FILESYSTEM_VERSION,
    IDENTITY_VERSION,
    PARSER_CAPABILITY_VERSION,
    inspect_button2_governed_internal_pdf_archive_destination_v1,
)


PDF_BYTES = b"%PDF-1.7\ninternal test fixture\n"


def _request(*, fixture_id="fixture_v1"):
    return {
        "contract_version": "button2-governed-internal-pdf-destination-inspection-v1",
        "requested_action": "inspect_internal_pdf_archive_destination",
        "fixture_id": fixture_id,
        "report_id": "report_v1",
        "report_version": "DRAFT_v1",
        "expected_filename": "report.pdf",
        "expected_sha256": hashlib.sha256(PDF_BYTES).hexdigest(),
        "expected_file_size_bytes": len(PDF_BYTES),
        "expected_page_count": 1,
        "source_boundary_id": "source-boundary",
        "archive_root_id": "archive-root",
        "archive_root_version": "v1",
        "archive_policy_id": "retain-internal-test-v1",
        "archive_boundary_id": "archive-boundary",
        "destination_relative_id": f"{fixture_id}/report_v1/DRAFT_v1/report.pdf",
        "request_id": "request-1",
        "idempotency_key": "idempotency-1",
    }


def _source(request):
    return {
        "inspection_contract_version": "button2-governed-internal-pdf-artifact-inspection-v1",
        "inspection_completed": True,
        "artifact_state": "ACTIVE_INTERNAL_TEST_ARTIFACT",
        "fixture_id": request["fixture_id"],
        "report_id": request["report_id"],
        "report_version": request["report_version"],
        "expected_filename": request["expected_filename"],
        "observed_filename": request["expected_filename"],
        "sha256": request["expected_sha256"],
        "file_size_bytes": len(PDF_BYTES),
        "page_count": 1,
        "pdf_signature_valid": True,
        "pdf_parse_valid": True,
        "identity_valid": True,
        "classification_valid": True,
        "internal_warning_valid": True,
        "source_boundary_id": request["source_boundary_id"],
        "source_identity": {"volume_identifier": "source-volume", "file_identifier": "source-file"},
        "source_artifact_version_token": "source-version-1",
        "customer_ready_possible": False,
        "customer_release_authorized": False,
        "queue_write_performed": False,
        "pdf_generation_performed": False,
        "artifact_archived": False,
        "artifact_removed": False,
        "artifact_overwritten": False,
        "permanent_mutation_performed": False,
        "action_performed": False,
    }


def _capability(tmp_path, request, *, parser=None, identity=None):
    root = tmp_path / "archive"
    target_parent = root / request["fixture_id"] / request["report_id"] / request["report_version"]
    target_parent.mkdir(parents=True)
    target = target_parent / request["expected_filename"]

    def identity_observer(path):
        if identity is not None:
            return identity
        return {"identity_completed": True, "identity_supported": True, "volume_identifier": "archive-volume", "file_identifier": "archive-file", "identity_version_token": "destination-identity-1"}

    metadata = {
        "contract_version": "button2-governed-internal-pdf-archive-destination-trusted-metadata-v1",
        "action_performed": False,
        "fixture_id": request["fixture_id"], "report_id": request["report_id"], "report_version": request["report_version"],
        "filename": request["expected_filename"], "sha256": request["expected_sha256"], "file_size_bytes": len(PDF_BYTES), "page_count": 1,
        "request_id": request["request_id"], "idempotency_key": request["idempotency_key"],
        "classification": "governed_internal_test_pdf", "internal_warning": "INTERNAL TEST FIXTURE NOT FOR CUSTOMER RELEASE",
        "provenance_verified": True, "provenance_fixture_bound": True,
        "archive_root_id": request["archive_root_id"], "archive_root_version": request["archive_root_version"],
        "destination_evidence_version_token": "destination-evidence-1", "evaluated_at": "2099-01-01T00:00:00Z",
    }

    def default_parser(target_path, parser_request):
        return {
            "contract_version": "button2-governed-internal-pdf-archive-destination-parser-result-v1",
            "ok": True, "status": "PARSER_RESULT_COMPLETE", "inspection_completed": True,
            "fixture_id": parser_request["fixture_id"], "report_id": parser_request["report_id"], "report_version": parser_request["report_version"],
            "expected_filename": parser_request["expected_filename"], "destination_relative_id": parser_request["destination_relative_id"],
            "destination_identity_version_token": parser_request["destination_identity_version_token"],
            "request_id": parser_request["request_id"], "idempotency_key": parser_request["idempotency_key"],
            "observed_page_count": 1, "network_access_performed": False, "filesystem_write_performed": False,
            "rendering_performed": False, "action_performed": False,
        }

    parser = parser or default_parser
    capability = {
        "capability_contract_version": COMPOSITE_VERSION, "capability_id": "capability-1",
        "archive_root_id": request["archive_root_id"], "archive_root_version": request["archive_root_version"],
        "archive_policy_id": request["archive_policy_id"], "archive_boundary_id": request["archive_boundary_id"],
        "platform": "windows", "filesystem_policy_id": "button2-governed-internal-pdf-archive-destination-windows-filesystem-policy-v1",
        "sanitization_policy_id": "ascii-reject-v1", "configured": True, "enabled": True, "server_controlled": True,
        "customer_isolated": True, "source_isolated": True, "action_performed": False,
        "internal_test_only": True, "fixture_only": True, "production_capable": False,
        "capability_source_id": "test-capability-source", "capability_source_version": "v1",
        "expiry_or_validity_evidence": "valid", "root_configuration_fingerprint": "root-fingerprint",
        "root_identity": {"identity_completed": True, "identity_supported": True}, "root_target": root,
        "root_observer": lambda path: False, "filesystem_observer": lambda path: False,
        "identity_observer": identity_observer,
        "parser_capability": {"capability_contract_version": PARSER_CAPABILITY_VERSION, "enabled": True, "supported": True, "internal_test_only": True, "fixture_only": True, "production_capable": False, "parser": parser, "trusted_metadata": metadata},
        "safety_flags": {name: False for name in ("customer_ready_possible", "customer_release_authorized", "queue_write_performed", "pdf_generation_performed", "learning_applied", "calibration_applied", "accuracy_ledger_written", "gcid_written", "model_weights_changed", "fighter_ratings_changed", "prediction_logic_changed", "artifact_archived", "artifact_removed", "artifact_overwritten", "permanent_mutation_performed", "action_performed")},
    }
    return capability, target


def test_absent_target_is_complete_and_does_not_invoke_parser(tmp_path):
    request = _request()
    source = _source(request)
    called = []

    def parser(*args):
        called.append(args)
        return {}

    capability, target = _capability(tmp_path, request, parser=parser)
    result = inspect_button2_governed_internal_pdf_archive_destination_v1(capability, source, request)
    assert result["status"] == "DESTINATION_INSPECTION_COMPLETE"
    assert result["destination_status"] == "DESTINATION_ABSENT"
    assert result["inspection_completed"] is True
    assert called == []
    assert not target.exists()
    assert all(value is False for value in result["safety_flags"].values())


def test_identical_archive_is_bounded_and_deterministic(tmp_path):
    request = _request()
    source = _source(request)
    capability, target = _capability(tmp_path, request)
    target.write_bytes(PDF_BYTES)
    before = (copy.deepcopy(capability), copy.deepcopy(source), copy.deepcopy(request))
    first = inspect_button2_governed_internal_pdf_archive_destination_v1(capability, source, request)
    second = inspect_button2_governed_internal_pdf_archive_destination_v1(capability, source, request)
    assert first == second
    assert first["destination_status"] == "IDENTICAL_ARCHIVE_PRESENT"
    assert first["ok"] is True
    assert all("\\" not in str(value) and str(tmp_path) not in str(value) for value in first.values())
    assert (capability, source, request) == before
    assert target.read_bytes() == PDF_BYTES


def test_first_failure_and_parser_prohibitions(tmp_path):
    request = _request()
    source = _source(request)
    called = []

    def parser(*args):
        called.append(args)
        return {}

    capability, target = _capability(tmp_path, request, parser=parser)
    invalid = dict(request)
    invalid["unexpected"] = True
    assert inspect_button2_governed_internal_pdf_archive_destination_v1(capability, source, invalid)["blocked_reason"] == "unexpected_destination_inspection_fields"
    target.write_bytes(b"not-pdf")
    assert inspect_button2_governed_internal_pdf_archive_destination_v1(capability, source, request)["blocked_reason"] == "pdf_signature_validation_failed"
    assert called == []


def test_same_identity_and_unsupported_platform_fail_closed(tmp_path):
    request = _request()
    source = _source(request)
    same = {"identity_completed": True, "identity_supported": True, "volume_identifier": "source-volume", "file_identifier": "source-file", "identity_version_token": "same"}
    capability, target = _capability(tmp_path, request, identity=same)
    target.write_bytes(PDF_BYTES)
    result = inspect_button2_governed_internal_pdf_archive_destination_v1(capability, source, request)
    assert result["blocked_reason"] == "source_destination_same"
    capability["platform"] = "linux"
    assert inspect_button2_governed_internal_pdf_archive_destination_v1(capability, source, request)["status"] == "DESTINATION_INSPECTION_UNSUPPORTED_PLATFORM"


def test_static_authority_surface_is_bounded():
    source = Path(__file__).with_name("button2_governed_internal_pdf_archive_destination_inspection_adapter_v1.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    prohibited = {"mkdir", "makedirs", "touch", "unlink", "remove", "rmdir", "rename", "replace", "copy", "move", "truncate", "subprocess", "eval", "exec"}
    calls = {node.func.attr for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
    assert not calls & prohibited
    assert "inspect_button2_governed_internal_pdf_archive_destination_v1" in {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
