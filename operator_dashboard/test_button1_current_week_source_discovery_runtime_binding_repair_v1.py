import json
import os
from datetime import date, datetime, timedelta

from operator_dashboard.app import app
from operator_dashboard.local_ai_orchestrator_readonly_runtime_context_loader import build_runtime_context_payload


def _is_iso_timestamp(s: str) -> bool:
    if not isinstance(s, str) or not s:
        return False
    try:
        if s.endswith("Z"):
            s = s[:-1]
        datetime.fromisoformat(s)
        return True
    except Exception:
        return False


def _write_feed(root: str, rows: list[dict]) -> str:
    feed_dir = os.path.join(root, "ops", "approved_sources")
    os.makedirs(feed_dir, exist_ok=True)
    feed_path = os.path.join(feed_dir, "button1_live_event_source_rows.json")
    with open(feed_path, "w", encoding="utf-8") as f:
        json.dump({"rows": rows}, f, indent=2)
    return feed_path


def _valid_row(event_name: str, event_date: str, source_url: str = "https://www.ufc.com/event/ufc-999") -> dict:
    return {
        "event_name": event_name,
        "event_date": event_date,
        "source_url": source_url,
        "event_url": source_url,
        "canonical_source_url": source_url,
        "source_name": "ufc_official_event_pages",
        "source_type": "official",
    }


def _status_for_workspace(root: str) -> dict:
    payload = build_runtime_context_payload("button1_find_fights", workspace_root=root)
    status = payload.get("live_source_status", {})
    assert isinstance(status, dict)
    return status


def test_workflow_preview_live_source_status_includes_required_fields():
    with app.test_client() as client:
        resp = client.post(
            "/api/local-ai/orchestrator/workflow-preview",
            json={"source_button": "button1_find_fights", "use_runtime_context": True, "execute_preview": True},
        )
        assert resp.status_code == 200
        body = resp.get_json() or {}
        assert body.get("ok") is True

        jobs = ((body.get("workflow") or {}).get("jobs") or [])
        assert jobs
        payload = (((jobs[0].get("input_ref") or {}).get("metadata") or {}).get("payload") or {})
        status = payload.get("live_source_status")
        assert isinstance(status, dict)

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
            "feed_used",
            "approved_source_event_rows_count",
            "current_week_rows_count",
            "source_backed_event_cards",
        ]
        for key in required_keys:
            assert key in status, f"missing {key} in live_source_status"


def test_generated_at_utc_timestamp_not_filename():
    status = build_runtime_context_payload("button1_find_fights").get("live_source_status", {})
    generated_at_utc = status.get("generated_at_utc")
    feed_used = status.get("feed_used", "")
    if generated_at_utc:
        assert _is_iso_timestamp(generated_at_utc)
        assert generated_at_utc != feed_used
        assert not generated_at_utc.endswith(".json")


def test_stale_feed_fails_closed(tmp_path):
    event_date = (date.today() + timedelta(days=3)).isoformat()
    feed_path = _write_feed(str(tmp_path), [_valid_row("UFC 999", event_date)])
    stale_epoch = 946684800  # 2000-01-01
    os.utime(feed_path, (stale_epoch, stale_epoch))

    status = _status_for_workspace(str(tmp_path))
    assert status.get("feed_status") == "stale"
    assert status.get("current_week_ready") is False
    assert status.get("save_allowed") is False


def test_demo_fixture_feed_fails_closed(tmp_path):
    event_date = (date.today() + timedelta(days=2)).isoformat()
    _write_feed(str(tmp_path), [_valid_row("demo fixture ufc card", event_date)])

    status = _status_for_workspace(str(tmp_path))
    assert status.get("feed_status") == "demo_or_fixture_feed"
    assert status.get("current_week_ready") is False
    assert status.get("save_allowed") is False


def test_no_current_week_source_backed_matchups_fails_closed(tmp_path):
    event_date = (date.today() + timedelta(days=60)).isoformat()
    _write_feed(str(tmp_path), [_valid_row("UFC 1000", event_date)])

    status = _status_for_workspace(str(tmp_path))
    assert status.get("feed_status") == "no_current_week_source_backed_matchups"
    assert status.get("current_week_ready") is False
    assert status.get("save_allowed") is False


def test_valid_current_week_source_backed_rows_ready(tmp_path):
    event_date = (date.today() + timedelta(days=3)).isoformat()
    _write_feed(str(tmp_path), [_valid_row("UFC 1001", event_date)])

    status = _status_for_workspace(str(tmp_path))
    assert status.get("feed_status") == "current_week_ready"
    assert status.get("current_week_ready") is True
    assert status.get("save_allowed") is True
    assert isinstance(status.get("source_backed_event_cards"), list)
    assert status.get("current_week_rows_count", 0) >= 1


def test_operator_approval_still_required_before_queue_save():
    with app.test_client() as client:
        resp = client.post(
            "/api/local-ai/orchestrator/workflow-preview",
            json={"source_button": "button1_find_fights", "use_runtime_context": True, "execute_preview": True},
        )
        body = resp.get_json() or {}
        workflow = body.get("workflow") or {}
        token_preview = workflow.get("gate_approval_token_preview") or {}
        assert workflow.get("gate_required") is True
        assert token_preview.get("approval_required") is True
        assert token_preview.get("write_authorized") is False
        assert token_preview.get("queue_write_performed") is False
        assert token_preview.get("database_write_performed") is False


def test_button2_and_button3_flags_unchanged():
    with app.test_client() as client:
        for source_button in ("button2_generate_pdfs", "button3_find_results"):
            resp = client.post(
                "/api/local-ai/orchestrator/workflow-preview",
                json={"source_button": source_button, "use_runtime_context": True, "execute_preview": True},
            )
            assert resp.status_code == 200
            body = resp.get_json() or {}
            telemetry = body.get("telemetry") or {}
            workflow = body.get("workflow") or {}

            assert telemetry.get("preview_only") is True
            assert telemetry.get("mutation_performed") is False
            assert telemetry.get("queue_write_performed") is False
            assert telemetry.get("learning_apply_performed") is False
            assert telemetry.get("calibration_write_performed") is False

            assert workflow.get("preview_only") is True
            assert workflow.get("queue_write_performed") is False
            assert workflow.get("durable_write_performed") is False
            assert workflow.get("learning_apply_performed") is False
            assert workflow.get("calibration_write_performed") is False
