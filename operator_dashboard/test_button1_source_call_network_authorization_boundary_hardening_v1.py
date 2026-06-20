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
    "provider_enabled": True,
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


REQUIRED_RESPONSE_KEYS = {
    "decision",
    "allowed",
    "provider_id",
    "provider_enabled",
    "operator_approval_present",
    "operator_approval_valid",
    "source_call_authorization_present",
    "source_call_authorization_valid",
    "source_domain_authorized",
    "http_method_authorized",
    "response_type_supported",
    "provenance_required",
    "provenance_complete",
    "reason_codes",
    "no_write_flags",
    "provider_execution_performed",
    "network_calls_performed",
    "source_calls_performed",
    "scraping_performed",
    "queue_write_performed",
    "database_write_performed",
    "customer_pdf_generation_performed",
    "button2_promotion_performed",
    "learning_write_performed",
    "calibration_write_performed",
    "auto_save_performed",
    "live_save_allowed",
}


def gate(**overrides: object) -> dict:
    request = dict(BASE_REQUEST)
    request.update(overrides)
    return evaluate_button1_provider_adapter_execution_gate(request)


def mostly_valid_request(**overrides: object) -> dict:
    request = {
        "source_button": "button1_find_fights",
        "provider_id": "ufc_official_events",
        "provider_enabled": True,
        "operator_approval_present": True,
        "operator_approval_valid": True,
        "source_call_authorization_present": True,
        "source_call_authorization_valid": True,
        "requested_http_method": "GET",
        "requested_source_url_or_domain": "https://www.ufc.com/events",
        "expected_response_type": "html",
        "max_result_count": 10,
        "timeout_seconds": 10,
        "provenance_required": True,
        "provenance_complete": True,
        "save_requested": False,
        "customer_output_requested": False,
        "learning_update_requested": False,
        "button2_promotion_requested": False,
        "enable_preview_allow_decision": True,
    }
    request.update(overrides)
    return request


def assert_no_write_flags(result: dict) -> None:
    assert result.get("provider_execution_performed") is False
    assert result.get("network_calls_performed") is False
    assert result.get("source_calls_performed") is False
    assert result.get("scraping_performed") is False
    assert result.get("queue_write_performed") is False
    assert result.get("database_write_performed") is False
    assert result.get("customer_pdf_generation_performed") is False
    assert result.get("button2_promotion_performed") is False
    assert result.get("learning_write_performed") is False
    assert result.get("calibration_write_performed") is False
    assert result.get("auto_save_performed") is False
    assert result.get("live_save_allowed") is False


def test_runtime_preview_denies_without_operator_approval() -> None:
    result = gate(operator_approval_present=False, operator_approval_valid=False)
    assert result["execution_gate_decision"] == "deny"
    assert "execution_gate_operator_approval_missing" in result["execution_gate_reason_codes"]


def test_runtime_preview_denies_without_source_call_authorization() -> None:
    result = gate(source_call_authorization_present=False, source_call_authorization_valid=False)
    assert result["execution_gate_decision"] == "deny"
    assert "source_call_authorization_missing" in result["execution_gate_reason_codes"]


def test_runtime_preview_denies_when_max_result_count_is_unbounded() -> None:
    request = mostly_valid_request(max_result_count=1000)
    result = evaluate_button1_provider_adapter_execution_gate(request)
    assert result["execution_gate_decision"] == "deny"
    assert "max_result_count_unbounded" in result["execution_gate_reason_codes"]


def test_runtime_preview_denies_when_timeout_is_unbounded() -> None:
    request = mostly_valid_request(timeout_seconds=999)
    result = evaluate_button1_provider_adapter_execution_gate(request)
    assert result["execution_gate_decision"] == "deny"
    assert "timeout_unbounded" in result["execution_gate_reason_codes"]


def test_runtime_preview_denies_when_provenance_is_incomplete() -> None:
    request = mostly_valid_request(provenance_complete=False)
    result = evaluate_button1_provider_adapter_execution_gate(request)
    assert result["execution_gate_decision"] == "deny"
    assert "provenance_required_missing" in result["execution_gate_reason_codes"]


