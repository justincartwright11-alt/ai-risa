"""Button 2 rendered visual overlap/depth QA repair tests v1."""

from __future__ import annotations

import json
import os
from pathlib import Path

from pypdf import PdfReader

from operator_dashboard.app import app
from operator_dashboard.button2_template_pack_asset_renderer_v1 import DEFAULT_TEMPLATE_PACK_ROOT

ROUTE = "/api/button2/selected-matchup/generate-guarded-v1"
OPEN_ROUTE = "/api/button2/generated-report/open"
LIBRARY_ROUTE = "/api/button2/generated-report/library"

SUMMARY_JSON = Path(
    r"C:\Users\jusin\OneDrive\Documents\Custom Office Templates\ops\release_checks\button2_pdf_rendered_visual_overlap_depth_qa_repair_v1\rendered_visual_overlap_depth_summary.json"
)

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

FORBIDDEN = [
    "Cover Page",
    "Premium Cover",
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
]

CONCAT_DEFECTS = [
    "Fighter A PathwayAnthony",
    "Fighter B Counter-Pathway Daniel",
    "Buyer Meaning / Coach MeaningBuyer",
    "Command Instruction Preserve scoring geography before pace expansion; avoid low-value with no completion",
]

VISUAL_MODULE_MARKERS = [
    "Fighter Overview",
    "Tale of the Tape",
    "Body Risk Heat Map",
    "Anatomical Risk Map",
    "Tactical Edge Table",
    "Failure Heat Map",
    "Round Control Graph",
    "Method Probability Chart",
    "Scenario Tree / Method Pathways",
]

DEPTH_MARKERS = [
    "Tactical Thesis",
    "Mechanism",
    "Fighter A Pathway",
    "Fighter B Counter-Pathway",
    "Watch Cue",
    "Command Instruction",
    "Failure Consequence",
    "Control Window",
    "Visual/Data Read",
    "Buyer Meaning",
    "Coach Meaning",
]

MATCHUPS = [
    ("Alex Pereira", "Jiri Prochazka", "UFC 300", "https://www.ufc.com/event/ufc-300"),
    ("Anthony Joshua", "Daniel Dubois", "Joshua vs Dubois", "https://www.matchroomboxing.com/events/joshua-vs-dubois"),
    ("Rico Verhoeven", "Tariq Osaro", "GLORY 100", "https://www.glorykickboxing.com/events/glory-100"),
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


def _joined_text(reader: PdfReader) -> str:
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def _generate(tmp_path: Path, fighter_a: str, fighter_b: str, event_name: str, source_url: str) -> tuple[dict, PdfReader]:
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
    payload = response.get_json()
    assert payload["ok"] is True
    return payload, PdfReader(payload["output_path"])


def _assert_report_contract(data: dict, reader: PdfReader) -> None:
    assert len(reader.pages) == 24
    text = _joined_text(reader)
    lower = text.lower()

    for section in REQUIRED_SECTIONS:
        assert section in text, f"Missing required section: {section}"

    for marker in VISUAL_MODULE_MARKERS:
        assert marker in text, f"Missing visual marker: {marker}"

    for marker in DEPTH_MARKERS:
        assert marker in text, f"Missing depth marker: {marker}"

    for bad in FORBIDDEN:
        assert bad.lower() not in lower, f"Forbidden/default text present: {bad}"

    for defect in CONCAT_DEFECTS:
        assert defect.lower() not in lower, f"Concatenation defect present: {defect}"

    assert data.get("pdf_open_url")
    assert OPEN_ROUTE in data["pdf_open_url"]
    assert data["delivery_performed"] is False
    assert data["external_api_delivery_performed"] is False
    assert data["queue_write_performed"] is False
    assert data["learning_apply_performed"] is False
    assert data["calibration_write_performed"] is False
    assert data["button3_mutation_performed"] is False


def test_button2_rendered_visual_overlap_depth_contract_all_matchups_v1(tmp_path):
    for fighter_a, fighter_b, event_name, source_url in MATCHUPS:
        data, reader = _generate(tmp_path, fighter_a, fighter_b, event_name, source_url)
        _assert_report_contract(data, reader)


def test_button2_rendered_visual_overlap_depth_json_flags_pass_v1():
    assert SUMMARY_JSON.exists(), f"Missing rendered visual summary JSON: {SUMMARY_JSON}"
    summary = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))

    assert summary.get("all_24_pages") is True
    assert summary.get("all_24_sections_present") is True
    assert summary.get("all_forbidden_text_clean") is True
    assert summary.get("all_cover_safe_zone_pass") is True
    assert summary.get("all_dashboard_card_fit_pass") is True
    assert summary.get("all_tactical_table_fit_pass") is True
    assert summary.get("all_heatmap_column_fit_pass") is True
    assert summary.get("all_lower_depth_panel_fit_pass") is True
    assert summary.get("all_footer_collision_pass") is True
    assert summary.get("all_source_page_clean_pass") is True

    for report in summary.get("reports", []):
        assert report.get("page_count") == 24
        assert report.get("forbidden_text_clean") is True
        assert report.get("sections_24_present") is True
        assert report.get("cover_safe_zone_pass") is True
        assert report.get("dashboard_card_fit_pass") is True
        assert report.get("tactical_table_fit_pass") is True
        assert report.get("heatmap_column_fit_pass") is True
        assert report.get("lower_depth_panel_fit_pass") is True
        assert report.get("footer_collision_pass") is True
        assert report.get("source_page_clean_pass") is True
        assert report.get("manual_visual_inspection_verdict") == "PASS"
        assert report.get("visual_proof_paths"), "Missing visual proof paths"


def test_button2_rendered_visual_overlap_depth_routes_and_governance_v1(tmp_path):
    app.config["TESTING"] = True
    os.environ["BUTTON2_PDF_OUTPUT_ROOT"] = str(tmp_path)

    with app.test_client() as client:
        home = client.get("/")
        library = client.get(LIBRARY_ROUTE)

    assert home.status_code == 200
    assert library.status_code == 200
    html = home.data.decode("utf-8")
    assert "Open Generated PDF" in html
    assert "PDF Reports Folder" in html
