import json
import os
import time

from pypdf import PdfReader

from operator_dashboard.app import app
from operator_dashboard.app import _build_ingest_payload_from_selected_matchup
from operator_dashboard.button2_dossier_handoff_report_context_preview import (
    build_button2_dossier_handoff_report_context_preview,
)
from operator_dashboard.button2_html_composition_entry_point_v1 import build_button2_report_html
from operator_dashboard.button2_readonly_dossier_handoff_ingest_preview import (
    build_button2_readonly_dossier_handoff_ingest_preview,
)


GENERATE_ROUTE = "/api/button2/selected-matchup/generate-guarded-v1"
LIBRARY_ROUTE = "/api/button2/generated-report/library"


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


def test_dashboard_contains_pdf_reports_folder_link():
    app.config["TESTING"] = True

    with app.test_client() as client:
        html = client.get("/").data.decode("utf-8")

    assert "PDF Reports Folder" in html
    assert "/api/button2/generated-report/library" in html


def test_pdf_library_lists_only_pdfs_newest_first_with_safe_open_links(monkeypatch, tmp_path):
    app.config["TESTING"] = True
    monkeypatch.setenv("BUTTON2_PDF_OUTPUT_ROOT", str(tmp_path))

    older = tmp_path / "older_report.pdf"
    newer = tmp_path / "newer_report.pdf"
    ignored = tmp_path / "notes.txt"
    older.write_bytes(b"%PDF-1.4\n%old\n")
    time.sleep(0.01)
    newer.write_bytes(b"%PDF-1.4\n%new\n")
    ignored.write_text("not a pdf", encoding="utf-8")

    with app.test_client() as client:
        response = client.get(LIBRARY_ROUTE)

    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "older_report.pdf" in html
    assert "newer_report.pdf" in html
    assert "notes.txt" not in html
    assert html.index("newer_report.pdf") < html.index("older_report.pdf")
    assert "/api/button2/generated-report/open?filename=newer_report.pdf" in html


def test_pdf_library_rejects_directory_override_query(monkeypatch, tmp_path):
    app.config["TESTING"] = True
    monkeypatch.setenv("BUTTON2_PDF_OUTPUT_ROOT", str(tmp_path))

    with app.test_client() as client:
        response = client.get(f"{LIBRARY_ROUTE}?path=..%2F")

    assert response.status_code == 400
    data = response.get_json()
    assert data["ok"] is False
    assert data["error"] == "invalid_query"


def test_html_composition_contains_premium_visual_polish_markers():
    ingest_payload = _build_ingest_payload_from_selected_matchup(_selected_matchup_preview())
    ingest_result = build_button2_readonly_dossier_handoff_ingest_preview(ingest_payload)
    assert ingest_result["ok"] is True

    context_result = build_button2_dossier_handoff_report_context_preview(
        {"button2_ingest_preview_context": ingest_result["button2_ingest_preview_context"]}
    )
    assert context_result["ok"] is True

    html_result = build_button2_report_html(context_result["report_context_preview"])
    assert html_result["ok"] is True

    html = html_result["html_content"]
    assert "Executive Command Dashboard" in html
    assert "Tactical Control" in html
    assert "Collapse Risk" in html
    assert "Energy/Fatigue" in html
    assert "Mental Stress" in html
    assert "Source Traceability" in html
    assert "Operator Traceability Appendix" in html
    assert "Selected Matchup Report Generation Context" not in html


def test_guarded_generation_pdf_has_minimum_12_pages_and_polished_sections(monkeypatch, tmp_path):
    app.config["TESTING"] = True
    monkeypatch.setenv("BUTTON2_PDF_OUTPUT_ROOT", str(tmp_path))
    monkeypatch.setenv("PATH", r"C:\msys64\ucrt64\bin;" + os.environ.get("PATH", ""))

    payload = {
        "operator_approved": True,
        "selected_matchup_preview": _selected_matchup_preview(),
    }

    with app.test_client() as client:
        response = client.post(GENERATE_ROUTE, data=json.dumps(payload), content_type="application/json")

    assert response.status_code == 200
    data = response.get_json()
    assert data["ok"] is True
    assert data["delivery_performed"] is False
    assert data["external_api_delivery_performed"] is False
    assert data["queue_write_performed"] is False
    assert data["learning_apply_performed"] is False
    assert data["calibration_write_performed"] is False
    assert data["button3_mutation_performed"] is False

    output_path = data["output_path"]
    assert os.path.exists(output_path)

    reader = PdfReader(output_path)
    assert len(reader.pages) >= 12

    text = "\n".join((page.extract_text() or "") for page in reader.pages)
    assert "AI-RISA Premium Fight Report" in text
    assert "Executive Command Dashboard" in text
    assert "Scenario Tree / Method Pathways" in text
    assert "Operator Traceability Appendix" in text
