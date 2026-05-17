"""Focused tests for Gate 1 writer + storage adapter preview integration (v1)."""

import json
import os
import socket
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from operator_dashboard.local_ai_orchestrator_gate1_approved_save_writer import (
    run_gate1_approved_save_writer_scaffold,
)
from operator_dashboard.local_ai_orchestrator_gate1_save_storage_adapter import (
    InMemoryGate1SaveStorageAdapter,
    TempPathGate1SaveStorageAdapter,
)


def _valid_request(write_target: str = "queue_preview", live_write_enabled: bool = False):
    token_preview = {
        "source_button": "button1_find_fights",
        "gate_name": "Approve Save Fights",
        "preview_only": True,
        "write_authorized": False,
        "queue_write_performed": False,
        "database_write_performed": False,
        "token_id": "tok123",
    }
    return {
        "operator_approved": True,
        "gate_approval_token_preview": token_preview,
        "candidate_scope": "f1",
        "candidate_rows": [{"fight_id": "f1", "source_url": "https://example.test/f1"}],
        "idempotency_key": "abc123",
        "write_target": write_target,
        "dry_run_required": True,
        "live_write_enabled": live_write_enabled,
    }


def test_writer_scaffold_works_unchanged_without_storage_adapter():
    result = run_gate1_approved_save_writer_scaffold(_valid_request())
    assert result.ok is True
    assert result.storage_adapter_checked is False
    assert result.persisted_preview_refs == []


def test_writer_scaffold_can_call_in_memory_storage_adapter():
    adapter = InMemoryGate1SaveStorageAdapter()
    result = run_gate1_approved_save_writer_scaffold(_valid_request(), storage_adapter=adapter)
    assert result.ok is True
    assert result.storage_adapter_checked is True


def test_in_memory_adapter_returns_persisted_preview_refs():
    adapter = InMemoryGate1SaveStorageAdapter()
    result = run_gate1_approved_save_writer_scaffold(_valid_request(), storage_adapter=adapter)
    assert result.persisted_preview_refs
    assert result.persisted_preview_refs[0].startswith("inmem:")


def test_writer_output_includes_storage_adapter_checked_true_when_adapter_supplied():
    adapter = InMemoryGate1SaveStorageAdapter()
    result = run_gate1_approved_save_writer_scaffold(_valid_request(), storage_adapter=adapter)
    assert result.storage_adapter_checked is True


def test_writer_output_keeps_live_write_enabled_false():
    adapter = InMemoryGate1SaveStorageAdapter()
    result = run_gate1_approved_save_writer_scaffold(_valid_request(), storage_adapter=adapter)
    assert result.live_write_enabled is False


def test_writer_output_keeps_write_performed_false():
    adapter = InMemoryGate1SaveStorageAdapter()
    result = run_gate1_approved_save_writer_scaffold(_valid_request(), storage_adapter=adapter)
    assert result.write_performed is False


def test_writer_output_keeps_queue_write_performed_false():
    adapter = InMemoryGate1SaveStorageAdapter()
    result = run_gate1_approved_save_writer_scaffold(_valid_request(), storage_adapter=adapter)
    assert result.queue_write_performed is False


def test_writer_output_keeps_database_write_performed_false():
    adapter = InMemoryGate1SaveStorageAdapter()
    result = run_gate1_approved_save_writer_scaffold(_valid_request(), storage_adapter=adapter)
    assert result.database_write_performed is False


def test_production_write_target_fails_closed():
    adapter = InMemoryGate1SaveStorageAdapter()
    result = run_gate1_approved_save_writer_scaffold(_valid_request(write_target="queue"), storage_adapter=adapter)
    assert result.ok is False
    assert "production_write_target_blocked" in result.blocking_reasons


def test_live_write_enabled_true_fails_closed():
    adapter = InMemoryGate1SaveStorageAdapter()
    result = run_gate1_approved_save_writer_scaffold(_valid_request(live_write_enabled=True), storage_adapter=adapter)
    assert result.ok is False
    assert "live_write_enabled_not_allowed" in result.blocking_reasons


def test_adapter_result_indicating_queue_write_performed_true_fails_closed(monkeypatch):
    class FakeStorageResult:
        ok = True
        queue_write_performed = True
        database_write_performed = False
        test_write_performed = False
        persisted_preview_refs = []
        blocking_reasons = []

    def fake_run_storage(*args, **kwargs):
        return FakeStorageResult()

    monkeypatch.setattr(
        "operator_dashboard.local_ai_orchestrator_gate1_save_storage_adapter.run_gate1_save_storage_adapter_scaffold",
        fake_run_storage,
    )
    result = run_gate1_approved_save_writer_scaffold(_valid_request(), storage_adapter=InMemoryGate1SaveStorageAdapter())
    assert result.ok is False
    assert "adapter_queue_write_not_allowed" in result.blocking_reasons


def test_adapter_result_indicating_database_write_performed_true_fails_closed(monkeypatch):
    class FakeStorageResult:
        ok = True
        queue_write_performed = False
        database_write_performed = True
        test_write_performed = False
        persisted_preview_refs = []
        blocking_reasons = []

    def fake_run_storage(*args, **kwargs):
        return FakeStorageResult()

    monkeypatch.setattr(
        "operator_dashboard.local_ai_orchestrator_gate1_save_storage_adapter.run_gate1_save_storage_adapter_scaffold",
        fake_run_storage,
    )
    result = run_gate1_approved_save_writer_scaffold(_valid_request(), storage_adapter=InMemoryGate1SaveStorageAdapter())
    assert result.ok is False
    assert "adapter_database_write_not_allowed" in result.blocking_reasons


def test_temp_path_adapter_writes_only_inside_explicit_temp_path(tmp_path: Path):
    adapter = TempPathGate1SaveStorageAdapter(tmp_path)
    result = run_gate1_approved_save_writer_scaffold(_valid_request(), storage_adapter=adapter)
    assert result.ok is True
    assert result.persisted_preview_refs
    persisted = Path(result.persisted_preview_refs[0]).resolve()
    assert str(persisted).lower().startswith(str(tmp_path.resolve()).lower())


def test_no_production_filesystem_writes_occur(monkeypatch):
    import builtins

    real_open = builtins.open

    def guarded_open(*args, **kwargs):
        mode = kwargs.get("mode", "r")
        if len(args) >= 2:
            mode = args[1]
        if any(flag in mode for flag in ("w", "a", "x", "+")):
            # in-memory integration should not call filesystem writes
            raise AssertionError("Unexpected production filesystem write")
        return real_open(*args, **kwargs)

    monkeypatch.setattr(builtins, "open", guarded_open)
    result = run_gate1_approved_save_writer_scaffold(_valid_request(), storage_adapter=InMemoryGate1SaveStorageAdapter())
    assert result.ok is True


def test_no_live_web_calls_occur(monkeypatch):
    def blocked_connect(*args, **kwargs):
        raise AssertionError("Live network call attempted")

    monkeypatch.setattr(socket, "create_connection", blocked_connect)
    result = run_gate1_approved_save_writer_scaffold(_valid_request(), storage_adapter=InMemoryGate1SaveStorageAdapter())
    assert result.ok is True


def test_response_serializes_to_json():
    result = run_gate1_approved_save_writer_scaffold(_valid_request(), storage_adapter=InMemoryGate1SaveStorageAdapter())
    payload = result.to_dict()
    encoded = json.dumps(payload)
    assert isinstance(encoded, str)
