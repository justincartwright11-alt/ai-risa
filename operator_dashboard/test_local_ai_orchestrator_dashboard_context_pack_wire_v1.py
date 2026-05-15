"""Tests for normal-dashboard context-pack wire into workflow preview route (v1)."""

import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from operator_dashboard.app import app as flask_app


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def _html(client):
    resp = client.get("/")
    assert resp.status_code == 200
    return resp.data.decode("utf-8")


def _function_body(html: str, function_name: str) -> str:
    pattern = rf"function\s+{re.escape(function_name)}\s*\([^)]*\)\s*\{{([\s\S]*?)\n\}}"
    match = re.search(pattern, html)
    assert match is not None
    return match.group(1)


def test_template_calls_local_ai_workflow_preview_route(client):
    html = _html(client)
    assert "/api/local-ai/orchestrator/workflow-preview" in html


def test_find_fights_button_sends_context_pack_for_button1(client):
    html = _html(client)
    assert "requestLocalAiWorkflowPreviewWithFallback(SOURCE_BUTTON_FIND_FIGHTS, buildButton1ContextPack())" in html
    assert "manual_text" in _function_body(html, "buildButton1ContextPack")
    assert "approved_source_refs" in _function_body(html, "buildButton1ContextPack")
    assert "candidate_rows" in _function_body(html, "buildButton1ContextPack")


def test_generate_pdfs_button_sends_context_pack_for_button2(client):
    html = _html(client)
    assert "requestLocalAiWorkflowPreviewWithFallback(SOURCE_BUTTON_GENERATE_PDFS, buildButton2ContextPack())" in html
    body = _function_body(html, "buildButton2ContextPack")
    assert "selected_fights" in body
    assert "queued_fight_refs" in body
    assert "customer_ready_refs" in body


def test_find_results_button_sends_context_pack_for_button3(client):
    html = _html(client)
    assert "requestLocalAiWorkflowPreviewWithFallback(SOURCE_BUTTON_FIND_RESULTS, buildButton3ContextPack())" in html
    body = _function_body(html, "buildButton3ContextPack")
    assert "waiting_rows" in body
    assert "selected_keys" in body
    assert "comparison_refs" in body


def test_execute_preview_true_remains_present(client):
    html = _html(client)
    assert "execute_preview: true" in html


def test_legacy_input_ref_fallback_remains_present(client):
    html = _html(client)
    body = _function_body(html, "requestLocalAiWorkflowPreviewWithFallback")
    assert "input_ref" in body
    assert "kind: 'empty'" in body


def test_template_does_not_add_new_main_buttons(client):
    html = _html(client)
    buttons = re.findall(r'class="btn-main"', html)
    assert len(buttons) == 3


def test_template_does_not_add_new_gates(client):
    html = _html(client)
    gates = re.findall(r'btn-gate', html)
    assert len(gates) == 3


def test_template_does_not_expose_raw_context_pack_in_normal_mode_rendering(client):
    html = _html(client)
    render_body = _function_body(html, "renderSimpleWorkflowSummary")
    assert "context_pack" not in render_body


def test_template_does_not_expose_telemetry_internals_in_normal_mode_rendering(client):
    html = _html(client)
    render_body = _function_body(html, "renderSimpleWorkflowSummary")
    assert "mutation_performed" not in render_body
    assert "durable_write_performed" not in render_body
    assert "learning_apply_performed" not in render_body
    assert "calibration_write_performed" not in render_body
    assert "auto_apply_performed" not in render_body


def test_template_does_not_expose_advanced_diagnostics(client):
    html = _html(client)
    lower = html.lower()
    assert "include_advanced_diagnostics" not in lower
    assert "row_details" not in lower
    assert "row-details" not in lower
