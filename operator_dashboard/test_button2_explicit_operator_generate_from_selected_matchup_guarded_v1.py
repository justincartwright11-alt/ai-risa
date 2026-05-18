import json

import operator_dashboard.app as app_module
from operator_dashboard.app import app


ROUTE = "/api/button2/selected-matchup/generate-guarded-v1"


def _selected_matchup_preview():
    return {
        "selected_for_button2": True,
        "selection_preview": True,
        "fighter_a": "Rodtang Jitmuangnon",
        "fighter_b": "Takeru Segawa",
        "event_name": "ONE SAMURAI 1",
        "source_url": "https://www.onefc.com/events/",
        "report_ready_status": "ready_for_button2_preview",
    }


def _assert_guard_false_flags(data):
    assert data["queue_write_performed"] is False
    assert data["delivery_performed"] is False
    assert data["external_api_delivery_performed"] is False
    assert data["learning_apply_performed"] is False
    assert data["calibration_write_performed"] is False
    assert data["button3_mutation_performed"] is False


def test_guarded_route_rejects_invalid_body_shape():
    app.config["TESTING"] = True
    with app.test_client() as client:
        response = client.post(
            ROUTE,
            data=json.dumps(["not", "an", "object"]),
            content_type="application/json",
        )

    assert response.status_code == 400
    data = response.get_json()
    assert data["ok"] is False
    assert data["error"] == "invalid_request_body"
    _assert_guard_false_flags(data)


def test_guarded_route_requires_operator_approval():
    app.config["TESTING"] = True
    payload = {
        "operator_approved": False,
        "selected_matchup_preview": _selected_matchup_preview(),
    }

    with app.test_client() as client:
        response = client.post(
            ROUTE,
            data=json.dumps(payload),
            content_type="application/json",
        )

    assert response.status_code == 403
    data = response.get_json()
    assert data["ok"] is False
    assert data["error"] == "operator_approval_required"
    _assert_guard_false_flags(data)


def test_guarded_route_requires_selected_matchup_preview_object():
    app.config["TESTING"] = True
    payload = {
        "operator_approved": True,
        "selected_matchup_preview": None,
    }

    with app.test_client() as client:
        response = client.post(
            ROUTE,
            data=json.dumps(payload),
            content_type="application/json",
        )

    assert response.status_code == 400
    data = response.get_json()
    assert data["ok"] is False
    assert data["error"] == "selected_matchup_required"
    _assert_guard_false_flags(data)


def test_guarded_route_requires_selected_for_button2_true():
    app.config["TESTING"] = True
    bad_preview = _selected_matchup_preview()
    bad_preview["selected_for_button2"] = False

    payload = {
        "operator_approved": True,
        "selected_matchup_preview": bad_preview,
    }

    with app.test_client() as client:
        response = client.post(
            ROUTE,
            data=json.dumps(payload),
            content_type="application/json",
        )

    assert response.status_code == 400
    data = response.get_json()
    assert data["ok"] is False
    assert data["error"] == "selected_matchup_not_ready"
    _assert_guard_false_flags(data)


def test_guarded_route_requires_source_backed_selected_matchup():
    app.config["TESTING"] = True
    bad_preview = _selected_matchup_preview()
    bad_preview["source_url"] = ""

    payload = {
        "operator_approved": True,
        "selected_matchup_preview": bad_preview,
    }

    with app.test_client() as client:
        response = client.post(
            ROUTE,
            data=json.dumps(payload),
            content_type="application/json",
        )

    assert response.status_code == 400
    data = response.get_json()
    assert data["ok"] is False
    assert data["error"] == "source_backed_matchup_required"
    _assert_guard_false_flags(data)


def test_guarded_route_delegates_generation_with_derived_fight_id(monkeypatch):
    app.config["TESTING"] = True

    captured = {}

    def _fake_generate(payload):
        captured["payload"] = payload
        return {
            "ok": True,
            "message": "PDF generated and saved successfully.",
            "output_path": "C:/tmp/fight_report.pdf",
            "pdf_generation_performed": True,
            "file_write_performed": True,
            "export_performed": False,
            "delivery_performed": False,
            "report_write_performed": False,
            "result_report_learning_calibration": False,
        }

    monkeypatch.setattr(app_module, "generate_button2_report_render_gate_integration", _fake_generate)

    payload = {
        "operator_approved": True,
        "selected_matchup_preview": _selected_matchup_preview(),
    }

    with app.test_client() as client:
        response = client.post(
            ROUTE,
            data=json.dumps(payload),
            content_type="application/json",
        )

    assert response.status_code == 200
    data = response.get_json()
    assert data["ok"] is True
    assert data["selected_matchup_generate_request_accepted"] is True
    assert data["delivery_performed"] is False
    assert data["external_api_delivery_performed"] is False
    assert data["queue_write_performed"] is False
    assert data["learning_apply_performed"] is False
    assert data["calibration_write_performed"] is False
    assert data["button3_mutation_performed"] is False

    delegated = captured["payload"]
    assert delegated["operator_approved"] is True
    assert "fight_id" in delegated and delegated["fight_id"]
    assert delegated["fight_id"].startswith("rodtang_jitmuangnon_vs_takeru_segawa")
    ingest_payload = delegated["ingest_payload"]
    assert ingest_payload["destination_marker"] == "button2_report_generation_preview"
    assert "Rodtang Jitmuangnon" in ingest_payload["dossier_summary_preview"]


def test_dashboard_wires_button2_guarded_generate_endpoint():
    app.config["TESTING"] = True
    with app.test_client() as client:
        html = client.get("/").data.decode("utf-8")

    assert "/api/button2/selected-matchup/generate-guarded-v1" in html
    assert "postButton2SelectedMatchupGenerateGuarded" in html
    assert "Running explicit operator-approved guarded generation" in html
    assert "Explicit operator action requires a selected matchup" in html
