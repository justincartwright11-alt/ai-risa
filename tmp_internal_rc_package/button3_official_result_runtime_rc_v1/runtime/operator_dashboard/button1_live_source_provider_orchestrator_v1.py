"""Button 1 live source provider orchestrator scaffold (fail-closed).

This module only scaffolds provider orchestration and payload normalization.
It does not perform queue/database writes and keeps operator approval required.
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Protocol
from urllib import error as urllib_error
from urllib import request as urllib_request
from urllib.parse import urljoin, urlparse


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


def _safe_int(value: Any) -> Optional[int]:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        txt = value.strip()
        if txt.isdigit():
            try:
                return int(txt)
            except Exception:
                return None
    return None


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


def _is_ufc_event_url(url: str) -> bool:
    txt = _safe_text(url)
    if not txt:
        return False
    parsed = urlparse(txt)
    if parsed.scheme not in {"http", "https"}:
        return False
    host = (parsed.netloc or "").lower()
    if host.startswith("www."):
        host = host[4:]
    return host == "ufc.com" and "/event/" in (parsed.path or "").lower()


_MONTHS = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}


def _normalize_ufc_event_url(url: str, base_url: str) -> str:
    txt = _safe_text(url)
    if not txt:
        return ""
    absolute = urljoin(base_url, txt)
    parsed = urlparse(absolute)
    if parsed.scheme not in {"http", "https"}:
        return ""
    host = (parsed.netloc or "").lower()
    if host.startswith("www."):
        host = host[4:]
    if host != "ufc.com":
        return ""
    path = parsed.path or ""
    if "/event/" not in path.lower():
        return ""
    normalized_path = path.rstrip("/")
    if not normalized_path:
        return ""
    return f"https://www.ufc.com{normalized_path}"


def _extract_json_blocks(html: str) -> List[str]:
    if not html:
        return []
    blocks = re.findall(
        r"<script[^>]*>(.*?)</script>",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return [block.strip() for block in blocks if _safe_text(block)]


def _iter_nested_values(node: Any):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _iter_nested_values(value)
    elif isinstance(node, list):
        for item in node:
            yield from _iter_nested_values(item)


def _parse_any_date_to_iso(value: Any, default_year: int) -> str:
    if isinstance(value, dict):
        for key in ("value", "date", "startDate", "datetime", "raw"):
            normalized = _parse_any_date_to_iso(value.get(key), default_year=default_year)
            if normalized:
                return normalized
        return ""
    if isinstance(value, list):
        for item in value:
            normalized = _parse_any_date_to_iso(item, default_year=default_year)
            if normalized:
                return normalized
        return ""

    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()

    txt = _safe_text(value)
    if not txt:
        return ""

    try:
        return datetime.fromisoformat(txt.replace("Z", "+00:00")).date().isoformat()
    except Exception:
        pass

    m = re.search(r"(?P<month>[A-Za-z]{3,9})\s+(?P<day>\d{1,2})(?:,\s*(?P<year>\d{4}))?", txt)
    if m:
        month_txt = _safe_text(m.group("month")).lower()
        day = _safe_int(m.group("day"))
        year = _safe_int(m.group("year")) or default_year
        month = _MONTHS.get(month_txt)
        if month and day and year:
            try:
                return date(year, month, day).isoformat()
            except Exception:
                return ""
    return ""


def _extract_event_date(candidate: Dict[str, Any], default_year: int) -> str:
    date_keys = (
        "event_date",
        "eventDate",
        "event_date_value",
        "event_date_iso",
        "startDate",
        "start_date",
        "dateTime",
        "datetime",
        "date",
        "field_date",
        "field_event_date",
        "field_event_datetime",
        "event_date_text",
        "display_date",
    )
    for key in date_keys:
        normalized = _parse_any_date_to_iso(candidate.get(key), default_year=default_year)
        if normalized:
            return normalized
    return ""


def _extract_event_name(candidate: Dict[str, Any]) -> str:
    name_keys = (
        "event_name",
        "name",
        "title",
        "event",
        "headline",
        "label",
        "card_title",
        "event_title",
    )
    for key in name_keys:
        value = candidate.get(key)
        if isinstance(value, dict):
            txt = _safe_text(value.get("rendered") or value.get("value") or value.get("text"))
        else:
            txt = _safe_text(value)
        if txt:
            return txt
    return ""


def _extract_event_url(candidate: Dict[str, Any], base_url: str) -> str:
    url_keys = (
        "source_url",
        "url",
        "event_url",
        "canonical_source_url",
        "canonical_url",
        "path",
        "link",
        "href",
        "alias",
        "slug",
    )
    for key in url_keys:
        value = candidate.get(key)
        if isinstance(value, dict):
            value = value.get("url") or value.get("href") or value.get("path") or value.get("value")
        normalized = _normalize_ufc_event_url(_safe_text(value), base_url)
        if normalized:
            return normalized
    return ""


def _extract_ufc_candidates_from_json(html: str) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    for block in _extract_json_blocks(html):
        parsed: Any = None
        try:
            parsed = json.loads(block)
        except Exception:
            continue
        for item in _iter_nested_values(parsed):
            if not isinstance(item, dict):
                continue
            maybe_url = _safe_text(item.get("url") or item.get("event_url") or item.get("path") or item.get("link"))
            if "/event/" not in maybe_url.lower():
                continue
            candidates.append(dict(item))
    return candidates


def _extract_ufc_candidates_from_html_links(html: str) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    anchor_pattern = re.compile(
        r"<a[^>]*href=[\"'](?P<href>[^\"']+)[\"'][^>]*>(?P<label>.*?)</a>",
        flags=re.IGNORECASE | re.DOTALL,
    )

    for match in anchor_pattern.finditer(html):
        href_txt = _safe_text(match.group("href"))
        if "/event/" not in href_txt.lower():
            continue
        label_raw = re.sub(r"<[^>]+>", " ", _safe_text(match.group("label")))
        label = re.sub(r"\s+", " ", label_raw).strip()
        start = max(0, match.start() - 300)
        end = min(len(html), match.end() + 300)
        context = html[start:end]

        context_date = ""
        for pattern in (
            r"datetime=[\"']([^\"']+)[\"']",
            r"data(?:-|_)event(?:-|_)date=[\"']([^\"']+)[\"']",
            r"\b(\d{4}-\d{2}-\d{2})\b",
            r"\b([A-Za-z]{3,9}\s+\d{1,2},\s*\d{4})\b",
        ):
            m = re.search(pattern, context, flags=re.IGNORECASE)
            if m:
                context_date = _safe_text(m.group(1))
                break

        candidate: Dict[str, Any] = {"url": href_txt}
        if label:
            candidate["name"] = label
        if context_date:
            candidate["event_date_text"] = context_date
        candidates.append(candidate)
    return candidates


def _extract_ufc_event_date_from_detail_html(html: str, default_year: int) -> str:
    if not html:
        return ""

    # Priority A: structured Event schedule fields.
    for block in _extract_json_blocks(html):
        parsed: Any = None
        try:
            parsed = json.loads(block)
        except Exception:
            continue
        for item in _iter_nested_values(parsed):
            if not isinstance(item, dict):
                continue
            if _safe_text(item.get("@type")).lower() not in {"event", "sports event", "sportsevent"}:
                continue
            for key in ("startDate", "eventDate", "date", "datePublished"):
                normalized = _parse_any_date_to_iso(item.get(key), default_year=default_year)
                if normalized:
                    return normalized

    # Priority B: event-associated schedule time on the detail page.
    for raw in re.findall(r"<time[^>]*datetime=[\"']([^\"']+)[\"']", html, flags=re.IGNORECASE):
        normalized = _parse_any_date_to_iso(raw, default_year=default_year)
        if normalized:
            return normalized

    # Priority C: explicit event-date metadata only.
    # Do not treat generic content/publication metadata as authoritative schedule date.
    for pattern in (
        r"(?:itemprop|property|name)=[\"'](?:startDate|eventDate|event_start_date|event-date|eventDateTime)[\"'][^>]*content=[\"']([^\"']+)[\"']",
        r"\bdata-[a-z0-9_-]*date[a-z0-9_-]*=[\"']([^\"']+)[\"']",
    ):
        for raw in re.findall(pattern, html, flags=re.IGNORECASE):
            normalized = _parse_any_date_to_iso(raw, default_year=default_year)
            if normalized:
                return normalized

    # Finally allow visible canonical date strings in detail page text.
    visible_text = re.sub(r"<[^>]+>", " ", html)
    visible_text = re.sub(r"\s+", " ", visible_text).strip()
    for pattern in (
        r"\b20\d{2}-\d{2}-\d{2}\b",
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s*20\d{2}\b",
    ):
        for raw in re.findall(pattern, visible_text, flags=re.IGNORECASE):
            normalized = _parse_any_date_to_iso(raw, default_year=default_year)
            if normalized:
                return normalized
    return ""


def _parse_ufc_event_rows(
    html: str,
    source_url: str,
    now_utc: datetime,
    max_result_count: int,
    detail_date_resolver: Optional[Callable[[str], str]] = None,
) -> List[Dict[str, Any]]:
    default_year = now_utc.year
    merged_candidates = _extract_ufc_candidates_from_json(html)
    if not merged_candidates:
        merged_candidates = _extract_ufc_candidates_from_html_links(html)

    listing_records: List[Dict[str, Any]] = []
    seen_urls = set()

    for candidate in merged_candidates:
        if len(listing_records) >= max_result_count:
            break
        normalized_url = _extract_event_url(candidate, source_url)
        if not normalized_url or normalized_url in seen_urls:
            continue
        event_name = _extract_event_name(candidate)
        if not event_name:
            slug = normalized_url.rsplit("/", 1)[-1].replace("-", " ").strip()
            event_name = slug.title() if slug else ""
        if not event_name:
            continue

        event_date = _extract_event_date(candidate, default_year=default_year)

        listing_records.append(
            {
                "event_name": event_name,
                "event_date": event_date,
                "source_url": normalized_url,
            }
        )
        seen_urls.add(normalized_url)

    rows: List[Dict[str, Any]] = []
    for record in listing_records:
        if len(rows) >= max_result_count:
            break
        event_date = _safe_text(record.get("event_date"))
        if not event_date and callable(detail_date_resolver):
            event_date = _safe_text(detail_date_resolver(_safe_text(record.get("source_url"))))
        if not event_date:
            continue

        rows.append(
            {
                "event_name": _safe_text(record.get("event_name")),
                "event_date": event_date,
                "source_url": _safe_text(record.get("source_url")),
                "source_name": "ufc_official_events",
                "source_type": "official",
                "provider_id": "ufc_official_events",
                "source_urls": [_safe_text(record.get("source_url"))],
            }
        )

    return rows


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
    provider_execution_performed: bool = False,
    network_calls_performed: bool = False,
    source_calls_performed: bool = False,
    source_execution_result: str = "not_executed",
    source_http_status: Optional[int] = None,
    parser_result_count: int = 0,
    source_url_or_domain: str = "",
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
        "provider_execution_performed": bool(provider_execution_performed),
        "network_calls_performed": bool(network_calls_performed),
        "source_calls_performed": bool(source_calls_performed),
        "source_execution_result": source_execution_result,
        "source_http_status": source_http_status,
        "parser_result_count": int(parser_result_count),
        "source_url_or_domain": source_url_or_domain,
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


class UfcOfficialEventsProviderAdapter:
    """Bounded provider adapter for UFC official events discovery."""

    def collect_current_week_upcoming(self, provider_config: Dict[str, Any], now_utc: datetime) -> Dict[str, Any]:
        config = _safe_dict(provider_config)
        source_url = _safe_text(config.get("endpoint_or_feed_location")) or "https://www.ufc.com/events"
        max_result_count = config.get("max_result_count")
        timeout_seconds = config.get("timeout_seconds")

        try:
            max_result_count = int(max_result_count)
        except Exception:
            max_result_count = 25
        try:
            timeout_seconds = int(timeout_seconds)
        except Exception:
            timeout_seconds = 20

        max_result_count = max(1, min(max_result_count, 100))
        timeout_seconds = max(1, min(timeout_seconds, 60))

        listing_request_performed = False
        unique_event_url_count = 0
        detail_requests_attempted = 0
        detail_requests_succeeded = 0
        detail_dates_extracted = 0
        detail_date_cache: Dict[str, str] = {}

        def _resolve_detail_date(event_url: str) -> str:
            nonlocal detail_requests_attempted, detail_requests_succeeded, detail_dates_extracted
            normalized_event_url = _normalize_ufc_event_url(event_url, source_url)
            if not normalized_event_url or not _is_ufc_event_url(normalized_event_url):
                return ""
            if normalized_event_url in detail_date_cache:
                return detail_date_cache[normalized_event_url]
            if detail_requests_attempted >= max_result_count:
                return ""

            detail_requests_attempted += 1
            detail_req = urllib_request.Request(
                normalized_event_url,
                method="GET",
                headers={"User-Agent": "AI-RISA-Button1-Discovery/1.0"},
            )
            try:
                with urllib_request.urlopen(detail_req, timeout=timeout_seconds) as detail_resp:
                    final_url = _safe_text(detail_resp.geturl())
                    if not _is_ufc_event_url(final_url):
                        detail_date_cache[normalized_event_url] = ""
                        return ""
                    detail_status = int(getattr(detail_resp, "status", 200) or 200)
                    if detail_status != 200:
                        detail_date_cache[normalized_event_url] = ""
                        return ""
                    detail_html = detail_resp.read().decode("utf-8", errors="ignore")
            except Exception:
                detail_date_cache[normalized_event_url] = ""
                return ""

            detail_requests_succeeded += 1
            extracted = _extract_ufc_event_date_from_detail_html(detail_html, default_year=now_utc.year)
            if extracted:
                detail_dates_extracted += 1
            detail_date_cache[normalized_event_url] = extracted
            return extracted

        req = urllib_request.Request(
            source_url,
            method="GET",
            headers={"User-Agent": "AI-RISA-Button1-Discovery/1.0"},
        )
        try:
            with urllib_request.urlopen(req, timeout=timeout_seconds) as resp:
                body_bytes = resp.read()
                status = int(getattr(resp, "status", 200) or 200)
                listing_request_performed = True
        except urllib_error.HTTPError as exc:
            return {
                "rows": [],
                "source_execution": {
                    "provider_execution_performed": True,
                    "network_calls_performed": True,
                    "source_calls_performed": True,
                    "source_execution_result": "http_error",
                    "source_http_status": int(getattr(exc, "code", 0) or 0),
                    "parser_result_count": 0,
                    "source_url_or_domain": source_url,
                    "listing_request_performed": listing_request_performed,
                    "unique_event_url_count": 0,
                    "detail_requests_attempted": 0,
                    "detail_requests_succeeded": 0,
                    "detail_dates_extracted": 0,
                },
            }
        except Exception:
            return {
                "rows": [],
                "source_execution": {
                    "provider_execution_performed": True,
                    "network_calls_performed": True,
                    "source_calls_performed": True,
                    "source_execution_result": "network_error",
                    "source_http_status": None,
                    "parser_result_count": 0,
                    "source_url_or_domain": source_url,
                    "listing_request_performed": listing_request_performed,
                    "unique_event_url_count": 0,
                    "detail_requests_attempted": 0,
                    "detail_requests_succeeded": 0,
                    "detail_dates_extracted": 0,
                },
            }

        html = body_bytes.decode("utf-8", errors="ignore")
        merged_candidates = _extract_ufc_candidates_from_json(html)
        if not merged_candidates:
            merged_candidates = _extract_ufc_candidates_from_html_links(html)
        unique_urls = set()
        for candidate in merged_candidates:
            if not isinstance(candidate, dict):
                continue
            normalized = _extract_event_url(candidate, source_url)
            if normalized:
                unique_urls.add(normalized)
        unique_event_url_count = len(unique_urls)

        rows = _parse_ufc_event_rows(
            html,
            source_url=source_url,
            now_utc=now_utc,
            max_result_count=max_result_count,
            detail_date_resolver=_resolve_detail_date,
        )

        return {
            "rows": rows[:max_result_count],
            "source_execution": {
                "provider_execution_performed": True,
                "network_calls_performed": True,
                "source_calls_performed": True,
                "source_execution_result": "ok" if status == 200 else "http_non_200",
                "source_http_status": status,
                "parser_result_count": int(len(rows)),
                "source_url_or_domain": source_url,
                "listing_request_performed": listing_request_performed,
                "unique_event_url_count": int(unique_event_url_count),
                "detail_requests_attempted": int(detail_requests_attempted),
                "detail_requests_succeeded": int(detail_requests_succeeded),
                "detail_dates_extracted": int(detail_dates_extracted),
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
    source_execution = _safe_dict(payload.get("source_execution"))
    provider_execution_performed = bool(source_execution.get("provider_execution_performed", False))
    network_calls_performed = bool(source_execution.get("network_calls_performed", False))
    source_calls_performed = bool(source_execution.get("source_calls_performed", False))
    source_execution_result = _safe_text(source_execution.get("source_execution_result")) or "not_executed"
    source_http_status_raw = source_execution.get("source_http_status")
    source_http_status: Optional[int] = None
    if isinstance(source_http_status_raw, int):
        source_http_status = source_http_status_raw
    parser_result_count = int(source_execution.get("parser_result_count", 0) or 0)
    source_url_or_domain = _safe_text(source_execution.get("source_url_or_domain"))
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
            provider_execution_performed=provider_execution_performed,
            network_calls_performed=network_calls_performed,
            source_calls_performed=source_calls_performed,
            source_execution_result=source_execution_result,
            source_http_status=source_http_status,
            parser_result_count=parser_result_count,
            source_url_or_domain=source_url_or_domain,
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
            provider_execution_performed=provider_execution_performed,
            network_calls_performed=network_calls_performed,
            source_calls_performed=source_calls_performed,
            source_execution_result=source_execution_result,
            source_http_status=source_http_status,
            parser_result_count=parser_result_count,
            source_url_or_domain=source_url_or_domain,
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
        provider_execution_performed=provider_execution_performed,
        network_calls_performed=network_calls_performed,
        source_calls_performed=source_calls_performed,
        source_execution_result=source_execution_result,
        source_http_status=source_http_status,
        parser_result_count=parser_result_count,
        source_url_or_domain=source_url_or_domain,
    )
