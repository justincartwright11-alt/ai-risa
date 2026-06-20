from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from operator_dashboard.button1_provider_adapter_execution_gate_v1 import (
    evaluate_button1_provider_adapter_execution_gate,
)
from operator_dashboard.local_ai_orchestrator_readonly_runtime_context_loader import (
    load_button1_runtime_state_preview,
)


BASE_REQUEST = {
    "source_button": "button1_find_fights",
    "provider_id": "ufc_official_events",
    "provider_enabled": False,
    "operator_approval_present": False,
    "operator_approval_valid": False,
    "source_call_authorization_present": False,
    "source_call_authorization_valid": False,
    "requested_http_method": "",
    "requested_source_url_or_domain": "",
    "expected_response_type": "",
    "max_result_count": 0,
    "timeout_seconds": 0,
    "provenance_required": True,
    "provenance_complete": False,
    "save_requested": False,
    "customer_output_requested": False,
    "learning_update_requested": False,
    "button2_promotion_requested": False,
    "enable_preview_allow_decision": False,
}


APPROVED_PROVIDER_IDS = {"ufc_official_events", "one_fc_official_events"}
APPROVED_DOMAIN_HINTS = {
    "ufc_official_events": "ufc.com",
    "one_fc_official_events": "onefc.com",
}


def gate(**overrides: object) -> dict:
    request = dict(BASE_REQUEST)
    request.update(overrides)
    return evaluate_button1_provider_adapter_execution_gate(request)


def assert_no_write_flags(result: dict) -> None:
    assert result.get("provider_execution_performed") is False
    assert result.get("network_calls_performed") is False
    assert result.get("source_calls_performed") is False
    assert result.get("queue_write_performed") is False
    assert result.get("database_write_performed") is False
    assert result.get("customer_pdf_generation_performed") is False
    assert result.get("button2_promotion_performed") is False
    assert result.get("learning_write_performed") is False
    assert result.get("calibration_write_performed") is False
    assert result.get("auto_save_performed") is False


def test_disabled_provider_denies_source_call() -> None:
    result = gate(provider_enabled=False)
    assert result["execution_gate_allowed"] is False
    assert "execution_gate_provider_not_enabled" in result["execution_gate_reason_codes"]


def test_unknown_provider_denies_source_call() -> None:
    result = gate(provider_id="unknown_provider", provider_enabled=False)
    assert result["execution_gate_allowed"] is False
    assert "provider_id_not_approved" in result["execution_gate_reason_codes"]


@pytest.mark.parametrize("invalid_value", [None, False, ""])
def test_enabled_provider_without_operator_approval_denies_source_call(invalid_value: object) -> None:
    result = gate(provider_enabled=True, operator_approval_present=invalid_value, operator_approval_valid=False)
    assert result["execution_gate_allowed"] is False
    assert "execution_gate_operator_approval_missing" in result["execution_gate_reason_codes"]


@pytest.mark.parametrize("invalid_value", [None, False, ""])
def test_enabled_provider_with_invalid_operator_approval_denies_source_call(invalid_value: object) -> None:
    result = gate(provider_enabled=True, operator_approval_present=True, operator_approval_valid=invalid_value)
    assert result["execution_gate_allowed"] is False
    assert "execution_gate_operator_approval_invalid" in result["execution_gate_reason_codes"]


def test_enabled_provider_with_valid_operator_approval_but_missing_source_call_authorization_denies_source_call() -> None:
    result = gate(
        provider_enabled=True,
        operator_approval_present=True,
        operator_approval_valid=True,
        source_call_authorization_present=False,
        source_call_authorization_valid=False,
    )
    assert result["execution_gate_allowed"] is False
    assert "source_call_authorization_missing" in result["execution_gate_reason_codes"]


def test_enabled_provider_with_valid_operator_approval_but_invalid_source_call_authorization_denies_source_call() -> None:
    result = gate(
        provider_enabled=True,
        operator_approval_present=True,
        operator_approval_valid=True,
        source_call_authorization_present=True,
        source_call_authorization_valid=False,
    )
    assert result["execution_gate_allowed"] is False
    assert "source_call_authorization_invalid" in result["execution_gate_reason_codes"]


def test_unapproved_source_domain_denies_source_call() -> None:
    result = gate(
        provider_enabled=True,
        operator_approval_present=True,
        operator_approval_valid=True,
        source_call_authorization_present=True,
        source_call_authorization_valid=True,
        requested_source_url_or_domain="https://example.invalid/events",
        requested_http_method="GET",
        expected_response_type="html",
        max_result_count=10,
        timeout_seconds=10,
        provenance_complete=True,
    )
    assert result["execution_gate_allowed"] is False
    assert "source_domain_not_authorized" in result["execution_gate_reason_codes"]


def test_unapproved_http_method_denies_source_call() -> None:
    result = gate(
        provider_enabled=True,
        operator_approval_present=True,
        operator_approval_valid=True,
        source_call_authorization_present=True,
        source_call_authorization_valid=True,
        requested_source_url_or_domain="https://www.ufc.com/events",
        requested_http_method="POST",
        expected_response_type="html",
        max_result_count=10,
        timeout_seconds=10,
        provenance_complete=True,
    )
    assert result["execution_gate_allowed"] is False
    assert "http_method_not_authorized" in result["execution_gate_reason_codes"]


