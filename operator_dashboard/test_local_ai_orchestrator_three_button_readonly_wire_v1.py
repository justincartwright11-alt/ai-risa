"""Tests for normal-dashboard read-only wire to local AI workflow preview route (v1)."""

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


def test_normal_dashboard_still_has_exactly_3_main_buttons(client):
    html = _html(client)
    buttons = re.findall(r'class="btn-main"', html)
    assert len(buttons) == 3


def test_find_fights_button_references_button1_source_button(client):
    html = _html(client)
    assert "button1_find_fights" in html


def test_generate_pdfs_button_references_button2_source_button(client):
    html = _html(client)
    assert "button2_generate_pdfs" in html


def test_find_results_button_references_button3_source_button(client):
    html = _html(client)
    assert "button3_find_results" in html


def test_template_calls_local_ai_workflow_preview_route(client):
    html = _html(client)
    assert "/api/local-ai/orchestrator/workflow-preview" in html


def test_execute_preview_true_is_used(client):
    html = _html(client)
    assert "execute_preview: true" in html


def test_ui_does_not_add_new_main_buttons(client):
    html = _html(client)
    buttons = re.findall(r'class="btn-main"', html)
    assert len(buttons) == 3


def test_ui_does_not_add_new_approval_gates(client):
    html = _html(client)
    gates = re.findall(r'btn-gate', html)
    assert len(gates) == 3


def test_ui_does_not_expose_telemetry_flags_in_normal_mode(client):
    html = _html(client)
    assert "mutation_performed" not in html
    assert "durable_write_performed" not in html
    assert "learning_apply_performed" not in html
    assert "calibration_write_performed" not in html
    assert "auto_apply_performed" not in html


def test_ui_does_not_expose_raw_job_internals_in_normal_mode(client):
    html = _html(client)
    assert "workflow_id" not in html
    assert "job_id" not in html
    assert "source_urls" not in html
    assert "trace" not in html


def test_ui_does_not_expose_learning_calibration_controls(client):
    html = _html(client).lower()
    assert "apply learning" not in html
    assert "calibration preview" not in html
    assert 'onclick="handleLearning' not in html