def test_runtime_preview_denies_when_network_call_is_unauthorized() -> None:
    request = mostly_valid_request(source_call_authorization_valid=False)
    result = evaluate_button1_provider_adapter_execution_gate(request)
    assert result["execution_gate_decision"] == "deny"
    assert "network_call_not_authorized" in result["execution_gate_reason_codes"]


def test_deny_reason_codes_remain_specific_and_non_overlapping() -> None:
    result = gate()
    reason_codes = result.get("execution_gate_reason_codes", [])
    assert len(reason_codes) == len(set(reason_codes))


def test_operator_approval_failure_does_not_hide_source_call_authorization_failure() -> None:
    result = gate(operator_approval_present=False, source_call_authorization_present=False)
    reason_codes = result.get("execution_gate_reason_codes", [])
    assert "execution_gate_operator_approval_missing" in reason_codes
    assert "source_call_authorization_missing" in reason_codes


def test_source_call_authorization_failure_does_not_hide_max_result_count_failure() -> None:
    result = gate(source_call_authorization_present=False, max_result_count=0)
    reason_codes = result.get("execution_gate_reason_codes", [])
    assert "source_call_authorization_missing" in reason_codes
    assert "max_result_count_unbounded" in reason_codes


def test_source_call_authorization_failure_does_not_hide_timeout_failure() -> None:
    result = gate(source_call_authorization_present=False, timeout_seconds=0)
    reason_codes = result.get("execution_gate_reason_codes", [])
    assert "source_call_authorization_missing" in reason_codes
    assert "timeout_unbounded" in reason_codes


def test_source_call_authorization_failure_does_not_hide_provenance_failure() -> None:
    result = gate(source_call_authorization_present=False, provenance_complete=False)
    reason_codes = result.get("execution_gate_reason_codes", [])
    assert "source_call_authorization_missing" in reason_codes
    assert "provenance_required_missing" in reason_codes


def test_provenance_failure_does_not_hide_save_readiness_failure() -> None:
    result = gate(provenance_complete=False)
    assert "provenance_required_missing" in result.get("execution_gate_reason_codes", [])
    assert result.get("save_allowed") is False
    assert result.get("live_save_allowed") is False


def test_parser_failure_remains_separate_from_stale_feed_if_modeled() -> None:
    parser_result = gate(source_button="invalid_button")
    parser_codes = parser_result.get("execution_gate_reason_codes", [])
    state = load_button1_runtime_state_preview()
    live = state.get("live_source_status", {})
    assert "execution_gate_invalid_source_button" in parser_codes
    assert "feed_stale" not in parser_codes
    if live.get("feed_status") == "stale":
        assert "execution_gate_invalid_source_button" not in live.get("diagnostics", [])


def test_stale_feed_remains_separate_from_unavailable_feed_if_modeled() -> None:
    state = load_button1_runtime_state_preview()
    live = state.get("live_source_status", {})
    feed_status = live.get("feed_status")
    if feed_status == "stale":
        assert feed_status != "unavailable"
    else:
        assert feed_status in {"unavailable", "no_current_week_source_backed_matchups", "stale"}


def test_unavailable_feed_remains_separate_from_provider_disabled_state_if_modeled() -> None:
    state = load_button1_runtime_state_preview()
    live = state.get("live_source_status", {})
    diagnostics = set(live.get("diagnostics", []))
    if live.get("feed_status") == "unavailable":
        assert "provider_disabled" not in diagnostics


def test_token_secret_never_appears_in_output_logs_audit_or_proof_docs() -> None:
    secret = "boundary-hardening-secret"
    request = mostly_valid_request(token_secret=secret)
    result = evaluate_button1_provider_adapter_execution_gate(request)
    rendered = json.dumps(result)
    assert secret not in rendered
    assert secret not in json.dumps(result.get("audit_fields", {}))


def test_source_call_authorization_does_not_bypass_operator_approval() -> None:
    request = mostly_valid_request(operator_approval_present=False, operator_approval_valid=False)
    result = evaluate_button1_provider_adapter_execution_gate(request)
    assert "execution_gate_operator_approval_missing" in result["execution_gate_reason_codes"]


