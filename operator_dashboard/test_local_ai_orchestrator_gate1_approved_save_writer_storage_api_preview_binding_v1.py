import pytest
import json
from operator_dashboard.app import app

def _post_preview(payload):
    with app.test_client() as client:
        resp = client.post(
            "/api/local-ai/gate1/save-fights/approved-save-writer-preview",
            data=json.dumps(payload),
            content_type="application/json",
        )
        return resp, resp.get_json()

def test_api_behavior_unchanged_without_storage_preview_mode():
    payload = {
        "gate_approval_token_preview": {
            "token_id": "tok-1",
            "source_button": "button1_find_fights",
            "gate_name": "Approve Save Fights",
            "preview_only": True,
            "write_authorized": False,
            "queue_write_performed": False,
            "database_write_performed": False,
        },
        "candidate_scope": ["A"],
        "candidate_rows": [{"candidate_id": "A", "source_url": "https://example.com/A"}],
        "operator_approved": True,
        "idempotency_key": "idemp-1",
        "write_target": "test-target",
    }
    resp, data = _post_preview(payload)
    assert resp.status_code == 200
    assert data["scaffold_only"] is True
    assert data["live_write_enabled"] is False
    assert data["write_performed"] is False
    assert data["queue_write_performed"] is False
    assert data["database_write_performed"] is False
    assert data["storage_adapter_checked"] is False
    assert data["test_write_performed"] is False
    assert data["persisted_preview_refs"] == []
    assert data["ok"] is True
    assert data["would_write"] is True
    assert data["blocking_reasons"] == []

def test_api_storage_preview_mode_none():
    payload = {
        "gate_approval_token_preview": {
            "token_id": "tok-2",
            "source_button": "button1_find_fights",
            "gate_name": "Approve Save Fights",
            "preview_only": True,
            "write_authorized": False,
            "queue_write_performed": False,
            "database_write_performed": False,
        },
        "candidate_scope": ["A"],
        "candidate_rows": [{"candidate_id": "A", "source_url": "https://example.com/A"}],
        "operator_approved": True,
        "idempotency_key": "idemp-2",
        "write_target": "test-target",
        "storage_preview_mode": "none",
    }
    resp, data = _post_preview(payload)
    assert resp.status_code == 200
    assert data["storage_adapter_checked"] is False
    assert data["test_write_performed"] is False
    assert data["persisted_preview_refs"] == []
    assert data["ok"] is True
    assert data["would_write"] is True
    assert data["blocking_reasons"] == []

def test_api_storage_preview_mode_in_memory():
    payload = {
        "gate_approval_token_preview": {
            "token_id": "tok-3",
            "source_button": "button1_find_fights",
            "gate_name": "Approve Save Fights",
            "preview_only": True,
            "write_authorized": False,
            "queue_write_performed": False,
            "database_write_performed": False,
        },
        "candidate_scope": ["A"],
        "candidate_rows": [{"candidate_id": "A", "source_url": "https://example.com/A"}],
        "operator_approved": True,
        "idempotency_key": "idemp-3",
        "write_target": "test-target",
        "storage_preview_mode": "in_memory",
    }
    resp, data = _post_preview(payload)
    assert resp.status_code == 200
    assert data["storage_adapter_checked"] is True
    assert data["test_write_performed"] is True
    assert isinstance(data["persisted_preview_refs"], list)
    assert data["ok"] is True
    assert data["would_write"] is True
    assert data["blocking_reasons"] == []

def test_api_invalid_storage_preview_mode_fails_closed():
    payload = {
        "gate_approval_token_preview": {
            "token_id": "tok-4",
            "source_button": "button1_find_fights",
            "gate_name": "Approve Save Fights",
            "preview_only": True,
            "write_authorized": False,
            "queue_write_performed": False,
            "database_write_performed": False,
        },
        "candidate_scope": ["A"],
        "candidate_rows": [{"candidate_id": "A", "source_url": "https://example.com/A"}],
        "operator_approved": True,
        "idempotency_key": "idemp-4",
        "write_target": "test-target",
        "storage_preview_mode": "invalid_mode",
    }
    resp, data = _post_preview(payload)
    assert resp.status_code == 400
    assert data["ok"] is False
    assert data["scaffold_only"] is True
    assert data["live_write_enabled"] is False
    assert data["write_performed"] is False
    assert data["queue_write_performed"] is False
    assert data["database_write_performed"] is False
    assert "invalid storage_preview_mode" in data["blocking_reasons"]

def test_api_live_write_enabled_true_forced_false():
    payload = {
        "gate_approval_token_preview": {
            "token_id": "tok-5",
            "source_button": "button1_find_fights",
            "gate_name": "Approve Save Fights",
            "preview_only": True,
            "write_authorized": False,
            "queue_write_performed": False,
            "database_write_performed": False,
        },
        "candidate_scope": ["A"],
        "candidate_rows": [{"candidate_id": "A", "source_url": "https://example.com/A"}],
        "operator_approved": True,
        "idempotency_key": "idemp-5",
        "write_target": "test-target",
        "live_write_enabled": True,
        "storage_preview_mode": "in_memory",
    }
    resp, data = _post_preview(payload)
    assert resp.status_code == 200
    assert data["live_write_enabled"] is False
    assert data["write_performed"] is False
    assert data["queue_write_performed"] is False
    assert data["database_write_performed"] is False
    assert data["ok"] is False
    assert "live_write_enabled_not_allowed" in data["blocking_reasons"]

def test_api_json_response_serialization():
    payload = {
        "gate_approval_token_preview": {
            "token_id": "tok-6",
            "source_button": "button1_find_fights",
            "gate_name": "Approve Save Fights",
            "preview_only": True,
            "write_authorized": False,
            "queue_write_performed": False,
            "database_write_performed": False,
        },
        "candidate_scope": ["A"],
        "candidate_rows": [{"candidate_id": "A", "source_url": "https://example.com/A"}],
        "operator_approved": True,
        "idempotency_key": "idemp-6",
        "write_target": "test-target",
        "storage_preview_mode": "in_memory",
    }
    resp, data = _post_preview(payload)
    # Should be JSON serializable
    json.dumps(data)
    assert resp.status_code == 200
    assert data["ok"] is True
    assert data["scaffold_only"] is True
    assert data["live_write_enabled"] is False
    assert data["write_performed"] is False
    assert data["queue_write_performed"] is False
    assert data["database_write_performed"] is False
    assert data["storage_adapter_checked"] is True
    assert data["test_write_performed"] is True
    assert isinstance(data["persisted_preview_refs"], list)
    assert data["would_write"] is True
    assert data["blocking_reasons"] == []
