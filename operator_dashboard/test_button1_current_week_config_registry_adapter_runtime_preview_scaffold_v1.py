from __future__ import annotations

import inspect

from operator_dashboard.app import app
import operator_dashboard.local_ai_orchestrator_readonly_runtime_context_loader as runtime_loader


def _workflow_payload_from_response(response_json: dict) -> dict:
    workflow = response_json.get("workflow") or {}
    jobs = workflow.get("jobs") or []
    assert jobs
    metadata = ((jobs[0].get("input_ref") or {}).get("metadata") or {})
    payload = metadata.get("payload") or {}
    assert isinstance(payload, dict)
    return payload


def test_preview_runtime_payload_includes_registry_adapter_status(monkeypatch, tmp_path):
    monkeypatch.setattr(runtime_loader, "_default_workspace_root", lambda: str(tmp_path))

    with app.test_client() as client:
        response = client.post(
            "/api/local-ai/orchestrator/workflow-preview",
            json={"source_button": "button1_find_fights", "use_runtime_context": True, "execute_preview": True},
        )
    assert response.status_code == 200
    body = response.get_json() or {}
    payload = _workflow_payload_from_response(body)

    adapter_status = payload.get("registry_adapter_status")
    assert isinstance(adapter_status, dict)
    assert "registry_candidate_valid" in adapter_status
    assert "registry_candidate_count" in adapter_status
    assert "diagnostics" in adapter_status


def test_missing_config_fail_closed_for_registry_adapter_status(monkeypatch, tmp_path):
    monkeypatch.setattr(runtime_loader, "_default_workspace_root", lambda: str(tmp_path))

    with app.test_client() as client:
        response = client.post(
            "/api/local-ai/orchestrator/workflow-preview",
            json={"source_button": "button1_find_fights", "use_runtime_context": True, "execute_preview": True},
        )

    body = response.get_json() or {}
    payload = _workflow_payload_from_response(body)
    adapter_status = payload.get("registry_adapter_status") or {}

    assert adapter_status.get("registry_candidate_valid") is False
    assert adapter_status.get("registration_valid") is False
    assert adapter_status.get("validation_valid") is False
    diagnostics = adapter_status.get("diagnostics") or []
    assert "provider_config_missing" in diagnostics


def test_registry_adapter_status_keeps_execution_and_network_flags_false(monkeypatch, tmp_path):
    monkeypatch.setattr(runtime_loader, "_default_workspace_root", lambda: str(tmp_path))

    with app.test_client() as client:
        response = client.post(
            "/api/local-ai/orchestrator/workflow-preview",
            json={"source_button": "button1_find_fights", "use_runtime_context": True, "execute_preview": True},
        )

    body = response.get_json() or {}
    payload = _workflow_payload_from_response(body)
    adapter_status = payload.get("registry_adapter_status") or {}

    assert adapter_status.get("network_calls_performed") is False
    assert adapter_status.get("provider_execution_performed") is False
    assert adapter_status.get("queue_write_performed") is False
    assert adapter_status.get("database_write_performed") is False
    assert adapter_status.get("operator_approval_required") is True


def test_button2_and_button3_modules_not_referenced_in_new_preview_adapter_surface():
    preview_source = inspect.getsource(runtime_loader.build_button1_runtime_context_preview)
    state_source = inspect.getsource(runtime_loader.load_button1_runtime_state_preview)
    adapter_loader_source = inspect.getsource(runtime_loader._load_button1_registry_adapter_status_preview)

    assert "button2_" not in preview_source
    assert "button3_" not in preview_source
    assert "button2_" not in state_source
    assert "button3_" not in state_source
    assert "button2_" not in adapter_loader_source
    assert "button3_" not in adapter_loader_source
