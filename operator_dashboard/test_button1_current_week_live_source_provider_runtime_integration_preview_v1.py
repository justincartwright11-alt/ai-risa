from __future__ import annotations

import inspect
import json
import os
from datetime import date, timedelta

from operator_dashboard.app import app
from operator_dashboard.button1_live_source_provider_orchestrator_v1 import (
    run_button1_live_source_provider_orchestrator,
)
import operator_dashboard.local_ai_orchestrator_readonly_runtime_context_loader as runtime_loader


class _DummyApprovedProviderAdapter:
    def __init__(self, rows):
        self.rows = rows

    def collect_current_week_upcoming(self, provider_config, now_utc):
        return {"rows": list(self.rows)}


def _make_row(event_name: str, event_date: str) -> dict:
    source_url = "https://www.ufc.com/event/current-week-preview"
    return {
        "event_name": event_name,
        "event_date": event_date,
        "source_url": source_url,
        "event_url": source_url,
        "canonical_source_url": source_url,
        "source_name": "ufc_official",
        "source_type": "official",
    }


def _write_stale_feed(root: str) -> str:
    feed_dir = os.path.join(root, "ops", "approved_sources")
    os.makedirs(feed_dir, exist_ok=True)
    feed_path = os.path.join(feed_dir, "button1_live_event_source_rows.json")
    with open(feed_path, "w", encoding="utf-8") as f:
        json.dump({"rows": [_make_row("Stale Event", (date.today() + timedelta(days=4)).isoformat())]}, f, indent=2)
    old_epoch = 946684800
    os.utime(feed_path, (old_epoch, old_epoch))
    return feed_path


def _workflow_status_from_response(response_json: dict) -> dict:
    workflow = response_json.get("workflow") or {}
    jobs = workflow.get("jobs") or []
    assert jobs
    payload = (((jobs[0].get("input_ref") or {}).get("metadata") or {}).get("payload") or {})
    status = payload.get("live_source_status") or {}
    assert isinstance(status, dict)
    return workflow, status


def test_workflow_preview_uses_orchestrator_status_when_no_provider_configured(monkeypatch, tmp_path):
    _write_stale_feed(str(tmp_path))
    monkeypatch.setattr(runtime_loader, "_default_workspace_root", lambda: str(tmp_path))

    with app.test_client() as client:
        resp = client.post(
            "/api/local-ai/orchestrator/workflow-preview",
            json={"source_button": "button1_find_fights", "use_runtime_context": True, "execute_preview": True},
        )
        assert resp.status_code == 200
        body = resp.get_json() or {}
        workflow, status = _workflow_status_from_response(body)

    assert status["feed_status"] == "unavailable"
    assert status["current_week_ready"] is False
    assert status["save_allowed"] is False
    assert "no_approved_live_source_provider_configured" in status["diagnostics"]
    assert status["queue_write_performed"] is False
    assert status["database_write_performed"] is False
    assert workflow.get("gate_required") is True
    token_preview = workflow.get("gate_approval_token_preview") or {}
    assert token_preview.get("approval_required") is True
    assert token_preview.get("write_authorized") is False


def test_no_provider_configured_returns_unavailable_fail_closed():
    result = run_button1_live_source_provider_orchestrator(provider_registry=[])
    assert result["feed_status"] == "unavailable"
    assert result["current_week_ready"] is False
    assert result["save_allowed"] is False
    assert "no_approved_live_source_provider_configured" in result["diagnostics"]
    assert result["queue_write_performed"] is False
    assert result["database_write_performed"] is False


def test_stale_approved_source_json_does_not_promote_live_discovery(monkeypatch, tmp_path):
    _write_stale_feed(str(tmp_path))
    monkeypatch.setattr(runtime_loader, "_default_workspace_root", lambda: str(tmp_path))

    with app.test_client() as client:
        resp = client.post(
            "/api/local-ai/orchestrator/workflow-preview",
            json={"source_button": "button1_find_fights", "use_runtime_context": True, "execute_preview": True},
        )
        body = resp.get_json() or {}
        _, status = _workflow_status_from_response(body)

    assert status["feed_status"] == "unavailable"
    assert status["current_week_ready"] is False
    assert status["save_allowed"] is False


def test_live_source_status_contains_full_required_field_contract(monkeypatch, tmp_path):
    monkeypatch.setattr(runtime_loader, "_default_workspace_root", lambda: str(tmp_path))

    with app.test_client() as client:
        resp = client.post(
            "/api/local-ai/orchestrator/workflow-preview",
            json={"source_button": "button1_find_fights", "use_runtime_context": True, "execute_preview": True},
        )
        body = resp.get_json() or {}
        _, status = _workflow_status_from_response(body)

    required_keys = [
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
        "queue_write_performed",
        "database_write_performed",
    ]
    for key in required_keys:
        assert key in status, f"missing {key}"


def test_operator_approval_metadata_remains_present(monkeypatch, tmp_path):
    monkeypatch.setattr(runtime_loader, "_default_workspace_root", lambda: str(tmp_path))

    with app.test_client() as client:
        resp = client.post(
            "/api/local-ai/orchestrator/workflow-preview",
            json={"source_button": "button1_find_fights", "use_runtime_context": True, "execute_preview": True},
        )
        body = resp.get_json() or {}
        workflow, _ = _workflow_status_from_response(body)

    token_preview = workflow.get("gate_approval_token_preview") or {}
    assert workflow.get("gate_required") is True
    assert token_preview.get("approval_required") is True
    assert token_preview.get("write_authorized") is False


def test_queue_and_database_writes_remain_false(monkeypatch, tmp_path):
    monkeypatch.setattr(runtime_loader, "_default_workspace_root", lambda: str(tmp_path))

    with app.test_client() as client:
        resp = client.post(
            "/api/local-ai/orchestrator/workflow-preview",
            json={"source_button": "button1_find_fights", "use_runtime_context": True, "execute_preview": True},
        )
        body = resp.get_json() or {}
        workflow, status = _workflow_status_from_response(body)

    assert status["queue_write_performed"] is False
    assert status["database_write_performed"] is False
    assert workflow.get("queue_write_performed") is False
    assert workflow.get("durable_write_performed") is False


def test_dummy_provider_can_produce_current_week_ready_in_isolated_unit_test():
    in_window_row = _make_row("Dummy Provider Event", (date.today() + timedelta(days=2)).isoformat())
    provider = {
        "name": "ufc_official",
        "enabled": True,
        "config": {},
        "adapter": _DummyApprovedProviderAdapter([in_window_row]),
    }
    result = run_button1_live_source_provider_orchestrator(provider_registry=[provider])
    assert result["feed_status"] == "current_week_ready"
    assert result["current_week_ready"] is True
    assert result["save_allowed"] is True
    assert result["current_week_rows_count"] == 1


def test_button2_and_button3_modules_not_imported_or_modified_in_preview_path():
    preview_source = inspect.getsource(runtime_loader.build_button1_runtime_context_preview)
    state_source = inspect.getsource(runtime_loader.load_button1_runtime_state_preview)
    assert "button2_" not in preview_source
    assert "button3_" not in preview_source
    assert "button2_" not in state_source
    assert "button3_" not in state_source
