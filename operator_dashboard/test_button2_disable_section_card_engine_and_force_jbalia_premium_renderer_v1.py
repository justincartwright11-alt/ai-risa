"""Button 2 hard-disable legacy section-card engine and force premium renderer tests v1."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

from pypdf import PdfReader

from operator_dashboard.app import app
from operator_dashboard.button2_template_pack_asset_renderer_v1 import DEFAULT_TEMPLATE_PACK_ROOT

ROUTE = "/api/button2/selected-matchup/generate-guarded-v1"
OPEN_ROUTE = "/api/button2/generated-report/open"
LIBRARY_ROUTE = "/api/button2/generated-report/library"

MATCHUPS = [
    ("Anthony Joshua", "Daniel Dubois", "Joshua vs Dubois", "https://www.matchroomboxing.com/events/joshua-vs-dubois"),
    ("Rico Verhoeven", "Tariq Osaro", "GLORY 100", "https://www.glorykickboxing.com/events/glory-100"),
    ("Alex Pereira", "Jiri Prochazka", "UFC 300", "https://www.ufc.com/event/ufc-300"),
    ("Nadaka Yoshinari", "Songchainoi Kiatsongrit", "ONE Samurai 1", "https://www.onefc.com/events/one-samurai-1"),
]

LEGACY_MARKERS = [
    "SECTION LENS",
    "MODEL STATUS",
    "REPORT TYPE",
    "ROUND BAND",
    "Fighter A Pathway",
    "Fighter B Counter-Pathway",
    "Buyer Meaning / Coach Meaning",
]

CONCAT_DEFECTS = [
    "Fighter B Counter-Pathway Daniel",
    "Fighter A Pathway Anthony",
    "Buyer Meaning / Coach MeaningBuyer",
    "Command Instruction Preserve",
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
        "matchup_id": f"{fighter_a.lower().replace(' ', '_')}_vs_{fighter_b.lower().replace(' ', '_')}",
    }


def _joined_text(reader: PdfReader) -> str:
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def _assert_governance_false(data: dict) -> None:
    assert data["delivery_performed"] is False
    assert data["external_api_delivery_performed"] is False
    assert data["queue_write_performed"] is False
    assert data["learning_apply_performed"] is False
    assert data["calibration_write_performed"] is False
    assert data["button3_mutation_performed"] is False


def test_no_customer_facing_renderer_source_emits_legacy_section_card_markers_v1():
    renderer_source = Path(__file__).with_name("button2_template_pack_asset_renderer_v1.py").read_text(encoding="utf-8")
    lowered = renderer_source.lower()
    for marker in LEGACY_MARKERS:
        assert marker.lower() not in lowered


def test_disable_section_card_engine_and_force_premium_renderer_all_matchups_v1(tmp_path):
    app.config["TESTING"] = True
    os.environ["BUTTON2_PDF_OUTPUT_ROOT"] = str(tmp_path)
    os.environ["BUTTON2_TEMPLATE_PACK_ROOT"] = DEFAULT_TEMPLATE_PACK_ROOT

    rows = []
    with app.test_client() as client:
        for fighter_a, fighter_b, event_name, source_url in MATCHUPS:
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
            assert data["customer_pdf_quality_gate_failed"] is False
            assert data["renderer_route_used"] == "template_pack_asset_renderer"
            assert data["template_pack_root"] == DEFAULT_TEMPLATE_PACK_ROOT
            assert data["template_pack_asset_backed"] is True
            assert data["stale_file_reused"] is False
            assert data["selected_matchup_matches_pdf_text"] is True
            assert data["page_count"] == 24

            reader = PdfReader(data["output_path"])
            assert len(reader.pages) == 24
            text = _joined_text(reader)
            lower_text = text.lower()

            assert fighter_a in text
            assert fighter_b in text

            for marker in LEGACY_MARKERS:
                assert marker.lower() not in lower_text
            for defect in CONCAT_DEFECTS:
                assert defect.lower() not in lower_text

            assert "Source Traceability" in text
            assert "SOURCE TRACEABILITY Source Traceability" not in text

            open_resp = client.get(OPEN_ROUTE, query_string={"filename": data["output_filename"]})
            assert open_resp.status_code == 200

            _assert_governance_false(data)
            rows.append(data)

        lib_resp = client.get(LIBRARY_ROUTE)
        assert lib_resp.status_code == 200
        library_html = lib_resp.data.decode("utf-8")
        for row in rows:
            assert row["output_filename"] in library_html


def test_quality_gate_fails_closed_when_legacy_marker_detected_v1(tmp_path):
    app.config["TESTING"] = True
    os.environ["BUTTON2_PDF_OUTPUT_ROOT"] = str(tmp_path)
    os.environ["BUTTON2_TEMPLATE_PACK_ROOT"] = DEFAULT_TEMPLATE_PACK_ROOT

    payload = {
        "operator_approved": True,
        "selected_matchup_preview": _preview_payload(
            "Anthony Joshua",
            "Daniel Dubois",
            "Joshua vs Dubois",
            "https://www.matchroomboxing.com/events/joshua-vs-dubois",
        ),
    }

    with app.test_client() as client:
        with patch(
            "operator_dashboard.app._scan_forbidden_markers",
            return_value={
                "any_forbidden_found": True,
                "found_markers": ["SECTION LENS"],
                "marker_hits": {"SECTION LENS": True},
                "found_concatenation_snippets": [],
                "concatenation_hits": {},
            },
        ):
            response = client.post(ROUTE, json=payload)

    assert response.status_code == 422
    data = response.get_json()
    assert data["ok"] is False
    assert data["customer_pdf_quality_gate_failed"] is True
    assert data["reason"] == "legacy_section_card_engine_detected"
    _assert_governance_false(data)
