from __future__ import annotations

import inspect

from operator_dashboard.button1_config_registration_to_orchestrator_registry_adapter_v1 import (
    REGISTRY_CANDIDATE_SCHEMA_VERSION,
    adapt_button1_registration_output_to_orchestrator_registry_candidates,
)
import operator_dashboard.button1_config_registration_to_orchestrator_registry_adapter_v1 as adapter_module


def _base_registration_output(**overrides):
    registration = {
        "registration_valid": True,
        "validation_valid": True,
        "feed_status": "unavailable",
        "current_week_ready": False,
        "save_allowed": False,
        "diagnostics": ["no_enabled_provider"],
        "config_path": "c:/tmp/button1_registry.json",
        "registration_schema_version": "button1_approved_provider_registry_v1",
        "provider_count": 1,
        "registered_provider_count": 1,
        "enabled_provider_count": 1,
        "registered_provider_ids": ["ufc_official_event_pages"],
        "registered_provider_names": ["UFC official event pages"],
        "enabled_provider_ids": ["ufc_official_event_pages"],
        "network_calls_performed": False,
        "provider_execution_performed": False,
        "queue_write_performed": False,
        "database_write_performed": False,
        "operator_approval_required": True,
    }
    registration.update(overrides)
    return registration


def test_valid_registration_maps_to_registry_candidates():
    result = adapt_button1_registration_output_to_orchestrator_registry_candidates(_base_registration_output())
    assert result["registry_candidate_valid"] is True
    assert result["registry_candidate_schema_version"] == REGISTRY_CANDIDATE_SCHEMA_VERSION
    assert result["registry_candidate_count"] == 1
    assert result["registry_candidates"][0]["provider_id"] == "ufc_official_event_pages"
    assert result["registry_candidates"][0]["enabled"] is True
    assert result["enabled_registry_candidate_ids"] == ["ufc_official_event_pages"]


def test_disabled_registration_maps_to_disabled_candidate():
    result = adapt_button1_registration_output_to_orchestrator_registry_candidates(
        _base_registration_output(
            enabled_provider_count=0,
            enabled_provider_ids=[],
            diagnostics=["no_enabled_provider"],
        )
    )
    assert result["registry_candidate_valid"] is True
    assert result["registry_candidate_count"] == 1
    assert result["registry_candidates"][0]["enabled"] is False
    assert result["enabled_registry_candidate_ids"] == []


def test_invalid_registration_fails_closed_with_no_candidates():
    result = adapt_button1_registration_output_to_orchestrator_registry_candidates(
        _base_registration_output(registration_valid=False, diagnostics=["provider_enabled_without_operator_approval"])
    )
    assert result["registry_candidate_valid"] is False
    assert result["registry_candidate_count"] == 0
    assert result["registry_candidates"] == []
    assert "provider_enabled_without_operator_approval" in result["diagnostics"]


def test_validation_invalid_registration_fails_closed():
    result = adapt_button1_registration_output_to_orchestrator_registry_candidates(
        _base_registration_output(validation_valid=False, registration_valid=False)
    )
    assert result["registry_candidate_valid"] is False
    assert result["registry_candidate_count"] == 0
    assert result["registry_candidates"] == []


def test_duplicate_provider_id_remains_blocked():
    result = adapt_button1_registration_output_to_orchestrator_registry_candidates(
        _base_registration_output(
            registration_valid=False,
            diagnostics=["duplicate_provider_id:ufc_official_event_pages"],
            registered_provider_count=2,
            registered_provider_ids=["ufc_official_event_pages", "ufc_official_event_pages"],
            registered_provider_names=["UFC official event pages", "Duplicate UFC official event pages"],
            enabled_provider_ids=["ufc_official_event_pages"],
        )
    )
    assert result["registry_candidate_valid"] is False
    assert result["registry_candidate_count"] == 0
    assert result["registry_candidates"] == []


def test_adapter_accepts_non_dict_input_fail_closed():
    result = adapt_button1_registration_output_to_orchestrator_registry_candidates(None)
    assert result["registry_candidate_valid"] is False
    assert result["registry_candidates"] == []
    assert "registration_output_invalid" in result["diagnostics"]


def test_adapter_performs_no_network_calls():
    result = adapt_button1_registration_output_to_orchestrator_registry_candidates(_base_registration_output())
    assert result["network_calls_performed"] is False


def test_adapter_performs_no_provider_execution():
    result = adapt_button1_registration_output_to_orchestrator_registry_candidates(_base_registration_output())
    assert result["provider_execution_performed"] is False


def test_adapter_queue_and_database_writes_remain_false():
    result = adapt_button1_registration_output_to_orchestrator_registry_candidates(_base_registration_output())
    assert result["queue_write_performed"] is False
    assert result["database_write_performed"] is False


def test_operator_approval_required_remains_true():
    result = adapt_button1_registration_output_to_orchestrator_registry_candidates(_base_registration_output())
    assert result["operator_approval_required"] is True


def test_adapter_preserves_input_metadata():
    result = adapt_button1_registration_output_to_orchestrator_registry_candidates(_base_registration_output())
    assert result["config_path"] == "c:/tmp/button1_registry.json"
    assert result["registration_schema_version"] == "button1_approved_provider_registry_v1"


def test_button2_and_button3_unchanged_by_adapter_module():
    source = inspect.getsource(adapter_module)
    assert "button2_" not in source
    assert "button3_" not in source
