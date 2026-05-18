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


def test_source_tag_and_source_notes_only_candidate_remains_blocked(client):
    row = {
        "candidate_id": "tag_only",
        "fight_name": "Fight tag_only",
        "source_tag": "bout_card_csv",
        "source_notes": "event_coverage_queue.csv + one_samurai_1_bouts.csv",
    }
    resp = client.post(ROUTE, json=_payload(token=_valid_token(), candidate_rows=[row]))
    data = resp.get_json()
    assert "tag_only" in data["blocked"]
    assert "tag_only" not in data["would_save"]


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


def test_identity_conflict_row_is_reported_in_identity_blocked_projection(client):
    row = _candidate_row("id_conflict")
    row["fighter_a_identity_status"] = "identity_conflict"
    row["identity_blocking_reasons"] = ["fighter_a:identity_conflict"]
    row["identity_ready_for_queue_review"] = False

    resp = client.post(ROUTE, json=_payload(token=_valid_token(), candidate_rows=[row]))
    data = resp.get_json()

    assert "id_conflict" in data["blocked"]
    assert "id_conflict" in data["identity_blocked"]
    assert data["identity_blocked_count"] >= 1
    assert "id_conflict" in data["identity_blocking_reasons_by_candidate"]


def test_identity_source_missing_and_ambiguous_rows_are_blocked(client):
    source_missing = _candidate_row("id_src_missing")
    source_missing["fighter_b_identity_status"] = "identity_source_missing"

    ambiguous = _candidate_row("id_ambiguous")
    ambiguous["fighter_a_identity_status"] = "identity_ambiguous"

    good = _candidate_row("id_good")

    resp = client.post(
        ROUTE,
        json=_payload(token=_valid_token(), candidate_rows=[source_missing, ambiguous, good]),
    )
    data = resp.get_json()

    assert "id_src_missing" in data["blocked"]
    assert "id_ambiguous" in data["blocked"]
    assert "id_good" in data["would_save"]


def test_current_runtime_cohort_without_urls_remains_fully_blocked(client):
    wf = client.post(
        "/api/local-ai/orchestrator/workflow-preview",
        json={
            "source_button": "button1_find_fights",
            "use_runtime_context": True,
            "execute_preview": True,
        },
    ).get_json()
    payload = wf["workflow"]["jobs"][0]["input_ref"]["metadata"]["payload"]
    rows = payload.get("candidate_rows", [])
    token = wf["workflow"].get("gate_approval_token_preview")

    scope = []
    for row in rows:
        cid = row.get("candidate_id") or row.get("fight_id") or row.get("fight_key") or row.get("matchup_key") or row.get("id") or row.get("fight_name")
        if isinstance(cid, str) and cid.strip():
            scope.append(cid)

    resp = client.post(ROUTE, json=_payload(token=token, candidate_scope=scope, candidate_rows=rows))
    data = resp.get_json()
    assert len(rows) == 31
    assert len(data["would_save"]) == 0
    assert len(data["blocked"]) == 31
