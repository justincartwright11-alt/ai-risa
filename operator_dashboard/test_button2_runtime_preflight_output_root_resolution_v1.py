from operator_dashboard.app import app


PANEL_TITLE = "Runtime Preflight Status (Display-Only)"


def test_runtime_preflight_resolves_output_root_from_reports_when_env_missing(monkeypatch):
    monkeypatch.delenv("BUTTON2_PDF_OUTPUT_ROOT", raising=False)
    app.config["TESTING"] = True

    with app.test_client() as client:
        html = client.get("/", base_url="http://127.0.0.1:5050").data.decode("utf-8")

    assert PANEL_TITLE in html
    assert "BUTTON2_PDF_OUTPUT_ROOT" in html
    assert "Status: READY" in html
    assert "Value: " in html
    assert "\\reports" in html


def test_button2_pdf_library_route_uses_resolved_output_root_when_env_missing(monkeypatch):
    monkeypatch.delenv("BUTTON2_PDF_OUTPUT_ROOT", raising=False)
    app.config["TESTING"] = True

    with app.test_client() as client:
        response = client.get("/api/button2/generated-report/library")

    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "reports" in html.lower()
