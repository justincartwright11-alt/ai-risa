import json

import operator_dashboard.app as app_module
from operator_dashboard.app import app


ROUTE = "/api/button2/selected-matchup/generate-guarded-v1"
OPEN_ROUTE = "/api/button2/generated-report/open"


def _selected_matchup_preview():
    return {
        "selected_for_button2": True,
        "selection_preview": True,
        "fighter_a": "Anthony Joshua",
        "fighter_b": "Daniel Dubois",
        "event_name": "Joshua vs Dubois",
        "event_date": "2026-09-21",
        "promotion": "Matchroom",
        "source_type": "official",
        "source_url": "https://www.matchroomboxing.com/events/joshua-vs-dubois",
        "report_ready_status": "ready_for_button2_preview",
    }


def test_successful_generation_response_includes_open_link_fields(monkeypatch):
    app.config["TESTING"] = True

    def _fake_generate(_payload):
        return {
            "ok": True,
            "message": "PDF generated and saved successfully.",
            "output_path": "C:/tmp/anthony_joshua_vs_daniel_dubois_joshua_vs_dubois_premium.pdf",
            "delivery_performed": False,
            "external_api_delivery_performed": False,
            "queue_write_performed": False,
            "learning_apply_performed": False,
            "calibration_write_performed": False,
            "button3_mutation_performed": False,
        }

    monkeypatch.setattr(app_module, "generate_button2_report_render_gate_integration", _fake_generate)

    payload = {
        "operator_approved": True,
        "selected_matchup_preview": _selected_matchup_preview(),
    }

    with app.test_client() as client:
        response = client.post(ROUTE, data=json.dumps(payload), content_type="application/json")

    assert response.status_code == 200
    data = response.get_json()
    assert data["ok"] is True
    assert data["output_filename"] == "anthony_joshua_vs_daniel_dubois_joshua_vs_dubois_premium.pdf"
    assert data["pdf_open_url"] == (
        "/api/button2/generated-report/open?filename="
        "anthony_joshua_vs_daniel_dubois_joshua_vs_dubois_premium.pdf"
    )


def test_dashboard_renderer_has_clickable_open_link_and_fallback_condition():
    app.config["TESTING"] = True
    with app.test_client() as client:
        html = client.get("/").data.decode("utf-8")

    assert "Open Generated PDF" in html
    assert "const openUrl = String(data.pdf_open_url || '').trim();" in html
    assert "const outputFilename = String(data.output_filename || '').trim();" in html
    assert "const openLink = openUrl" in html
    assert "<a href=\"' + escapeHtml(openUrl) + '\" target=\"_blank\" rel=\"noopener noreferrer\">Open Generated PDF</a><br>" in html


def test_link_only_rendered_in_success_branch_not_failure_text():
    app.config["TESTING"] = True
    with app.test_client() as client:
        html = client.get("/").data.decode("utf-8")

    assert "if (ok)" in html
    assert "Guarded generation failed. No delivery was performed." in html


def test_safe_open_route_serves_existing_pdf(monkeypatch, tmp_path):
    app.config["TESTING"] = True
    monkeypatch.setenv("BUTTON2_PDF_OUTPUT_ROOT", str(tmp_path))

    filename = "anthony_joshua_vs_daniel_dubois_joshua_vs_dubois_premium.pdf"
    pdf_path = tmp_path / filename
    payload = b"%PDF-1.4\n%link-repair\n"
    pdf_path.write_bytes(payload)

    with app.test_client() as client:
        response = client.get(f"{OPEN_ROUTE}?filename={filename}")

    assert response.status_code == 200
    assert response.data == payload


def test_safe_open_route_rejects_path_traversal_and_non_pdf(monkeypatch, tmp_path):
    app.config["TESTING"] = True
    monkeypatch.setenv("BUTTON2_PDF_OUTPUT_ROOT", str(tmp_path))

    with app.test_client() as client:
        traversal = client.get(f"{OPEN_ROUTE}?filename=..%2Fsecret.pdf")
        non_pdf = client.get(f"{OPEN_ROUTE}?filename=report.txt")

    assert traversal.status_code == 400
    assert traversal.get_json()["error"] == "invalid_filename"
    assert non_pdf.status_code == 400
    assert non_pdf.get_json()["error"] == "invalid_filename"


def test_success_response_preserves_governance_flags(monkeypatch):
    app.config["TESTING"] = True

    def _fake_generate(_payload):
        return {
            "ok": True,
            "message": "PDF generated and saved successfully.",
            "output_path": "C:/tmp/a_vs_b_event_premium.pdf",
            "delivery_performed": False,
            "external_api_delivery_performed": False,
            "queue_write_performed": False,
            "learning_apply_performed": False,
            "calibration_write_performed": False,
            "button3_mutation_performed": False,
        }

    monkeypatch.setattr(app_module, "generate_button2_report_render_gate_integration", _fake_generate)

    payload = {
        "operator_approved": True,
        "selected_matchup_preview": _selected_matchup_preview(),
    }

    with app.test_client() as client:
        response = client.post(ROUTE, data=json.dumps(payload), content_type="application/json")

    data = response.get_json()
    assert data["delivery_performed"] is False
    assert data["external_api_delivery_performed"] is False
    assert data["queue_write_performed"] is False
    assert data["learning_apply_performed"] is False
    assert data["calibration_write_performed"] is False
    assert data["button3_mutation_performed"] is False
