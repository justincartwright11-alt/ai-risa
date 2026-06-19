from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from operator_dashboard.local_ai_orchestrator_gate1_save_fights_dry_run_apply_preview import (
    run_gate1_save_fights_dry_run_apply_preview,
)
from operator_dashboard.local_ai_orchestrator_readonly_runtime_context_loader import (
    load_button1_runtime_state_preview,
)


def _provider(*, provider_id: str, provider_name: str, enabled: bool, include_approval: bool = True) -> dict:
    provider = {
        "provider_id": provider_id,
        "provider_name": provider_name,
        "provider_type": "official",
        "enabled": enabled,
        "source_tier": "official_promotion",
        "allowed_domains": ["example.com"],
        "endpoint_or_feed_location": "https://example.com/events",
        "auth_required": False,
        "refresh_cadence_minutes": 120,
        "max_feed_age_hours": 24,
        "ruleset_scope": ["event_card_discovery"],
        "promotion_scope": ["Example"],
        "region_scope": ["global"],
        "output_schema_version": "button1_live_provider_registry_v1",
        "provenance_notes": "test",
    }
    if include_approval:
        provider["operator_approved_by"] = "operator@example.com"
        provider["approval_timestamp_utc"] = "2026-06-18T00:00:00Z"
    return provider


def _write_registry(workspace_root: Path, providers: list[dict]) -> None:
    reg_path = workspace_root / "ops" / "approved_sources" / "button1_live_provider_registry.json"
    reg_path.parent.mkdir(parents=True, exist_ok=True)
    reg_path.write_text(
        json.dumps({"schema_version": "button1_live_provider_registry_v1", "providers": providers}, indent=2),
        encoding="utf-8",
    )


def _load_preview(workspace_root: Path) -> dict:
    return load_button1_runtime_state_preview(workspace_root=str(workspace_root))


def test_empty_provider_registry_returns_no_approved_live_source_provider_configured(tmp_path: Path):
    _write_registry(tmp_path, [])
    state = _load_preview(tmp_path)
    live = state["live_source_status"]

    assert "no_approved_live_source_provider_configured" in live.get("diagnostics", [])
    assert live.get("feed_status") == "unavailable"
    assert live.get("save_allowed") is False


def test_registry_with_both_providers_disabled_returns_no_enabled_provider(tmp_path: Path):
    _write_registry(
        tmp_path,
        [
            _provider(provider_id="ufc_official_events", provider_name="UFC Official Events", enabled=False),
            _provider(provider_id="one_fc_official_events", provider_name="ONE Championship Official Events", enabled=False),
        ],
    )
    state = _load_preview(tmp_path)

    assert "no_enabled_provider" in state["registry_adapter_status"].get("diagnostics", [])
    assert "no_enabled_provider" in state["live_source_status"].get("diagnostics", [])


def test_disabled_ufc_official_events_remains_denied(tmp_path: Path):
    _write_registry(
        tmp_path,
        [
            _provider(provider_id="ufc_official_events", provider_name="UFC Official Events", enabled=False),
            _provider(provider_id="one_fc_official_events", provider_name="ONE Championship Official Events", enabled=False),
        ],
    )
    state = _load_preview(tmp_path)
    gate = state["execution_gate_status"]

    assert gate.get("provider_id") == "ufc_official_events"
    assert gate.get("execution_gate_allowed") is False
    assert "execution_gate_provider_not_enabled" in gate.get("execution_gate_reason_codes", [])


def test_enabled_provider_without_operator_approval_remains_denied(tmp_path: Path):
    _write_registry(
        tmp_path,
        [_provider(provider_id="ufc_official_events", provider_name="UFC Official Events", enabled=True, include_approval=False)],
    )
    state = _load_preview(tmp_path)
    gate = state["execution_gate_status"]

    assert gate.get("execution_gate_allowed") is False
    assert "execution_gate_operator_approval_missing" in gate.get("execution_gate_reason_codes", [])


def test_operator_approval_missing_returns_execution_gate_operator_approval_missing(tmp_path: Path):
    _write_registry(
        tmp_path,
        [_provider(provider_id="ufc_official_events", provider_name="UFC Official Events", enabled=False)],
    )
    state = _load_preview(tmp_path)
    gate = state["execution_gate_status"]

    assert "execution_gate_operator_approval_missing" in gate.get("execution_gate_reason_codes", [])


