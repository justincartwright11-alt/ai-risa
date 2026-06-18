"""Button 1 approved-provider config registration scaffold.

This module is config-only. It converts validated approved-provider config into
an orchestrator registry shape without executing providers, calling sources,
scraping, saving fights, or promoting anything to Button 2.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List

from operator_dashboard.button1_approved_provider_config_validator_v1 import (
    validate_button1_approved_provider_config,
)


REGISTRY_SCHEMA_VERSION = "button1_approved_provider_registry_v1"


def _safe_text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _safe_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _safe_list(value: Any) -> List[Any]:
    return list(value) if isinstance(value, list) else []


def _base_result(config_path: str) -> Dict[str, Any]:
    return {
        "registration_valid": False,
        "validation_valid": False,
        "feed_status": "unavailable",
        "current_week_ready": False,
        "save_allowed": False,
        "diagnostics": [],
        "config_path": config_path,
        "provider_count": 0,
        "registered_provider_count": 0,
        "enabled_provider_count": 0,
        "registered_provider_ids": [],
        "registered_provider_names": [],
        "enabled_provider_ids": [],
        "registry_schema_version": REGISTRY_SCHEMA_VERSION,
        "network_calls_performed": False,
        "provider_execution_performed": False,
        "queue_write_performed": False,
        "database_write_performed": False,
        "operator_approval_required": True,
    }


def _add_diag(diagnostics: List[str], message: str) -> None:
    if message and message not in diagnostics:
        diagnostics.append(message)


def _load_config_doc(config_path: str) -> Dict[str, Any]:
    if not config_path or not os.path.exists(config_path):
        return {}
    try:
        with open(config_path, "r", encoding="utf-8") as handle:
            doc = json.load(handle)
        return doc if isinstance(doc, dict) else {}
    except Exception:
        return {}


def _normalize_providers(doc: Dict[str, Any]) -> List[Dict[str, Any]]:
    providers = doc.get("providers")
    if isinstance(providers, list):
        return [provider for provider in providers if isinstance(provider, dict)]
    registry = doc.get("registry")
    if isinstance(registry, list):
        return [provider for provider in registry if isinstance(provider, dict)]
    return []


def _build_registry_rows(providers: List[Dict[str, Any]]) -> Dict[str, Any]:
    registered_provider_ids: List[str] = []
    registered_provider_names: List[str] = []
    enabled_provider_ids: List[str] = []
    enabled_provider_count = 0

    for provider in providers:
        provider_id = _safe_text(provider.get("provider_id"))
        provider_name = _safe_text(provider.get("provider_name"))
        if provider_id:
            registered_provider_ids.append(provider_id)
        if provider_name:
            registered_provider_names.append(provider_name)
        if provider.get("enabled") is True and provider_id:
            enabled_provider_count += 1
            enabled_provider_ids.append(provider_id)

    return {
        "registered_provider_ids": registered_provider_ids,
        "registered_provider_names": registered_provider_names,
        "enabled_provider_ids": enabled_provider_ids,
        "enabled_provider_count": enabled_provider_count,
        "registered_provider_count": len(providers),
    }


def register_button1_approved_provider_config(config_path: str) -> Dict[str, Any]:
    """Register validated approved-provider config into a registry-shaped preview object."""

    result = _base_result(config_path)
    validator_result = validate_button1_approved_provider_config(config_path)
    result["validation_valid"] = bool(validator_result.get("valid", False))
    result["diagnostics"] = _safe_list(validator_result.get("diagnostics", []))
    result["provider_count"] = int(validator_result.get("provider_count", 0) or 0)
    result["enabled_provider_count"] = int(validator_result.get("enabled_provider_count", 0) or 0)

    if not result["validation_valid"]:
        result["feed_status"] = _safe_text(validator_result.get("feed_status", "unavailable")) or "unavailable"
        result["current_week_ready"] = False
        result["save_allowed"] = False
        return result

    doc = _load_config_doc(config_path)
    providers = _normalize_providers(doc)
    if not providers:
        _add_diag(result["diagnostics"], "provider_config_missing")
        result["feed_status"] = "unavailable"
        return result

    seen_ids = set()
    for provider in providers:
        provider_id = _safe_text(provider.get("provider_id"))
        if provider_id in seen_ids:
            _add_diag(result["diagnostics"], f"duplicate_provider_id:{provider_id}")
            result["registration_valid"] = False
            result["feed_status"] = "unavailable"
            result["registered_provider_count"] = 0
            result["enabled_provider_count"] = 0
            result["registered_provider_ids"] = []
            result["registered_provider_names"] = []
            result["enabled_provider_ids"] = []
            return result
        if provider_id:
            seen_ids.add(provider_id)

    for provider in providers:
        if provider.get("enabled") is True:
            if not _safe_text(provider.get("operator_approved_by")) or not _safe_text(provider.get("approval_timestamp_utc")):
                _add_diag(result["diagnostics"], "provider_enabled_without_operator_approval")
                result["registration_valid"] = False
                result["feed_status"] = "unavailable"
                return result

    registry_rows = _build_registry_rows(providers)
    result["registered_provider_count"] = registry_rows["registered_provider_count"]
    result["registered_provider_ids"] = registry_rows["registered_provider_ids"]
    result["registered_provider_names"] = registry_rows["registered_provider_names"]
    result["enabled_provider_ids"] = registry_rows["enabled_provider_ids"]
    result["enabled_provider_count"] = registry_rows["enabled_provider_count"]

    result["registration_valid"] = True
    result["feed_status"] = "unavailable"
    result["current_week_ready"] = False
    result["save_allowed"] = False

    if result["enabled_provider_count"] == 0:
        _add_diag(result["diagnostics"], "no_enabled_provider")

    return result


__all__ = [
    "REGISTRY_SCHEMA_VERSION",
    "register_button1_approved_provider_config",
]
