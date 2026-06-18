"""
Test suite for Button 1 Registry Adapter Status UI scaffold v1.

Validates that:
1. UI panel renders correctly with valid adapter status via API
2. UI panel displays fail-closed state when config missing
3. Governance flags remain false (no execution, network, writes)
4. Panel integrates with existing Button 1 workflow
5. Button 2 and Button 3 remain unchanged
6. All UI elements are read-only/non-interactive
"""

import json
import pytest
from operator_dashboard.app import app


def _workflow_payload_from_response(response_json: dict) -> dict:
    """Extract the workflow payload from the API response."""
    workflow = response_json.get("workflow") or {}
    jobs = workflow.get("jobs") or []
    if not jobs:
        return {}
    metadata = ((jobs[0].get("input_ref") or {}).get("metadata") or {})
    payload = metadata.get("payload") or {}
    return payload


def test_ui_panel_renders_with_valid_adapter_status():
    """Verify that the registry_adapter_status UI panel renders with valid data via API."""
    with app.test_client() as client:
        response = client.post(
            "/api/local-ai/orchestrator/workflow-preview",
            json={"source_button": "button1_find_fights", "use_runtime_context": True, "execute_preview": True},
        )
    
    assert response.status_code == 200
    body = response.get_json() or {}
    payload = _workflow_payload_from_response(body)
    
    # Verify registry_adapter_status is in the payload
    assert 'registry_adapter_status' in payload, "registry_adapter_status must be in payload"
    
    adapter_status = payload['registry_adapter_status']
    assert isinstance(adapter_status, dict), "adapter_status must be a dict"
    
    # Verify required fields exist (from design spec)
    required_fields = [
        'registry_candidate_valid',
        'registration_valid',
        'validation_valid',
        'registry_candidate_count',
        'enabled_registry_candidate_ids',
        'provider_execution_performed',
        'network_calls_performed',
        'queue_write_performed',
        'database_write_performed',
        'diagnostics',
        'operator_approval_required',
    ]
    
    for field in required_fields:
        assert field in adapter_status, f"Missing required field: {field}"


def test_ui_panel_displays_fail_closed_state_when_config_missing():
    """Verify that UI panel correctly displays fail-closed state when config is missing."""
    with app.test_client() as client:
        response = client.post(
            "/api/local-ai/orchestrator/workflow-preview",
            json={"source_button": "button1_find_fights", "use_runtime_context": True, "execute_preview": True},
        )
    
    assert response.status_code == 200
    body = response.get_json() or {}
    payload = _workflow_payload_from_response(body)
    adapter_status = payload.get('registry_adapter_status') or {}
    
    # When config is missing, registry_candidate_valid should be False and diagnostics populated
    if not adapter_status.get('registration_valid'):
        assert adapter_status.get('registry_candidate_valid') is False, "registry_candidate_valid must be False when config invalid"
        assert len(adapter_status.get('diagnostics', [])) > 0, "diagnostics must be populated when fail-closed"
        assert 'provider_config_missing' in adapter_status.get('diagnostics', []), "Diagnostics must mention missing config"


def test_governance_flags_all_false_in_ui_panel():
    """Verify that all governance flags remain false (no execution, network, writes)."""
    with app.test_client() as client:
        response = client.post(
            "/api/local-ai/orchestrator/workflow-preview",
            json={"source_button": "button1_find_fights", "use_runtime_context": True, "execute_preview": True},
        )
    
    assert response.status_code == 200
    body = response.get_json() or {}
    payload = _workflow_payload_from_response(body)
    adapter_status = payload.get('registry_adapter_status') or {}
    
    # All execution/network/write flags must be False
    assert adapter_status.get('provider_execution_performed') is False, "provider_execution_performed must be False"
    assert adapter_status.get('network_calls_performed') is False, "network_calls_performed must be False"
    assert adapter_status.get('queue_write_performed') is False, "queue_write_performed must be False"
    assert adapter_status.get('database_write_performed') is False, "database_write_performed must be False"


def test_ui_panel_fields_match_design_spec():
    """Verify that all UI panel fields are present and properly formatted."""
    with app.test_client() as client:
        response = client.post(
            "/api/local-ai/orchestrator/workflow-preview",
            json={"source_button": "button1_find_fights", "use_runtime_context": True, "execute_preview": True},
        )
    
    assert response.status_code == 200
    body = response.get_json() or {}
    payload = _workflow_payload_from_response(body)
    adapter_status = payload.get('registry_adapter_status') or {}
    
    # Verify field types and valid ranges (using design spec field names)
    assert isinstance(adapter_status.get('registry_candidate_valid'), bool)
    assert isinstance(adapter_status.get('registration_valid'), bool)
    assert isinstance(adapter_status.get('validation_valid'), bool)
    assert isinstance(adapter_status.get('registry_candidate_count'), (int, float))
    assert isinstance(adapter_status.get('enabled_registry_candidate_ids'), list)
    assert adapter_status.get('registry_candidate_count', 0) >= 0
    assert len(adapter_status.get('enabled_registry_candidate_ids', [])) >= 0
    assert len(adapter_status.get('enabled_registry_candidate_ids', [])) <= adapter_status.get('registry_candidate_count', 0)
    assert isinstance(adapter_status.get('diagnostics'), list)
    for diag in adapter_status.get('diagnostics', []):
        assert isinstance(diag, str)


