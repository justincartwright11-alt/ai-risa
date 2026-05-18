import os

from operator_dashboard.app import app


OPEN_ROUTE = "/api/button2/generated-report/open"


def test_open_route_serves_existing_pdf_from_configured_root(monkeypatch, tmp_path):
    app.config["TESTING"] = True
    monkeypatch.setenv("BUTTON2_PDF_OUTPUT_ROOT", str(tmp_path))

    filename = "anthony_joshua_vs_daniel_dubois_joshua_vs_dubois_premium.pdf"
    pdf_path = tmp_path / filename
    pdf_bytes = b"%PDF-1.4\n%test\n"
    pdf_path.write_bytes(pdf_bytes)

    with app.test_client() as client:
        response = client.get(f"{OPEN_ROUTE}?filename={filename}")

    assert response.status_code == 200
    assert response.data == pdf_bytes
    assert "application/pdf" in (response.content_type or "")


def test_open_route_rejects_path_traversal_attempt(monkeypatch, tmp_path):
    app.config["TESTING"] = True
    monkeypatch.setenv("BUTTON2_PDF_OUTPUT_ROOT", str(tmp_path))

    with app.test_client() as client:
        response = client.get(f"{OPEN_ROUTE}?filename=..%2Fsecrets.pdf")

    assert response.status_code == 400
    data = response.get_json()
    assert data["ok"] is False
    assert data["error"] == "invalid_filename"


def test_open_route_rejects_non_pdf_extension(monkeypatch, tmp_path):
    app.config["TESTING"] = True
    monkeypatch.setenv("BUTTON2_PDF_OUTPUT_ROOT", str(tmp_path))

    with app.test_client() as client:
        response = client.get(f"{OPEN_ROUTE}?filename=not_a_pdf.txt")

    assert response.status_code == 400
    data = response.get_json()
    assert data["ok"] is False
    assert data["error"] == "invalid_filename"


def test_open_route_rejects_missing_file(monkeypatch, tmp_path):
    app.config["TESTING"] = True
    monkeypatch.setenv("BUTTON2_PDF_OUTPUT_ROOT", str(tmp_path))

    with app.test_client() as client:
        response = client.get(f"{OPEN_ROUTE}?filename=missing_report.pdf")

    assert response.status_code == 404
    data = response.get_json()
    assert data["ok"] is False
    assert data["error"] == "file_not_found"


def test_open_route_fails_closed_when_output_root_unavailable(monkeypatch):
    app.config["TESTING"] = True
    monkeypatch.delenv("BUTTON2_PDF_OUTPUT_ROOT", raising=False)

    with app.test_client() as client:
        response = client.get(f"{OPEN_ROUTE}?filename=valid_report.pdf")

    assert response.status_code == 400
    data = response.get_json()
    assert data["ok"] is False
    assert data["error"] == "output_root_unavailable"
