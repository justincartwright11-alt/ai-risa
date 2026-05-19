"""Button 2 premium PDF full-density visual/layout/content engine tests v1."""

from __future__ import annotations

import os
from pathlib import Path

from pypdf import PdfReader

from operator_dashboard.app import app
from operator_dashboard.button2_template_pack_asset_renderer_v1 import DEFAULT_TEMPLATE_PACK_ROOT

ROUTE = "/api/button2/selected-matchup/generate-guarded-v1"
OPEN_ROUTE = "/api/button2/generated-report/open"
LIBRARY_ROUTE = "/api/button2/generated-report/library"

REQUIRED_SECTIONS = [
    "AI-RISA PREMIUM FIGHT INTELLIGENCE REPORT",
    "Fight Intelligence Dashboard",
    "Headline Projection",
    "Matchup Snapshot",
    "Fighter Architecture Radar",
    "Tactical Edge Map",
    "Decision Structure",
    "Energy Use Analysis",
    "Fatigue Failure Points",
    "Mental Condition Under Stress",
    "Collapse Triggers",
    "Deception and Unpredictability",
    "Range / Geography Control",
    "Round-by-Round Control Projection",
    "Scenario Tree / Method Pathways",
    "Scorecard Scenario",
    "Stoppage Windows",
    "Risk Warnings and Exposure Discipline",
    "Betting Market Intelligence",
    "Coach / Corner Notes",
    "Final Projection",
    "Confidence Explanation",
    "Traceability / Source Map",
    "Disclaimer / Risk Control",
]

REQUIRED_MARKERS = [
    "Fighter Overview",
    "Tale of the Tape",
    "Body Risk Heat Map",
    "Anatomical Risk Map",
    "Tactical Edge Table",
    "Failure Heat Map",
    "Round Control Graph",
    "Method Probability Chart",
    "Scenario Tree / Method Pathways",
    "Tactical Thesis",
    "Mechanism",
    "Fighter A Pathway",
    "Fighter B Counter-Pathway",
    "Watch Cue",
    "Command Instruction",
    "Failure Consequence",
    "Round Band",
    "Visual/Data Read",
    "Buyer Meaning",
    "Coach Meaning",
]

FORBIDDEN_STRINGS = [
    "where the fight is owned",
    "where the fight can flip",
    "what the corner must solve",
    "SOURCE TRACEABILITY Source Traceability",
    "customer_ready_not_ready",
    "draft_only",
    "controlled_export_not_eligible",
    "visual QA rollup",
    "template renderer profile",
    "raw ingest mode",
    "valid layers",
    "missing layers",
    "Cover Page",
    "Premium Cover",
]


def _preview_payload(fighter_a: str, fighter_b: str, event_name: str, source_url: str) -> dict:
    return {
        "selected_for_button2": True,
        "selection_preview": True,
        "fighter_a": fighter_a,
        "fighter_b": fighter_b,
        "event_name": event_name,
        "event_date": "2026-09-21",
        "promotion": "Premium Promotion",
        "source_type": "official",
        "source_url": source_url,
        "report_ready_status": "ready_for_button2_preview",
        "source_traceability": [
            {
                "id": "SRC-001",
                "type": "official",
                "tier": "official",
                "url": source_url,
                "date": "2026-09-21",
                "discipline": "source traceable",
            }
        ],
    }


def _generate_pdf(tmp_path: Path, fighter_a: str, fighter_b: str, event_name: str, source_url: str) -> tuple[dict, PdfReader]:
    app.config["TESTING"] = True
    os.environ["BUTTON2_PDF_OUTPUT_ROOT"] = str(tmp_path)
    os.environ["BUTTON2_TEMPLATE_PACK_ROOT"] = DEFAULT_TEMPLATE_PACK_ROOT

    with app.test_client() as client:
        response = client.post(
            ROUTE,
            json={
                "operator_approved": True,
                "selected_matchup_preview": _preview_payload(fighter_a, fighter_b, event_name, source_url),
            },
        )

    assert response.status_code == 200
    data = response.get_json()
    assert data["ok"] is True
    return data, PdfReader(data["output_path"])


def _joined_text(reader: PdfReader) -> str:
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def _assert_full_density_contract(data: dict, reader: PdfReader, fighter_a: str, fighter_b: str):
    assert len(reader.pages) == 24
    full_text = _joined_text(reader)
    lower_text = full_text.lower()

    for section in REQUIRED_SECTIONS:
        assert section in full_text, f"Missing required section: {section}"

    for marker in REQUIRED_MARKERS:
        assert marker in full_text, f"Missing required marker: {marker}"

    for phrase in FORBIDDEN_STRINGS:
        assert phrase.lower() not in lower_text, f"Found forbidden/default/debug string: {phrase}"

    assert fighter_a in full_text
    assert fighter_b in full_text

    assert data.get("pdf_open_url")
    assert OPEN_ROUTE in data.get("pdf_open_url")

    assert data["delivery_performed"] is False
    assert data["external_api_delivery_performed"] is False
    assert data["queue_write_performed"] is False
    assert data["learning_apply_performed"] is False
    assert data["calibration_write_performed"] is False
    assert data["button3_mutation_performed"] is False


def test_full_density_alex_vs_jiri(monkeypatch, tmp_path):
    data, reader = _generate_pdf(
        tmp_path,
        "Alex Pereira",
        "Jiri Prochazka",
        "UFC 300",
        "https://www.ufc.com/event/ufc-300",
    )
    _assert_full_density_contract(data, reader, "Alex Pereira", "Jiri Prochazka")


def test_full_density_anthony_vs_daniel(monkeypatch, tmp_path):
    data, reader = _generate_pdf(
        tmp_path,
        "Anthony Joshua",
        "Daniel Dubois",
        "Joshua vs Dubois",
        "https://www.matchroomboxing.com/events/joshua-vs-dubois",
    )
    _assert_full_density_contract(data, reader, "Anthony Joshua", "Daniel Dubois")


def test_full_density_rico_vs_tariq(monkeypatch, tmp_path):
    data, reader = _generate_pdf(
        tmp_path,
        "Rico Verhoeven",
        "Tariq Osaro",
        "GLORY 100",
        "https://www.glorykickboxing.com/events/glory-100",
    )
    _assert_full_density_contract(data, reader, "Rico Verhoeven", "Tariq Osaro")


def test_full_density_dashboard_routes_live(tmp_path):
    app.config["TESTING"] = True
    os.environ["BUTTON2_PDF_OUTPUT_ROOT"] = str(tmp_path)

    with app.test_client() as client:
        home = client.get("/")
        library = client.get(LIBRARY_ROUTE)

    assert home.status_code == 200
    html = home.data.decode("utf-8")
    assert "Open Generated PDF" in html
    assert "PDF Reports Folder" in html
    assert library.status_code == 200
