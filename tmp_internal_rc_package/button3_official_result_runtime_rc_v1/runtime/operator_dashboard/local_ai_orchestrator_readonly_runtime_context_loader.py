"""Read-only runtime context loader for three-button local AI preview flows.

Builds sanitized context packs from existing local runtime state without mutation.
This module never performs queue/database writes, exports, applies, learning,
calibration, or live web execution.
"""

from __future__ import annotations

import csv
import json
import os
import re
import time
from datetime import datetime, date, timedelta, timezone
from typing import Any, Dict, List

from operator_dashboard.local_ai_orchestrator_input_context_pack import (
    ALLOWED_SOURCE_BUTTONS,
    LocalAIInputContextPack,
    build_button2_generate_pdfs_context,
    build_button3_find_results_context,
)
from operator_dashboard.button1_auto_discovery_readiness_ranking_v1 import (
    build_button1_auto_discovery_readiness_ranking,
)
from operator_dashboard.button1_live_source_provider_orchestrator_v1 import (
    run_button1_live_source_provider_orchestrator,
)
from operator_dashboard.button1_approved_provider_config_registration_v1 import (
    register_button1_approved_provider_config,
)
from operator_dashboard.button1_config_registration_to_orchestrator_registry_adapter_v1 import (
    adapt_button1_registration_output_to_orchestrator_registry_candidates,
)
from operator_dashboard.button1_provider_adapter_execution_gate_v1 import (
    evaluate_button1_provider_adapter_execution_gate,
)


def _default_workspace_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _safe_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}


def _safe_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return list(value)
    return []


def _safe_list_of_dict(value: Any) -> List[Dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(v) for v in value if isinstance(v, dict)]


def _safe_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    return ""


def _safe_bool(value: Any) -> bool:
    return bool(value)


_RUNTIME_GATE_REASON_CODE_PRIORITY = (
    "execution_gate_operator_approval_missing",
    "source_call_authorization_missing",
    "max_result_count_unbounded",
    "timeout_unbounded",
    "provenance_required_missing",
    "network_call_not_authorized",
)


def _normalized_gate_reason_codes(reason_codes: List[Any]) -> List[str]:
    normalized = {_safe_text(code) for code in reason_codes if _safe_text(code)}
    ordered = [code for code in _RUNTIME_GATE_REASON_CODE_PRIORITY if code in normalized]
    extras = sorted(code for code in normalized if code not in set(_RUNTIME_GATE_REASON_CODE_PRIORITY))
    return ordered + extras


def _default_button1_provider_registry_config_path(root: str) -> str:
    return os.path.join(root, "ops", "approved_sources", "button1_live_provider_registry.json")


def _load_button1_registry_adapter_status_preview(root: str) -> Dict[str, Any]:
    """Build read-only registry-adapter status for Button 1 runtime preview.

    This path is config-only and must not execute providers, call sources,
    scrape, or write queue/database rows.
    """

    config_path = _default_button1_provider_registry_config_path(root)
    registration_output = register_button1_approved_provider_config(config_path)
    adapter_status = adapt_button1_registration_output_to_orchestrator_registry_candidates(registration_output)

    # Enforce fail-closed governance flags in preview/runtime payloads.
    adapter_status["network_calls_performed"] = False
    adapter_status["provider_execution_performed"] = False
    adapter_status["queue_write_performed"] = False
    adapter_status["database_write_performed"] = False
    adapter_status["operator_approval_required"] = True
    return _safe_dict(adapter_status)


