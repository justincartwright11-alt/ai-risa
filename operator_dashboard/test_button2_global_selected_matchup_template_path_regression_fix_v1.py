"""Button 2 global selected-matchup template-path regression fix tests v1."""

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
    (
        "Nadaka Yoshinari",
        "Songchainoi Kiatsongrit",
        "ONE Samurai 1",
        "https://www.onefc.com/events/one-samurai-1",
    ),
    (
        "Rico Verhoeven",
        "Tariq Osaro",
        "GLORY 100",
        "https://www.glorykickboxing.com/events/glory-100",
    ),
    (
        "Anthony Joshua",
        "Daniel Dubois",
        "Joshua vs Dubois",
        "https://www.matchroomboxing.com/events/joshua-vs-dubois",
    ),
    (
        "Alex Pereira",
        "Jiri Prochazka",
        "UFC 300",
        "https://www.ufc.com/event/ufc-300",
    ),
]

REQUIRED_MARKERS = [
    "PREMIUM FIGHT INTELLIGENCE REPORT",
    "THE INTELLIGENCE BENEATH THE VIOLENCE",
    "Fight Intelligence Dashboard",
    "HEADLINE PREDICTION",
    "Control Zone",
    "Danger Zone",
    "Collapse Trigger",
    "CONTROL LENS",
    "DANGER LENS",
    "COMMAND READ",
    "Traceability / Source Map",
    "Disclaimer / Risk Control",
]

FORBIDDEN_MARKERS = [
    "SECTION LENS",
    "MODEL STATUS",
    "REPORT TYPE",
    "ROUND BAND",
    "Cover Page",
    "Premium Cover",
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


def _normalize_path(path_value: str) -> str:
    return os.path.normcase(os.path.normpath(path_value.strip()))


def _joined_text(reader: PdfReader) -> str:
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def _generate_pdf(
    tmp_path: Path,
    fighter_a: str,
    fighter_b: str,
    event_name: str,
    source_url: str,
) -> tuple[dict, PdfReader]:
    app.config["TESTING"] = True
    os.environ["BUTTON2_PDF_OUTPUT_ROOT"] = str(tmp_path)
    os.environ["BUTTON2_TEMPLATE_PACK_ROOT"] = DEFAULT_TEMPLATE_PACK_ROOT

    with app.test_client() as client:
        response = client.post(
            ROUTE,
            json={
                "operator_approved": True,
                "selected_matchup_preview": _preview_payload(
                    fighter_a,
                    fighter_b,
                    event_name,
                    source_url,
                ),
            },
        )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert payload.get("premium_template_render_used") is True
    assert str(payload.get("renderer_profile", "")).startswith("premium_template_pack_v29")
    assert _normalize_path(str(payload.get("template_pack_root", ""))) == _normalize_path(DEFAULT_TEMPLATE_PACK_ROOT)
    return payload, PdfReader(payload["output_path"])


def _assert_common_contract(data: dict, reader: PdfReader, fighter_a: str, fighter_b: str) -> None:
    assert len(reader.pages) == 24
    text = _joined_text(reader)
    lower_text = text.lower()

    for marker in REQUIRED_MARKERS:
        assert marker in text, f"Missing required marker: {marker}"

    for marker in FORBIDDEN_MARKERS:
        assert marker.lower() not in lower_text, f"Forbidden marker present: {marker}"

    assert fighter_a in text
    assert fighter_b in text

    assert data.get("pdf_open_url")
    assert OPEN_ROUTE in data["pdf_open_url"]
    assert data.get("output_filename")

    assert data.get("delivery_performed") is False
    assert data.get("external_api_delivery_performed") is False
    assert data.get("queue_write_performed") is False
    assert data.get("learning_apply_performed") is False
    assert data.get("calibration_write_performed") is False
    assert data.get("button3_mutation_performed") is False


def test_global_selected_matchup_template_path_regression_contract_v1(tmp_path):
    generated_rows = []
    app.config["TESTING"] = True
    os.environ["BUTTON2_PDF_OUTPUT_ROOT"] = str(tmp_path)
    os.environ["BUTTON2_TEMPLATE_PACK_ROOT"] = DEFAULT_TEMPLATE_PACK_ROOT

    for fighter_a, fighter_b, event_name, source_url in MATCHUPS:
        data, reader = _generate_pdf(tmp_path, fighter_a, fighter_b, event_name, source_url)
        _assert_common_contract(data, reader, fighter_a, fighter_b)
        generated_rows.append(data)

    with app.test_client() as client:
        library_response = client.get(LIBRARY_ROUTE)
        assert library_response.status_code == 200

        for item in generated_rows:
            open_response = client.get(
                OPEN_ROUTE,
                query_string={"filename": item["output_filename"]},
            )
            assert open_response.status_code == 200