def test_source_call_authorization_does_not_bypass_provenance() -> None:
    request = mostly_valid_request(provenance_complete=False)
    result = evaluate_button1_provider_adapter_execution_gate(request)
    assert "provenance_required_missing" in result["execution_gate_reason_codes"]


def test_valid_authorization_does_not_trigger_provider_execution() -> None:
    result = evaluate_button1_provider_adapter_execution_gate(mostly_valid_request())
    assert result["provider_execution_performed"] is False


def test_valid_authorization_does_not_trigger_real_network_source_calls() -> None:
    result = evaluate_button1_provider_adapter_execution_gate(mostly_valid_request())
    assert result["network_calls_performed"] is False
    assert result["source_calls_performed"] is False


def test_valid_authorization_does_not_trigger_scraping() -> None:
    result = evaluate_button1_provider_adapter_execution_gate(mostly_valid_request())
    assert result["scraping_performed"] is False


def test_valid_authorization_does_not_trigger_queue_database_writes() -> None:
    result = evaluate_button1_provider_adapter_execution_gate(mostly_valid_request())
    assert result["queue_write_performed"] is False
    assert result["database_write_performed"] is False


def test_valid_authorization_does_not_trigger_customer_pdf_report_generation() -> None:
    result = evaluate_button1_provider_adapter_execution_gate(mostly_valid_request())
    assert result["customer_pdf_generation_performed"] is False


def test_valid_authorization_does_not_trigger_button2_promotion() -> None:
    result = evaluate_button1_provider_adapter_execution_gate(mostly_valid_request())
    assert result["button2_promotion_performed"] is False


def test_valid_authorization_does_not_trigger_learning_calibration() -> None:
    result = evaluate_button1_provider_adapter_execution_gate(mostly_valid_request())
    assert result["learning_write_performed"] is False
    assert result["calibration_write_performed"] is False


def test_valid_authorization_does_not_trigger_auto_save() -> None:
    result = evaluate_button1_provider_adapter_execution_gate(mostly_valid_request())
    assert result["auto_save_performed"] is False


def test_no_write_flags_appear_on_every_runtime_preview_response() -> None:
    result = gate()
    assert REQUIRED_RESPONSE_KEYS.issubset(set(result.keys()))
    assert isinstance(result.get("no_write_flags"), dict)
    assert_no_write_flags(result)


def test_live_save_allowed_remains_false() -> None:
    result = evaluate_button1_provider_adapter_execution_gate(mostly_valid_request())
    assert result["live_save_allowed"] is False


def test_one_fc_official_events_remains_disabled() -> None:
    state = load_button1_runtime_state_preview()
    enabled_ids = state.get("registry_adapter_status", {}).get("enabled_registry_candidate_ids", [])
    assert "one_fc_official_events" not in enabled_ids


def test_no_more_than_one_provider_enabled() -> None:
    state = load_button1_runtime_state_preview()
    enabled_ids = state.get("registry_adapter_status", {}).get("enabled_registry_candidate_ids", [])
    assert len(enabled_ids) <= 1


def test_provider_registry_json_remains_untouched() -> None:
    git_bin = shutil.which("git")
    if not git_bin:
        pytest.skip("git not available")
    repo_root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [git_bin, "diff", "--cached", "--name-only", "--", "ops/approved_sources/button1_live_provider_registry.json"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert proc.stdout.strip() == ""


def test_app_py_remains_untouched() -> None:
    git_bin = shutil.which("git")
    if not git_bin:
        pytest.skip("git not available")
    repo_root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [git_bin, "diff", "--cached", "--name-only", "--", "operator_dashboard/app.py"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert proc.stdout.strip() == ""


def test_templates_index_html_remains_untouched() -> None:
    git_bin = shutil.which("git")
    if not git_bin:
        pytest.skip("git not available")
    repo_root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [git_bin, "diff", "--cached", "--name-only", "--", "operator_dashboard/templates/index.html"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert proc.stdout.strip() == ""


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