def _build_button1_orchestrator_registry_preview(adapter_status: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build preview-only orchestrator registry candidates from adapter status.

    This preserves non-executing behavior by not attaching live adapters.
    """

    status = _safe_dict(adapter_status)
    candidates = _safe_list_of_dict(status.get("registry_candidates", []))
    provider_registry: List[Dict[str, Any]] = []

    for candidate in candidates:
        provider_id = _safe_text(candidate.get("provider_id"))
        provider_name = _safe_text(candidate.get("provider_name")) or provider_id
        if not provider_id or not provider_name:
            continue

        provider_registry.append(
            {
                "provider_id": provider_id,
                "name": provider_name,
                "enabled": bool(candidate.get("enabled", False)),
                # Keep preview config-only context and do not bind execution adapters.
                "config": {"provider_id": provider_id},
                "adapter": None,
            }
        )

    return provider_registry


def _load_button1_execution_gate_status_preview(state: Dict[str, Any]) -> Dict[str, Any]:
    """Build preview-only execution gate status for Button 1 runtime preview.

    This status path must remain non-executing and deny-by-default.
    """

    state_dict = _safe_dict(state)
    registry_adapter_status = _safe_dict(state_dict.get("registry_adapter_status", {}))
    enabled_ids = [
        _safe_text(provider_id)
        for provider_id in _safe_list(registry_adapter_status.get("enabled_registry_candidate_ids", []))
        if _safe_text(provider_id)
    ]
    registered_ids = [
        _safe_text(provider_id)
        for provider_id in _safe_list(registry_adapter_status.get("registered_provider_ids", []))
        if _safe_text(provider_id)
    ]

    provider_id = enabled_ids[0] if enabled_ids else (registered_ids[0] if registered_ids else "")
    provider_enabled = bool(provider_id and provider_id in set(enabled_ids))

    gate_status = evaluate_button1_provider_adapter_execution_gate(
        {
            "source_button": "button1_find_fights",
            "provider_id": provider_id,
            "provider_enabled": provider_enabled,
            # Runtime preview is deny-by-default and non-executing.
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
    )

    no_write_flags = {
        "provider_execution_performed": False,
        "network_calls_performed": False,
        "source_calls_performed": False,
        "scraping_performed": False,
        "queue_write_performed": False,
        "database_write_performed": False,
        "customer_pdf_generation_performed": False,
        "button2_promotion_performed": False,
        "learning_write_performed": False,
        "calibration_write_performed": False,
        "auto_save_performed": False,
    }

    reason_codes = _normalized_gate_reason_codes(_safe_list(gate_status.get("execution_gate_reason_codes", [])))

    gate_status["execution_gate_allowed"] = False
    gate_status["execution_gate_decision"] = "deny"
    gate_status["execution_gate_reason_codes"] = list(reason_codes)
    gate_status["allowed"] = False
    gate_status["decision"] = "deny"
    gate_status["reason_codes"] = list(reason_codes)
    gate_status["preview_only"] = True
    gate_status["operator_approval_required"] = True
    gate_status["live_save_allowed"] = False
    gate_status["save_allowed"] = False
    gate_status["no_write_flags"] = dict(no_write_flags)
    gate_status.update(no_write_flags)
    return _safe_dict(gate_status)


def _read_text_file(path: str) -> str:
    try:
        if not os.path.exists(path):
            return ""
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return ""


def _read_json_file(path: str) -> Dict[str, Any]:
    try:
        if not os.path.exists(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _read_csv_rows(path: str, max_rows: int = 250) -> List[Dict[str, Any]]:
    try:
        if not os.path.exists(path):
            return []
        rows: List[Dict[str, Any]] = []
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if isinstance(row, dict):
                    rows.append(dict(row))
                if len(rows) >= max_rows:
                    break
        return rows
    except Exception:
        return []


def _urls_from_text(value: Any) -> List[str]:
    text = _safe_text(value)
    if not text:
        return []
    return [u.strip() for u in re.findall(r"https?://[^\s,;]+", text) if u.strip()]


def _coerce_source_urls(value: Any) -> List[str]:
    if isinstance(value, list):
        return [u for u in (_safe_text(v) for v in value) if u]
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return []
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [u for u in (_safe_text(v) for v in parsed) if u]
        except Exception:
            pass
        return _urls_from_text(raw)
    return []


_DEFAULT_APPROVED_SOURCE_URL_PATTERNS = [
    r"https?://(?:www\.)?ufc\.com/event/",
    r"https?://(?:www\.)?ufcstats\.com/event-details/",
    r"https?://(?:www\.)?onefc\.com/events/",
    r"https?://(?:www\.)?onefc\.com/.*/fight-results",
    r"https?://(?:www\.)?glorykickboxing\.com/events/",
    r"https?://(?:www\.)?matchroom\.com/events/",
    r"https?://(?:www\.)?queensberrypromotions\.com/events/",
    r"https?://(?:www\.)?toprank\.com/(?:events|fights)/",
    r"https?://(?:www\.)?nolimitboxing\.com\.au/",
]


def _load_approved_source_ingestion_config(root: str) -> Dict[str, Any]:
    config_path = os.path.join(root, "ops", "approved_sources", "button1_live_event_ingestion_config.json")
    config = _read_json_file(config_path)
    enabled = True if "enabled" not in config else bool(config.get("enabled"))
    patterns = _coerce_source_urls(config.get("approved_source_url_patterns"))
    if not patterns:
        raw_patterns = config.get("approved_source_url_patterns")
        if isinstance(raw_patterns, list):
            patterns = [_safe_text(v) for v in raw_patterns if _safe_text(v)]
    if not patterns:
        patterns = list(_DEFAULT_APPROVED_SOURCE_URL_PATTERNS)

    feed_paths = config.get("feed_paths")
    if isinstance(feed_paths, list):
        feed_files = [_safe_text(p) for p in feed_paths if _safe_text(p)]
    else:
        feed_files = [
            "ops/approved_sources/button1_live_event_source_rows.json",
            "ops/approved_sources/button1_live_event_source_rows.jsonl",
            "ops/approved_sources/live_event_source_rows.json",
        ]

    return {
        "enabled": enabled,
        "approved_source_url_patterns": patterns,
        "feed_paths": feed_files,
    }


def _url_matches_approved_patterns(url: str, patterns: List[str]) -> bool:
    if not url:
        return False
    for pattern in patterns:
        try:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        except re.error:
            continue
    return False


def _guess_source_name_from_url(url: str) -> str:
    txt = _safe_text(url).lower()
    if "ufc.com" in txt or "ufcstats.com" in txt:
        return "ufc_official"
    if "onefc.com" in txt:
        return "one_championship_official"
    if "glorykickboxing.com" in txt:
        return "glory_official"
    if "matchroom.com" in txt:
        return "matchroom_official"
    if "queensberrypromotions.com" in txt:
        return "queensberry_official"
    if "toprank.com" in txt:
        return "top_rank_official"
    if "nolimitboxing.com.au" in txt:
        return "no_limit_boxing_official"
    return "approved_official_source"


def _parse_approved_source_feed_rows(path: str) -> List[Dict[str, Any]]:
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == ".jsonl":
            rows: List[Dict[str, Any]] = []
            if not os.path.exists(path):
                return []
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parsed = json.loads(line)
                    if isinstance(parsed, dict):
                        rows.append(dict(parsed))
            return rows

        doc = _read_json_file(path)
        if isinstance(doc.get("rows"), list):
            return _safe_list_of_dict(doc.get("rows"))
        if isinstance(doc.get("events"), list):
            return _safe_list_of_dict(doc.get("events"))
        return []
    except Exception:
        return []


def _normalize_approved_source_event_row(raw: Dict[str, Any], patterns: List[str]) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        return {}

    event_name = _safe_text(raw.get("event_name") or raw.get("event") or raw.get("event_title"))
    source_url = _safe_text(
        raw.get("source_url")
        or raw.get("event_url")
        or raw.get("canonical_source_url")
        or raw.get("url")
    )
    canonical_source_url = _safe_text(raw.get("canonical_source_url") or source_url)
    event_url = _safe_text(raw.get("event_url") or source_url)
    source_name = _safe_text(raw.get("source_name") or _guess_source_name_from_url(source_url))
    source_type = _safe_text(raw.get("source_type") or "official")

    if not event_name or not source_url:
        return {}
    if not _url_matches_approved_patterns(source_url, patterns):
        return {}

    out = dict(raw)
    out["event_name"] = event_name
    out["source_url"] = source_url
    out["event_url"] = event_url
    out["canonical_source_url"] = canonical_source_url
    out["source_name"] = source_name
    out["source_type"] = source_type
    out["source_urls"] = [source_url]
    out["provenance"] = {
        "source_url": source_url,
        "source_urls": [source_url],
        "source_name": source_name,
        "source_type": source_type,
    }
    out["provenance_origin"] = "approved_source_live_event_ingestion"
    return out


def _get_current_week_window() -> tuple[date, date, date]:
    """Return (current_week_start, current_week_end, upcoming_window_end) for current-week discovery."""
    today = date.today()
    # Current week: Monday to Sunday
    days_since_monday = today.weekday()
    current_week_start = today - timedelta(days=days_since_monday)
    current_week_end = current_week_start + timedelta(days=6)
    # Upcoming window: extend 14 days into the future
    upcoming_window_end = today + timedelta(days=14)
    return current_week_start, current_week_end, upcoming_window_end


def _parse_event_date(date_str: str) -> date | None:
    """Parse event date from ISO format string."""
    if not date_str or not isinstance(date_str, str):
        return None
    try:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
    except (ValueError, AttributeError):
        return None


def _is_event_in_window(event_row: Dict[str, Any], window_end: date) -> bool:
    """Check if event date falls within current week or upcoming window."""
    event_date_str = _safe_text(event_row.get("event_date"))
    if not event_date_str:
        return False
    event_date = _parse_event_date(event_date_str)
    if not event_date:
        return False
    today = date.today()
    return today <= event_date <= window_end


def _is_demo_or_fixture_feed(rows: List[Dict[str, Any]]) -> bool:
    """Detect if rows contain demo/fixture markers (e.g., old static events)."""
    if not rows:
        return False
    
    # Check if any event is dated far in the past or has demo markers
    for row in rows:
        event_date_str = _safe_text(row.get("event_date"))
        event_name = _safe_text(row.get("event_name", "")).lower()
        
        # Demo/fixture markers
        demo_markers = ["demo", "fixture", "test", "sample", "placeholder"]
        if any(marker in event_name for marker in demo_markers):
            return True
        
        # If we have a date, check if it's far in the past
        if event_date_str:
            event_date = _parse_event_date(event_date_str)
            if event_date:
                # More than 30 days in the past is likely a fixture
                days_old = (date.today() - event_date).days
                if days_old > 30:
                    return True
    
    return False


def _check_feed_freshness(feed_path: str, max_age_seconds: int = 86400) -> tuple[bool, str]:
    """Check if feed file is fresh (modified within max_age_seconds).
    
    Returns: (is_fresh, status_message)
    """
    try:
        if not os.path.exists(feed_path):
            return False, "feed_file_missing"

        file_mtime = os.path.getmtime(feed_path)
        current_time = time.time()
        age_seconds = current_time - file_mtime

        if age_seconds > max_age_seconds:
            return False, "feed_stale"

        return True, "feed_fresh"
    except Exception as e:
        return False, f"feed_freshness_check_failed: {str(e)}"


def _load_approved_source_live_event_rows(root: str) -> Dict[str, Any]:
    config = _load_approved_source_ingestion_config(root)
    diagnostics: List[str] = []

    enabled = bool(config.get("enabled", True))
    patterns = [p for p in config.get("approved_source_url_patterns", []) if _safe_text(p)]
    feed_paths = [p for p in config.get("feed_paths", []) if _safe_text(p)]
    upcoming_window_days = 14
    current_week_start, current_week_end, upcoming_window_end = _get_current_week_window()

    if not enabled or not patterns:
        diagnostics.append("approved_source_not_configured")
        return {
            "rows": [],
            "diagnostics": diagnostics,
            "configured": False,
            "feed_used": "",
            "feed_status": "not_configured",
            "current_week_ready": False,
            "save_allowed": False,
            "current_week_start": str(current_week_start),
            "current_week_end": str(upcoming_window_end),
            "upcoming_window_days": upcoming_window_days,
            "current_week_rows_count": 0,
        }

    existing_feed_path = ""
    for rel_path in feed_paths:
        candidate = os.path.join(root, rel_path)
        if os.path.exists(candidate):
            existing_feed_path = candidate
            break

    fallback_used = False
    if not existing_feed_path:
        diagnostics.append("live_source_unavailable")
        fallback_used = True
        return {
            "rows": [],
            "diagnostics": diagnostics,
            "configured": True,
            "feed_used": "",
            "feed_status": "unavailable",
            "current_week_ready": False,
            "save_allowed": False,
            "current_week_start": str(current_week_start),
            "current_week_end": str(upcoming_window_end),
            "generated_at_utc": "",
            "total_rows_in_feed": 0,
            "current_week_rows": 0,
            "current_week_rows_count": 0,
            "feed_age_seconds": None,
            "source_freshness": "unavailable",
            "fallback_used": fallback_used,
            "upcoming_window_days": upcoming_window_days,
            "source_backed_event_cards": [],
        }

    # Check feed freshness
    is_fresh, freshness_status = _check_feed_freshness(existing_feed_path)
    # compute feed mtime and age
    try:
        file_mtime = os.path.getmtime(existing_feed_path)
        generated_at_utc = datetime.fromtimestamp(file_mtime, tz=timezone.utc).isoformat()
        feed_age_seconds = int(time.time() - file_mtime)
    except Exception:
        generated_at_utc = ""
        feed_age_seconds = None

    if not is_fresh:
        diagnostics.append(freshness_status)
        return {
            "rows": [],
            "diagnostics": diagnostics,
            "configured": True,
            "feed_used": existing_feed_path,
            "feed_status": "stale",
            "current_week_ready": False,
            "save_allowed": False,
            "current_week_start": str(current_week_start),
            "current_week_end": str(upcoming_window_end),
            "generated_at_utc": generated_at_utc,
            "total_rows_in_feed": 0,
            "current_week_rows": 0,
            "current_week_rows_count": 0,
            "feed_age_seconds": feed_age_seconds,
            "source_freshness": freshness_status,
            "fallback_used": False,
            "upcoming_window_days": upcoming_window_days,
            "source_backed_event_cards": [],
        }

    raw_rows = _parse_approved_source_feed_rows(existing_feed_path)
    normalized_rows = [
        _normalize_approved_source_event_row(row, patterns)
        for row in raw_rows
        if isinstance(row, dict)
    ]
    approved_rows = [row for row in normalized_rows if row]

    if not approved_rows:
        diagnostics.append("no_source_backed_events_found")
        return {
            "rows": [],
            "diagnostics": diagnostics,
            "configured": True,
            "feed_used": existing_feed_path,
            "feed_status": "no_events",
            "current_week_ready": False,
            "save_allowed": False,
            "current_week_start": str(current_week_start),
            "current_week_end": str(upcoming_window_end),
            "generated_at_utc": generated_at_utc if 'generated_at_utc' in locals() else "",
            "total_rows_in_feed": 0,
            "current_week_rows": 0,
            "current_week_rows_count": 0,
            "feed_age_seconds": feed_age_seconds if 'feed_age_seconds' in locals() else None,
            "source_freshness": freshness_status,
            "fallback_used": False,
            "upcoming_window_days": upcoming_window_days,
            "source_backed_event_cards": [],
        }

    # Detect demo/fixture feeds
    if _is_demo_or_fixture_feed(approved_rows):
        diagnostics.append("demo_or_fixture_feed_detected")
        return {
            "rows": [],
            "diagnostics": diagnostics,
            "configured": True,
            "feed_used": existing_feed_path,
            "feed_status": "demo_or_fixture_feed",
            "current_week_ready": False,
            "save_allowed": False,
            "current_week_start": str(current_week_start),
            "current_week_end": str(upcoming_window_end),
            "generated_at_utc": generated_at_utc if 'generated_at_utc' in locals() else "",
            "total_rows_in_feed": len(approved_rows),
            "current_week_rows": 0,
            "current_week_rows_count": 0,
            "feed_age_seconds": feed_age_seconds if 'feed_age_seconds' in locals() else None,
            "source_freshness": freshness_status,
            "fallback_used": False,
            "upcoming_window_days": upcoming_window_days,
            "source_backed_event_cards": [],
        }

    # Get current-week window and filter rows
    current_week_rows = [
        row for row in approved_rows
        if _is_event_in_window(row, upcoming_window_end)
    ]

    # Add metadata about discovery window and freshness
    for row in current_week_rows:
        row["_discovery_window_start"] = str(current_week_start)
        row["_discovery_window_end"] = str(upcoming_window_end)
        row["_discovery_generated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        row["_source_feed_status"] = "fresh"

    if not current_week_rows:
        diagnostics.append("no_current_week_events_found")
        return {
            "rows": [],
            "diagnostics": diagnostics,
            "configured": True,
            "feed_used": existing_feed_path,
            "feed_status": "no_current_week_source_backed_matchups",
            "current_week_ready": False,
            "save_allowed": False,
            "current_week_start": str(current_week_start),
            "current_week_end": str(upcoming_window_end),
            "total_rows_in_feed": len(approved_rows),
            "current_week_rows": 0,
            "current_week_rows_count": 0,
            "upcoming_window_days": upcoming_window_days,
            "generated_at_utc": generated_at_utc if 'generated_at_utc' in locals() else "",
            "feed_age_seconds": feed_age_seconds if 'feed_age_seconds' in locals() else None,
            "source_freshness": freshness_status,
            "fallback_used": False,
            "source_backed_event_cards": [],
        }

    diagnostics.append("current_week_events_found")
    return {
        "rows": current_week_rows,
        "diagnostics": diagnostics,
        "configured": True,
        "feed_used": existing_feed_path,
        "feed_status": "current_week_ready",
        "current_week_ready": True,
        "save_allowed": True,
        "current_week_start": str(current_week_start),
        "current_week_end": str(upcoming_window_end),
        "total_rows_in_feed": len(approved_rows),
        "current_week_rows": len(current_week_rows),
        "current_week_rows_count": len(current_week_rows),
        "upcoming_window_days": upcoming_window_days,
        "generated_at_utc": datetime.fromtimestamp(os.path.getmtime(existing_feed_path), tz=timezone.utc).isoformat(),
        "feed_age_seconds": int(time.time() - os.path.getmtime(existing_feed_path)),
        "source_freshness": "feed_fresh",
        "fallback_used": False,
        "source_backed_event_cards": current_week_rows,
    }


def _normalize_candidate_row_provenance(row: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(row) if isinstance(row, dict) else {}

    urls: List[str] = []

    provenance = out.get("provenance")
    if isinstance(provenance, dict):
        src = _safe_text(provenance.get("source_url"))
        if src:
            urls.append(src)
        urls.extend(_coerce_source_urls(provenance.get("source_urls")))

    candidate_url_fields = [
        "source_url",
        "canonical_source_url",
        "provenance_url",
        "url",
        "event_url",
        "official_url",
        "source_link",
    ]
    for key in candidate_url_fields:
        src = _safe_text(out.get(key))
        if src:
            urls.append(src)

    urls.extend(_coerce_source_urls(out.get("source_urls")))
    urls.extend(_urls_from_text(out.get("source_notes")))

    deduped_urls: List[str] = []
    seen = set()
    for url in urls:
        if url not in seen:
            deduped_urls.append(url)
            seen.add(url)

    if not deduped_urls:
        return out

    if not _safe_text(out.get("source_url")):
        out["source_url"] = deduped_urls[0]

    existing_source_urls = _coerce_source_urls(out.get("source_urls"))
    merged_urls = []
    merged_seen = set()
    for url in existing_source_urls + deduped_urls:
        if url not in merged_seen:
            merged_urls.append(url)
            merged_seen.add(url)
    out["source_urls"] = merged_urls

    provenance_dict = out.get("provenance") if isinstance(out.get("provenance"), dict) else {}
    provenance_dict = dict(provenance_dict)
    if not _safe_text(provenance_dict.get("source_url")):
        provenance_dict["source_url"] = merged_urls[0]
    provenance_dict["source_urls"] = merged_urls
    out["provenance"] = provenance_dict

    return out


def _extract_row_provenance_urls(row: Dict[str, Any]) -> List[str]:
    if not isinstance(row, dict):
        return []

    urls: List[str] = []
    provenance = row.get("provenance")
    if isinstance(provenance, dict):
        src = _safe_text(provenance.get("source_url"))
        if src:
            urls.append(src)
        urls.extend(_coerce_source_urls(provenance.get("source_urls")))

    for key in ("source_url", "canonical_source_url", "provenance_url", "url", "event_url", "official_url", "source_link"):
        src = _safe_text(row.get(key))
        if src:
            urls.append(src)

    urls.extend(_coerce_source_urls(row.get("source_urls")))

    deduped: List[str] = []
    seen = set()
    for url in urls:
        if url and url not in seen:
            deduped.append(url)
            seen.add(url)
    return deduped


def _build_event_provenance_lookup(event_rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    lookup: Dict[str, Dict[str, Any]] = {}
    for row in event_rows:
        if not isinstance(row, dict):
            continue
        event_name = _safe_text(row.get("event_name") or row.get("event") or row.get("event_title"))
        if not event_name:
            continue
        urls = _extract_row_provenance_urls(row)
        if not urls:
            continue
        lookup[event_name.lower()] = {
            "urls": urls,
            "source_name": _safe_text(row.get("source_name") or _guess_source_name_from_url(urls[0])),
            "source_type": _safe_text(row.get("source_type") or "official"),
            "event_url": _safe_text(row.get("event_url") or urls[0]),
            "canonical_source_url": _safe_text(row.get("canonical_source_url") or urls[0]),
        }
    return lookup


def _propagate_event_provenance(
    candidate_rows: List[Dict[str, Any]],
    event_provenance_lookup: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    out_rows: List[Dict[str, Any]] = []
    for row in candidate_rows:
        normalized = _normalize_candidate_row_provenance(row)
        if _extract_row_provenance_urls(normalized):
            out_rows.append(normalized)
            continue

        event_name = _safe_text(normalized.get("event_name") or normalized.get("event") or normalized.get("event_title"))
        key = event_name.lower() if event_name else ""
        event_meta = event_provenance_lookup.get(key, {}) if key else {}
        event_urls = event_meta.get("urls", []) if isinstance(event_meta, dict) else []
        if not event_urls:
            out_rows.append(normalized)
            continue

        enriched = dict(normalized)
        enriched["source_url"] = event_urls[0]
        enriched["source_urls"] = list(event_urls)
        if not _safe_text(enriched.get("source_name")):
            enriched["source_name"] = _safe_text(event_meta.get("source_name")) or _guess_source_name_from_url(event_urls[0])
        if not _safe_text(enriched.get("source_type")):
            enriched["source_type"] = _safe_text(event_meta.get("source_type") or "official")
        if not _safe_text(enriched.get("event_url")):
            enriched["event_url"] = _safe_text(event_meta.get("event_url") or event_urls[0])
        if not _safe_text(enriched.get("canonical_source_url")):
            enriched["canonical_source_url"] = _safe_text(event_meta.get("canonical_source_url") or event_urls[0])
        provenance = enriched.get("provenance") if isinstance(enriched.get("provenance"), dict) else {}
        provenance = dict(provenance)
        provenance["source_url"] = event_urls[0]
        provenance["source_urls"] = list(event_urls)
        if not _safe_text(provenance.get("source_name")):
            provenance["source_name"] = _safe_text(enriched.get("source_name"))
        if not _safe_text(provenance.get("source_type")):
            provenance["source_type"] = _safe_text(enriched.get("source_type") or "official")
        enriched["provenance"] = provenance
        enriched["provenance_origin"] = "event_level_source"
        out_rows.append(enriched)
    return out_rows


def _build_fight_ref_from_row(row: Dict[str, Any]) -> str:
    if not isinstance(row, dict):
        return ""

    direct_ref = _safe_text(row.get("fight_key") or row.get("fight_name") or row.get("matchup_key") or row.get("id"))
    if direct_ref:
        return direct_ref

    red = _safe_text(row.get("red_fighter") or row.get("fighter_a") or row.get("fighter1") or row.get("fighter_a_name"))
    blue = _safe_text(row.get("blue_fighter") or row.get("fighter_b") or row.get("fighter2") or row.get("fighter_b_name"))
    if red and blue:
        return f"{red} vs {blue}"

    return ""


def _normalize_runtime_state(runtime_state: Dict[str, Any]) -> Dict[str, Any]:
    state = _safe_dict(runtime_state)
    return {
        "manual_intake_text": _safe_text(state.get("manual_intake_text", "")),
        "discovered_candidate_rows": _safe_list_of_dict(state.get("discovered_candidate_rows", [])),
        "approved_source_preview_rows": _safe_list(state.get("approved_source_preview_rows", [])),
        "live_source_status": _safe_dict(state.get("live_source_status", {})),
        "approved_historical_records": _safe_list_of_dict(state.get("approved_historical_records", [])),
        "report_history_records": _safe_list_of_dict(state.get("report_history_records", [])),
        "result_ledger_records": _safe_list_of_dict(state.get("result_ledger_records", [])),
        "global_read_projection_records": _safe_list_of_dict(state.get("global_read_projection_records", [])),
        "event_hint": _safe_text(state.get("event_hint", "")),
        "promotion_hint": _safe_text(state.get("promotion_hint", "")),
        "date_window": _safe_dict(state.get("date_window", {})),
        "local_candidate_rows": _safe_list_of_dict(state.get("local_candidate_rows", [])),
        "selected_fights": _safe_list_of_dict(state.get("selected_fights", [])),
        "saved_fight_queue_refs": _safe_list(state.get("saved_fight_queue_refs", [])),
        "report_status_refs": _safe_list(state.get("report_status_refs", [])),
        "analysis_ready_refs": _safe_list(state.get("analysis_ready_refs", [])),
        "customer_ready_refs": _safe_list(state.get("customer_ready_refs", [])),
        "selected_fight_refs": _safe_list(state.get("selected_fight_refs", [])),
        "waiting_result_rows": _safe_list_of_dict(state.get("waiting_result_rows", [])),
        "selected_result_keys": _safe_list(state.get("selected_result_keys", [])),
        "result_source_refs": _safe_list(state.get("result_source_refs", [])),
        "report_refs": _safe_list(state.get("report_refs", [])),
        "comparison_refs": _safe_list(state.get("comparison_refs", [])),
        "source_yield_preview_rows": _safe_list_of_dict(state.get("source_yield_preview_rows", [])),
        "accuracy_ledger_missing": _safe_bool(state.get("accuracy_ledger_missing", False)),
    }


def load_readonly_runtime_state(
    runtime_state_override: Dict[str, Any] | None = None,
    workspace_root: str | None = None,
) -> Dict[str, Any]:
    """Load read-only runtime state with safe defaults and optional override.

    If a key is present in runtime_state_override, it takes precedence.
    Missing keys are populated from local files when safely available.
    """
    root = workspace_root or _default_workspace_root()
    override = _safe_dict(runtime_state_override)

    status_text = _read_text_file(os.path.join(root, "status.txt"))
    event_rows = _read_csv_rows(os.path.join(root, "event_coverage_queue.csv"))
    queue_rows = _read_csv_rows(os.path.join(root, "fighter_intake_unresolved_queue.csv"))
    bout_rows = _read_csv_rows(os.path.join(root, "one_samurai_1_bouts.csv"))
    ledger = _read_json_file(os.path.join(root, "ops", "accuracy", "accuracy_ledger.json"))
    ledger_path = os.path.join(root, "ops", "accuracy", "accuracy_ledger.json")

    approved_source_live = _load_approved_source_live_event_rows(root)
    approved_source_rows = _safe_list_of_dict(approved_source_live.get("rows", []))
    merged_event_rows = approved_source_rows + event_rows

    approved_source_refs: List[str] = []
    seen_refs = set()
    for row in approved_source_rows:
        src = _safe_text(row.get("source_name") or row.get("source_url"))
        if src and src not in seen_refs:
            approved_source_refs.append(src)
            seen_refs.add(src)

    live_source_status = {
        "enabled": bool(approved_source_live.get("configured", False)),
        "approved_source_event_rows_count": len(approved_source_rows),
        "diagnostics": _safe_list(approved_source_live.get("diagnostics", [])),
        "feed_used": _safe_text(approved_source_live.get("feed_used", "")),
        "feed_status": _safe_text(approved_source_live.get("feed_status", "unknown")),
        "current_week_ready": bool(approved_source_live.get("current_week_ready", False)),
        "save_allowed": bool(approved_source_live.get("save_allowed", False)),
        "current_week_start": _safe_text(approved_source_live.get("current_week_start", "")),
        "current_week_end": _safe_text(approved_source_live.get("current_week_end", "")),
        "generated_at_utc": _safe_text(approved_source_live.get("generated_at_utc", "")),
        "total_rows_in_feed": int(approved_source_live.get("total_rows_in_feed", 0)) if approved_source_live.get("total_rows_in_feed") else 0,
        "current_week_rows": int(approved_source_live.get("current_week_rows", 0)) if approved_source_live.get("current_week_rows") else 0,
        "current_week_rows_count": int(approved_source_live.get("current_week_rows_count", approved_source_live.get("current_week_rows", 0))) if approved_source_live.get("current_week_rows_count") is not None else 0,
        "upcoming_window_days": int(approved_source_live.get("upcoming_window_days", 14)) if approved_source_live.get("upcoming_window_days") is not None else 14,
        "feed_age_seconds": approved_source_live.get("feed_age_seconds") if approved_source_live.get("feed_age_seconds") is not None else None,
        "source_freshness": _safe_text(approved_source_live.get("source_freshness", "")),
        "fallback_used": bool(approved_source_live.get("fallback_used", False)),
        "source_backed_event_cards": _safe_list_of_dict(approved_source_live.get("source_backed_event_cards", [])),
    }

    state = {
        "manual_intake_text": status_text,
        "discovered_candidate_rows": merged_event_rows,
        "approved_source_preview_rows": approved_source_refs,
        "live_source_status": live_source_status,
        "approved_historical_records": [],
        "report_history_records": [],
        "result_ledger_records": [],
        "global_read_projection_records": [],
        "event_hint": "",
        "promotion_hint": "",
        "date_window": {},
        "local_candidate_rows": queue_rows,
        "selected_fights": [],
        "saved_fight_queue_refs": [],
        "report_status_refs": [],
        "analysis_ready_refs": [],
        "customer_ready_refs": [],
        "selected_fight_refs": [ref for ref in (_build_fight_ref_from_row(row) for row in bout_rows) if ref],
        "waiting_result_rows": _safe_list_of_dict(ledger.get("waiting_for_results", [])),
        "selected_result_keys": [],
        "result_source_refs": [],
        "report_refs": [],
        "comparison_refs": [],
        "source_yield_preview_rows": _safe_list_of_dict(ledger.get("waiting_for_results", [])),
        "accuracy_ledger_missing": not os.path.exists(ledger_path),
    }

    state.update(override)
    return _normalize_runtime_state(state)


def load_button1_runtime_state_preview(
    runtime_state_override: Dict[str, Any] | None = None,
    workspace_root: str | None = None,
) -> Dict[str, Any]:
    """Load Button 1 preview state with orchestrated live-source status.

    This preview path keeps stale approved-source JSON from acting as live
    discovery authority when no approved provider is configured.
    """
    root = workspace_root or _default_workspace_root()
    state = load_readonly_runtime_state(runtime_state_override, workspace_root=root)
    preview_state = dict(state)
    preview_state["registry_adapter_status"] = _load_button1_registry_adapter_status_preview(root)
    provider_registry = _build_button1_orchestrator_registry_preview(preview_state["registry_adapter_status"])
    preview_state["live_source_status"] = run_button1_live_source_provider_orchestrator(
        provider_registry=provider_registry
    )

    # Preserve adapter diagnostics in the live-source status payload for fail-closed visibility.
    adapter_diagnostics = [
        _safe_text(d)
        for d in _safe_list(preview_state["registry_adapter_status"].get("diagnostics", []))
        if _safe_text(d)
    ]
    live_source_status = _safe_dict(preview_state.get("live_source_status", {}))
    live_diagnostics = [
        _safe_text(d)
        for d in _safe_list(live_source_status.get("diagnostics", []))
        if _safe_text(d)
    ]
    for diag in adapter_diagnostics:
        if diag not in live_diagnostics:
            live_diagnostics.append(diag)
    live_source_status["diagnostics"] = live_diagnostics
    preview_state["live_source_status"] = live_source_status

    preview_state["execution_gate_status"] = _load_button1_execution_gate_status_preview(preview_state)
    preview_state["approved_source_preview_rows"] = []
    preview_state["discovered_candidate_rows"] = _safe_list_of_dict(preview_state.get("local_candidate_rows", []))
    return preview_state


def build_button1_runtime_context(
    runtime_state_override: Dict[str, Any] | None = None,
    workspace_root: str | None = None,
) -> LocalAIInputContextPack:
    state = load_readonly_runtime_state(runtime_state_override, workspace_root=workspace_root)
    raw_candidate_rows = _safe_list_of_dict(state.get("discovered_candidate_rows", [])) + _safe_list_of_dict(
        state.get("local_candidate_rows", [])
    )
    event_rows = _safe_list_of_dict(state.get("discovered_candidate_rows", []))
    event_provenance_lookup = _build_event_provenance_lookup(event_rows)
    candidate_rows = _propagate_event_provenance(raw_candidate_rows, event_provenance_lookup)

    ranked_candidate_rows = build_button1_auto_discovery_readiness_ranking(candidate_rows)

    payload = {
        "manual_text": state.get("manual_intake_text", ""),
        "approved_source_refs": _safe_list(state.get("approved_source_preview_rows", [])),
        "live_source_status": _safe_dict(state.get("live_source_status", {})),
        "registry_adapter_status": _safe_dict(state.get("registry_adapter_status", {})),
        "event_hint": state.get("event_hint", ""),
        "promotion_hint": state.get("promotion_hint", ""),
        "date_window": _safe_dict(state.get("date_window", {})),
        "candidate_rows": ranked_candidate_rows,
        # Advanced read-only known-record projection context for Button 1 preview.
        "approved_historical_records": _safe_list_of_dict(state.get("approved_historical_records", [])),
        "report_history_records": _safe_list_of_dict(state.get("report_history_records", [])),
        "result_ledger_records": _safe_list_of_dict(state.get("result_ledger_records", [])),
        "global_read_projection_records": _safe_list_of_dict(state.get("global_read_projection_records", [])),
    }

    pack = LocalAIInputContextPack(
        source_button="button1_find_fights",
        input_ref={
            "kind": "discovery_preview",
            "ref_id": "b1_discovery_preview",
            "payload": payload,
        },
    )
    pack.validate()
    return pack


def build_button1_runtime_context_preview(
    runtime_state_override: Dict[str, Any] | None = None,
    workspace_root: str | None = None,
) -> LocalAIInputContextPack:
    state = load_button1_runtime_state_preview(runtime_state_override, workspace_root=workspace_root)
    raw_candidate_rows = _safe_list_of_dict(state.get("discovered_candidate_rows", [])) + _safe_list_of_dict(
        state.get("local_candidate_rows", [])
    )
    event_rows = _safe_list_of_dict(state.get("discovered_candidate_rows", []))
    event_provenance_lookup = _build_event_provenance_lookup(event_rows)
    candidate_rows = _propagate_event_provenance(raw_candidate_rows, event_provenance_lookup)

    ranked_candidate_rows = build_button1_auto_discovery_readiness_ranking(candidate_rows)

    payload = {
        "manual_text": state.get("manual_intake_text", ""),
        "approved_source_refs": _safe_list(state.get("approved_source_preview_rows", [])),
        "live_source_status": _safe_dict(state.get("live_source_status", {})),
        "registry_adapter_status": _safe_dict(state.get("registry_adapter_status", {})),
        "execution_gate_status": _safe_dict(state.get("execution_gate_status", {})),
        "event_hint": state.get("event_hint", ""),
        "promotion_hint": state.get("promotion_hint", ""),
        "date_window": _safe_dict(state.get("date_window", {})),
        "candidate_rows": ranked_candidate_rows,
        "approved_historical_records": _safe_list_of_dict(state.get("approved_historical_records", [])),
        "report_history_records": _safe_list_of_dict(state.get("report_history_records", [])),
        "result_ledger_records": _safe_list_of_dict(state.get("result_ledger_records", [])),
        "global_read_projection_records": _safe_list_of_dict(state.get("global_read_projection_records", [])),
    }

    pack = LocalAIInputContextPack(
        source_button="button1_find_fights",
        input_ref={
            "kind": "discovery_preview",
            "ref_id": "b1_discovery_preview",
            "payload": payload,
        },
    )
    pack.validate()
    return pack


def build_button2_runtime_context(
    runtime_state_override: Dict[str, Any] | None = None,
    workspace_root: str | None = None,
) -> LocalAIInputContextPack:
    state = load_readonly_runtime_state(runtime_state_override, workspace_root=workspace_root)

    selected_fights = _safe_list_of_dict(state.get("selected_fights", []))
    if not selected_fights:
        selected_refs = _safe_list(state.get("selected_fight_refs", []))
        selected_fights = [{"fight_ref": str(ref)} for ref in selected_refs if isinstance(ref, str) and ref.strip()]

    raw_input = {
        "selected_fights": selected_fights,
        "queued_fight_refs": _safe_list(state.get("saved_fight_queue_refs", [])),
        "report_status_refs": _safe_list(state.get("report_status_refs", [])),
        "analysis_ready_refs": _safe_list(state.get("analysis_ready_refs", [])),
        "customer_ready_refs": _safe_list(state.get("customer_ready_refs", [])),
    }
    return build_button2_generate_pdfs_context(raw_input)


def build_button3_runtime_context(
    runtime_state_override: Dict[str, Any] | None = None,
    workspace_root: str | None = None,
) -> LocalAIInputContextPack:
    state = load_readonly_runtime_state(runtime_state_override, workspace_root=workspace_root)

    waiting_rows = _safe_list_of_dict(state.get("waiting_result_rows", []))
    if not waiting_rows:
        waiting_rows = _safe_list_of_dict(state.get("source_yield_preview_rows", []))

    raw_input = {
        "waiting_rows": waiting_rows,
        "selected_keys": _safe_list(state.get("selected_result_keys", [])),
        "result_source_refs": _safe_list(state.get("result_source_refs", [])),
        "report_refs": _safe_list(state.get("report_refs", [])),
        "comparison_refs": _safe_list(state.get("comparison_refs", [])),
        "source_status": {
            "accuracy_ledger_missing": bool(state.get("accuracy_ledger_missing", False)),
        },
    }
    return build_button3_find_results_context(raw_input)


def build_runtime_context_pack(
    source_button: str,
    runtime_state_override: Dict[str, Any] | None = None,
    workspace_root: str | None = None,
) -> LocalAIInputContextPack:
    if source_button not in ALLOWED_SOURCE_BUTTONS:
        raise ValueError(f"invalid source_button: {source_button}")

    if source_button == "button1_find_fights":
        return build_button1_runtime_context(runtime_state_override, workspace_root=workspace_root)
    if source_button == "button2_generate_pdfs":
        return build_button2_runtime_context(runtime_state_override, workspace_root=workspace_root)
    return build_button3_runtime_context(runtime_state_override, workspace_root=workspace_root)


def build_runtime_context_payload(
    source_button: str,
    runtime_state_override: Dict[str, Any] | None = None,
    workspace_root: str | None = None,
) -> Dict[str, Any]:
    """Return route-ready context_pack payload for workflow-preview API."""
    pack = build_runtime_context_pack(
        source_button,
        runtime_state_override=runtime_state_override,
        workspace_root=workspace_root,
    )
    return _safe_dict(pack.input_ref.get("payload", {}))


__all__ = [
    "build_button1_runtime_context",
    "build_button1_runtime_context_preview",
    "build_button2_runtime_context",
    "build_button3_runtime_context",
    "build_runtime_context_pack",
    "build_runtime_context_payload",
    "load_button1_runtime_state_preview",
    "load_readonly_runtime_state",
]
