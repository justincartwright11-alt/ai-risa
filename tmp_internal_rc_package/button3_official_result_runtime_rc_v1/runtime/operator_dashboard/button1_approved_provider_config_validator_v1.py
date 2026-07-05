"""Button 1 approved-provider config parser/validator scaffold.

This module is config-only. It parses approved-provider registry files,
validates required contract fields, and returns deterministic fail-closed
results without creating providers, scraping, calling APIs, or wiring live
discovery.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


ALLOWED_SOURCE_TIERS = {
    "official_promotion",
    "official_commission",
    "verified_database",
    "internal_operator_approved",
}

ALLOWED_OUTPUT_SCHEMA_VERSION = "button1_live_provider_registry_v1"

REQUIRED_PROVIDER_FIELDS = [
    "provider_id",
    "provider_name",
    "provider_type",
    "enabled",
    "source_tier",
    "allowed_domains",
    "endpoint_or_feed_location",
    "auth_required",
    "refresh_cadence_minutes",
    "max_feed_age_hours",
    "ruleset_scope",
    "promotion_scope",
    "region_scope",
    "output_schema_version",
    "operator_approved_by",
    "approval_timestamp_utc",
    "provenance_notes",
]


def _safe_text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _safe_list(value: Any) -> List[Any]:
    return list(value) if isinstance(value, list) else []


def _safe_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _base_result(config_path: str) -> Dict[str, Any]:
    return {
        "valid": False,
        "feed_status": "unavailable",
        "current_week_ready": False,
        "save_allowed": False,
        "diagnostics": [],
        "provider_count": 0,
        "enabled_provider_count": 0,
        "enabled_provider_ids": [],
        "config_path": config_path,
        "schema_version": ALLOWED_OUTPUT_SCHEMA_VERSION,
        "network_calls_performed": False,
        "provider_execution_performed": False,
        "queue_write_performed": False,
        "database_write_performed": False,
    }


def _add_diag(diagnostics: List[str], message: str) -> None:
    if message and message not in diagnostics:
        diagnostics.append(message)


def _parse_approval_timestamp(value: Any) -> bool:
    text = _safe_text(value)
    if not text:
        return False
    try:
        normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
        datetime.fromisoformat(normalized)
        return True
    except Exception:
        return False


def _validate_provider(provider: Dict[str, Any], diagnostics: List[str]) -> bool:
    provider = _safe_dict(provider)
    missing_fields = [field for field in REQUIRED_PROVIDER_FIELDS if field not in provider]

    if "allowed_domains" in missing_fields:
        _add_diag(diagnostics, "missing_allowed_domains")
        return False

    if "max_feed_age_hours" in missing_fields:
        _add_diag(diagnostics, "missing_max_feed_age_hours")
        return False

    if "operator_approved_by" in missing_fields and provider.get("enabled") is True:
        _add_diag(diagnostics, "provider_enabled_without_operator_approval")
        return False

    if missing_fields:
        for field in missing_fields:
            _add_diag(diagnostics, f"missing_required_field:{field}")
        return False

    provider_id = _safe_text(provider.get("provider_id"))
    if not provider_id:
        _add_diag(diagnostics, "missing_required_field:provider_id")
        return False

    provider_name = _safe_text(provider.get("provider_name"))
    if not provider_name:
        _add_diag(diagnostics, "missing_required_field:provider_name")
        return False

    if provider.get("enabled") is True:
        approved_by = _safe_text(provider.get("operator_approved_by"))
        if not approved_by:
            _add_diag(diagnostics, "provider_enabled_without_operator_approval")
            return False
        if not _parse_approval_timestamp(provider.get("approval_timestamp_utc")):
            _add_diag(diagnostics, "missing_required_field:approval_timestamp_utc")
            return False

    allowed_domains = provider.get("allowed_domains")
    if not isinstance(allowed_domains, list) or not [d for d in allowed_domains if _safe_text(d)]:
        _add_diag(diagnostics, "missing_allowed_domains")
        return False

    source_tier = _safe_text(provider.get("source_tier"))
    if source_tier not in ALLOWED_SOURCE_TIERS:
        _add_diag(diagnostics, "unknown_source_tier")
        return False

    output_schema_version = _safe_text(provider.get("output_schema_version"))
    if output_schema_version != ALLOWED_OUTPUT_SCHEMA_VERSION:
        _add_diag(diagnostics, "unsupported_output_schema_version")
        return False

    if provider.get("max_feed_age_hours") in (None, ""):
        _add_diag(diagnostics, "missing_max_feed_age_hours")
        return False

    if not _safe_text(provider.get("endpoint_or_feed_location")):
        _add_diag(diagnostics, "missing_required_field:endpoint_or_feed_location")
        return False

    return True


def _normalize_registry(doc: Dict[str, Any]) -> List[Dict[str, Any]]:
    if isinstance(doc.get("providers"), list):
        return [p for p in doc.get("providers", []) if isinstance(p, dict)]
    if isinstance(doc.get("registry"), list):
        return [p for p in doc.get("registry", []) if isinstance(p, dict)]
    if isinstance(doc.get("providers"), dict):
        return [doc.get("providers")]
    return []


def validate_button1_approved_provider_config(config_path: str) -> Dict[str, Any]:
    """Parse and validate the approved-provider config file at `config_path`."""

    result = _base_result(config_path)
    diagnostics = result["diagnostics"]

    if not config_path or not os.path.exists(config_path):
        _add_diag(diagnostics, "provider_config_missing")
        return result

    try:
        with open(config_path, "r", encoding="utf-8") as handle:
            raw_text = handle.read()
        doc = json.loads(raw_text)
    except json.JSONDecodeError:
        _add_diag(diagnostics, "provider_config_invalid_json")
        return result
    except Exception:
        _add_diag(diagnostics, "provider_config_invalid_json")
        return result

    if not isinstance(doc, dict):
        _add_diag(diagnostics, "provider_config_invalid_json")
        return result

    schema_version = _safe_text(doc.get("schema_version"))
    if schema_version and schema_version != ALLOWED_OUTPUT_SCHEMA_VERSION:
        _add_diag(diagnostics, "unsupported_output_schema_version")
        return result

    providers = _normalize_registry(doc)
    result["provider_count"] = len(providers)

    enabled_provider_ids: List[str] = []
    enabled_provider_count = 0
    at_least_one_enabled = False
    valid = True

    for provider in providers:
        if not _validate_provider(provider, diagnostics):
            valid = False
            continue
        if provider.get("enabled") is True:
            at_least_one_enabled = True
            enabled_provider_count += 1
            enabled_provider_ids.append(_safe_text(provider.get("provider_id")))

    result["enabled_provider_count"] = enabled_provider_count
    result["enabled_provider_ids"] = enabled_provider_ids

    if valid and not at_least_one_enabled:
        _add_diag(diagnostics, "no_enabled_provider")

    if not valid:
        result["valid"] = False
        result["feed_status"] = "unavailable"
        result["current_week_ready"] = False
        result["save_allowed"] = False
        return result

    result["valid"] = True
    if at_least_one_enabled:
        result["feed_status"] = "unavailable"
        result["current_week_ready"] = False
        result["save_allowed"] = False
    else:
        result["feed_status"] = "unavailable"
        result["current_week_ready"] = False
        result["save_allowed"] = False

    return result


__all__ = [
    "ALLOWED_OUTPUT_SCHEMA_VERSION",
    "ALLOWED_SOURCE_TIERS",
    "REQUIRED_PROVIDER_FIELDS",
    "validate_button1_approved_provider_config",
]
