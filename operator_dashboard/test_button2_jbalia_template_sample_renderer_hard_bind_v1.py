"""Button 2 Jbalia template sample renderer hard-bind tests v1."""

from __future__ import annotations

import os
from pathlib import Path

from pypdf import PdfReader

from operator_dashboard.app import app
from operator_dashboard.button2_template_pack_asset_renderer_v1 import DEFAULT_TEMPLATE_PACK_ROOT

ROUTE = "/api/button2/selected-matchup/generate-guarded-v1"
OPEN_ROUTE = "/api/button2/generated-report/open"
LIBRARY_ROUTE = "/api/button2/generated-report/library"

MATCHUPS = [
    ("Rico Verhoeven", "Tariq Osaro", "GLORY 100", "https://www.glorykickboxing.com/events/glory-100"),
    ("Anthony Joshua", "Daniel Dubois", "Joshua vs Dubois", "https://www.matchroomboxing.com/events/joshua-vs-dubois"),
    ("Alex Pereira", "Jiri Prochazka", "UFC 300", "https://www.ufc.com/event/ufc-300"),
    ("Nadaka Yoshinari", "Songchainoi Kiatsongrit", "ONE Samurai 1", "https://www.onefc.com/events/one-samurai-1"),
]

REQUIRED_SECTIONS = [
    "HEADLINE PROJECTION",
    "MATCHUP SNAPSHOT",
    "FIGHTER ARCHITECTURE RADAR",
    "TACTICAL EDGE MAP",
    "DECISION STRUCTURE",
    "ENERGY USE ANALYSIS",
    "FATIGUE FAILURE POINTS",
    "MENTAL CONDITION UNDER STRESS",
    "COLLAPSE TRIGGERS",
    "DECEPTION AND UNPREDICTABILITY",
    "RANGE / GEOGRAPHY CONTROL",
    "ROUND-BY-ROUND CONTROL PROJECTION",
    "SCENARIO TREE / METHOD PATHWAYS",
    "SCORECARD SCENARIO",
    "STOPPAGE WINDOWS",
    "RISK WARNINGS AND EXPOSURE DISCIPLINE",
    "BETTING MARKET INTELLIGENCE",
    "COACH / CORNER NOTES",
    "FINAL PROJECTION",
    "CONFIDENCE EXPLANATION",
    "TRACEABILITY / SOURCE MAP",
    "DISCLAIMER / RISK CONTROL",
]

REQUIRED_COVER_MARKERS = [
    "PREMIUM FIGHT",
    "INTELLIGENCE REPORT",
    "THE INTELLIGENCE BENEATH THE VIOLENCE",
    "CUSTOMER READY",
    "Report ID:",
    "Confidence:",
    "Generated:",
    "AI-RISA | COMBAT INTELLIGENCE | OPERATOR APPROVED | SOURCE TRACEABLE",
    "template_pack_sample",
]

REQUIRED_DASHBOARD_MARKERS = [
    "EXECUTIVE COMMAND DASHBOARD",
    "HEADLINE PREDICTION",
    "CONFIDENCE",
    "VOLATILITY",
    "EXECUTIVE SUMMARY",
    "CONTROL ZONE",
    "DANGER ZONE",
    "COLLAPSE TRIGGER",
    "FIGHT CONTROL INTELLIGENCE STRIP",
    "CONTROL THESIS",
    "FLIP POINT",
    "WATCH CUE",
    "COMMAND RULE",
    "ROUND CONTROL PROJECTION",
    "METHOD PROBABILITY",
    "RISK CONTROL",
]

FORBIDDEN = [
    "SECTION LENS",
    "MODEL STATUS",
    "REPORT TYPE",
    "ROUND BAND",
    "Cover Page",
    "Premium Cover",
    "AI-RISA Premium Fight Report",
    "Report Type: Premium Fight Intelligence Report",
    "Fighter A Pathway",
    "Fighter B Counter-Pathway",
    "Buyer Meaning / Coach Meaning",
    "customer_ready_not_ready",
    "draft_only",
    "controlled_export_not_eligible",
    "visual QA rollup",
    "template renderer profile",
    "raw ingest mode",
    "valid layers",
    "missing layers",
    "SOURCE TRACEABILITY Source Traceability",
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


def test_template_pack_path_and_assets_exist_v1():
    root = Path(DEFAULT_TEMPLATE_PACK_ROOT)
    assert root.exists()
    assert (root / "ai_risa_report_template_v29_bar_alignment_fix.py").exists()
    assert (root / "AI-RISA Logo.png").exists()
    assert (root / "ai_risa_logo_clean_blend.png").exists()
    assert (root / "ai_risa_logo_watermark_blend.png").exists()


def test_selected_matchup_hard_bind_to_jbalia_template_sample_renderer_v1(tmp_path):
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

            assert data["renderer_route_used"] == "template_pack_asset_renderer"
            assert data["renderer_profile"] == "premium_template_pack_v29_selected_matchup_jbalia_hard_bind_v1"
            assert data["template_pack_root"] == DEFAULT_TEMPLATE_PACK_ROOT
            assert data["template_pack_asset_backed"] is True

            assert data["output_filename"]
            assert data["output_filename"].endswith(".pdf")
            assert data["stale_file_reused"] is False
            assert data["selected_matchup_matches_pdf_text"] is True
            assert data["page_count"] == 24

            reader = PdfReader(data["output_path"])
            assert len(reader.pages) == 24
            text = _joined_text(reader)
            lower = text.lower()

            for marker in REQUIRED_COVER_MARKERS:
                assert marker in text, f"Missing cover marker: {marker}"
            for marker in REQUIRED_DASHBOARD_MARKERS:
                assert marker in text, f"Missing dashboard marker: {marker}"
            for section in REQUIRED_SECTIONS:
                assert section in text, f"Missing section marker: {section}"

            for forbidden in FORBIDDEN:
                assert forbidden.lower() not in lower, f"Forbidden marker present: {forbidden}"

            open_resp = client.get(OPEN_ROUTE, query_string={"filename": data["output_filename"]})
            assert open_resp.status_code == 200

            _assert_governance_false(data)
            rows.append(data)

        library_resp = client.get(LIBRARY_ROUTE)
        assert library_resp.status_code == 200
        library_html = library_resp.data.decode("utf-8")
        for row in rows:
            assert row["output_filename"] in library_html
