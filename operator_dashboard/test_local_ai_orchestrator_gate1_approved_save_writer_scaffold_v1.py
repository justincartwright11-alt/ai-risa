"""
test_local_ai_orchestrator_gate1_approved_save_writer_scaffold_v1.py
Focused tests for Gate 1 approved save writer scaffold.
"""
import pytest
from operator_dashboard.local_ai_orchestrator_gate1_save_fights_dry_run_apply_preview import Gate1SaveFightsDryRunApplyPreviewResult
from operator_dashboard.local_ai_orchestrator_gate1_approved_save_writer import run_gate1_approved_save_writer_scaffold

def valid_request():
    # Use a valid token preview contract
    from operator_dashboard.local_ai_orchestrator_gate1_token_check import Gate1ApprovalTokenCheckResult
    token_preview = {
        "ok": True,
        "source_button": "button1_find_fights",
        "gate_name": "Approve Save Fights",
        "preview_only": True,
        "write_authorized": False,
        "queue_write_performed": False,
        "database_write_performed": False,
        "token_id": "tok123"
    }
    return {
        "operator_approved": True,
        "gate_approval_token_preview": token_preview,
        "candidate_scope": "f1",
        "candidate_rows": [{"fight_id": "f1", "source_url": "https://example.test/f1"}],
        "idempotency_key": "abc123",
        "write_target": "queue",
        "dry_run_required": True,
        "live_write_enabled": False
    }

def test_valid_approved_request_returns_ok():
    req = valid_request()
    result = run_gate1_approved_save_writer_scaffold(req)
    assert result.ok
    assert result.scaffold_only
    assert not result.live_write_enabled
    assert not result.write_performed
    assert not result.queue_write_performed
    assert not result.database_write_performed
    assert result.audit_record_preview is not None
    assert result.rollback_pointer_preview is not None
    assert result.idempotency_key == "abc123"
    assert result.would_write
    assert result.blocking_reasons == []

def test_missing_operator_approval_fails_closed():
    req = valid_request()
    req["operator_approved"] = False
    result = run_gate1_approved_save_writer_scaffold(req)
    assert not result.ok
    assert "operator_approval_missing" in result.blocking_reasons

def test_invalid_token_fails_closed():
    req = valid_request()
    req["gate_approval_token_preview"] = {"ok": False}
    result = run_gate1_approved_save_writer_scaffold(req)
    assert not result.ok
    assert "token_check_failed" in result.blocking_reasons

def test_failed_dry_run_fails_closed(monkeypatch):
    req = valid_request()
    req["candidate_rows"] = [{"fight_id": "f1", "source_url": "https://example.test/f1"}]
    def fake_dry_run(*_, **__):
        return Gate1SaveFightsDryRunApplyPreviewResult(
            ok=False,
            eligible_for_future_approval=False,
            future_write_eligibility=False,
            preview_only=True,
            write_authorized=False,
            mutation_performed=False,
            queue_write_performed=False,
            database_write_performed=False,
            candidate_scope_present=True,
            candidate_scope_empty=False,
            scoped_candidate_count=1,
            would_save_count=0,
            duplicate_or_conflict_count=0,
            provenance_missing_count=0,
            blocking_reasons=["test_block"],
            would_save_candidate_ids=[],
            blocked_candidate_ids=["f1"]
        )
    monkeypatch.setattr(
        "operator_dashboard.local_ai_orchestrator_gate1_approved_save_writer.run_gate1_save_fights_dry_run_apply_preview",
        fake_dry_run,
    )
    result = run_gate1_approved_save_writer_scaffold(req)
    assert not result.ok
    assert "dry_run_not_eligible" in result.blocking_reasons

def test_missing_provenance_fails_closed():
    req = valid_request()
    req["candidate_rows"] = [{"fight_id": "f1"}]
    result = run_gate1_approved_save_writer_scaffold(req)
    assert not result.ok
    assert "provenance_missing" in result.blocking_reasons

