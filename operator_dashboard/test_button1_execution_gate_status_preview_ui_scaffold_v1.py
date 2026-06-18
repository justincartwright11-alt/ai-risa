"""
Test suite for Button 1 Execution Gate Status UI scaffold v1.

Validates that:
1. execution_gate_status is present in Button 1 preview payload
2. UI scaffold remains deny-by-default and read-only
3. Side-effect governance flags remain false
4. No Button 2/3 coupling fields are introduced
"""

from operator_dashboard.app import app


def _workflow_payload_from_response(response_json: dict) -> dict:
    workflow = response_json.get("workflow") or {}
    jobs = workflow.get("jobs") or []
    if not jobs:
        return {}
    metadata = ((jobs[0].get("input_ref") or {}).get("metadata") or {})
    payload = metadata.get("payload") or {}
    return payload


def test_execution_gate_ui_payload_presence_and_contract():
    with app.test_client() as client:
        response = client.post(
            "/api/local-ai/orchestrator/workflow-preview",
            json={"source_button": "button1_find_fights", "use_runtime_context": True, "execute_preview": True},
        )

    assert response.status_code == 200
    body = response.get_json() or {}
    payload = _workflow_payload_from_response(body)

    assert "execution_gate_status" in payload
    gate = payload["execution_gate_status"]
    assert isinstance(gate, dict)

    required_fields = [
        "execution_gate_checked",
        "execution_gate_allowed",
        "execution_gate_decision",
        "execution_gate_reason_codes",
        "source_button",
        "provider_id",
        "operator_approval_required",
        "preview_only",
        "provider_execution_performed",
        "network_calls_performed",
        "source_calls_performed",
        "scraping_performed",
        "queue_write_performed",
        "database_write_performed",
        "button2_promotion_performed",
    ]
    for field in required_fields:
        assert field in gate, f"Missing required execution_gate_status field: {field}"


def test_execution_gate_ui_scaffold_is_deny_by_default():
    with app.test_client() as client:
        response = client.post(
            "/api/local-ai/orchestrator/workflow-preview",
            json={"source_button": "button1_find_fights", "use_runtime_context": True, "execute_preview": True},
        )

    payload = _workflow_payload_from_response(response.get_json() or {})
    gate = payload.get("execution_gate_status") or {}

    assert gate.get("execution_gate_checked") is True
    assert gate.get("execution_gate_allowed") is False
    assert gate.get("execution_gate_decision") == "deny"
    assert gate.get("preview_only") is True


def test_execution_gate_ui_scaffold_governance_flags_false():
    with app.test_client() as client:
        response = client.post(
            "/api/local-ai/orchestrator/workflow-preview",
            json={"source_button": "button1_find_fights", "use_runtime_context": True, "execute_preview": True},
        )

    payload = _workflow_payload_from_response(response.get_json() or {})
    gate = payload.get("execution_gate_status") or {}

    assert gate.get("provider_execution_performed") is False
    assert gate.get("network_calls_performed") is False
    assert gate.get("source_calls_performed") is False
    assert gate.get("scraping_performed") is False
    assert gate.get("queue_write_performed") is False
    assert gate.get("database_write_performed") is False
    assert gate.get("button2_promotion_performed") is False


def test_execution_gate_ui_scaffold_reason_codes_present():
    with app.test_client() as client:
        response = client.post(
            "/api/local-ai/orchestrator/workflow-preview",
            json={"source_button": "button1_find_fights", "use_runtime_context": True, "execute_preview": True},
        )

    payload = _workflow_payload_from_response(response.get_json() or {})
    gate = payload.get("execution_gate_status") or {}
    reasons = gate.get("execution_gate_reason_codes") or []

    assert isinstance(reasons, list)
    assert len(reasons) > 0


def test_execution_gate_ui_panel_template_is_read_only_non_interactive():
    with open("operator_dashboard/templates/index.html", "r", encoding="utf-8") as handle:
        template = handle.read()

    assert "id=\"b1-execution-gate-status-panel\"" in template
    assert "Execution Gate Status (Preview-Only)" in template
    assert "🔒 Read-Only" in template

    panel_start = template.find('id="b1-execution-gate-status-panel"')
    assert panel_start != -1
    panel_end = template.find('id="b1-event-cards-panel"', panel_start)
    assert panel_end != -1
    panel_html = template[panel_start:panel_end]

    lowered = panel_html.lower()
    assert "<button" not in lowered
    assert "<input" not in lowered
    assert "<select" not in lowered
    assert "onclick=" not in lowered


def test_execution_gate_ui_scaffold_isolation_from_button2_and_button3_payloads():
    with app.test_client() as client:
        response = client.post(
            "/api/local-ai/orchestrator/workflow-preview",
            json={"source_button": "button1_find_fights", "use_runtime_context": True, "execute_preview": True},
        )

    payload = _workflow_payload_from_response(response.get_json() or {})

    button2_fields = ["pdf_generation_status", "report_queue", "render_output"]
    button3_fields = ["result_source_status", "accuracy_metrics", "learning_calibration"]

    for field in button2_fields:
        assert field not in payload

    for field in button3_fields:
        assert field not in payload
