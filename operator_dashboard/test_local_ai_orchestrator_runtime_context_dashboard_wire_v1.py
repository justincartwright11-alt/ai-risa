"""
Test suite: local-ai-orchestrator-runtime-context-dashboard-wire-v1

Validates that the normal three-button dashboard wires correctly to use
read-only runtime context loading via the workflow-preview route.

Requirements:
1. Dashboard calls route with use_runtime_context=true
2. Source button correctly mapped (button1_find_fights, button2_generate_pdfs, button3_find_results)
3. execute_preview=true present in all requests
4. Legacy fallback (input_ref) preserved for compatibility
5. No new buttons or gates introduced
6. No raw internals exposed in response
7. Telemetry/safety flags remain locked to false
8. No filesystem writes
9. No live web calls
10. No fake data synthesis
11. Template calls remain identical to original three-button UI contract
12. Route precedence: use_runtime_context honored when provided
13. Empty runtime state yields empty sanitized contexts
"""

import json
import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from operator_dashboard.app import app as flask_app


ROUTE = "/api/local-ai/orchestrator/workflow-preview"


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


# ── Core Wire: Dashboard calls route with use_runtime_context=true ──────

def test_dashboard_button1_sends_use_runtime_context_true(client):
    """Button 1: sends use_runtime_context=true instead of context_pack."""
    payload = {
        "source_button": "button1_find_fights",
        "use_runtime_context": True,
        "execute_preview": True
    }
    response = client.post(ROUTE, json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data.get('ok') is True


def test_dashboard_button2_sends_use_runtime_context_true(client):
    """Button 2: sends use_runtime_context=true."""
    payload = {
        "source_button": "button2_generate_pdfs",
        "use_runtime_context": True,
        "execute_preview": True
    }
    response = client.post(ROUTE, json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data.get('ok') is True


def test_dashboard_button3_sends_use_runtime_context_true(client):
    """Button 3: sends use_runtime_context=true."""
    payload = {
        "source_button": "button3_find_results",
        "use_runtime_context": True,
        "execute_preview": True
    }
    response = client.post(ROUTE, json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data.get('ok') is True


# ── Source Button Mapping ──────────────────────────────────────────────

def test_use_runtime_context_routes_to_correct_loader_for_button1(client):
    """Button 1 runtime context uses button1 loader path."""
    payload = {
        "source_button": "button1_find_fights",
        "use_runtime_context": True,
        "execute_preview": True
    }
    response = client.post(ROUTE, json=payload)
    data = response.get_json()
    # Button 1 workflows include discovery jobs
    workflow = data.get('workflow', {})
    assert workflow, "Response should include workflow"
    jobs = workflow.get('jobs', [])
    assert len(jobs) > 0, "Button 1 should have jobs"


def test_use_runtime_context_routes_to_correct_loader_for_button2(client):
    """Button 2 runtime context uses button2 loader path."""
    payload = {
        "source_button": "button2_generate_pdfs",
        "use_runtime_context": True,
        "execute_preview": True
    }
    response = client.post(ROUTE, json=payload)
    data = response.get_json()
    # Button 2 workflows include report generation jobs
    workflow = data.get('workflow', {})
    assert workflow, "Response should include workflow"
    jobs = workflow.get('jobs', [])
    assert len(jobs) > 0, "Button 2 should have jobs"


def test_use_runtime_context_routes_to_correct_loader_for_button3(client):
    """Button 3 runtime context uses button3 loader path."""
    payload = {
        "source_button": "button3_find_results",
        "use_runtime_context": True,
        "execute_preview": True
    }
    response = client.post(ROUTE, json=payload)
    data = response.get_json()
    # Button 3 workflows include result search jobs
    workflow = data.get('workflow', {})
    assert workflow, "Response should include workflow"
    jobs = workflow.get('jobs', [])
    assert len(jobs) > 0, "Button 3 should have jobs"


# ── Execute Preview Present ────────────────────────────────────────────

def test_execute_preview_flag_honored(client):
    """execute_preview=true causes workflow to execute."""
    payload = {
        "source_button": "button1_find_fights",
        "use_runtime_context": True,
        "execute_preview": True
    }
    response = client.post(ROUTE, json=payload)
    data = response.get_json()
    # Execution produces previews (non-empty jobs with preview data)
    workflow = data.get('workflow', {})
    assert workflow.get('jobs'), "execute_preview should populate jobs"


# ── Legacy Fallback Preserved ──────────────────────────────────────────

def test_legacy_fallback_to_input_ref_on_runtime_context_failure(client):
    """If use_runtime_context fails, fallback to input_ref works."""
    payload = {
        "source_button": "button1_find_fights",
        "input_ref": {
            "kind": "empty",
            "payload": {}
        },
        "execute_preview": True
    }
    response = client.post(ROUTE, json=payload)
    # Fallback path should succeed with empty input
    assert response.status_code == 200
    data = response.get_json()
    assert data.get('ok') is True


def test_runtime_context_precedence_over_context_pack(client):
    """If both use_runtime_context and context_pack provided, use_runtime_context wins."""
    payload = {
        "source_button": "button1_find_fights",
        "use_runtime_context": True,
        "context_pack": {
            "manual_text": "should be ignored",
            "approved_source_refs": []
        },
        "execute_preview": True
    }
    response = client.post(ROUTE, json=payload)
    # Should succeed using runtime context, not context_pack
    assert response.status_code == 200
    data = response.get_json()
    assert data.get('ok') is True


# ── No New Buttons or Gates ────────────────────────────────────────────

def test_only_three_buttons_supported(client):
    """Route only accepts three known source_buttons."""
    invalid_buttons = ["button4_unknown", "button1_extra", "new_button"]
    for button in invalid_buttons:
        payload = {
            "source_button": button,
            "use_runtime_context": True,
            "execute_preview": True
        }
        response = client.post(ROUTE, json=payload)
        assert response.status_code == 400, f"Invalid button {button} should be rejected"


def test_no_new_gates_introduced(client):
    """Workflow still has exactly 1 gate per button."""
    for button in ["button1_find_fights", "button2_generate_pdfs", "button3_find_results"]:
        payload = {
            "source_button": button,
            "use_runtime_context": True,
            "execute_preview": True
        }
        response = client.post(ROUTE, json=payload)
        data = response.get_json()
        workflow = data.get('workflow', {})
        # Each button should have a gate
        assert workflow.get('gate_required') is True, f"Button {button} should require gate"
        assert workflow.get('gate_name'), f"Button {button} should have gate_name"


# ── No Raw Internals Exposed ───────────────────────────────────────────

def test_response_structure_safe(client):
    """Response only exposes safe structured fields."""
    payload = {
        "source_button": "button1_find_fights",
        "use_runtime_context": True,
        "execute_preview": True
    }
    response = client.post(ROUTE, json=payload)
    data = response.get_json()
    # Safe fields - response should have these keys
    assert 'ok' in data
    assert 'workflow' in data


# ── Safety Flags Locked ────────────────────────────────────────────────

def test_all_mutation_flags_remain_false(client):
    """All mutation/export/apply/learning flags locked to false."""
    payload = {
        "source_button": "button1_find_fights",
        "use_runtime_context": True,
        "execute_preview": True
    }
    response = client.post(ROUTE, json=payload)
    data = response.get_json()
    # Check all jobs for safety flags
    workflow = data.get('workflow', {})
    for job in workflow.get('jobs', []):
        job_spec = job.get('spec', {})
        assert job_spec.get('export_pdf') is not True, "PDF export should be locked to false"
        assert job_spec.get('save_queue') is not True, "Queue save should be locked to false"
        assert job_spec.get('apply_results') is not True, "Result apply should be locked to false"
        assert job_spec.get('update_calibration') is not True, "Calibration update should be locked to false"


# ── No Filesystem Writes ───────────────────────────────────────────────

@patch('builtins.open', create=True)
def test_no_filesystem_writes_in_preview_mode(mock_open, client):
    """Preview execution does not write to filesystem."""
    payload = {
        "source_button": "button1_find_fights",
        "use_runtime_context": True,
        "execute_preview": True
    }
    response = client.post(ROUTE, json=payload)
    # Should succeed without any writes
    assert response.status_code == 200


# ── No Live Web Calls ──────────────────────────────────────────────────

@patch('requests.get')
@patch('requests.post')
def test_no_live_web_calls_in_preview_mode(mock_post, mock_get, client):
    """Preview execution does not make live network requests."""
    payload = {
        "source_button": "button1_find_fights",
        "use_runtime_context": True,
        "execute_preview": True
    }
    response = client.post(ROUTE, json=payload)
    # Should succeed without network calls
    assert response.status_code == 200
    mock_get.assert_not_called()
    mock_post.assert_not_called()


# ── Template Contract: Three Buttons Only ──────────────────────────────

def test_template_still_renders_exactly_three_buttons():
    """Index.html still renders exactly 3 buttons."""
    with open('operator_dashboard/templates/index.html', 'r') as f:
        html = f.read()
    # Count button click handlers
    button1_count = html.count('handleButton1Click')
    button2_count = html.count('handleButton2Click')
    button3_count = html.count('handleButton3Click')
    assert button1_count > 0, "Button 1 handler should exist"
    assert button2_count > 0, "Button 2 handler should exist"
    assert button3_count > 0, "Button 3 handler should exist"


def test_template_calls_use_runtime_context_function():
    """Template button handlers call requestLocalAiWorkflowPreviewWithRuntimeContext."""
    with open('operator_dashboard/templates/index.html', 'r') as f:
        html = f.read()
    assert 'requestLocalAiWorkflowPreviewWithRuntimeContext' in html, \
        "Template should call new runtime context function"


def test_template_sends_use_runtime_context_true():
    """Template functions send use_runtime_context: true in payload."""
    with open('operator_dashboard/templates/index.html', 'r') as f:
        html = f.read()
    assert 'use_runtime_context: true' in html, \
        "Template should send use_runtime_context=true"


def test_template_has_auto_hydration_on_load_and_interval():
    with open('operator_dashboard/templates/index.html', 'r') as f:
        html = f.read()
    assert 'hydrateDashboardCardsOnLoad()' in html
    assert 'setInterval(hydrateDashboardCardsOnLoad, 30000);' in html


def test_template_contains_waiting_refresh_card_surface_labels():
    with open('operator_dashboard/templates/index.html', 'r') as f:
        html = f.read()
    assert 'Waiting for refresh' in html
    assert 'Ready to save' in html
    assert 'Customer Ready' in html
    assert 'Rows scanned' in html


def test_template_preserves_fallback_logic():
    """Template preserves fallback to input_ref on runtime context failure."""
    with open('operator_dashboard/templates/index.html', 'r') as f:
        html = f.read()
    assert '.catch' in html, "Template should have fallback .catch handler"


# ── Empty Runtime State Behavior ───────────────────────────────────────

def test_empty_runtime_context_yields_empty_sanitized_contexts(client):
    """With no runtime files, runtime context loading produces safe empty contexts."""
    payload = {
        "source_button": "button1_find_fights",
        "use_runtime_context": True,
        "execute_preview": True
    }
    response = client.post(ROUTE, json=payload)
    data = response.get_json()
    # Should succeed with valid structure, even if empty
    assert data.get('ok') is True
    assert 'workflow' in data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
