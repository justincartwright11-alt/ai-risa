"""Evidence-only smoke tests for Button 1 approved-save preview dashboard wire (v1)."""

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


def test_button1_panel_references_approved_save_writer_preview_route(client):
    html = _html(client)
    assert "/api/local-ai/gate1/save-fights/approved-save-writer-preview" in html


def test_button1_panel_renders_writer_preview_checked(client):
    html = _html(client)
    body = _function_body(html, "renderButton1Gate1ApprovedSavePreview")
    assert "Writer preview checked" in body


def test_button1_panel_renders_would_write_count(client):
    html = _html(client)
    body = _function_body(html, "renderButton1Gate1ApprovedSavePreview")
    assert "Would write count" in body


def test_button1_panel_renders_audit_preview_ready(client):
    html = _html(client)
    body = _function_body(html, "renderButton1Gate1ApprovedSavePreview")
    assert "Audit preview ready" in body


def test_button1_panel_renders_rollback_preview_ready(client):
    html = _html(client)
    body = _function_body(html, "renderButton1Gate1ApprovedSavePreview")
    assert "Rollback preview ready" in body


def test_button1_panel_renders_blocking_reasons(client):
    html = _html(client)
    body = _function_body(html, "renderButton1Gate1ApprovedSavePreview")
    assert "Blocking reasons" in body


def test_button1_panel_renders_live_write_disabled(client):
    html = _html(client)
    body = _function_body(html, "renderButton1Gate1ApprovedSavePreview")
    assert "Live write disabled" in body


def test_no_save_now_button_present(client):
    html = _html(client).lower()
    assert "save now" not in html


def test_no_real_save_endpoint_referenced(client):
    html = _html(client)
    body = _function_body(html, "handleButton1Click")
    assert "/api/operator/button1/save-selected" not in body


def test_no_queue_database_write_endpoint_referenced(client):
    html = _html(client)
    body = _function_body(html, "handleButton1Click")
    lowered = body.lower()
    assert "queue_write" not in lowered
    assert "database_write" not in lowered


def test_live_write_enabled_false_present_in_button1_payload(client):
    html = _html(client)
    body = _function_body(html, "handleButton1Click")
    assert "live_write_enabled: false" in body


def test_normal_dashboard_remains_three_buttons_three_gates(client):
    html = _html(client)
    assert len(re.findall(r'class="btn-main"', html)) == 3
    assert len(re.findall(r'btn-gate', html)) == 3
