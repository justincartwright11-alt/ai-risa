"""Normal-dashboard wire tests for Gate 1 dry-run save preview evidence (v1)."""

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


def test_template_contains_gate1_dry_run_preview_endpoint(client):
    html = _html(client)
    assert "/api/local-ai/gate1/save-fights/dry-run-apply-preview" in html


def test_template_posts_gate1_dry_run_preview(client):
    html = _html(client)
    post_body = _function_body(html, "postLocalAiGate1DryRunApplyPreview")
    assert "LOCAL_AI_GATE1_DRY_RUN_APPLY_PREVIEW_ENDPOINT" in post_body
    assert "method: 'POST'" in post_body


def test_button1_handler_requests_gate1_dry_run_after_workflow_preview(client):
    html = _html(client)
    body = _function_body(html, "handleButton1Click")
    assert "requestLocalAiWorkflowPreviewWithRuntimeContext(SOURCE_BUTTON_FIND_FIGHTS)" in body
    assert "postLocalAiGate1DryRunApplyPreview" in body
    assert "gate_approval_token_preview" in body
    assert "candidate_rows" in body


def test_button1_dry_run_render_exposes_only_requested_evidence_fields(client):
    html = _html(client)
    body = _function_body(html, "renderButton1Gate1DryRunPreview")
    assert "Would save count" in body
    assert "Blocked count" in body
    assert "Blocking reasons" in body
    assert "Eligible for future approval" in body
    assert "Gate 1 token check status" in body


def test_button1_dry_run_render_does_not_include_save_actions(client):
    html = _html(client)
    body = _function_body(html, "renderButton1Gate1DryRunPreview")
    lower = body.lower()
    assert "save-selected" not in lower
    assert "operator_approved" not in lower
    assert "write_authorized: true" not in lower


def test_dashboard_still_has_three_main_buttons_and_three_gates(client):
    html = _html(client)
    assert len(re.findall(r'class="btn-main"', html)) == 3
    assert len(re.findall(r'btn-gate', html)) == 3