def test_duplicate_candidate_fails_closed(monkeypatch):
    req = valid_request()
    def fake_dry_run(*_, **__):
        return Gate1SaveFightsDryRunApplyPreviewResult(
            ok=True,
            eligible_for_future_approval=True,
            future_write_eligibility=True,
            preview_only=True,
            write_authorized=False,
            mutation_performed=False,
            queue_write_performed=False,
            database_write_performed=False,
            candidate_scope_present=True,
            candidate_scope_empty=False,
            scoped_candidate_count=1,
            would_save_count=0,
            duplicate_or_conflict_count=1,
            provenance_missing_count=0,
            blocking_reasons=["duplicate"],
            would_save_candidate_ids=[],
            blocked_candidate_ids=["f1"]
        )
    monkeypatch.setattr(
        "operator_dashboard.local_ai_orchestrator_gate1_approved_save_writer.run_gate1_save_fights_dry_run_apply_preview",
        fake_dry_run,
    )
    result = run_gate1_approved_save_writer_scaffold(req)
    assert not result.ok
    assert "duplicate_or_conflict" in result.blocking_reasons

def test_conflict_candidate_fails_closed(monkeypatch):
    req = valid_request()
    def fake_dry_run(*_, **__):
        return Gate1SaveFightsDryRunApplyPreviewResult(
            ok=True,
            eligible_for_future_approval=True,
            future_write_eligibility=True,
            preview_only=True,
            write_authorized=False,
            mutation_performed=False,
            queue_write_performed=False,
            database_write_performed=False,
            candidate_scope_present=True,
            candidate_scope_empty=False,
            scoped_candidate_count=1,
            would_save_count=0,
            duplicate_or_conflict_count=1,
            provenance_missing_count=0,
            blocking_reasons=["conflict"],
            would_save_candidate_ids=[],
            blocked_candidate_ids=["f1"]
        )
    monkeypatch.setattr(
        "operator_dashboard.local_ai_orchestrator_gate1_approved_save_writer.run_gate1_save_fights_dry_run_apply_preview",
        fake_dry_run,
    )
    result = run_gate1_approved_save_writer_scaffold(req)
    assert not result.ok
    assert "duplicate_or_conflict" in result.blocking_reasons

def test_missing_idempotency_key_fails_closed():
    req = valid_request()
    req["idempotency_key"] = None
    result = run_gate1_approved_save_writer_scaffold(req)
    assert not result.ok
    assert "idempotency_key_missing" in result.blocking_reasons

def test_missing_write_target_fails_closed():
    req = valid_request()
    req["write_target"] = None
    result = run_gate1_approved_save_writer_scaffold(req)
    assert not result.ok
    assert "write_target_missing" in result.blocking_reasons

def test_live_write_enabled_defaults_false():
    req = valid_request()
    req.pop("live_write_enabled")
    result = run_gate1_approved_save_writer_scaffold(req)
    assert not result.live_write_enabled

def test_write_performed_remains_false():
    req = valid_request()
    result = run_gate1_approved_save_writer_scaffold(req)
    assert not result.write_performed

def test_queue_write_performed_remains_false():
    req = valid_request()
    result = run_gate1_approved_save_writer_scaffold(req)
    assert not result.queue_write_performed

def test_database_write_performed_remains_false():
    req = valid_request()
    result = run_gate1_approved_save_writer_scaffold(req)
    assert not result.database_write_performed

def test_audit_record_preview_generated():
    req = valid_request()
    result = run_gate1_approved_save_writer_scaffold(req)
    assert result.audit_record_preview is not None

def test_rollback_pointer_preview_generated():
    req = valid_request()
    result = run_gate1_approved_save_writer_scaffold(req)
    assert result.rollback_pointer_preview is not None

def test_result_serializes_to_json():
    import json
    req = valid_request()
    result = run_gate1_approved_save_writer_scaffold(req)
    d = result.to_dict()
    s = json.dumps(d)
    assert isinstance(s, str)

def test_scaffold_performs_no_filesystem_writes(monkeypatch):
    # No file writes should occur
    import builtins
    open_orig = builtins.open
    def fail_open(*a, **k):
        raise AssertionError("Filesystem write attempted")
    monkeypatch.setattr(builtins, "open", fail_open)
    req = valid_request()
    run_gate1_approved_save_writer_scaffold(req)
    monkeypatch.setattr(builtins, "open", open_orig)

def test_scaffold_performs_no_live_web_calls(monkeypatch):
    # No web calls should occur
    import requests
    get_orig = requests.get
    def fail_get(*a, **k):
        raise AssertionError("Live web call attempted")
    monkeypatch.setattr(requests, "get", fail_get)
    req = valid_request()
    run_gate1_approved_save_writer_scaffold(req)
    monkeypatch.setattr(requests, "get", get_orig)
