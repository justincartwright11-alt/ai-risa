"""Tests for preview-only Gate 1 save-fights dry-run apply API route (v1)."""

import json
import os
import socket
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from operator_dashboard.app import app as flask_app
from operator_dashboard.local_ai_orchestrator_job_schema import LocalAIJobInputRef
from operator_dashboard.local_ai_orchestrator_workflow_plan import build_three_button_workflow_plan

ROUTE = "/api/local-ai/gate1/save-fights/dry-run-apply-preview"


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def _input_ref(key: str = "seed_001") -> LocalAIJobInputRef:
    return LocalAIJobInputRef(ref_type="entity", ref_key=key, snapshot_hash="snap_v1")


def _valid_token(candidate_scope=None):
    plan = build_three_button_workflow_plan("button1_find_fights", _input_ref("gate1_api"))
    token = dict(plan.gate_approval_token_preview)
    if candidate_scope is not None:
        token["candidate_scope"] = candidate_scope
    return token


def _candidate_row(candidate_id: str, with_provenance: bool = True, duplicate: bool = False, conflict: bool = False):
    row = {
        "candidate_id": candidate_id,
        "fight_name": f"Fight {candidate_id}",
        "duplicate": duplicate,
        "conflict": conflict,
    }
    if with_provenance:
        row["source_url"] = f"https://example.com/{candidate_id}"
    return row


def _payload(token=None, candidate_scope=None, candidate_rows=None):
    data = {}
    if token is not None:
        data["gate_approval_token_preview"] = token
    if candidate_scope is not None:
        data["candidate_scope"] = candidate_scope
    if candidate_rows is not None:
        data["candidate_rows"] = candidate_rows
    return data


def test_route_exists(client):
    resp = client.post(ROUTE, json=_payload(token=_valid_token(), candidate_rows=[]))
    assert resp.status_code == 200


def test_valid_token_and_candidate_scope_returns_ok_true(client):
    resp = client.post(
        ROUTE,
        json=_payload(
            token=_valid_token(candidate_scope=["good"]),
            candidate_scope=["good"],
            candidate_rows=[_candidate_row("good")],
        ),
    )
    data = resp.get_json()
    assert data["ok"] is True
    assert data["eligible_for_future_approval"] is True


def test_response_is_preview_only_true(client):
    resp = client.post(ROUTE, json=_payload(token=_valid_token(), candidate_rows=[_candidate_row("good")]))
    data = resp.get_json()
    assert data["preview_only"] is True


def test_response_write_authorized_false(client):
    resp = client.post(ROUTE, json=_payload(token=_valid_token(), candidate_rows=[_candidate_row("good")]))
    data = resp.get_json()
    assert data["write_authorized"] is False


def test_response_queue_write_performed_false(client):
    resp = client.post(ROUTE, json=_payload(token=_valid_token(), candidate_rows=[_candidate_row("good")]))
    data = resp.get_json()
    assert data["queue_write_performed"] is False


def test_response_database_write_performed_false(client):
    resp = client.post(ROUTE, json=_payload(token=_valid_token(), candidate_rows=[_candidate_row("good")]))
    data = resp.get_json()
    assert data["database_write_performed"] is False


def test_missing_token_fails_closed(client):
    resp = client.post(ROUTE, json=_payload(candidate_rows=[_candidate_row("good")]))
    data = resp.get_json()
    assert data["ok"] is False
    assert any("missing gate_approval_token_preview" in reason for reason in data["blocking_reasons"])


def test_invalid_token_fails_closed(client):
    bad = _valid_token()
    bad["source_button"] = "button2_generate_pdfs"

    resp = client.post(ROUTE, json=_payload(token=bad, candidate_rows=[_candidate_row("good")]))
    data = resp.get_json()
    assert data["ok"] is False
    assert any("source_button" in reason for reason in data["blocking_reasons"])


def test_duplicate_candidate_is_blocked(client):
    resp = client.post(
        ROUTE,
        json=_payload(token=_valid_token(), candidate_rows=[_candidate_row("dup", duplicate=True)]),
    )
    data = resp.get_json()
    assert "dup" in data["blocked"]


def test_conflict_candidate_is_blocked(client):
    resp = client.post(
        ROUTE,
        json=_payload(token=_valid_token(), candidate_rows=[_candidate_row("conf", conflict=True)]),
    )
    data = resp.get_json()
    assert "conf" in data["blocked"]


def test_missing_provenance_candidate_is_blocked(client):
    resp = client.post(
        ROUTE,
        json=_payload(token=_valid_token(), candidate_rows=[_candidate_row("no_src", with_provenance=False)]),
    )
    data = resp.get_json()
    assert "no_src" in data["blocked"]


def test_valid_candidate_appears_in_would_save(client):
    resp = client.post(
        ROUTE,
        json=_payload(token=_valid_token(), candidate_rows=[_candidate_row("good")]),
    )
    data = resp.get_json()
    assert "good" in data["would_save"]


def test_dry_run_route_does_not_write_files(client, monkeypatch):
    opened_for_write = []
    real_open = open

    def guarded_open(*args, **kwargs):
        mode = kwargs.get("mode", "r")
        if len(args) >= 2:
            mode = args[1]
        if any(flag in mode for flag in ("w", "a", "x", "+")):
            opened_for_write.append((args, kwargs))
            raise AssertionError("Unexpected write during dry-run API execution")
        return real_open(*args, **kwargs)

    monkeypatch.setattr("builtins.open", guarded_open)

    resp = client.post(ROUTE, json=_payload(token=_valid_token(), candidate_rows=[_candidate_row("good")]))
    assert resp.status_code == 200
    assert opened_for_write == []


def test_dry_run_route_does_not_call_live_web(client, monkeypatch):
    def blocked_connect(*args, **kwargs):
        raise AssertionError("Live network call attempted")

    monkeypatch.setattr(socket, "create_connection", blocked_connect)

    resp = client.post(ROUTE, json=_payload(token=_valid_token(), candidate_rows=[_candidate_row("good")]))
    assert resp.status_code == 200


def test_route_response_serializes_to_json(client):
    resp = client.post(ROUTE, json=_payload(token=_valid_token(), candidate_rows=[_candidate_row("good")]))
    payload = resp.get_json()
    _ = json.dumps(payload)