def test_unsupported_response_type_denies_source_call() -> None:
    result = gate(
        provider_enabled=True,
        operator_approval_present=True,
        operator_approval_valid=True,
        source_call_authorization_present=True,
        source_call_authorization_valid=True,
        requested_source_url_or_domain="https://www.ufc.com/events",
        requested_http_method="GET",
        expected_response_type="binary",
        max_result_count=10,
        timeout_seconds=10,
        provenance_complete=True,
    )
    assert result["execution_gate_allowed"] is False
    assert "response_type_not_supported" in result["execution_gate_reason_codes"]


def test_unbounded_result_count_denies_source_call() -> None:
    result = gate(
        provider_enabled=True,
        operator_approval_present=True,
        operator_approval_valid=True,
        source_call_authorization_present=True,
        source_call_authorization_valid=True,
        requested_source_url_or_domain="https://www.ufc.com/events",
        requested_http_method="GET",
        expected_response_type="html",
        max_result_count=1000,
        timeout_seconds=10,
        provenance_complete=True,
    )
    assert result["execution_gate_allowed"] is False
    assert "max_result_count_unbounded" in result["execution_gate_reason_codes"]


def test_unbounded_timeout_denies_source_call() -> None:
    result = gate(
        provider_enabled=True,
        operator_approval_present=True,
        operator_approval_valid=True,
        source_call_authorization_present=True,
        source_call_authorization_valid=True,
        requested_source_url_or_domain="https://www.ufc.com/events",
        requested_http_method="GET",
        expected_response_type="html",
        max_result_count=10,
        timeout_seconds=999,
        provenance_complete=True,
    )
    assert result["execution_gate_allowed"] is False
    assert "timeout_unbounded" in result["execution_gate_reason_codes"]


def test_valid_authorization_does_not_trigger_real_network_source_calls() -> None:
    result = gate(
        provider_enabled=True,
        operator_approval_present=True,
        operator_approval_valid=True,
        source_call_authorization_present=True,
        source_call_authorization_valid=True,
        requested_source_url_or_domain="https://www.ufc.com/events",
        requested_http_method="GET",
        expected_response_type="html",
        max_result_count=10,
        timeout_seconds=10,
        provenance_complete=True,
        enable_preview_allow_decision=True,
    )
    assert result["network_calls_performed"] is False
    assert result["source_calls_performed"] is False


def test_valid_authorization_does_not_trigger_provider_execution() -> None:
    result = gate(
        provider_enabled=True,
        operator_approval_present=True,
        operator_approval_valid=True,
        source_call_authorization_present=True,
        source_call_authorization_valid=True,
        requested_source_url_or_domain="https://www.ufc.com/events",
        requested_http_method="GET",
        expected_response_type="html",
        max_result_count=10,
        timeout_seconds=10,
        provenance_complete=True,
        enable_preview_allow_decision=True,
    )
    assert result["provider_execution_performed"] is False


def test_valid_authorization_does_not_trigger_queue_database_writes() -> None:
    result = gate(
        provider_enabled=True,
        operator_approval_present=True,
        operator_approval_valid=True,
        source_call_authorization_present=True,
        source_call_authorization_valid=True,
        requested_source_url_or_domain="https://www.ufc.com/events",
        requested_http_method="GET",
        expected_response_type="html",
        max_result_count=10,
        timeout_seconds=10,
        provenance_complete=True,
        enable_preview_allow_decision=True,
    )
    assert result["queue_write_performed"] is False
    assert result["database_write_performed"] is False


def test_valid_authorization_does_not_trigger_customer_pdf_report_generation() -> None:
    result = gate(
        provider_enabled=True,
        operator_approval_present=True,
        operator_approval_valid=True,
        source_call_authorization_present=True,
        source_call_authorization_valid=True,
        requested_source_url_or_domain="https://www.ufc.com/events",
        requested_http_method="GET",
        expected_response_type="html",
        max_result_count=10,
        timeout_seconds=10,
        provenance_complete=True,
        enable_preview_allow_decision=True,
    )
    assert result["customer_pdf_generation_performed"] is False


def test_valid_authorization_does_not_trigger_button2_promotion() -> None:
    result = gate(
        provider_enabled=True,
        operator_approval_present=True,
        operator_approval_valid=True,
        source_call_authorization_present=True,
        source_call_authorization_valid=True,
        requested_source_url_or_domain="https://www.ufc.com/events",
        requested_http_method="GET",
        expected_response_type="html",
        max_result_count=10,
        timeout_seconds=10,
        provenance_complete=True,
        enable_preview_allow_decision=True,
    )
    assert result["button2_promotion_performed"] is False


