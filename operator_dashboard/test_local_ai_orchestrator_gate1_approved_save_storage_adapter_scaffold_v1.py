"""Focused tests for Gate 1 approved save storage adapter scaffold (v1)."""

import json
import os
import socket
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from operator_dashboard.local_ai_orchestrator_gate1_save_storage_adapter import (
    InMemoryGate1SaveStorageAdapter,
    TempPathGate1SaveStorageAdapter,
    run_gate1_save_storage_adapter_scaffold,
)


def _valid_request(write_target: str = "queue_preview"):
    return {
        "operator_approved": True,
        "live_write_enabled": False,
        "write_target": write_target,
        "idempotency_key": "idem_123",
        "audit_record_preview": {"action": "scaffold_save_preview", "candidate_rows_count": 1},
        "rollback_pointer_preview": {"pre_write_state": "scaffold_only"},
        "would_write_candidates": ["fight_1"],
    }


def test_in_memory_adapter_accepts_valid_scaffold_result():
    adapter = InMemoryGate1SaveStorageAdapter()
    result = run_gate1_save_storage_adapter_scaffold(request=_valid_request(), adapter=adapter)
    assert result.ok is True
    assert result.adapter_scaffold_only is True
    assert result.test_write_performed is True
    assert len(result.persisted_preview_refs) == 1


def test_missing_idempotency_key_fails_closed():
    req = _valid_request()
    req["idempotency_key"] = None
    result = run_gate1_save_storage_adapter_scaffold(request=req)
    assert result.ok is False
    assert "idempotency_key_missing" in result.blocking_reasons


def test_missing_audit_record_preview_fails_closed():
    req = _valid_request()
    req["audit_record_preview"] = None
    result = run_gate1_save_storage_adapter_scaffold(request=req)
    assert result.ok is False
    assert "audit_record_preview_missing" in result.blocking_reasons


def test_missing_rollback_pointer_preview_fails_closed():
    req = _valid_request()
    req["rollback_pointer_preview"] = None
    result = run_gate1_save_storage_adapter_scaffold(request=req)
    assert result.ok is False
    assert "rollback_pointer_preview_missing" in result.blocking_reasons


def test_missing_would_write_fails_closed():
    req = _valid_request()
    req["would_write_candidates"] = None
    result = run_gate1_save_storage_adapter_scaffold(request=req)
    assert result.ok is False
    assert "would_write_candidates_missing" in result.blocking_reasons


def test_live_write_enabled_false_blocks_production_write():
    req = _valid_request(write_target="queue")
    req["live_write_enabled"] = False
    result = run_gate1_save_storage_adapter_scaffold(request=req)
    assert result.ok is False
    assert "live_write_disabled" in result.blocking_reasons


def test_production_write_target_fails_closed():
    req = _valid_request(write_target="database")
    req["live_write_enabled"] = True
    result = run_gate1_save_storage_adapter_scaffold(request=req)
    assert result.ok is False
    assert "production_write_target_blocked" in result.blocking_reasons


def test_in_memory_adapter_can_record_persisted_preview_refs():
    adapter = InMemoryGate1SaveStorageAdapter()
    result = run_gate1_save_storage_adapter_scaffold(request=_valid_request(), adapter=adapter)
    assert result.ok is True
    assert result.persisted_preview_refs
    assert result.persisted_preview_refs[0].startswith("inmem:")


def test_temp_path_adapter_works_only_with_explicit_temp_path(tmp_path: Path):
    adapter = TempPathGate1SaveStorageAdapter(tmp_path)
    result = run_gate1_save_storage_adapter_scaffold(request=_valid_request(), adapter=adapter)
    assert result.ok is True
    assert len(result.persisted_preview_refs) == 1
    assert Path(result.persisted_preview_refs[0]).exists()


def test_temp_path_adapter_never_writes_outside_supplied_temp_path(tmp_path: Path):
    adapter = TempPathGate1SaveStorageAdapter(tmp_path)
    req = _valid_request()
    req["idempotency_key"] = "../../escape"
    result = run_gate1_save_storage_adapter_scaffold(request=req, adapter=adapter)
    assert result.ok is True
    persisted = Path(result.persisted_preview_refs[0]).resolve()
    assert str(persisted).lower().startswith(str(tmp_path.resolve()).lower())


def test_queue_write_performed_remains_false():
    result = run_gate1_save_storage_adapter_scaffold(request=_valid_request())
    assert result.queue_write_performed is False


def test_database_write_performed_remains_false():
    result = run_gate1_save_storage_adapter_scaffold(request=_valid_request())
    assert result.database_write_performed is False


def test_production_write_performed_remains_false():
    result = run_gate1_save_storage_adapter_scaffold(request=_valid_request())
    assert result.production_write_performed is False


def test_no_live_web_calls_occur(monkeypatch):
    def blocked_connect(*args, **kwargs):
        raise AssertionError("Live network call attempted")

    monkeypatch.setattr(socket, "create_connection", blocked_connect)
    result = run_gate1_save_storage_adapter_scaffold(request=_valid_request())
    assert result.ok is True


def test_response_serializes_to_json():
    result = run_gate1_save_storage_adapter_scaffold(request=_valid_request())
    payload = result.to_dict()
    encoded = json.dumps(payload)
    assert isinstance(encoded, str)
