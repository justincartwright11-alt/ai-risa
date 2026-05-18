import json
import os

from pypdf import PdfReader

from operator_dashboard.app import app
from operator_dashboard.app import _build_ingest_payload_from_selected_matchup
from operator_dashboard.button2_readonly_dossier_handoff_ingest_preview import (
    build_button2_readonly_dossier_handoff_ingest_preview,
)
from operator_dashboard.button2_dossier_handoff_report_context_preview import (
    build_button2_dossier_handoff_report_context_preview,
)
from operator_dashboard.button2_html_composition_entry_point_v1 import build_button2_report_html


ROUTE = "/api/button2/selected-matchup/generate-guarded-v1"


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


def test_html_composition_contains_full_premium_multipage_structure():
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
    assert html.count('class="report-page') >= 8
    assert "Premium Cover" in html
    assert "Executive Command Dashboard" in html
    assert "Matchup Snapshot" in html
    assert "Tactical Edge Map" in html
    assert "Fighter Architecture / Radar Section" in html
    assert "Decision Structure" in html
    assert "Energy Use Analysis" in html
    assert "Fatigue Failure Points" in html
    assert "Mental Condition Under Stress" in html
    assert "Collapse Triggers" in html
    assert "Range / Geography Control" in html
    assert "Round-by-Round Projection" in html
    assert "Scenario Tree / Method Pathways" in html
    assert "Risk Warnings" in html
    assert "Final Projection" in html
    assert "Confidence Explanation" in html
    assert "Source Traceability" in html
    assert "Disclaimer / Risk Control" in html


def test_guarded_selected_matchup_generation_produces_multipage_pdf(monkeypatch, tmp_path):
    app.config["TESTING"] = True
    monkeypatch.setenv("BUTTON2_PDF_OUTPUT_ROOT", str(tmp_path))
    monkeypatch.setenv("PATH", r"C:\msys64\ucrt64\bin;" + os.environ.get("PATH", ""))

    payload = {
        "operator_approved": True,
        "selected_matchup_preview": _selected_matchup_preview(),
    }

    with app.test_client() as client:
        response = client.post(ROUTE, data=json.dumps(payload), content_type="application/json")

    assert response.status_code == 200
    data = response.get_json()
    assert data["ok"] is True
    assert data["output_filename"].endswith("_premium.pdf")
    assert data["pdf_open_url"].endswith(data["output_filename"])

    output_path = data["output_path"]
    assert os.path.exists(output_path)

    reader = PdfReader(output_path)
    assert len(reader.pages) >= 8

    text = "\n".join((page.extract_text() or "") for page in reader.pages)
    assert "AI-RISA Premium Fight Report" in text
    assert "Anthony Joshua" in text and "Daniel Dubois" in text
    assert "Joshua vs Dubois" in text
    assert "Source Traceability" in text
    assert "Executive Command Dashboard" in text
    assert "Selected Matchup Report Generation Context" not in text


def test_guarded_selected_matchup_generation_preserves_governance_flags(monkeypatch, tmp_path):
    app.config["TESTING"] = True
    monkeypatch.setenv("BUTTON2_PDF_OUTPUT_ROOT", str(tmp_path))

    payload = {
        "operator_approved": True,
        "selected_matchup_preview": _selected_matchup_preview(),
    }

    with app.test_client() as client:
        response = client.post(ROUTE, data=json.dumps(payload), content_type="application/json")

    assert response.status_code == 200
    data = response.get_json()
    assert data["ok"] is True
    assert data["delivery_performed"] is False
    assert data["external_api_delivery_performed"] is False
    assert data["queue_write_performed"] is False
    assert data["learning_apply_performed"] is False
    assert data["calibration_write_performed"] is False
    assert data["button3_mutation_performed"] is False