def test_provider_not_enabled_returns_execution_gate_provider_not_enabled(tmp_path: Path):
    _write_registry(
        tmp_path,
        [_provider(provider_id="ufc_official_events", provider_name="UFC Official Events", enabled=False)],
    )
    state = _load_preview(tmp_path)
    gate = state["execution_gate_status"]

    assert "execution_gate_provider_not_enabled" in gate.get("execution_gate_reason_codes", [])


def test_registry_candidates_flow_into_orchestrator_preview_when_present(tmp_path: Path):
    _write_registry(
        tmp_path,
        [
            _provider(provider_id="ufc_official_events", provider_name="UFC Official Events", enabled=False),
            _provider(provider_id="one_fc_official_events", provider_name="ONE Championship Official Events", enabled=False),
        ],
    )
    state = _load_preview(tmp_path)
    live = state["live_source_status"]

    assert live.get("provider_count") == 2
    assert "UFC Official Events" in live.get("provider_names", [])
    assert "ONE Championship Official Events" in live.get("provider_names", [])


def test_orchestrator_preview_does_not_write_queue_or_database(tmp_path: Path):
    _write_registry(tmp_path, [_provider(provider_id="ufc_official_events", provider_name="UFC Official Events", enabled=False)])
    state = _load_preview(tmp_path)
    live = state["live_source_status"]

    assert live.get("queue_write_performed") is False
    assert live.get("database_write_performed") is False


def test_button2_promotion_remains_false(tmp_path: Path):
    _write_registry(tmp_path, [_provider(provider_id="ufc_official_events", provider_name="UFC Official Events", enabled=False)])
    state = _load_preview(tmp_path)

    assert state["execution_gate_status"].get("button2_promotion_performed") is False


def test_customer_pdf_generation_remains_false(tmp_path: Path):
    _write_registry(tmp_path, [_provider(provider_id="ufc_official_events", provider_name="UFC Official Events", enabled=False)])
    state = _load_preview(tmp_path)

    # No customer-PDF generation path is exposed in preview state; fail closed to False.
    assert state.get("customer_pdf_generation_performed", False) is False


def test_learning_and_calibration_writes_remain_false(tmp_path: Path):
    _write_registry(tmp_path, [_provider(provider_id="ufc_official_events", provider_name="UFC Official Events", enabled=False)])
    state = _load_preview(tmp_path)

    assert state.get("learning_write_performed", False) is False
    assert state.get("calibration_write_performed", False) is False


def test_source_backed_preview_rows_remain_blocked_if_provenance_missing():
    result = run_gate1_save_fights_dry_run_apply_preview(
        gate_approval_token_preview={},
        candidate_rows=[{"candidate_id": "cand-1", "event_name": "UFC Event", "source_url": ""}],
    )

    assert result.provenance_missing_count >= 1
    assert "cand-1" in result.blocked_candidate_ids


def test_stale_or_unavailable_feed_fails_closed(tmp_path: Path):
    _write_registry(tmp_path, [_provider(provider_id="ufc_official_events", provider_name="UFC Official Events", enabled=False)])
    state = _load_preview(tmp_path)
    live = state["live_source_status"]

    assert live.get("feed_status") == "unavailable"
    assert live.get("source_freshness") == "unavailable"
    assert live.get("save_allowed") is False


def test_parser_failure_is_reported_separately(tmp_path: Path):
    reg_path = tmp_path / "ops" / "approved_sources" / "button1_live_provider_registry.json"
    reg_path.parent.mkdir(parents=True, exist_ok=True)
    reg_path.write_text("{ invalid json", encoding="utf-8")

    state = _load_preview(tmp_path)

    assert "provider_config_invalid_json" in state["registry_adapter_status"].get("diagnostics", [])
    assert "no_approved_live_source_provider_configured" in state["live_source_status"].get("diagnostics", [])


def test_pre_existing_dirty_files_are_not_staged():
    git_bin = shutil.which("git")
    if not git_bin:
        pytest.skip("git not available")

    repo_root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [git_bin, "diff", "--cached", "--name-only"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0

    staged = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    assert "operator_dashboard/local_ai_orchestrator_readonly_runtime_context_loader.py" not in staged
    assert "operator_dashboard/test_button1_provider_registry_to_orchestrator_preview_wiring_v1.py" not in staged
