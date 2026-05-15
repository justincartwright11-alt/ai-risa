"""Tests for context-pack API binding on local AI workflow preview route (v1)."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from operator_dashboard.app import app as flask_app

ROUTE = "/api/local-ai/orchestrator/workflow-preview"


def _payload_with_context_pack(source_button: str, context_pack: dict, execute_preview: bool = False):
    return {
        "source_button": source_button,
        "context_pack": context_pack,
        "execute_preview": execute_preview,
    }


def _payload_with_input_ref(source_button: str, execute_preview: bool = False):
    return {
        "source_button": source_button,
        "input_ref": {
            "kind": "manual",
            "ref_id": "seed_001",
            "payload": {"sample": True},
        },
        "execute_preview": execute_preview,
    }


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def test_route_accepts_button1_context_pack_and_returns_workflow_preview(client):
    resp = client.post(
        ROUTE,
        json=_payload_with_context_pack(
            "button1_find_fights",
            {"manual_text": "UFC", "candidate_rows": [{"fight_name": "A vs B"}]},
        ),
    )
    data = resp.get_json()

    assert resp.status_code == 200
    assert data["ok"] is True
    assert len(data["workflow"]["jobs"]) == 6


def test_route_accepts_button2_context_pack_and_returns_workflow_preview(client):
    resp = client.post(
        ROUTE,
        json=_payload_with_context_pack(
            "button2_generate_pdfs",
            {"selected_fights": [{"fight_key": "f1"}], "queued_fight_refs": ["f1"]},
        ),
    )
    data = resp.get_json()

    assert resp.status_code == 200
    assert data["ok"] is True
    assert len(data["workflow"]["jobs"]) == 4


def test_route_accepts_button3_context_pack_and_returns_workflow_preview(client):
    resp = client.post(
        ROUTE,
        json=_payload_with_context_pack(
            "button3_find_results",
            {"waiting_rows": [{"selected_key": "r1"}], "selected_keys": ["r1"]},
        ),
    )
    data = resp.get_json()

    assert resp.status_code == 200
    assert data["ok"] is True
    assert len(data["workflow"]["jobs"]) == 4


def test_button1_context_pack_maps_to_discovery_preview(client):
    resp = client.post(
        ROUTE,
        json=_payload_with_context_pack("button1_find_fights", {"manual_text": "UFC"}),
    )
    data = resp.get_json()

    ref = data["workflow"]["jobs"][0]["input_ref"]
    assert ref["ref_type"] == "discovery_preview"


def test_button2_context_pack_maps_to_report_preview(client):
    resp = client.post(
        ROUTE,
        json=_payload_with_context_pack("button2_generate_pdfs", {"selected_fights": []}),
    )
    data = resp.get_json()

    ref = data["workflow"]["jobs"][0]["input_ref"]
    assert ref["ref_type"] == "report_preview"


def test_button3_context_pack_maps_to_result_review_preview(client):
    resp = client.post(
        ROUTE,
        json=_payload_with_context_pack("button3_find_results", {"waiting_rows": []}),
    )
    data = resp.get_json()

    ref = data["workflow"]["jobs"][0]["input_ref"]
    assert ref["ref_type"] == "result_review_preview"


def test_existing_input_ref_behavior_unchanged_when_context_pack_absent(client):
    resp = client.post(ROUTE, json=_payload_with_input_ref("button1_find_fights"))
    data = resp.get_json()

    ref = data["workflow"]["jobs"][0]["input_ref"]
    assert ref["ref_type"] == "manual"
    assert ref["ref_key"] == "seed_001"
    assert ref["metadata"]["payload"] == {"sample": True}


def test_empty_context_pack_does_not_create_fake_fights_reports_or_results(client):
    resp1 = client.post(ROUTE, json=_payload_with_context_pack("button1_find_fights", {}))
    resp2 = client.post(ROUTE, json=_payload_with_context_pack("button2_generate_pdfs", {}))
    resp3 = client.post(ROUTE, json=_payload_with_context_pack("button3_find_results", {}))

    p1 = resp1.get_json()["workflow"]["jobs"][0]["input_ref"]["metadata"]["payload"]
    p2 = resp2.get_json()["workflow"]["jobs"][0]["input_ref"]["metadata"]["payload"]
    p3 = resp3.get_json()["workflow"]["jobs"][0]["input_ref"]["metadata"]["payload"]

    assert p1["candidate_rows"] == []
    assert p2["selected_fights"] == []
    assert p3["waiting_rows"] == []


def test_malformed_context_pack_fails_closed(client):
    resp = client.post(
        ROUTE,
        json={
            "source_button": "button1_find_fights",
            "context_pack": ["not", "a", "dict"],
            "execute_preview": False,
        },
    )
    data = resp.get_json()

    assert resp.status_code == 400
    assert data["ok"] is False


def test_invalid_source_button_fails_closed(client):
    resp = client.post(
        ROUTE,
        json=_payload_with_context_pack("button4_invalid", {"manual_text": "x"}),
    )
    data = resp.get_json()

    assert resp.status_code == 400
    assert data["ok"] is False


def test_execute_preview_false_remains_plan_only(client):
    resp = client.post(
        ROUTE,
        json=_payload_with_context_pack("button1_find_fights", {"manual_text": "UFC"}, execute_preview=False),
    )
    data = resp.get_json()

    assert data["ok"] is True
    assert data["workflow"]["status"] == "preview_planned"
    assert all(job["status"] == "pending" for job in data["workflow"]["jobs"])


def test_execute_preview_true_remains_preview_only(client):
    resp = client.post(
        ROUTE,
        json=_payload_with_context_pack("button1_find_fights", {"manual_text": "UFC"}, execute_preview=True),
    )
    data = resp.get_json()

    assert data["ok"] is True
    assert data["workflow"]["preview_only"] is True
    assert data["workflow"]["mutation_performed"] is False
    assert data["workflow"]["queue_write_performed"] is False
    assert data["workflow"]["report_export_approved"] is False
    assert data["workflow"]["durable_write_performed"] is False
    assert data["workflow"]["learning_apply_performed"] is False
    assert data["workflow"]["calibration_write_performed"] is False
    assert data["workflow"]["auto_apply_performed"] is False


def test_all_route_telemetry_flags_remain_safe(client):
    resp = client.post(
        ROUTE,
        json=_payload_with_context_pack("button3_find_results", {"waiting_rows": []}, execute_preview=True),
    )
    data = resp.get_json()

    telemetry = data["telemetry"]
    assert telemetry["preview_only"] is True
    assert telemetry["mutation_performed"] is False
    assert telemetry["queue_write_performed"] is False
    assert telemetry["report_export_approved"] is False
    assert telemetry["durable_write_performed"] is False
    assert telemetry["learning_apply_performed"] is False
    assert telemetry["calibration_write_performed"] is False
    assert telemetry["auto_apply_performed"] is False


def test_route_with_context_pack_serializes_to_json(client):
    resp = client.post(
        ROUTE,
        json=_payload_with_context_pack("button2_generate_pdfs", {"selected_fights": []}),
    )
    assert resp.content_type.startswith("application/json")
    _ = json.dumps(resp.get_json())


def test_route_context_pack_performs_no_filesystem_writes(client, monkeypatch):
    opened_for_write = []
    real_open = open

    def guarded_open(*args, **kwargs):
        mode = kwargs.get("mode", "r")
        if len(args) >= 2:
            mode = args[1]
        if any(flag in mode for flag in ("w", "a", "x", "+")):
            opened_for_write.append((args, kwargs))
            raise AssertionError("Unexpected write during context-pack route execution")
        return real_open(*args, **kwargs)

    monkeypatch.setattr("builtins.open", guarded_open)

    resp = client.post(
        ROUTE,
        json=_payload_with_context_pack("button1_find_fights", {}, execute_preview=True),
    )
    assert resp.status_code == 200
    assert opened_for_write == []
