"""Smoke proof: Button 2 dossier handoff ingest API remains preview-only and approval-gated."""

import json
import socket

from operator_dashboard.app import app


def _assert_preview_zero_write_flags(data):
    assert data["preview_only"] is True
    assert data["button2_generation_performed"] is False
    assert data["pdf_generation_performed"] is False
    assert data["file_write_performed"] is False
    assert data["export_performed"] is False
    assert data["delivery_performed"] is False
    assert data["report_write_performed"] is False
    assert data["gate2_approval_required"] is True


def test_ingest_api_route_exists_and_valid_handoff_returns_preview(monkeypatch):
    def _blocked_open(*args, **kwargs):
        raise AssertionError("filesystem access is not allowed in ingest preview API")

    def _blocked_connection(*args, **kwargs):
        raise AssertionError("live network access is not allowed in ingest preview API")

    monkeypatch.setattr("builtins.open", _blocked_open)
    monkeypatch.setattr(socket, "create_connection", _blocked_connection)

    app.config["TESTING"] = True

    payload = {
        "handoff_payload": {
            "destination_marker": "button2_report_generation_preview",
            "dossier_summary_preview": "Button1 Read-Only Dossier Handoff Preview\nFighter: Jon Jones",
            "internal_notes": "do not leak",
            "write_authorized": True,
            "merge_instruction": "force",
            "database_pointer": "db://secret",
        }
    }

    with app.test_client() as client:
        route_rules = {rule.rule for rule in app.url_map.iter_rules()}
        assert "/api/button2/dossier-handoff/ingest-preview" in route_rules

        response = client.post(
            "/api/button2/dossier-handoff/ingest-preview",
            data=json.dumps(payload),
            content_type="application/json",
        )

    assert response.status_code == 200
    data = response.get_json()

    assert data["ok"] is True
    assert data["destination_marker"] == "button2_report_generation_preview"
    _assert_preview_zero_write_flags(data)

    context = data["button2_ingest_preview_context"]
    assert context["destination_marker"] == "button2_report_generation_preview"
    assert context["ingest_mode"] == "preview_only"
    assert context["context_kind"] == "button1_dossier_handoff"

    assert "internal_notes" not in context
    assert "write_authorized" not in context
    assert "merge_instruction" not in context
    assert "database_pointer" not in context


def test_ingest_api_invalid_destination_marker_fails_closed(monkeypatch):
    def _blocked_open(*args, **kwargs):
        raise AssertionError("filesystem access is not allowed in ingest preview API")

    def _blocked_connection(*args, **kwargs):
        raise AssertionError("live network access is not allowed in ingest preview API")

    monkeypatch.setattr("builtins.open", _blocked_open)
    monkeypatch.setattr(socket, "create_connection", _blocked_connection)

    app.config["TESTING"] = True

    payload = {
        "handoff_payload": {
            "destination_marker": "button2_generate_now",
            "dossier_summary_preview": "invalid marker",
        }
    }

    with app.test_client() as client:
        response = client.post(
            "/api/button2/dossier-handoff/ingest-preview",
            data=json.dumps(payload),
            content_type="application/json",
        )

    assert response.status_code == 400
    data = response.get_json()

    assert data["ok"] is False
    assert data["error"] == "invalid_destination_marker"
    assert data["button2_ingest_preview_context"] is None
    _assert_preview_zero_write_flags(data)


def test_button2_generation_endpoint_remains_approval_gated():
    app.config["TESTING"] = True

    with app.test_client() as client:
        response = client.post(
            "/api/operator/button2/generate-report",
            data=json.dumps({"operator_approved": False}),
            content_type="application/json",
        )

    assert response.status_code == 403
    data = response.get_json()
    assert data["ok"] is False
    assert data["error"] == "operator_approval_required"
