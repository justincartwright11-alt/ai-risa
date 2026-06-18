from __future__ import annotations

import inspect
import json

from operator_dashboard.button1_approved_provider_config_validator_v1 import (
    ALLOWED_OUTPUT_SCHEMA_VERSION,
    validate_button1_approved_provider_config,
)
import operator_dashboard.button1_approved_provider_config_validator_v1 as validator_module


def _write_config(tmp_path, payload):
    path = tmp_path / "button1_live_provider_registry.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return str(path)


def _base_provider(**overrides):
    provider = {
        "provider_id": "ufc_official_event_pages",
        "provider_name": "UFC official event pages",
        "provider_type": "official",
        "enabled": False,
        "source_tier": "official_promotion",
        "allowed_domains": ["ufc.com"],
        "endpoint_or_feed_location": "https://www.ufc.com/event/",
        "auth_required": False,
        "refresh_cadence_minutes": 120,
        "max_feed_age_hours": 24,
        "ruleset_scope": ["event_card_discovery"],
        "promotion_scope": ["UFC"],
        "region_scope": ["global"],
        "output_schema_version": ALLOWED_OUTPUT_SCHEMA_VERSION,
        "operator_approved_by": "operator@example.com",
        "approval_timestamp_utc": "2026-06-18T00:00:00Z",
        "provenance_notes": "example only",
    }
    provider.update(overrides)
    return provider


def test_missing_config_fails_closed(tmp_path):
    result = validate_button1_approved_provider_config(str(tmp_path / "missing.json"))
    assert result["valid"] is False
    assert result["feed_status"] == "unavailable"
    assert result["current_week_ready"] is False
    assert result["save_allowed"] is False
    assert "provider_config_missing" in result["diagnostics"]


def test_invalid_json_fails_closed(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{not-json", encoding="utf-8")
    result = validate_button1_approved_provider_config(str(path))
    assert result["valid"] is False
    assert "provider_config_invalid_json" in result["diagnostics"]


def test_missing_required_field_fails_closed(tmp_path):
    provider = _base_provider()
    provider.pop("provider_name")
    result = validate_button1_approved_provider_config(_write_config(tmp_path, {"schema_version": ALLOWED_OUTPUT_SCHEMA_VERSION, "providers": [provider]}))
    assert result["valid"] is False
    assert any(item.startswith("missing_required_field:provider_name") for item in result["diagnostics"])


def test_enabled_without_approval_fails_closed(tmp_path):
    provider = _base_provider(enabled=True, operator_approved_by="")
    result = validate_button1_approved_provider_config(_write_config(tmp_path, {"schema_version": ALLOWED_OUTPUT_SCHEMA_VERSION, "providers": [provider]}))
    assert result["valid"] is False
    assert "provider_enabled_without_operator_approval" in result["diagnostics"]


def test_missing_allowed_domains_fails_closed(tmp_path):
    provider = _base_provider(allowed_domains=[])
    result = validate_button1_approved_provider_config(_write_config(tmp_path, {"schema_version": ALLOWED_OUTPUT_SCHEMA_VERSION, "providers": [provider]}))
    assert result["valid"] is False
    assert "missing_allowed_domains" in result["diagnostics"]


def test_unknown_source_tier_fails_closed(tmp_path):
    provider = _base_provider(source_tier="unknown_tier")
    result = validate_button1_approved_provider_config(_write_config(tmp_path, {"schema_version": ALLOWED_OUTPUT_SCHEMA_VERSION, "providers": [provider]}))
    assert result["valid"] is False
    assert "unknown_source_tier" in result["diagnostics"]


def test_unsupported_schema_version_fails_closed(tmp_path):
    provider = _base_provider()
    result = validate_button1_approved_provider_config(_write_config(tmp_path, {"schema_version": "other_v9", "providers": [provider]}))
    assert result["valid"] is False
    assert "unsupported_output_schema_version" in result["diagnostics"]


def test_missing_max_feed_age_hours_fails_closed(tmp_path):
    provider = _base_provider()
    provider.pop("max_feed_age_hours")
    result = validate_button1_approved_provider_config(_write_config(tmp_path, {"schema_version": ALLOWED_OUTPUT_SCHEMA_VERSION, "providers": [provider]}))
    assert result["valid"] is False
    assert "missing_max_feed_age_hours" in result["diagnostics"]


def test_valid_disabled_config_passes_validation_but_enables_zero_providers(tmp_path):
    provider = _base_provider(enabled=False)
    result = validate_button1_approved_provider_config(_write_config(tmp_path, {"schema_version": ALLOWED_OUTPUT_SCHEMA_VERSION, "providers": [provider]}))
    assert result["valid"] is True
    assert result["enabled_provider_count"] == 0
    assert "no_enabled_provider" in result["diagnostics"]
    assert result["network_calls_performed"] is False
    assert result["provider_execution_performed"] is False


def test_valid_enabled_approved_config_passes_validation_but_performs_no_network_or_execution(tmp_path):
    provider = _base_provider(enabled=True)
    result = validate_button1_approved_provider_config(_write_config(tmp_path, {"schema_version": ALLOWED_OUTPUT_SCHEMA_VERSION, "providers": [provider]}))
    assert result["valid"] is True
    assert result["enabled_provider_count"] >= 1
    assert result["network_calls_performed"] is False
    assert result["provider_execution_performed"] is False
    assert result["queue_write_performed"] is False
    assert result["database_write_performed"] is False


def test_output_contract_includes_all_fail_closed_write_flags(tmp_path):
    provider = _base_provider()
    result = validate_button1_approved_provider_config(_write_config(tmp_path, {"schema_version": ALLOWED_OUTPUT_SCHEMA_VERSION, "providers": [provider]}))
    for key in (
        "network_calls_performed",
        "provider_execution_performed",
        "queue_write_performed",
        "database_write_performed",
        "provider_count",
        "enabled_provider_count",
        "enabled_provider_ids",
        "config_path",
        "schema_version",
    ):
        assert key in result


def test_button2_and_button3_unchanged_by_validator_module():
    source = inspect.getsource(validator_module)
    assert "button2_" not in source
    assert "button3_" not in source
