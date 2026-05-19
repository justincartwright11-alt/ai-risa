"""Button 2 selected-matchup Ares 24-section customer-ready parity tests v1."""

from __future__ import annotations

import os
from pathlib import Path

from pypdf import PdfReader

from operator_dashboard.app import app
from operator_dashboard.button2_template_pack_asset_renderer_v1 import DEFAULT_TEMPLATE_PACK_ROOT

ROUTE = "/api/button2/selected-matchup/generate-guarded-v1"
LIBRARY_ROUTE = "/api/button2/generated-report/library"

REQUIRED_SECTIONS = [
    "Cover Page",
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

FORBIDDEN_STRINGS = [
    "report_status=PENDING",
    "report_quality_status=draft_only",
    "customer_ready_not_ready",
    "controlled_export_not_eligible",
    "visual QA rollup",
    "template renderer profile",
    "raw ingest mode",
    "valid layers",
    "missing layers",
    "Radar data unavailable",
    "Heat map data unavailable",
    "Control-shift data unavailable",
    "Method distribution data unavailable",
    "Operator Summary Preview",
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


def _assert_ares_24_parity(data: dict, reader: PdfReader, fighter_a: str, fighter_b: str):
    assert len(reader.pages) >= 24
    full_text = _joined_text(reader)
    lower_text = full_text.lower()

    assert "AI-RISA PREMIUM FIGHT INTELLIGENCE REPORT" in full_text
    assert "THE INTELLIGENCE BENEATH THE VIOLENCE" in full_text

    for section in REQUIRED_SECTIONS:
        assert section in full_text, f"Missing required section: {section}"

    for marker in [
        "Fighter Architecture Radar",
        "Tactical Edge Table",
        "Failure Heat Map",
        "Round Control Graph",
        "Method Probability Chart",
    ]:
        assert marker in full_text, f"Missing required visual-intelligence marker: {marker}"

    for phrase in FORBIDDEN_STRINGS:
        assert phrase.lower() not in lower_text, f"Found forbidden/default/debug string: {phrase}"

    assert fighter_a in full_text
    assert fighter_b in full_text
    assert "Fighter A vs Fighter B" not in full_text
    assert "Unknown Fighter A" not in full_text
    assert "Unknown Fighter B" not in full_text

    assert "Source" in full_text
    assert "Event" in full_text
    assert "Report ID" in full_text
    assert "Operator Approval Requirement" in full_text
    assert "Source Discipline Statement" in full_text

    # Customer-ready metadata consistency for approved generation
    assert data.get("customer_approved") is True
    assert data.get("customer_ready_gates_passed") is True
    assert data.get("report_status") not in {"PENDING", "pending"}
    assert data.get("report_quality_status") != "draft_only"

    # Dashboard + library + governance checks
    assert data.get("pdf_open_url")
    assert data.get("output_filename")
    assert data["delivery_performed"] is False
    assert data["external_api_delivery_performed"] is False
    assert data["queue_write_performed"] is False
    assert data["learning_apply_performed"] is False
    assert data["calibration_write_performed"] is False
    assert data["button3_mutation_performed"] is False


def test_rico_vs_tariq_ares_24_section_customer_ready_parity(monkeypatch, tmp_path):
    data, reader = _generate_pdf(
        tmp_path,
        "Rico Verhoeven",
        "Tariq Osaro",
        "GLORY 100",
        "https://www.glorykickboxing.com/events/glory-100",
    )
    _assert_ares_24_parity(data, reader, "Rico Verhoeven", "Tariq Osaro")


def test_anthony_vs_daniel_ares_24_section_customer_ready_parity(monkeypatch, tmp_path):
    data, reader = _generate_pdf(
        tmp_path,
        "Anthony Joshua",
        "Daniel Dubois",
        "Joshua vs Dubois",
        "https://www.matchroomboxing.com/events/joshua-vs-dubois",
    )
    _assert_ares_24_parity(data, reader, "Anthony Joshua", "Daniel Dubois")


def test_alex_vs_jiri_ares_24_section_customer_ready_parity(monkeypatch, tmp_path):
    data, reader = _generate_pdf(
        tmp_path,
        "Alex Pereira",
        "Jiri Prochazka",
        "UFC 300",
        "https://www.ufc.com/event/ufc-300",
    )
    _assert_ares_24_parity(data, reader, "Alex Pereira", "Jiri Prochazka")


def test_dashboard_link_and_library_stay_live_for_ares_parity():
    app.config["TESTING"] = True
    with app.test_client() as client:
        home = client.get("/")
        library = client.get(LIBRARY_ROUTE)

    assert home.status_code == 200
    html = home.data.decode("utf-8")
    assert "Open Generated PDF" in html
    assert "PDF Reports Folder" in html
    assert library.status_code == 200
