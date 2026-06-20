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


EXPECTED_BLOCKER_CODES = [
    "execution_gate_operator_approval_missing",
    "source_call_authorization_missing",
    "max_result_count_unbounded",
    "timeout_unbounded",
    "provenance_required_missing",
    "network_call_not_authorized",
]


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


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _run_git(*args: str) -> subprocess.CompletedProcess[str]:
    git_bin = shutil.which("git")
    if not git_bin:
        pytest.skip("git not available")
    return subprocess.run(
        [git_bin, *args],
        cwd=str(_repo_root()),
        capture_output=True,
        text=True,
        check=False,
    )


def _baseline_request(**overrides: object) -> dict:
    request = {
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
    request.update(overrides)
    return request


def _baseline_gate_result(**overrides: object) -> dict:
    return evaluate_button1_provider_adapter_execution_gate(_baseline_request(**overrides))


def _preview_execution_gate() -> dict:
    state = load_button1_runtime_state_preview(workspace_root=str(_repo_root()))
    return state.get("execution_gate_status", {})


def test_current_reason_code_set_remains_visible() -> None:
    result = _baseline_gate_result()
    reason_codes = result.get("execution_gate_reason_codes", [])
    for code in EXPECTED_BLOCKER_CODES:
        assert code in reason_codes


def test_reason_code_ordering_is_deterministic() -> None:
    first = _baseline_gate_result().get("execution_gate_reason_codes", [])
    second = _baseline_gate_result().get("execution_gate_reason_codes", [])
    assert first == EXPECTED_BLOCKER_CODES
    assert second == EXPECTED_BLOCKER_CODES


def test_no_write_flags_remain_present() -> None:
    gate = _preview_execution_gate()
    assert isinstance(gate.get("no_write_flags"), dict)
    assert gate.get("no_write_flags")


def test_live_save_allowed_remains_false() -> None:
    gate = _preview_execution_gate()
    assert gate.get("live_save_allowed") is False


def test_token_secret_absent_from_runtime_output() -> None:
    secret = "normalization-secret-marker"
    result = _baseline_gate_result(token_secret=secret)
    rendered = json.dumps(result)
    assert secret not in rendered


def test_no_provider_execution_occurs() -> None:
    gate = _preview_execution_gate()
    assert gate.get("provider_execution_performed") is False


def test_no_network_or_source_calls_occur() -> None:
    gate = _preview_execution_gate()
    assert gate.get("network_calls_performed") is False
    assert gate.get("source_calls_performed") is False


def test_no_scraping_occurs() -> None:
    gate = _preview_execution_gate()
    assert gate.get("scraping_performed") is False


def test_no_writes_occur() -> None:
    gate = _preview_execution_gate()
    assert gate.get("queue_write_performed") is False
    assert gate.get("database_write_performed") is False


def test_no_button2_promotion_occurs() -> None:
    gate = _preview_execution_gate()
    assert gate.get("button2_promotion_performed") is False


def test_no_customer_output_occurs() -> None:
    gate = _preview_execution_gate()
    assert gate.get("customer_pdf_generation_performed") is False


def test_no_learning_or_calibration_occurs() -> None:
    gate = _preview_execution_gate()
    assert gate.get("learning_write_performed") is False
    assert gate.get("calibration_write_performed") is False


def test_one_fc_official_events_remains_disabled() -> None:
    state = load_button1_runtime_state_preview(workspace_root=str(_repo_root()))
    enabled_ids = state.get("registry_adapter_status", {}).get("enabled_registry_candidate_ids", [])
    assert "one_fc_official_events" not in enabled_ids


def test_no_more_than_one_provider_enabled() -> None:
    state = load_button1_runtime_state_preview(workspace_root=str(_repo_root()))
    enabled_ids = state.get("registry_adapter_status", {}).get("enabled_registry_candidate_ids", [])
    assert len(enabled_ids) <= 1


def test_provider_registry_json_remains_untouched() -> None:
    proc = _run_git("diff", "--cached", "--name-only", "--", "ops/approved_sources/button1_live_provider_registry.json")
    assert proc.returncode == 0
    assert proc.stdout.strip() == ""


def test_app_py_remains_untouched() -> None:
    proc = _run_git("diff", "--cached", "--name-only", "--", "operator_dashboard/app.py")
    assert proc.returncode == 0
    assert proc.stdout.strip() == ""


def test_templates_index_html_remains_untouched() -> None:
    proc = _run_git("diff", "--cached", "--name-only", "--", "operator_dashboard/templates/index.html")
    assert proc.returncode == 0
    assert proc.stdout.strip() == ""


def test_orchestrator_file_remains_untouched() -> None:
    proc = _run_git(
        "diff",
        "--cached",
        "--name-only",
        "--",
        "operator_dashboard/button1_live_source_provider_orchestrator_v1.py",
    )
    assert proc.returncode == 0
    assert proc.stdout.strip() == ""


def test_registration_adapter_file_remains_untouched() -> None:
    proc = _run_git(
        "diff",
        "--cached",
        "--name-only",
        "--",
        "operator_dashboard/button1_config_registration_to_orchestrator_registry_adapter_v1.py",
    )
    assert proc.returncode == 0
    assert proc.stdout.strip() == ""


def test_pre_existing_dirty_files_are_not_staged() -> None:
    proc = _run_git("diff", "--cached", "--name-only")
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


def test_response_contract_preserves_all_required_fields() -> None:
    result = _baseline_gate_result()
    assert REQUIRED_RESPONSE_KEYS.issubset(result.keys())


def test_normalization_does_not_remove_any_current_blocker() -> None:
    reason_codes = _baseline_gate_result().get("execution_gate_reason_codes", [])
    assert set(EXPECTED_BLOCKER_CODES).issubset(set(reason_codes))


def test_normalization_does_not_change_deny_decision() -> None:
    result = _baseline_gate_result()
    assert result.get("decision") == "deny"
    assert result.get("allowed") is False


def test_normalization_does_not_set_live_save_allowed_true() -> None:
    result = _baseline_gate_result()
    assert result.get("live_save_allowed") is False
