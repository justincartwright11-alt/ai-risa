import json

from operator_dashboard.app import app


def test_button1_to_button2_dossier_handoff_api_preview_success():
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
            "merge_instruction": "force",
        }
    }

    with app.test_client() as client:
        response = client.post(
            "/api/button1-to-button2/dossier-handoff-preview",
            data=json.dumps(payload),
            content_type="application/json",
        )

    assert response.status_code == 200
    data = response.get_json()

    assert data["ok"] is True
    assert data["destination_marker"] == "button2_report_generation_preview"
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

    summary = data["dossier_summary_preview"]
    assert "Button1 Read-Only Dossier Handoff Preview" in summary
    assert "internal_notes" not in summary
    assert "do not leak" not in summary
    assert "write_authorized" not in summary
    assert "merge_instruction" not in summary

    assert "internal_notes" not in data
    assert "write_authorized" not in data
    assert "merge_instruction" not in data


def test_button1_to_button2_dossier_handoff_api_preview_rejects_invalid_body():
    app.config["TESTING"] = True

    with app.test_client() as client:
        response = client.post(
            "/api/button1-to-button2/dossier-handoff-preview",
            data=json.dumps(["not", "an", "object"]),
            content_type="application/json",
        )

    assert response.status_code == 400
    data = response.get_json()

    assert data["ok"] is False
    assert data["error"] == "invalid_request_body"
    assert data["destination_marker"] == "button2_report_generation_preview"
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
