"""Tests for preview-only Gate 1 approved save writer scaffold API route (v1)."""

import json
import os
import socket
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from operator_dashboard.app import app as flask_app
from operator_dashboard.local_ai_orchestrator_job_schema import LocalAIJobInputRef
from operator_dashboard.local_ai_orchestrator_workflow_plan import build_three_button_workflow_plan

ROUTE = "/api/local-ai/gate1/save-fights/approved-save-writer-preview"


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def _input_ref(key: str = "seed_approved_001") -> LocalAIJobInputRef:
    return LocalAIJobInputRef(ref_type="entity", ref_key=key, snapshot_hash="snap_v1")


def _valid_token(candidate_scope=None):
    plan = build_three_button_workflow_plan("button1_find_fights", _input_ref("gate1_approved_api"))
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


def _payload(
    token=None,
    candidate_scope=None,
    candidate_rows=None,
    operator_approved=True,
    idempotency_key="idem_001",
    write_target="queue_preview",
    dry_run_required=True,
    live_write_enabled=False,
):
    return {
        "gate_approval_token_preview": token if token is not None else _valid_token(candidate_scope=["good"]),
        "candidate_scope": candidate_scope if candidate_scope is not None else ["good"],
        "candidate_rows": candidate_rows if candidate_rows is not None else [_candidate_row("good")],
        "operator_approved": operator_approved,
        "idempotency_key": idempotency_key,
        "write_target": write_target,
        "dry_run_required": dry_run_required,
        "live_write_enabled": live_write_enabled,
    }


def test_route_exists(client):
    resp = client.post(ROUTE, json=_payload())
    assert resp.status_code == 200


def test_valid_scaffold_request_returns_ok_true(client):
    resp = client.post(ROUTE, json=_payload())
    data = resp.get_json()
    assert data["ok"] is True


def test_route_forces_live_write_enabled_false(client):
    resp = client.post(ROUTE, json=_payload(live_write_enabled=True))
    data = resp.get_json()
    assert data["live_write_enabled"] is False


def test_route_returns_write_performed_false(client):
    resp = client.post(ROUTE, json=_payload())
    data = resp.get_json()
    assert data["write_performed"] is False


def test_route_returns_queue_write_performed_false(client):
    resp = client.post(ROUTE, json=_payload())
    data = resp.get_json()
    assert data["queue_write_performed"] is False


def test_route_returns_database_write_performed_false(client):
    resp = client.post(ROUTE, json=_payload())
    data = resp.get_json()
    assert data["database_write_performed"] is False


def test_route_returns_audit_record_preview(client):
    resp = client.post(ROUTE, json=_payload())
    data = resp.get_json()
    assert data["audit_record_preview"] is not None


def test_route_returns_rollback_pointer_preview(client):
    resp = client.post(ROUTE, json=_payload())
    data = resp.get_json()
    assert data["rollback_pointer_preview"] is not None


def test_missing_operator_approval_fails_closed(client):
    resp = client.post(ROUTE, json=_payload(operator_approved=False))
    data = resp.get_json()
    assert data["ok"] is False
    assert "operator_approval_missing" in data["blocking_reasons"]


def test_invalid_token_fails_closed(client):
    bad = _valid_token(candidate_scope=["good"])
    bad["source_button"] = "button2_generate_pdfs"
    resp = client.post(ROUTE, json=_payload(token=bad))
    data = resp.get_json()
    assert data["ok"] is False
    assert "token_check_failed" in data["blocking_reasons"]


def test_missing_provenance_fails_closed(client):
    resp = client.post(
        ROUTE,
        json=_payload(candidate_rows=[_candidate_row("good", with_provenance=False)]),
    )
    data = resp.get_json()
    assert data["ok"] is False
    assert "provenance_missing" in data["blocking_reasons"]


def test_source_backed_row_is_not_blocked_by_provenance(client):
    resp = client.post(
        ROUTE,
        json=_payload(candidate_rows=[{"candidate_id": "good_src", "fight_name": "Fight good_src", "source_url": "https://example.com/good_src"}], candidate_scope=["good_src"]),
    )
    data = resp.get_json()
    assert data["ok"] is True
    assert data["would_write"] is True
    assert "provenance_missing" not in data["blocking_reasons"]


def test_duplicate_candidate_fails_closed(client):
    resp = client.post(
        ROUTE,
        json=_payload(candidate_rows=[_candidate_row("good", duplicate=True)]),
    )
    data = resp.get_json()
    assert data["ok"] is False
    assert "duplicate_or_conflict" in data["blocking_reasons"]


def test_conflict_candidate_fails_closed(client):
    resp = client.post(
        ROUTE,
        json=_payload(candidate_rows=[_candidate_row("good", conflict=True)]),
    )
    data = resp.get_json()
    assert data["ok"] is False
    assert "duplicate_or_conflict" in data["blocking_reasons"]


def test_missing_idempotency_key_fails_closed(client):
    resp = client.post(ROUTE, json=_payload(idempotency_key=None))
    data = resp.get_json()
    assert data["ok"] is False
    assert "idempotency_key_missing" in data["blocking_reasons"]


def test_missing_write_target_fails_closed(client):
    resp = client.post(ROUTE, json=_payload(write_target=None))
    data = resp.get_json()
    assert data["ok"] is False
    assert "write_target_missing" in data["blocking_reasons"]


def test_live_write_enabled_true_request_cannot_perform_write(client):
    resp = client.post(ROUTE, json=_payload(live_write_enabled=True))
    data = resp.get_json()
    assert data["live_write_enabled"] is False
    assert data["write_performed"] is False
    assert data["queue_write_performed"] is False
    assert data["database_write_performed"] is False


def test_route_performs_no_filesystem_writes(client, monkeypatch):
    opened_for_write = []
    real_open = open

    def guarded_open(*args, **kwargs):
        mode = kwargs.get("mode", "r")
        if len(args) >= 2:
            mode = args[1]
        if any(flag in mode for flag in ("w", "a", "x", "+")):
            opened_for_write.append((args, kwargs))
            raise AssertionError("Unexpected write during approved-save writer preview API execution")
        return real_open(*args, **kwargs)

    monkeypatch.setattr("builtins.open", guarded_open)
    resp = client.post(ROUTE, json=_payload())
    assert resp.status_code == 200
    assert opened_for_write == []


def test_route_performs_no_live_web_calls(client, monkeypatch):
    def blocked_connect(*args, **kwargs):
        raise AssertionError("Live network call attempted")

    monkeypatch.setattr(socket, "create_connection", blocked_connect)
    resp = client.post(ROUTE, json=_payload())
    assert resp.status_code == 200


def test_response_serializes_to_json(client):
    resp = client.post(ROUTE, json=_payload())
    payload = resp.get_json()
    _ = json.dumps(payload)


def test_current_runtime_cohort_without_urls_remains_provenance_blocked(client):
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

    resp = client.post(
        ROUTE,
        json=_payload(
            token=token,
            candidate_scope=scope,
            candidate_rows=rows,
            operator_approved=True,
            idempotency_key="cohort-check",
            write_target="queue_preview",
            dry_run_required=True,
            live_write_enabled=False,
        ),
    )
    data = resp.get_json()
    assert len(rows) == 31
    assert data["ok"] is False
    assert "provenance_missing" in data["blocking_reasons"]
