"""Button 2 premium PDF visual QA layout and depth hardening tests v1."""

from __future__ import annotations

import os
from pathlib import Path

from pypdf import PdfReader

from operator_dashboard.app import app
from operator_dashboard.button2_template_pack_asset_renderer_v1 import DEFAULT_TEMPLATE_PACK_ROOT

ROUTE = "/api/button2/selected-matchup/generate-guarded-v1"


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
    reader = PdfReader(data["output_path"])
    return data, reader


def _joined_text(reader: PdfReader) -> str:
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def _assert_common_quality(reader: PdfReader, full_text: str):
    assert len(reader.pages) >= 14
    assert "THE INTELLIGENCE BENEATH THE VIOLENCE" in full_text
    assert "AI-RISA PREMIUM FIGHT INTELLIGENCE REPORT" in full_text
    assert "Traceability / Source Map" in full_text
    assert "Disclaimer / Risk Control" in full_text
    assert "Premium Cover" not in full_text
    forbidden_placeholders = [
        "where the fight is owned",
        "where the fight can flip",
        "what the corner must solve",
    ]
    for phrase in forbidden_placeholders:
        assert phrase not in full_text.lower()
    internal_strings = [
        "Operator Summary Preview",
        "Template renderer profile",
        "Visual QA rollup",
        "controlled_export_not_eligible",
        "customer_ready_not_ready",
    ]
    for phrase in internal_strings:
        assert phrase.lower() not in full_text.lower()
    assert "Source Traceability Source Traceability" not in full_text


def test_rico_pdf_layout_and_depth_hardening(monkeypatch, tmp_path):
    data, reader = _generate_pdf(
        tmp_path,
        "Rico Verhoeven",
        "Tariq Osaro",
        "GLORY 100",
        "https://www.glorykickboxing.com/events/glory-100",
    )
    full_text = _joined_text(reader)
    _assert_common_quality(reader, full_text)
    assert "EXECUTIVE SUMMARY / ROUND-CONTROL PROJECTION" in full_text
    assert "Command Read" in full_text or "COMMAND READ" in full_text
    assert "delivery_performed" in data and data["delivery_performed"] is False
    assert data["external_api_delivery_performed"] is False
    assert data["queue_write_performed"] is False
    assert data["learning_apply_performed"] is False
    assert data["calibration_write_performed"] is False
    assert data["button3_mutation_performed"] is False
    assert reader.pages[0].extract_text() and "AI-RISA PREMIUM FIGHT INTELLIGENCE REPORT" in reader.pages[0].extract_text()
    assert reader.pages[1].extract_text() and "EXECUTIVE SUMMARY / ROUND-CONTROL PROJECTION" in reader.pages[1].extract_text()
    assert any("Traceability / Source Map" in (page.extract_text() or "") for page in reader.pages)
    assert any("Disclaimer / Risk Control" in (page.extract_text() or "") for page in reader.pages)


def test_anthony_joshua_pdf_layout_and_depth_hardening(monkeypatch, tmp_path):
    data, reader = _generate_pdf(
        tmp_path,
        "Anthony Joshua",
        "Daniel Dubois",
        "Joshua vs Dubois",
        "https://www.matchroomboxing.com/events/joshua-vs-dubois",
    )
    full_text = _joined_text(reader)
    _assert_common_quality(reader, full_text)
    assert len(reader.pages) >= 14
    assert "Anthony Joshua" in full_text
    assert "Daniel Dubois" in full_text
    assert "control lane" in full_text.lower()
    assert "danger lane" in full_text.lower()
    assert data["delivery_performed"] is False
    assert data["external_api_delivery_performed"] is False
    assert data["queue_write_performed"] is False
    assert data["learning_apply_performed"] is False
    assert data["calibration_write_performed"] is False
    assert data["button3_mutation_performed"] is False


def test_jiri_pdf_layout_and_depth_hardening(monkeypatch, tmp_path):
    data, reader = _generate_pdf(
        tmp_path,
        "Jiri Prochazka",
        "Carlos Ulberg",
        "UFC 320",
        "https://www.ufc.com/event/ufc-320",
    )
    full_text = _joined_text(reader)
    _assert_common_quality(reader, full_text)
    assert len(reader.pages) >= 14
    assert "Jiri Prochazka" in full_text
    assert "Carlos Ulberg" in full_text
    assert "model-derived" in full_text.lower()
    assert "round-control projection" in full_text.lower()
    assert data["delivery_performed"] is False
    assert data["external_api_delivery_performed"] is False
    assert data["queue_write_performed"] is False
    assert data["learning_apply_performed"] is False
    assert data["calibration_write_performed"] is False
    assert data["button3_mutation_performed"] is False
