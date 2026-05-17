"""Smoke proof: Button1->Button2 dossier handoff API remains preview-only and zero-write."""

import json
import socket

from operator_dashboard.app import app


def _assert_zero_write_flags(data):
    assert data["preview_only"] is True
    assert data["button1_export_performed"] is False
    assert data["button2_generation_performed"] is False
    assert data["pdf_generation_performed"] is False
    assert data["file_write_performed"] is False
    assert data["delivery_performed"] is False
    assert data["report_write_performed"] is False
    assert data["profile_create_update_merge"] is False
    assert data["database_ranking_writes"] is False
    assert data["result_report_learning_calibration"] is False


def test_route_exists_and_returns_sanitized_preview_payload(monkeypatch):
    # Smoke guard: route must not use filesystem writes.
    def _blocked_open(*args, **kwargs):
        raise AssertionError("filesystem access is not allowed in preview route")

    # Smoke guard: route must not perform live network calls.
    def _blocked_connection(*args, **kwargs):
        raise AssertionError("live network access is not allowed in preview route")

    monkeypatch.setattr("builtins.open", _blocked_open)
    monkeypatch.setattr(socket, "create_connection", _blocked_connection)

    app.config["TESTING"] = True
    payload = {
        "dossier_data": {
            "fighter_name": "Jon Jones",
            "promotion": "UFC",
            "division": "Light Heavyweight",
            "record": "27W-1L-0D",
            "confidence": "A+",
            "source": "approved_historical",
            "internal_notes": "do not leak",
            "write_authorized": True,
            "database_pointer": "db://secret",
            "merge_instruction": "force",
        }
    }

    with app.test_client() as client:
        route_rules = {rule.rule for rule in app.url_map.iter_rules()}
        assert "/api/button1-to-button2/dossier-handoff-preview" in route_rules

        response = client.post(
            "/api/button1-to-button2/dossier-handoff-preview",
            data=json.dumps(payload),
            content_type="application/json",
        )

    assert response.status_code == 200
    data = response.get_json()

    assert data["ok"] is True
    assert data["destination_marker"] == "button2_report_generation_preview"
    _assert_zero_write_flags(data)

    summary = data["dossier_summary_preview"]
    assert "Button1 Read-Only Dossier Handoff Preview" in summary
    assert "internal_notes" not in summary
    assert "do not leak" not in summary
    assert "write_authorized" not in summary
    assert "database_pointer" not in summary
    assert "merge_instruction" not in summary

    assert "internal_notes" not in data
    assert "write_authorized" not in data
    assert "database_pointer" not in data
    assert "merge_instruction" not in data


def test_malformed_payload_fails_safe_without_generation_or_writes(monkeypatch):
    # Smoke guard: route must not use filesystem writes.
    def _blocked_open(*args, **kwargs):
        raise AssertionError("filesystem access is not allowed in preview route")

    # Smoke guard: route must not perform live network calls.
    def _blocked_connection(*args, **kwargs):
        raise AssertionError("live network access is not allowed in preview route")

    monkeypatch.setattr("builtins.open", _blocked_open)
    monkeypatch.setattr(socket, "create_connection", _blocked_connection)

    app.config["TESTING"] = True

    with app.test_client() as client:
        response = client.post(
            "/api/button1-to-button2/dossier-handoff-preview",
            data=json.dumps(["malformed"]),
            content_type="application/json",
        )

    assert response.status_code == 400
    data = response.get_json()

    assert data["ok"] is False
    assert data["error"] == "invalid_request_body"
    assert data["destination_marker"] == "button2_report_generation_preview"
    _assert_zero_write_flags(data)
