from operator_dashboard.app import app


PANEL_TITLE = "Runtime Preflight Status (Display-Only)"


def test_runtime_preflight_panel_is_rendered_with_required_signals(monkeypatch):
    monkeypatch.setenv(
        "BUTTON2_PDF_OUTPUT_ROOT",
        "C:/Users/jusin/OneDrive/Documents/Custom Office Templates/reports",
    )
    app.config["TESTING"] = True

    with app.test_client() as client:
        html = client.get("/", base_url="http://127.0.0.1:5050").data.decode("utf-8")

    assert PANEL_TITLE in html
    assert "BUTTON2_PDF_OUTPUT_ROOT" in html
    assert "MSYS2 / GTK DLL path" in html
    assert "WeasyPrint render readiness" in html
    assert "reports output directory" in html
    assert "safe PDF open route availability" in html
    assert "current server port" in html


def test_runtime_preflight_panel_includes_safe_pdf_open_route_and_port(monkeypatch):
    monkeypatch.setenv(
        "BUTTON2_PDF_OUTPUT_ROOT",
        "C:/Users/jusin/OneDrive/Documents/Custom Office Templates/reports",
    )
    app.config["TESTING"] = True

    with app.test_client() as client:
        html = client.get("/", base_url="http://127.0.0.1:5050").data.decode("utf-8")

    assert "/api/button2/generated-report/open" in html
    assert "Value: 5050" in html


def test_runtime_preflight_panel_shows_missing_output_root_status(monkeypatch):
    monkeypatch.delenv("BUTTON2_PDF_OUTPUT_ROOT", raising=False)
    app.config["TESTING"] = True

    with app.test_client() as client:
        html = client.get("/").data.decode("utf-8")

    assert "BUTTON2_PDF_OUTPUT_ROOT" in html
    assert "PDF output root missing - start dashboard with Windows launch script." in html
    assert "Status: MISSING" in html
