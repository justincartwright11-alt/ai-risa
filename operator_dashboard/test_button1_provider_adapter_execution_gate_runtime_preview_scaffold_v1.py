from operator_dashboard.app import app
from operator_dashboard.local_ai_orchestrator_readonly_runtime_context_loader import (
    build_button1_runtime_context,
    build_button1_runtime_context_preview,
)


def _workflow_payload_from_response(response_json):
    workflow = response_json.get("workflow") if isinstance(response_json, dict) else {}
    jobs = workflow.get("jobs") if isinstance(workflow, dict) else []
    if not isinstance(jobs, list) or not jobs:
        return {}
    first_job = jobs[0] if isinstance(jobs[0], dict) else {}
    input_ref = first_job.get("input_ref") if isinstance(first_job, dict) else {}
    metadata = input_ref.get("metadata") if isinstance(input_ref, dict) else {}
    payload = metadata.get("payload") if isinstance(metadata, dict) else {}
    return payload if isinstance(payload, dict) else {}


def test_execution_gate_status_exposed_in_button1_runtime_preview_payload():
    with app.test_client() as client:
        response = client.post(
            "/api/local-ai/orchestrator/workflow-preview",
            json={"source_button": "button1_find_fights", "use_runtime_context": True, "execute_preview": True},
        )

    assert response.status_code == 200
    payload = _workflow_payload_from_response(response.get_json())
    execution_gate_status = payload.get("execution_gate_status")

    assert isinstance(execution_gate_status, dict)
    assert execution_gate_status.get("execution_gate_checked") is True
    assert execution_gate_status.get("execution_gate_allowed") is False
    assert execution_gate_status.get("execution_gate_decision") == "deny"


def test_execution_gate_status_is_preview_only_and_requires_operator_approval():
    with app.test_client() as client:
        response = client.post(
            "/api/local-ai/orchestrator/workflow-preview",
            json={"source_button": "button1_find_fights", "use_runtime_context": True, "execute_preview": True},
        )

    payload = _workflow_payload_from_response(response.get_json())
    execution_gate_status = payload.get("execution_gate_status", {})

    assert execution_gate_status.get("preview_only") is True
    assert execution_gate_status.get("operator_approval_required") is True


def test_execution_gate_status_side_effect_flags_remain_false():
    with app.test_client() as client:
        response = client.post(
            "/api/local-ai/orchestrator/workflow-preview",
            json={"source_button": "button1_find_fights", "use_runtime_context": True, "execute_preview": True},
        )

    payload = _workflow_payload_from_response(response.get_json())
    execution_gate_status = payload.get("execution_gate_status", {})

    assert execution_gate_status.get("provider_execution_performed") is False
    assert execution_gate_status.get("network_calls_performed") is False
    assert execution_gate_status.get("source_calls_performed") is False
    assert execution_gate_status.get("scraping_performed") is False
    assert execution_gate_status.get("queue_write_performed") is False
    assert execution_gate_status.get("database_write_performed") is False
    assert execution_gate_status.get("button2_promotion_performed") is False


def test_execution_gate_status_not_exposed_in_non_preview_runtime_context():
    preview_pack = build_button1_runtime_context_preview()
    runtime_pack = build_button1_runtime_context()

    preview_payload = preview_pack.input_ref.get("payload", {})
    runtime_payload = runtime_pack.input_ref.get("payload", {})

    assert "execution_gate_status" in preview_payload
    assert "execution_gate_status" not in runtime_payload


def test_execution_gate_status_contains_deny_reason_codes():
    with app.test_client() as client:
        response = client.post(
            "/api/local-ai/orchestrator/workflow-preview",
            json={"source_button": "button1_find_fights", "use_runtime_context": True, "execute_preview": True},
        )

    payload = _workflow_payload_from_response(response.get_json())
    execution_gate_status = payload.get("execution_gate_status", {})
    reasons = execution_gate_status.get("execution_gate_reason_codes", [])

    assert isinstance(reasons, list)
    assert reasons
    assert "execution_gate_operator_approval_missing" in reasons or "execution_gate_provider_not_enabled" in reasons
