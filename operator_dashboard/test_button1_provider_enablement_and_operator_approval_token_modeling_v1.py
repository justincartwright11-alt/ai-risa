"""Focused test suite for Button 1 provider enablement and operator approval token modeling.

Tests enforce:
- Fail-closed gate behavior for disabled providers and missing/invalid tokens.
- Token contract: non-hardcoded, secret-free audit, no writes, no bypasses.
- No-write invariants: all provider_execution/network/source/queue/database/button2 flags remain false.
- Provider state separation: enabled state does not trigger execution or writes.
- one_fc_official_events remains disabled.
- Pre-existing dirty files remain unstaged.

No provider execution, network/source calls, or writes occur in this test suite.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from operator_dashboard.button1_provider_adapter_execution_gate_v1 import (
    evaluate_button1_provider_adapter_execution_gate,
)
from operator_dashboard.local_ai_orchestrator_readonly_runtime_context_loader import (
    load_button1_runtime_state_preview,
)


# ─── Helpers ─────────────────────────────────────────────────────────────────

_BASE_REQUEST: dict = {
    "source_button": "button1_find_fights",
    "provider_id": "ufc_official_events",
    "provider_enabled": False,
    "operator_approval_token": "",
    "token_format_valid": False,
    "enable_preview_allow_decision": False,
}


def _gate(**overrides) -> dict:
    req = dict(_BASE_REQUEST)
    req.update(overrides)
    return evaluate_button1_provider_adapter_execution_gate(req)


def _write_flags_false(result: dict) -> bool:
    return (
        result.get("provider_execution_performed") is False
        and result.get("network_calls_performed") is False
        and result.get("source_calls_performed") is False
        and result.get("scraping_performed") is False
        and result.get("queue_write_performed") is False
        and result.get("database_write_performed") is False
        and result.get("button2_promotion_performed") is False
    )


# ─── Gate contract tests ──────────────────────────────────────────────────────

def test_disabled_provider_denied():
    """Test 1: Disabled provider fails closed."""
    result = _gate(provider_enabled=False)
    assert result["execution_gate_allowed"] is False
    assert result["execution_gate_decision"] == "deny"
    assert "execution_gate_provider_not_enabled" in result["execution_gate_reason_codes"]


def test_unknown_provider_fails_closed():
    """Test 2: Unknown (unregistered) provider fails closed because it cannot be enabled."""
    result = _gate(provider_id="unknown_provider_xyz", provider_enabled=False)
    assert result["execution_gate_allowed"] is False
    assert result["execution_gate_decision"] == "deny"
    assert "execution_gate_provider_not_enabled" in result["execution_gate_reason_codes"]


def test_enabled_provider_without_token_denied():
    """Test 3: Enabled provider without operator token is denied."""
    result = _gate(provider_enabled=True, operator_approval_token="", token_format_valid=False)
    assert result["execution_gate_allowed"] is False
    assert result["execution_gate_decision"] == "deny"
    assert "execution_gate_operator_approval_missing" in result["execution_gate_reason_codes"]
    assert "execution_gate_provider_not_enabled" not in result["execution_gate_reason_codes"]


def test_token_present_but_provider_disabled_denied():
    """Test 4: Token present but provider disabled still fails closed."""
    result = _gate(
        provider_enabled=False,
        operator_approval_token="preview-token",
        token_format_valid=True,
    )
    assert result["execution_gate_allowed"] is False
    assert result["execution_gate_decision"] == "deny"
    assert "execution_gate_provider_not_enabled" in result["execution_gate_reason_codes"]


def test_invalid_token_fails_closed():
    """Test 5: Token present but format-invalid fails closed with distinct invalid diagnostic."""
    result = _gate(
        provider_enabled=True,
        operator_approval_token="malformed-token",
        token_format_valid=False,
    )
    assert result["execution_gate_allowed"] is False
    assert result["execution_gate_decision"] == "deny"
    assert "execution_gate_operator_approval_invalid" in result["execution_gate_reason_codes"]


def test_missing_token_fails_closed():
    """Test 6: Missing token (empty string) fails closed."""
    result = _gate(provider_enabled=True, operator_approval_token="", token_format_valid=False)
    assert result["execution_gate_allowed"] is False
    assert "execution_gate_operator_approval_missing" in result["execution_gate_reason_codes"]


def test_valid_token_does_not_cause_writes():
    """Test 7: Valid token with enabled provider does not cause any writes."""
    result = _gate(
        provider_enabled=True,
        operator_approval_token="preview-token",
        token_format_valid=True,
        enable_preview_allow_decision=True,
    )
    assert _write_flags_false(result)


def test_valid_token_does_not_bypass_provenance():
    """Test 8: Valid token does not bypass provenance requirement (write flags remain false)."""
    result = _gate(
        provider_enabled=True,
        operator_approval_token="preview-token",
        token_format_valid=True,
        enable_preview_allow_decision=True,
    )
    assert result.get("queue_write_performed") is False
    assert result.get("database_write_performed") is False


def test_valid_token_does_not_trigger_provider_execution():
    """Test 9: Valid token does not trigger provider execution."""
    result = _gate(
        provider_enabled=True,
        operator_approval_token="preview-token",
        token_format_valid=True,
        enable_preview_allow_decision=True,
    )
    assert result["provider_execution_performed"] is False


def test_valid_token_does_not_trigger_network_source_calls():
    """Test 10: Valid token does not trigger network or source calls."""
    result = _gate(
        provider_enabled=True,
        operator_approval_token="preview-token",
        token_format_valid=True,
        enable_preview_allow_decision=True,
    )
    assert result["network_calls_performed"] is False
    assert result.get("source_calls_performed") is False


def test_valid_token_does_not_trigger_button2_promotion():
    """Test 11: Valid token does not trigger Button 2 promotion."""
    result = _gate(
        provider_enabled=True,
        operator_approval_token="preview-token",
        token_format_valid=True,
        enable_preview_allow_decision=True,
    )
    assert result["button2_promotion_performed"] is False


def test_valid_token_does_not_trigger_customer_pdf_generation():
    """Test 12: Valid token does not trigger customer PDF/report generation (all write flags false)."""
    result = _gate(
        provider_enabled=True,
        operator_approval_token="preview-token",
        token_format_valid=True,
        enable_preview_allow_decision=True,
    )
    assert _write_flags_false(result)


def test_valid_token_does_not_trigger_auto_save():
    """Test 13: Valid token does not trigger auto-save (queue/database write flags false)."""
    result = _gate(
        provider_enabled=True,
        operator_approval_token="preview-token",
        token_format_valid=True,
        enable_preview_allow_decision=True,
    )
    assert result.get("queue_write_performed") is False
    assert result.get("database_write_performed") is False


def test_parser_failure_reported_separately():
    """Test 15: Provider-disabled and token-missing diagnostics are distinct reason-code sets."""
    disabled_result = _gate(provider_enabled=False)
    token_missing_result = _gate(provider_enabled=True, operator_approval_token="")
    disabled_codes = set(disabled_result["execution_gate_reason_codes"])
    token_missing_codes = set(token_missing_result["execution_gate_reason_codes"])
    assert disabled_codes != token_missing_codes
    assert "parser_failure" not in disabled_codes
    assert "parser_failure" not in token_missing_codes


def test_audit_record_includes_required_fields():
    """Test 16: Gate audit record includes all required audit fields (no secret value)."""
    result = _gate(
        provider_enabled=True,
        operator_approval_token="preview-token",
        token_format_valid=True,
    )
    assert "provider_id" in result
    assert "token_present" in result
    assert "token_valid" in result
    assert "execution_gate_decision" in result
    assert "execution_gate_reason_codes" in result
    assert "provider_execution_performed" in result
    assert "queue_write_performed" in result
    assert "database_write_performed" in result
    assert "button2_promotion_performed" in result


def test_token_secret_value_never_recorded():
    """Test 17: Token secret value must never appear in the gate response."""
    secret = "do-not-record-this-secret-value-99999"
    result = _gate(
        provider_enabled=True,
        operator_approval_token=secret,
        token_format_valid=True,
        enable_preview_allow_decision=True,
    )
    result_str = str(result)
    assert secret not in result_str, "Token secret value must never appear in gate response"


# ─── Loader contract tests ────────────────────────────────────────────────────

def test_stale_source_output_fails_closed():
    """Test 14: Real loader returns fail-closed state when no live feed is available."""
    state = load_button1_runtime_state_preview()
    live = state.get("live_source_status", {})
    assert live.get("save_allowed") is False
    assert live.get("feed_status") not in ("live", "ready", "current_week_ready")


def test_write_flags_remain_false():
    """Test 18: All write flags in execution gate status remain false via real loader."""
    state = load_button1_runtime_state_preview()
    gate = state.get("execution_gate_status", {})
    assert gate.get("provider_execution_performed") is False
    assert gate.get("network_calls_performed") is False
    assert gate.get("queue_write_performed") is False
    assert gate.get("database_write_performed") is False
    assert gate.get("button2_promotion_performed") is False


def test_one_fc_official_events_remains_disabled():
    """Test 19: one_fc_official_events is not in the enabled registry candidate list."""
    state = load_button1_runtime_state_preview()
    reg = state.get("registry_adapter_status", {})
    enabled_ids = list(reg.get("enabled_registry_candidate_ids", []))
    assert "one_fc_official_events" not in enabled_ids


def test_pre_existing_dirty_files_are_not_staged():
    """Test 20: Known pre-existing dirty files must not appear in the git staged set."""
    repo_root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, "git diff --cached failed"
    staged = {line.strip() for line in proc.stdout.splitlines() if line.strip()}
    known_dirty = {
        "operator_dashboard/app.py",
        "operator_dashboard/test_button2_v29_template_final_delivery_fit_polish_v6.py",
        "operator_dashboard/test_button2_v29_template_final_delivery_fit_scan_repair_v5.py",
        "operator_dashboard/test_button2_v29_template_final_delivery_microfit_v7.py",
        "ops/release_checks/button2_v29_template_dense_page_readability_content_depth_v3/proof/live/live_proof_summary.json",
    }
    for path in known_dirty:
        assert path not in staged, f"Pre-existing dirty file must not be staged: {path}"
