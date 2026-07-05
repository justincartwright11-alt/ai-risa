"""Button 1 live source provider orchestrator scaffold (fail-closed).

This module only scaffolds provider orchestration and payload normalization.
It does not perform queue/database writes and keeps operator approval required.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Protocol


class Button1LiveSourceProviderAdapter(Protocol):
    """Adapter contract for approved live-source providers."""

    def collect_current_week_upcoming(self, provider_config: Dict[str, Any], now_utc: datetime) -> Dict[str, Any]:
        """Return provider payload containing source-backed event rows."""


def _safe_text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _safe_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _safe_list(value: Any) -> List[Any]:
    return list(value) if isinstance(value, list) else []


def _utc_now(now_utc: Optional[datetime] = None) -> datetime:
    if isinstance(now_utc, datetime):
        if now_utc.tzinfo is None:
            return now_utc.replace(tzinfo=timezone.utc)
        return now_utc.astimezone(timezone.utc)
    return datetime.now(timezone.utc)


def _iso_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _get_discovery_window(now_utc: datetime, upcoming_window_days: int) -> tuple[date, date]:
    today = now_utc.date()
    current_week_start = today - timedelta(days=today.weekday())
    current_week_end = today + timedelta(days=upcoming_window_days)
    return current_week_start, current_week_end


def _parse_event_date(row: Dict[str, Any]) -> Optional[date]:
    txt = _safe_text(row.get("event_date"))
    if not txt:
        return None
    try:
        return datetime.strptime(txt, "%Y-%m-%d").date()
    except ValueError:
        return None


def _normalize_source_row(row: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(row, dict):
        return {}

    event_name = _safe_text(row.get("event_name") or row.get("event") or row.get("event_title"))
    source_url = _safe_text(
        row.get("source_url") or row.get("event_url") or row.get("canonical_source_url") or row.get("url")
    )
    source_name = _safe_text(row.get("source_name") or "approved_live_source")
    source_type = _safe_text(row.get("source_type") or "official")
    event_date = _parse_event_date(row)

    if not event_name or not source_url or not event_date:
        return {}

    out = dict(row)
    out["event_name"] = event_name
    out["source_url"] = source_url
    out["source_name"] = source_name
    out["source_type"] = source_type
    out["event_date"] = event_date.isoformat()

    source_urls = _safe_list(out.get("source_urls"))
    deduped_urls: List[str] = []
    seen = set()
    for url in [source_url] + [_safe_text(x) for x in source_urls]:
        if not url or url in seen:
            continue
        deduped_urls.append(url)
        seen.add(url)
    out["source_urls"] = deduped_urls
    return out


def _base_result(
    *,
    now_utc: datetime,
    upcoming_window_days: int,
    provider_names: List[str],
    selected_provider: str,
    diagnostics: List[str],
    feed_status: str,
    feed_used: str,
    source_freshness: str,
    feed_age_seconds: Optional[int],
    current_week_ready: bool,
    save_allowed: bool,
    source_backed_event_cards: List[Dict[str, Any]],
    total_rows_in_feed: int,
    current_week_rows: int,
    approved_source_event_rows_count: int,
    current_week_rows_count: int,
    source_call_authorization_present: bool = False,
    source_call_authorization_valid: bool = False,
    source_domain_authorized: bool = False,
    http_method_authorized: bool = False,
    response_type_supported: bool = False,
    provenance_required: bool = True,
    provenance_complete: bool = False,
) -> Dict[str, Any]:
    window_start, window_end = _get_discovery_window(now_utc, upcoming_window_days)

    return {
        "feed_status": feed_status,
        "feed_used": feed_used,
        "generated_at_utc": _iso_utc(now_utc),
        "current_week_start": window_start.isoformat(),
        "current_week_end": window_end.isoformat(),
        "upcoming_window_days": int(upcoming_window_days),
        "source_freshness": source_freshness,
        "feed_age_seconds": feed_age_seconds,
        "total_rows_in_feed": int(total_rows_in_feed),
        "current_week_rows": int(current_week_rows),
        "current_week_ready": bool(current_week_ready),
        "save_allowed": bool(save_allowed),
        "fallback_used": False,
        "diagnostics": list(dict.fromkeys([d for d in diagnostics if _safe_text(d)])),
        "provider_count": len(provider_names),
        "provider_names": provider_names,
        "selected_provider": selected_provider,
        "source_backed_event_cards": source_backed_event_cards,
        "current_week_rows_count": int(current_week_rows_count),
        "approved_source_event_rows_count": int(approved_source_event_rows_count),
        # Explicit governance marker: save_allowed indicates preview eligibility only.
        "operator_approval_required": True,
        "source_call_authorization_present": source_call_authorization_present,
        "source_call_authorization_valid": source_call_authorization_valid,
        "source_domain_authorized": source_domain_authorized,
        "http_method_authorized": http_method_authorized,
        "response_type_supported": response_type_supported,
        "provenance_required": provenance_required,
        "provenance_complete": provenance_complete,
        "customer_pdf_generation_performed": False,
        "learning_write_performed": False,
        "calibration_write_performed": False,
        "auto_save_performed": False,
        "queue_write_performed": False,
        "database_write_performed": False,
        "refreshed_feed_artifact": {
            "schema_version": "button1_live_source_provider_orchestrator_scaffold_v1",
            "generated_at_utc": _iso_utc(now_utc),
            "provider_results": [],
            "rows": source_backed_event_cards,
            "diagnostics": list(dict.fromkeys([d for d in diagnostics if _safe_text(d)])),
        },
    }


def run_button1_live_source_provider_orchestrator(
    provider_registry: Optional[List[Dict[str, Any]]] = None,
    now_utc: Optional[datetime] = None,
    upcoming_window_days: int = 14,
) -> Dict[str, Any]:
    """Execute approved-provider scaffold flow and return normalized status.

    Fail-closed guarantees:
    - No provider configured/enabled => unavailable and save disallowed.
    - Invalid provider payload => unavailable and save disallowed.
    - No in-window rows => no_current_week_source_backed_matchups.
    - Ready state only when valid source-backed rows are in the window.
    """

    current_now = _utc_now(now_utc)
    window_start, window_end = _get_discovery_window(current_now, int(upcoming_window_days))
    registry = [r for r in _safe_list(provider_registry) if isinstance(r, dict)]
    provider_names = [_safe_text(r.get("name")) for r in registry if _safe_text(r.get("name"))]
    selected_name = provider_names[0] if provider_names else ""

    if not registry:
        return _base_result(
            now_utc=current_now,
            upcoming_window_days=upcoming_window_days,
            provider_names=[],
            selected_provider="",
            diagnostics=["no_approved_live_source_provider_configured"],
            feed_status="unavailable",
            feed_used="",
            source_freshness="unavailable",
            feed_age_seconds=None,
            current_week_ready=False,
            save_allowed=False,
            source_backed_event_cards=[],
            total_rows_in_feed=0,
            current_week_rows=0,
            approved_source_event_rows_count=0,
            current_week_rows_count=0,
        )

    enabled_providers = [r for r in registry if bool(r.get("enabled", False))]
    if not enabled_providers:
        return _base_result(
            now_utc=current_now,
            upcoming_window_days=upcoming_window_days,
            provider_names=provider_names,
            selected_provider="",
            diagnostics=["provider_disabled"],
            feed_status="unavailable",
            feed_used=selected_name,
            source_freshness="unavailable",
            feed_age_seconds=None,
            current_week_ready=False,
            save_allowed=False,
            source_backed_event_cards=[],
            total_rows_in_feed=0,
            current_week_rows=0,
            approved_source_event_rows_count=0,
            current_week_rows_count=0,
        )

    selected = enabled_providers[0]
    selected_name = _safe_text(selected.get("name"))
    adapter = selected.get("adapter")
    provider_config = _safe_dict(selected.get("config"))

    if adapter is None or not hasattr(adapter, "collect_current_week_upcoming"):
        return _base_result(
            now_utc=current_now,
            upcoming_window_days=upcoming_window_days,
            provider_names=provider_names,
            selected_provider=selected_name,
            diagnostics=["provider_payload_invalid"],
            feed_status="unavailable",
            feed_used=selected_name,
            source_freshness="provider_payload_invalid",
            feed_age_seconds=None,
            current_week_ready=False,
            save_allowed=False,
            source_backed_event_cards=[],
            total_rows_in_feed=0,
            current_week_rows=0,
            approved_source_event_rows_count=0,
            current_week_rows_count=0,
        )

    try:
        payload = adapter.collect_current_week_upcoming(provider_config, current_now)
    except Exception:
        return _base_result(
            now_utc=current_now,
            upcoming_window_days=upcoming_window_days,
            provider_names=provider_names,
            selected_provider=selected_name,
            diagnostics=["provider_payload_invalid"],
            feed_status="unavailable",
            feed_used=selected_name,
            source_freshness="provider_payload_invalid",
            feed_age_seconds=None,
            current_week_ready=False,
            save_allowed=False,
            source_backed_event_cards=[],
            total_rows_in_feed=0,
            current_week_rows=0,
            approved_source_event_rows_count=0,
            current_week_rows_count=0,
        )

    if not isinstance(payload, dict):
        return _base_result(
            now_utc=current_now,
            upcoming_window_days=upcoming_window_days,
            provider_names=provider_names,
            selected_provider=selected_name,
            diagnostics=["provider_payload_invalid"],
            feed_status="unavailable",
            feed_used=selected_name,
            source_freshness="provider_payload_invalid",
            feed_age_seconds=None,
            current_week_ready=False,
            save_allowed=False,
            source_backed_event_cards=[],
            total_rows_in_feed=0,
            current_week_rows=0,
            approved_source_event_rows_count=0,
            current_week_rows_count=0,
        )

    payload_rows = payload.get("rows")
    if not isinstance(payload_rows, list):
        return _base_result(
            now_utc=current_now,
            upcoming_window_days=upcoming_window_days,
            provider_names=provider_names,
            selected_provider=selected_name,
            diagnostics=["provider_payload_invalid"],
            feed_status="unavailable",
            feed_used=selected_name,
            source_freshness="provider_payload_invalid",
            feed_age_seconds=None,
            current_week_ready=False,
            save_allowed=False,
            source_backed_event_cards=[],
            total_rows_in_feed=0,
            current_week_rows=0,
            approved_source_event_rows_count=0,
            current_week_rows_count=0,
        )

    normalized_rows = [_normalize_source_row(r) for r in payload_rows if isinstance(r, dict)]
    approved_rows = [r for r in normalized_rows if r]

    in_window_rows: List[Dict[str, Any]] = []
    for row in approved_rows:
        event_date = _parse_event_date(row)
        if event_date is None:
            continue
        if window_start <= event_date <= window_end:
            in_window_rows.append(row)

    if not in_window_rows:
        return _base_result(
            now_utc=current_now,
            upcoming_window_days=upcoming_window_days,
            provider_names=provider_names,
            selected_provider=selected_name,
            diagnostics=["no_current_week_source_backed_matchups"],
            feed_status="no_current_week_source_backed_matchups",
            feed_used=selected_name,
            source_freshness="provider_fresh",
            feed_age_seconds=None,
            current_week_ready=False,
            save_allowed=False,
            source_backed_event_cards=[],
            total_rows_in_feed=len(approved_rows),
            current_week_rows=0,
            approved_source_event_rows_count=len(approved_rows),
            current_week_rows_count=0,
        )

    return _base_result(
        now_utc=current_now,
        upcoming_window_days=upcoming_window_days,
        provider_names=provider_names,
        selected_provider=selected_name,
        diagnostics=["current_week_source_backed_matchups_found"],
        feed_status="current_week_ready",
        feed_used=selected_name,
        source_freshness="provider_fresh",
        feed_age_seconds=None,
        current_week_ready=True,
        save_allowed=True,
        source_backed_event_cards=in_window_rows,
        total_rows_in_feed=len(approved_rows),
        current_week_rows=len(in_window_rows),
        approved_source_event_rows_count=len(approved_rows),
        current_week_rows_count=len(in_window_rows),
    )
