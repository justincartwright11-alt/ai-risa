from __future__ import annotations

import inspect
import json

from operator_dashboard.button1_approved_provider_config_validator_v1 import ALLOWED_OUTPUT_SCHEMA_VERSION
from operator_dashboard.button1_approved_provider_config_registration_v1 import (
    REGISTRY_SCHEMA_VERSION,
    register_button1_approved_provider_config,
)
import operator_dashboard.button1_approved_provider_config_registration_v1 as registration_module


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
        "output_schema_version": "button1_live_provider_registry_v1",
        "operator_approved_by": "operator@example.com",
        "approval_timestamp_utc": "2026-06-18T00:00:00Z",
        "provenance_notes": "example only",
    }
    provider.update(overrides)
    return provider


def test_missing_config_fails_closed_and_registers_zero_providers(tmp_path):
    result = register_button1_approved_provider_config(str(tmp_path / "missing.json"))
    assert result["registration_valid"] is False
    assert result["feed_status"] == "unavailable"
    assert "provider_config_missing" in result["diagnostics"]
    assert result["registered_provider_count"] == 0
    assert result["enabled_provider_count"] == 0


def test_invalid_config_fails_closed_and_registers_zero_providers(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{not-json", encoding="utf-8")
    result = register_button1_approved_provider_config(str(path))
    assert result["registration_valid"] is False
    assert result["registered_provider_count"] == 0
    assert result["enabled_provider_count"] == 0


def test_valid_disabled_config_registers_but_enables_zero_providers(tmp_path):
    provider = _base_provider(enabled=False)
    result = register_button1_approved_provider_config(
        _write_config(tmp_path, {"schema_version": ALLOWED_OUTPUT_SCHEMA_VERSION, "providers": [provider]})
    )
    assert result["registration_valid"] is True
    assert result["registered_provider_count"] == 1
    assert result["enabled_provider_count"] == 0
    assert "no_enabled_provider" in result["diagnostics"]
    assert result["provider_execution_performed"] is False


def test_valid_enabled_approved_config_registers_enabled_provider_metadata(tmp_path):
    provider = _base_provider(enabled=True)
    result = register_button1_approved_provider_config(
        _write_config(tmp_path, {"schema_version": ALLOWED_OUTPUT_SCHEMA_VERSION, "providers": [provider]})
    )
    assert result["registration_valid"] is True
    assert result["registered_provider_count"] == 1
    assert result["enabled_provider_count"] == 1
    assert result["registered_provider_ids"] == [provider["provider_id"]]
    assert result["registered_provider_names"] == [provider["provider_name"]]
    assert result["network_calls_performed"] is False
    assert result["provider_execution_performed"] is False
    assert result["queue_write_performed"] is False
    assert result["database_write_performed"] is False


def test_duplicate_provider_id_fails_closed(tmp_path):
    provider_one = _base_provider(enabled=True)
    provider_two = _base_provider(provider_name="Duplicate Provider", enabled=True)
    result = register_button1_approved_provider_config(
        _write_config(tmp_path, {"schema_version": ALLOWED_OUTPUT_SCHEMA_VERSION, "providers": [provider_one, provider_two]})
    )
    assert result["registration_valid"] is False
    assert any(item.startswith("duplicate_provider_id:") for item in result["diagnostics"])


def test_enabled_but_unapproved_provider_fails_closed(tmp_path):
    provider = _base_provider(enabled=True, operator_approved_by="", approval_timestamp_utc="")
    result = register_button1_approved_provider_config(
        _write_config(tmp_path, {"schema_version": ALLOWED_OUTPUT_SCHEMA_VERSION, "providers": [provider]})
    )
    assert result["registration_valid"] is False
    assert "provider_enabled_without_operator_approval" in result["diagnostics"]


def test_registration_performs_no_network_calls(tmp_path):
    provider = _base_provider(enabled=True)
    result = register_button1_approved_provider_config(
        _write_config(tmp_path, {"schema_version": ALLOWED_OUTPUT_SCHEMA_VERSION, "providers": [provider]})
    )
    assert result["network_calls_performed"] is False


def test_registration_performs_no_provider_execution(tmp_path):
    provider = _base_provider(enabled=True)
    result = register_button1_approved_provider_config(
        _write_config(tmp_path, {"schema_version": ALLOWED_OUTPUT_SCHEMA_VERSION, "providers": [provider]})
    )
    assert result["provider_execution_performed"] is False


def test_queue_and_database_writes_remain_false(tmp_path):
    provider = _base_provider(enabled=True)
    result = register_button1_approved_provider_config(
        _write_config(tmp_path, {"schema_version": REGISTRY_SCHEMA_VERSION, "providers": [provider]})
    )
    assert result["queue_write_performed"] is False
    assert result["database_write_performed"] is False


def test_operator_approval_required_remains_true(tmp_path):
    provider = _base_provider(enabled=True)
    result = register_button1_approved_provider_config(
        _write_config(tmp_path, {"schema_version": REGISTRY_SCHEMA_VERSION, "providers": [provider]})
    )
    assert result["operator_approval_required"] is True


def test_button2_and_button3_unchanged_by_registration_module():
    source = inspect.getsource(registration_module)
    assert "button2_" not in source
    assert "button3_" not in source
