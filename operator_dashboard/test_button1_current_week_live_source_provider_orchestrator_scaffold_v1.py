from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import inspect
import re

from operator_dashboard import button1_live_source_provider_orchestrator_v1 as orchestrator


class _FakeAdapter:
    def __init__(self, payload):
        self.payload = payload

    def collect_current_week_upcoming(self, provider_config, now_utc):
        return self.payload


def _provider(name: str, enabled: bool, payload):
    return {
        "name": name,
        "enabled": enabled,
        "config": {},
        "adapter": _FakeAdapter(payload),
    }


def _required_keys():
    return [
        "feed_status",
        "generated_at_utc",
        "current_week_start",
        "current_week_end",
        "upcoming_window_days",
        "source_freshness",
        "feed_age_seconds",
        "current_week_ready",
        "save_allowed",
        "fallback_used",
        "diagnostics",
        "provider_count",
        "provider_names",
        "selected_provider",
        "source_backed_event_cards",
        "current_week_rows_count",
        "approved_source_event_rows_count",
    ]


def _assert_fail_closed(result):
    assert result["current_week_ready"] is False
    assert result["save_allowed"] is False
    assert result["fallback_used"] is False
    assert result["source_backed_event_cards"] == []
    assert result["current_week_rows_count"] == 0


def test_empty_registry_fails_closed():
    result = orchestrator.run_button1_live_source_provider_orchestrator(provider_registry=[])
    for key in _required_keys():
        assert key in result
    assert result["feed_status"] == "unavailable"
    _assert_fail_closed(result)
    assert "no_approved_live_source_provider_configured" in result["diagnostics"]


def test_disabled_provider_fails_closed():
    registry = [_provider("ufc_official", False, {"rows": []})]
    result = orchestrator.run_button1_live_source_provider_orchestrator(provider_registry=registry)
    assert result["feed_status"] == "unavailable"
    _assert_fail_closed(result)
    assert "provider_disabled" in result["diagnostics"]


def test_invalid_provider_payload_fails_closed():
    registry = [_provider("ufc_official", True, {"rows": "bad"})]
    result = orchestrator.run_button1_live_source_provider_orchestrator(provider_registry=registry)
    assert result["feed_status"] == "unavailable"
    _assert_fail_closed(result)
    assert "provider_payload_invalid" in result["diagnostics"]


def test_valid_payload_outside_window_fails_closed():
    out_of_window_date = (date.today() + timedelta(days=40)).isoformat()
    payload = {
        "rows": [
            {
                "event_name": "UFC Future Event",
                "event_date": out_of_window_date,
                "source_url": "https://www.ufc.com/event/future-card",
                "source_name": "ufc_official",
                "source_type": "official",
            }
        ]
    }
    registry = [_provider("ufc_official", True, payload)]
    result = orchestrator.run_button1_live_source_provider_orchestrator(provider_registry=registry)
    assert result["feed_status"] == "no_current_week_source_backed_matchups"
    _assert_fail_closed(result)


def test_valid_payload_inside_window_current_week_ready():
    in_window_date = (date.today() + timedelta(days=2)).isoformat()
    payload = {
        "rows": [
            {
                "event_name": "UFC Current Week Event",
                "event_date": in_window_date,
                "source_url": "https://www.ufc.com/event/current-week-card",
                "source_name": "ufc_official",
                "source_type": "official",
            }
        ]
    }
    registry = [_provider("ufc_official", True, payload)]
    result = orchestrator.run_button1_live_source_provider_orchestrator(provider_registry=registry)
    assert result["feed_status"] == "current_week_ready"
    assert result["current_week_ready"] is True
    assert result["save_allowed"] is True
    assert result["current_week_rows_count"] == 1
    assert result["approved_source_event_rows_count"] == 1


def test_generated_at_utc_is_timestamp_like_not_filename():
    now_utc = datetime.now(timezone.utc)
    result = orchestrator.run_button1_live_source_provider_orchestrator(provider_registry=[], now_utc=now_utc)
    generated_at_utc = result["generated_at_utc"]
    assert isinstance(generated_at_utc, str)
    assert re.match(r"^\d{4}-\d{2}-\d{2}T", generated_at_utc)
    assert not generated_at_utc.endswith(".json")
    assert "button1_live_event_source_rows" not in generated_at_utc


def test_save_allowed_does_not_bypass_operator_approval():
    in_window_date = (date.today() + timedelta(days=1)).isoformat()
    payload = {
        "rows": [
            {
                "event_name": "UFC Approval Gate Test",
                "event_date": in_window_date,
                "source_url": "https://www.ufc.com/event/approval-gate-test",
                "source_name": "ufc_official",
                "source_type": "official",
            }
        ]
    }
    registry = [_provider("ufc_official", True, payload)]
    result = orchestrator.run_button1_live_source_provider_orchestrator(provider_registry=registry)
    assert result["save_allowed"] is True
    assert result["operator_approval_required"] is True
    assert result["queue_write_performed"] is False
    assert result["database_write_performed"] is False


def test_no_button2_or_button3_modules_imported_or_modified():
    module_source = inspect.getsource(orchestrator)
    assert "from operator_dashboard import button2" not in module_source
    assert "from operator_dashboard import button3" not in module_source
    assert "operator_dashboard.button2_" not in module_source
    assert "operator_dashboard.button3_" not in module_source
