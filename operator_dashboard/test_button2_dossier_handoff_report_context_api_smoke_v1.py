"""Smoke proof: Button 2 report-context API remains preview-only, zero-write, and approval-gated."""

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
    assert data["gate2_bypass_performed"] is False


def test_route_exists_and_valid_ingest_returns_report_context_preview(monkeypatch):
    def _blocked_open(*args, **kwargs):
        raise AssertionError("filesystem access is not allowed in report-context preview route")

    def _blocked_connection(*args, **kwargs):
        raise AssertionError("live network access is not allowed in report-context preview route")

    monkeypatch.setattr("builtins.open", _blocked_open)
    monkeypatch.setattr(socket, "create_connection", _blocked_connection)

    app.config["TESTING"] = True

    payload = {
        "ingest_payload": {
            "button2_ingest_preview_context": {
                "destination_marker": "button2_report_generation_preview",
                "context_kind": "button1_dossier_handoff",
                "ingest_mode": "preview_only",
                "dossier_summary_preview": "Button1 Read-Only Dossier Handoff Preview\nFighter: Jon Jones",
                "internal_notes": "do not leak",
                "write_authorized": True,
                "database_pointer": "db://secret",
            }
        }
    }

    with app.test_client() as client:
        route_rules = {rule.rule for rule in app.url_map.iter_rules()}
        assert "/api/button2/dossier-handoff/report-context-preview" in route_rules

        response = client.post(
            "/api/button2/dossier-handoff/report-context-preview",
            data=json.dumps(payload),
            content_type="application/json",
        )

    assert response.status_code == 200
    data = response.get_json()

    assert data["ok"] is True
    assert data["destination_marker"] == "button2_report_generation_preview"
    _assert_preview_zero_write_flags(data)

    preview = data["report_context_preview"]
    assert preview["destination_marker"] == "button2_report_generation_preview"
    assert preview["report_context_kind"] == "dossier_handoff_report_context_preview"
    assert preview["source_context_kind"] == "button1_dossier_handoff"
    assert preview["source_ingest_mode"] == "preview_only"

    assert "internal_notes" not in preview
    assert "write_authorized" not in preview
    assert "database_pointer" not in preview


def test_invalid_or_malformed_payload_fails_closed(monkeypatch):
    def _blocked_open(*args, **kwargs):
        raise AssertionError("filesystem access is not allowed in report-context preview route")

    def _blocked_connection(*args, **kwargs):
        raise AssertionError("live network access is not allowed in report-context preview route")

    monkeypatch.setattr("builtins.open", _blocked_open)
    monkeypatch.setattr(socket, "create_connection", _blocked_connection)

    app.config["TESTING"] = True

    with app.test_client() as client:
        invalid_marker_response = client.post(
            "/api/button2/dossier-handoff/report-context-preview",
            data=json.dumps(
                {
                    "ingest_payload": {
                        "button2_ingest_preview_context": {
                            "destination_marker": "button2_generate_now",
                            "dossier_summary_preview": "invalid marker",
                        }
                    }
                }
            ),
            content_type="application/json",
        )

        malformed_response = client.post(
            "/api/button2/dossier-handoff/report-context-preview",
            data=json.dumps(["malformed"]),
            content_type="application/json",
        )

    assert invalid_marker_response.status_code == 400
    invalid_data = invalid_marker_response.get_json()
    assert invalid_data["ok"] is False
    assert invalid_data["error"] == "invalid_destination_marker"
    assert invalid_data["report_context_preview"] is None
    assert invalid_data["preview_only"] is True
    assert invalid_data["report_context_preview_ready"] is False
    _assert_preview_zero_write_flags(invalid_data)

    assert malformed_response.status_code == 400
    malformed_data = malformed_response.get_json()
    assert malformed_data["ok"] is False
    assert malformed_data["error"] == "invalid_request_body"
    assert malformed_data["report_context_preview"] is None
    assert malformed_data["preview_only"] is True
    assert malformed_data["report_context_preview_ready"] is False
    _assert_preview_zero_write_flags(malformed_data)


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
