import json
import pytest
from operator_dashboard.app import app

def _post_preview(payload):
    with app.test_client() as client:
        resp = client.post(
            "/api/local-ai/gate1/save-fights/approved-save-writer-preview",
            data=json.dumps(payload),
            content_type="application/json",
        )
        return resp, resp.get_json()

def _valid_token(token_id):
    return {
        "token_id": token_id,
        "source_button": "button1_find_fights",
        "gate_name": "Approve Save Fights",
        "preview_only": True,
        "write_authorized": False,
        "queue_write_performed": False,
        "database_write_performed": False,
    }

def _payload(token_id, storage_preview_mode=None, live_write_enabled=False):
    payload = {
        "gate_approval_token_preview": _valid_token(token_id),
        "candidate_scope": ["A"],
        "candidate_rows": [{"candidate_id": "A", "source_url": "https://example.com/A"}],
        "operator_approved": True,
        "idempotency_key": f"idemp-{token_id}",
        "write_target": "test-target",
        "dry_run_required": True,
        "live_write_enabled": live_write_enabled,
    }
    if storage_preview_mode is not None:
        payload["storage_preview_mode"] = storage_preview_mode
    return payload

def test_api_accepts_storage_preview_mode_none():
    resp, data = _post_preview(_payload("smoke1", storage_preview_mode="none"))
    assert resp.status_code == 200
    assert data["storage_adapter_checked"] is False
    assert data["ok"] is True

def test_api_accepts_storage_preview_mode_in_memory():
    resp, data = _post_preview(_payload("smoke2", storage_preview_mode="in_memory"))
    assert resp.status_code == 200
    assert data["storage_adapter_checked"] is True
    assert isinstance(data["persisted_preview_refs"], list)
    assert data["ok"] is True

def test_storage_preview_mode_none_adapter_checked_false():
    resp, data = _post_preview(_payload("smoke3", storage_preview_mode="none"))
    assert data["storage_adapter_checked"] is False

def test_storage_preview_mode_in_memory_adapter_checked_true():
    resp, data = _post_preview(_payload("smoke4", storage_preview_mode="in_memory"))
    assert data["storage_adapter_checked"] is True

def test_storage_preview_mode_in_memory_returns_persisted_refs():
    resp, data = _post_preview(_payload("smoke5", storage_preview_mode="in_memory"))
    assert isinstance(data["persisted_preview_refs"], list)
    assert len(data["persisted_preview_refs"]) > 0

def test_storage_preview_mode_in_memory_live_write_enabled_false():
    resp, data = _post_preview(_payload("smoke6", storage_preview_mode="in_memory"))
    assert data["live_write_enabled"] is False

def test_storage_preview_mode_in_memory_write_performed_false():
    resp, data = _post_preview(_payload("smoke7", storage_preview_mode="in_memory"))
    assert data["write_performed"] is False

def test_storage_preview_mode_in_memory_queue_write_performed_false():
    resp, data = _post_preview(_payload("smoke8", storage_preview_mode="in_memory"))
    assert data["queue_write_performed"] is False

def test_storage_preview_mode_in_memory_database_write_performed_false():
    resp, data = _post_preview(_payload("smoke9", storage_preview_mode="in_memory"))
    assert data["database_write_performed"] is False

def test_invalid_storage_preview_mode_fails_closed():
    resp, data = _post_preview(_payload("smoke10", storage_preview_mode="invalid_mode"))
    assert resp.status_code == 400
    assert data["ok"] is False
    assert "invalid storage_preview_mode" in data["blocking_reasons"]

def test_live_write_enabled_true_fails_closed():
    resp, data = _post_preview(_payload("smoke11", storage_preview_mode="in_memory", live_write_enabled=True))
    assert resp.status_code == 200
    assert data["ok"] is False
    assert data["live_write_enabled"] is False
    assert "live_write_enabled_not_allowed" in data["blocking_reasons"]

def test_response_serializes_to_json():
    resp, data = _post_preview(_payload("smoke12", storage_preview_mode="in_memory"))
    json.dumps(data)  # Should not raise
    assert resp.status_code == 200
    assert data["ok"] is True
