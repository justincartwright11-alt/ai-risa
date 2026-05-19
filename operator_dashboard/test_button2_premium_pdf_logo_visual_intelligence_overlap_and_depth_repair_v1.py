"""Button 2 premium PDF logo + visual intelligence + overlap/depth repair tests v1."""

from __future__ import annotations

import os
from pathlib import Path

from pypdf import PdfReader

from operator_dashboard.app import app
from operator_dashboard.button2_template_pack_asset_renderer_v1 import DEFAULT_TEMPLATE_PACK_ROOT

ROUTE = "/api/button2/selected-matchup/generate-guarded-v1"
LIBRARY_ROUTE = "/api/button2/generated-report/library"


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


def _assert_collision_phrase_guards(full_text: str):
    known_collision_phrases = [
        "executive summary",
        "traceability / source map",
        "disclaimer / risk control",
        "what this report includes",
    ]
    lines = [ln.strip().lower() for ln in full_text.splitlines() if ln.strip()]
    for phrase in known_collision_phrases:
        for ln in lines:
            if phrase in ln:
                assert "----" not in ln
                assert "____" not in ln
                assert "||||" not in ln


def _assert_common(data: dict, reader: PdfReader):
    full_text = _joined_text(reader)

    assert len(reader.pages) >= 14

    assert "AI-RISA PREMIUM FIGHT INTELLIGENCE REPORT" in full_text
    assert "THE INTELLIGENCE BENEATH THE VIOLENCE" in full_text

    assert "Premium Cover" not in full_text
    assert "SOURCE TRACEABILITY Source Traceability" not in full_text

    forbidden_placeholders = [
        "where the fight is owned",
        "where the fight can flip",
        "what the corner must solve",
    ]
    lowered = full_text.lower()
    for phrase in forbidden_placeholders:
        assert phrase not in lowered

    required_visual_blocks = [
        "Fighter Architecture Radar",
        "Tactical Edge Table",
        "Round Control Graph",
        "Failure Heat Map",
        "Method Probability Chart",
        "Scenario Tree / Method Pathways",
        "Traceability / Source Map",
        "Disclaimer / Risk Control",
    ]
    for marker in required_visual_blocks:
        assert marker in full_text

    forbidden_internal = [
        "Operator Summary Preview",
        "Template renderer profile",
        "premium_template_pack_v29",
        "Renderer mode",
        "Source context",
        "Ingest mode",
        "Visual QA rollup",
        "controlled_export_not_eligible",
        "customer_ready_not_ready",
    ]
    for marker in forbidden_internal:
        assert marker.lower() not in lowered

    assert "EXECUTIVE SUMMARY / ROUND-CONTROL PROJECTION" in full_text

    _assert_collision_phrase_guards(full_text)

    assert data["delivery_performed"] is False
    assert data["external_api_delivery_performed"] is False
    assert data["queue_write_performed"] is False
    assert data["learning_apply_performed"] is False
    assert data["calibration_write_performed"] is False
    assert data["button3_mutation_performed"] is False


def test_alex_vs_jiri_logo_visual_intelligence_overlap_depth(monkeypatch, tmp_path):
    data, reader = _generate_pdf(
        tmp_path,
        "Alex Pereira",
        "Jiri Prochazka",
        "UFC 300",
        "https://www.ufc.com/event/ufc-300",
    )
    _assert_common(data, reader)
    full_text = _joined_text(reader)
    assert "Alex Pereira" in full_text
    assert "Jiri Prochazka" in full_text


def test_rico_vs_tariq_logo_visual_intelligence_overlap_depth(monkeypatch, tmp_path):
    data, reader = _generate_pdf(
        tmp_path,
        "Rico Verhoeven",
        "Tariq Osaro",
        "GLORY 100",
        "https://www.glorykickboxing.com/events/glory-100",
    )
    _assert_common(data, reader)


def test_anthony_vs_daniel_logo_visual_intelligence_overlap_depth(monkeypatch, tmp_path):
    data, reader = _generate_pdf(
        tmp_path,
        "Anthony Joshua",
        "Daniel Dubois",
        "Joshua vs Dubois",
        "https://www.matchroomboxing.com/events/joshua-vs-dubois",
    )
    _assert_common(data, reader)


def test_dashboard_open_and_library_routes_remain_live():
    app.config["TESTING"] = True
    with app.test_client() as client:
        home = client.get("/")
        library = client.get(LIBRARY_ROUTE)

    assert home.status_code == 200
    html = home.data.decode("utf-8")
    assert "Open Generated PDF" in html
    assert "PDF Reports Folder" in html
    assert library.status_code == 200
