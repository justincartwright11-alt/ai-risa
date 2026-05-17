"""Normal-dashboard wire tests for Gate 1 approved-save writer preview evidence (v1)."""

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


def test_template_contains_gate1_approved_save_writer_preview_endpoint(client):
    html = _html(client)
    assert "/api/local-ai/gate1/save-fights/approved-save-writer-preview" in html


def test_template_posts_gate1_approved_save_writer_preview(client):
    html = _html(client)
    post_body = _function_body(html, "postLocalAiGate1ApprovedSaveWriterPreview")
    assert "LOCAL_AI_GATE1_APPROVED_SAVE_WRITER_PREVIEW_ENDPOINT" in post_body
    assert "method: 'POST'" in post_body


def test_button1_handler_requests_gate1_approved_save_writer_preview_after_workflow_preview(client):
    html = _html(client)
    body = _function_body(html, "handleButton1Click")
    assert "requestLocalAiWorkflowPreviewWithRuntimeContext(SOURCE_BUTTON_FIND_FIGHTS)" in body
    assert "postLocalAiGate1ApprovedSaveWriterPreview" in body
    assert "gate_approval_token_preview" in body
    assert "operator_approved: true" in body
    assert "idempotency_key" in body
    assert "write_target: 'queue_preview'" in body
    assert "candidate_rows" in body


def test_button1_approved_save_render_exposes_only_requested_evidence_fields(client):
    html = _html(client)
    body = _function_body(html, "renderButton1Gate1ApprovedSavePreview")
    assert "Writer preview checked" in body
    assert "Would write count" in body
    assert "Audit preview ready" in body
    assert "Rollback preview ready" in body
    assert "Blocking reasons" in body
    assert "Live write disabled" in body


def test_button1_approved_save_render_does_not_include_save_actions(client):
    html = _html(client)
    body = _function_body(html, "renderButton1Gate1ApprovedSavePreview")
    lower = body.lower()
    assert "save-selected" not in lower
    assert "operator_approved" not in lower
    assert "write_authorized: true" not in lower
    assert "save now" not in lower


def test_dashboard_still_has_three_main_buttons_and_three_gates(client):
    html = _html(client)
    assert len(re.findall(r'class="btn-main"', html)) == 3
    assert len(re.findall(r'btn-gate', html)) == 3