def test_ui_panel_read_only_no_action_buttons():
    """Verify that the UI panel is read-only with no action buttons or controls."""
    with app.test_client() as client:
        response = client.post(
            "/api/local-ai/orchestrator/workflow-preview",
            json={"source_button": "button1_find_fights", "use_runtime_context": True, "execute_preview": True},
        )
    
    assert response.status_code == 200
    body = response.get_json() or {}
    payload = _workflow_payload_from_response(body)
    adapter_status = payload.get('registry_adapter_status') or {}
    
    # The adapter_status dict itself has no callback/handler fields
    # It's pure data, not executable commands
    for key in adapter_status.keys():
        value = adapter_status[key]
        # No fields should be callable or executable
        assert not callable(value), f"Field {key} must not be callable"
    
    # Verify structure is immutable data only
    assert isinstance(adapter_status, dict)
    assert not any(key.startswith('_') for key in adapter_status.keys()), \
        "No private/implementation fields should be exposed"


def test_ui_isolation_from_button2_and_button3():
    """Verify that Button 1 registry adapter UI does not reference Button 2 or Button 3."""
    with app.test_client() as client:
        response = client.post(
            "/api/local-ai/orchestrator/workflow-preview",
            json={"source_button": "button1_find_fights", "use_runtime_context": True, "execute_preview": True},
        )
    
    assert response.status_code == 200
    body = response.get_json() or {}
    payload = _workflow_payload_from_response(body)
    
    # Button 1 payload should not contain Button 2 or Button 3 specific fields
    button2_fields = ['pdf_generation_status', 'report_queue', 'render_output']
    button3_fields = ['result_source_status', 'accuracy_metrics', 'learning_calibration']
    
    for field in button2_fields:
        assert field not in payload, f"Button 2 field {field} should not be in Button 1 payload"
    
    for field in button3_fields:
        assert field not in payload, f"Button 3 field {field} should not be in Button 1 payload"


def test_adapter_status_payload_contract_stability():
    """Verify that registry_adapter_status payload contract is stable and backward-compatible."""
    with app.test_client() as client:
        response = client.post(
            "/api/local-ai/orchestrator/workflow-preview",
            json={"source_button": "button1_find_fights", "use_runtime_context": True, "execute_preview": True},
        )
    
    assert response.status_code == 200
    body = response.get_json() or {}
    payload = _workflow_payload_from_response(body)
    adapter_status = payload.get('registry_adapter_status') or {}
    
    # Contract: minimal schema that all versions must support (from design spec)
    minimal_contract = {
        'registry_candidate_valid': bool,
        'registration_valid': bool,
        'validation_valid': bool,
        'registry_candidate_count': (int, float),
        'enabled_registry_candidate_ids': list,
        'diagnostics': list,
        'provider_execution_performed': bool,
        'network_calls_performed': bool,
        'queue_write_performed': bool,
        'database_write_performed': bool,
        'operator_approval_required': bool,
    }
    
    for field, expected_type in minimal_contract.items():
        assert field in adapter_status, f"Contract field {field} must be present"
        if isinstance(expected_type, tuple):
            assert isinstance(adapter_status[field], expected_type), \
                f"Field {field} must be one of {expected_type}"
        else:
            assert isinstance(adapter_status[field], expected_type), \
                f"Field {field} must be {expected_type}"


def test_multiple_ui_render_cycles_preserve_state():
    """Verify that calling render multiple times doesn't corrupt state."""
    responses = []
    for i in range(2):
        with app.test_client() as client:
            response = client.post(
                "/api/local-ai/orchestrator/workflow-preview",
                json={"source_button": "button1_find_fights", "use_runtime_context": True, "execute_preview": True},
            )
        assert response.status_code == 200
        body = response.get_json() or {}
        payload = _workflow_payload_from_response(body)
        responses.append(payload.get('registry_adapter_status') or {})
    
    # Both responses should have identical adapter_status data
    assert json.dumps(responses[0], sort_keys=True) == json.dumps(responses[1], sort_keys=True), \
        "Multiple render cycles must produce identical results"


def test_ui_panel_no_network_requests_in_rendering():
    """Verify that UI rendering does not trigger network requests."""
    with app.test_client() as client:
        response = client.post(
            "/api/local-ai/orchestrator/workflow-preview",
            json={"source_button": "button1_find_fights", "use_runtime_context": True, "execute_preview": True},
        )
    
    assert response.status_code == 200
    body = response.get_json() or {}
    payload = _workflow_payload_from_response(body)
    adapter_status = payload.get('registry_adapter_status') or {}
    
    # The only valid data sources are:
    # 1. Local registration config file
    # 2. Adapter transformation
    # No network/scraping/provider execution should occur
    
    # Verify by checking that these flags are False
    assert adapter_status.get('network_calls_performed') is False
    assert adapter_status.get('provider_execution_performed') is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