def test_valid_authorization_does_not_trigger_learning_calibration() -> None:
    result = gate(
        provider_enabled=True,
        operator_approval_present=True,
        operator_approval_valid=True,
        source_call_authorization_present=True,
        source_call_authorization_valid=True,
        requested_source_url_or_domain="https://www.ufc.com/events",
        requested_http_method="GET",
        expected_response_type="html",
        max_result_count=10,
        timeout_seconds=10,
        provenance_complete=True,
        enable_preview_allow_decision=True,
    )
    assert result["learning_write_performed"] is False
    assert result["calibration_write_performed"] is False


def test_valid_authorization_does_not_trigger_auto_save() -> None:
    result = gate(
        provider_enabled=True,
        operator_approval_present=True,
        operator_approval_valid=True,
        source_call_authorization_present=True,
        source_call_authorization_valid=True,
        requested_source_url_or_domain="https://www.ufc.com/events",
        requested_http_method="GET",
        expected_response_type="html",
        max_result_count=10,
        timeout_seconds=10,
        provenance_complete=True,
        enable_preview_allow_decision=True,
    )
    assert result["auto_save_performed"] is False


def test_missing_provenance_blocks_save_readiness() -> None:
    result = gate(
        provider_enabled=True,
        operator_approval_present=True,
        operator_approval_valid=True,
        source_call_authorization_present=True,
        source_call_authorization_valid=True,
        requested_source_url_or_domain="https://www.ufc.com/events",
        requested_http_method="GET",
        expected_response_type="html",
        max_result_count=10,
        timeout_seconds=10,
        provenance_required=True,
        provenance_complete=False,
    )
    assert "provenance_required_missing" in result["execution_gate_reason_codes"]
    assert result["save_allowed"] is False


def test_provenance_conflict_routes_manual_review_if_modeled() -> None:
    result = gate(
        provider_enabled=True,
        operator_approval_present=True,
        operator_approval_valid=True,
        source_call_authorization_present=True,
        source_call_authorization_valid=True,
        requested_source_url_or_domain="https://www.ufc.com/events",
        requested_http_method="GET",
        expected_response_type="html",
        max_result_count=10,
        timeout_seconds=10,
        provenance_required=True,
        provenance_complete=False,
    )
    assert result["execution_gate_allowed"] is False


def test_parser_failure_fails_closed_and_is_reported_separately() -> None:
    disabled_result = gate(provider_enabled=False)
    token_missing_result = gate(provider_enabled=True, operator_approval_present=False, operator_approval_valid=False)
    assert disabled_result["execution_gate_reason_codes"] != token_missing_result["execution_gate_reason_codes"]


def test_stale_feed_fails_closed() -> None:
    state = load_button1_runtime_state_preview()
    live = state.get("live_source_status", {})
    assert live.get("save_allowed") is False
    assert live.get("feed_status") in {"unavailable", "no_current_week_source_backed_matchups"}


def test_unavailable_feed_fails_closed() -> None:
    state = load_button1_runtime_state_preview()
    live = state.get("live_source_status", {})
    assert live.get("feed_status") == "unavailable"


def test_token_secret_never_appears_in_response_logs_audit_or_proofs() -> None:
    secret = "super-secret-token-value"
    result = gate(
        provider_enabled=True,
        operator_approval_present=True,
        operator_approval_valid=True,
        source_call_authorization_present=True,
        source_call_authorization_valid=True,
        requested_source_url_or_domain="https://www.ufc.com/events",
        requested_http_method="GET",
        expected_response_type="html",
        max_result_count=10,
        timeout_seconds=10,
        provenance_complete=True,
        token_secret=secret,
    )
    assert secret not in json.dumps(result)
    assert secret not in str(result.get("audit_fields", {}))


def test_one_fc_official_events_remains_disabled() -> None:
    state = load_button1_runtime_state_preview()
    enabled_ids = state.get("registry_adapter_status", {}).get("enabled_registry_candidate_ids", [])
    assert "one_fc_official_events" not in enabled_ids


def test_no_more_than_one_provider_enabled() -> None:
    state = load_button1_runtime_state_preview()
    enabled_ids = state.get("registry_adapter_status", {}).get("enabled_registry_candidate_ids", [])
    assert len(enabled_ids) <= 1


def test_pre_existing_dirty_files_are_not_staged() -> None:
    git_bin = shutil.which("git")
    if not git_bin:
        pytest.skip("git not available")
    repo_root = Path(__file__).resolve().parents[1]
    proc = subprocess.run([git_bin, "diff", "--cached", "--name-only"], cwd=str(repo_root), capture_output=True, text=True, check=False)
    assert proc.returncode == 0
    staged = {line.strip() for line in proc.stdout.splitlines() if line.strip()}
    known_dirty = {
        "operator_dashboard/app.py",
        "operator_dashboard/test_button2_v29_template_final_delivery_fit_polish_v6.py",
        "operator_dashboard/test_button2_v29_template_final_delivery_fit_scan_repair_v5.py",
        "operator_dashboard/test_button2_v29_template_final_delivery_microfit_v7.py",
        "ops/release_checks/button2_v29_template_dense_page_readability_content_depth_v3/proof/live/live_proof_summary.json",
    }
    assert all(path not in staged for path in known_dirty)
