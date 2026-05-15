"""Preview-only Gate 1 token check tests (v1)."""

import json
import os
import socket
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from operator_dashboard.local_ai_orchestrator_gate1_token_check import (
    check_gate1_approval_token_preview,
)
from operator_dashboard.local_ai_orchestrator_job_schema import LocalAIJobInputRef
from operator_dashboard.local_ai_orchestrator_workflow_plan import (
    build_three_button_workflow_plan,
)


def _input_ref(key: str = "seed_001") -> LocalAIJobInputRef:
    return LocalAIJobInputRef(ref_type="entity", ref_key=key, snapshot_hash="snap_v1")


def _valid_gate1_token_payload():
    plan = build_three_button_workflow_plan("button1_find_fights", _input_ref("gate1_ok"))
    return dict(plan.gate_approval_token_preview)


def test_valid_gate1_token_preview_passes_check():
    result = check_gate1_approval_token_preview(_valid_gate1_token_payload())

    assert result.ok is True
    assert result.eligible_for_future_approval is True
    assert result.blocking_reasons == []


def test_missing_token_fails_closed():
    result = check_gate1_approval_token_preview(None)

    assert result.ok is False
    assert result.eligible_for_future_approval is False


def test_wrong_gate_fails_closed():
    token = _valid_gate1_token_payload()
    token["gate_name"] = "Approve Customer PDF Delivery"

    result = check_gate1_approval_token_preview(token)

    assert result.ok is False
    assert any("gate_name" in reason for reason in result.blocking_reasons)


def test_wrong_source_button_fails_closed():
    token = _valid_gate1_token_payload()
    token["source_button"] = "button2_generate_pdfs"

    result = check_gate1_approval_token_preview(token)

    assert result.ok is False
    assert any("source_button" in reason for reason in result.blocking_reasons)


def test_token_with_write_authorized_true_fails_closed():
    token = _valid_gate1_token_payload()
    token["write_authorized"] = True

    result = check_gate1_approval_token_preview(token)

    assert result.ok is False
    assert any("write_authorized" in reason for reason in result.blocking_reasons)


def test_token_with_queue_write_performed_true_fails_closed():
    token = _valid_gate1_token_payload()
    token["queue_write_performed"] = True

    result = check_gate1_approval_token_preview(token)

    assert result.ok is False
    assert any("queue_write_performed" in reason for reason in result.blocking_reasons)


def test_token_with_database_write_performed_true_fails_closed():
    token = _valid_gate1_token_payload()
    token["database_write_performed"] = True

    result = check_gate1_approval_token_preview(token)

    assert result.ok is False
    assert any("database_write_performed" in reason for reason in result.blocking_reasons)


def test_token_check_returns_preview_only_true():
    result = check_gate1_approval_token_preview(_valid_gate1_token_payload())
    assert result.preview_only is True


def test_token_check_returns_mutation_performed_false():
    result = check_gate1_approval_token_preview(_valid_gate1_token_payload())
    assert result.mutation_performed is False


def test_token_check_returns_queue_and_database_write_flags_false():
    result = check_gate1_approval_token_preview(_valid_gate1_token_payload())
    assert result.queue_write_performed is False
    assert result.database_write_performed is False
    assert result.write_authorized is False


def test_token_check_serializes_to_json():
    result = check_gate1_approval_token_preview(_valid_gate1_token_payload())
    payload = result.to_json()
    loaded = json.loads(payload)

    assert loaded["ok"] is True
    assert loaded["preview_only"] is True


def test_token_check_performs_no_filesystem_writes(monkeypatch):
    opened_for_write = []
    real_open = open

    def guarded_open(*args, **kwargs):
        mode = kwargs.get("mode", "r")
        if len(args) >= 2:
            mode = args[1]
        if any(flag in mode for flag in ("w", "a", "x", "+")):
            opened_for_write.append((args, kwargs))
            raise AssertionError("Unexpected write during gate1 token check")
        return real_open(*args, **kwargs)

    monkeypatch.setattr("builtins.open", guarded_open)

    result = check_gate1_approval_token_preview(_valid_gate1_token_payload())
    assert result.ok is True
    assert opened_for_write == []


def test_token_check_performs_no_live_web_calls(monkeypatch):
    def blocked_connect(*args, **kwargs):
        raise AssertionError("Live network call attempted")

    monkeypatch.setattr(socket, "create_connection", blocked_connect)

    result = check_gate1_approval_token_preview(_valid_gate1_token_payload())
    assert result.ok is True
