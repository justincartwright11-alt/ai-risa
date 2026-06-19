"""Button 1 registration-to-orchestrator-registry adapter scaffold.

This module is config-only and pure. It converts approved-provider registration
output into orchestrator registry candidates without contacting sources,
executing providers, writing queues, or promoting anything to Button 2.
"""

from __future__ import annotations

from typing import Any, Dict, List


REGISTRY_CANDIDATE_SCHEMA_VERSION = "button1_orchestrator_registry_candidate_v1"


def _safe_text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _safe_list(value: Any) -> List[Any]:
    return list(value) if isinstance(value, list) else []


def _safe_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _base_result() -> Dict[str, Any]:
    return {
        "registry_candidate_valid": False,
        "registration_valid": False,
        "validation_valid": False,
        "feed_status": "unavailable",
        "current_week_ready": False,
        "save_allowed": False,
        "diagnostics": [],
        "config_path": "",
        "registration_schema_version": "",
        "registry_candidate_schema_version": REGISTRY_CANDIDATE_SCHEMA_VERSION,
        "provider_count": 0,
        "registered_provider_count": 0,
        "enabled_provider_count": 0,
        "registry_candidate_count": 0,
        "registry_candidates": [],
        "registered_provider_ids": [],
        "registered_provider_names": [],
        "enabled_provider_ids": [],
        "enabled_registry_candidate_ids": [],
        "network_calls_performed": False,
        "provider_execution_performed": False,
        "queue_write_performed": False,
        "database_write_performed": False,
        "operator_approval_required": True,
    }


def _candidate_for_provider(provider_id: str, provider_name: str, enabled: bool) -> Dict[str, Any]:
    return {
        "provider_id": provider_id,
        "provider_name": provider_name,
        "enabled": bool(enabled),
        "candidate_status": "enabled" if enabled else "registered_disabled",
        "source_of_truth": "registration_output",
        "registry_candidate_valid": True,
        "network_calls_performed": False,
        "provider_execution_performed": False,
        "queue_write_performed": False,
        "database_write_performed": False,
        "operator_approval_required": True,
    }


def adapt_button1_registration_output_to_orchestrator_registry_candidates(registration_output: Dict[str, Any]) -> Dict[str, Any]:
    """Convert registration output into fail-closed orchestrator registry candidates."""

    result = _base_result()
    if not isinstance(registration_output, dict):
        result["diagnostics"] = ["registration_output_invalid"]
        return result

    result["registration_valid"] = bool(registration_output.get("registration_valid", False))
    result["validation_valid"] = bool(registration_output.get("validation_valid", False))
    result["feed_status"] = _safe_text(registration_output.get("feed_status", "unavailable")) or "unavailable"
    result["current_week_ready"] = bool(registration_output.get("current_week_ready", False))
    result["save_allowed"] = bool(registration_output.get("save_allowed", False))
    result["diagnostics"] = [d for d in _safe_list(registration_output.get("diagnostics", [])) if _safe_text(d)]
    result["config_path"] = _safe_text(registration_output.get("config_path", ""))
    result["registration_schema_version"] = _safe_text(
        registration_output.get("registry_schema_version") or registration_output.get("registration_schema_version") or ""
    )
    result["provider_count"] = int(registration_output.get("provider_count", 0) or 0)
    result["registered_provider_count"] = int(registration_output.get("registered_provider_count", 0) or 0)
    result["enabled_provider_count"] = int(registration_output.get("enabled_provider_count", 0) or 0)
    result["registered_provider_ids"] = [
        _safe_text(provider_id) for provider_id in _safe_list(registration_output.get("registered_provider_ids", [])) if _safe_text(provider_id)
    ]
    result["registered_provider_names"] = [
        _safe_text(provider_name) for provider_name in _safe_list(registration_output.get("registered_provider_names", [])) if _safe_text(provider_name)
    ]
    result["enabled_provider_ids"] = [
        _safe_text(provider_id) for provider_id in _safe_list(registration_output.get("enabled_provider_ids", [])) if _safe_text(provider_id)
    ]
    result["operator_approval_required"] = bool(registration_output.get("operator_approval_required", True))

    if not result["registration_valid"] or not result["validation_valid"]:
        if not result["diagnostics"]:
            result["diagnostics"] = ["registration_output_not_ready"]
        return result

    if any(diag.startswith("duplicate_provider_id:") for diag in result["diagnostics"]):
        result["registry_candidates"] = []
        result["registry_candidate_count"] = 0
        return result

    if result["registered_provider_count"] == 0:
        result["diagnostics"].append("registration_output_empty")
        return result

    candidate_names = result["registered_provider_names"]
    candidate_ids = result["registered_provider_ids"]
    enabled_ids = set(result["enabled_provider_ids"])
    registry_candidates: List[Dict[str, Any]] = []

    for index, provider_id in enumerate(candidate_ids):
        provider_name = candidate_names[index] if index < len(candidate_names) else ""
        registry_candidates.append(_candidate_for_provider(provider_id, provider_name, provider_id in enabled_ids))

    result["registry_candidates"] = registry_candidates
    result["registry_candidate_count"] = len(registry_candidates)
    result["enabled_registry_candidate_ids"] = [candidate["provider_id"] for candidate in registry_candidates if candidate["enabled"]]
    result["registry_candidate_valid"] = True
    return result


__all__ = [
    "REGISTRY_CANDIDATE_SCHEMA_VERSION",
    "adapt_button1_registration_output_to_orchestrator_registry_candidates",
]
