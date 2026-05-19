"""Button 2 selected-matchup live route/output path repair tests v1."""

from __future__ import annotations

import os
from pathlib import Path

from operator_dashboard.app import app
from operator_dashboard.button2_template_pack_asset_renderer_v1 import DEFAULT_TEMPLATE_PACK_ROOT

ROUTE = "/api/button2/selected-matchup/generate-guarded-v1"
OPEN_ROUTE = "/api/button2/generated-report/open"
LIBRARY_ROUTE = "/api/button2/generated-report/library"

MATCHUPS = [
    (
        "Rico Verhoeven",
        "Tariq Osaro",
        "GLORY 100",
        "https://www.glorykickboxing.com/events/glory-100",
    ),
    (
        "Nadaka Yoshinari",
        "Songchainoi Kiatsongrit",
        "ONE Samurai 1",
        "https://www.onefc.com/events/one-samurai-1",
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

FORBIDDEN = [
    "01 | PREMIUM COVER",
    "PREMIUM COVER",
    "Cover Page",
    "where the fight is owned",
    "where the fight can flip",
    "what the corner must solve",
    "SECTION LENS",
    "MODEL STATUS",
    "REPORT TYPE",
    "ROUND BAND",
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
        "matchup_id": f"{fighter_a.lower().replace(' ', '_')}_vs_{fighter_b.lower().replace(' ', '_')}",
    }


def _assert_governance_false(data: dict) -> None:
    assert data["delivery_performed"] is False
    assert data["external_api_delivery_performed"] is False
    assert data["queue_write_performed"] is False
    assert data["learning_apply_performed"] is False
    assert data["calibration_write_performed"] is False
    assert data["button3_mutation_performed"] is False


def test_selected_matchup_live_route_output_path_repair_v1(tmp_path):
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
                    "selected_matchup_preview": _preview_payload(
                        fighter_a,
                        fighter_b,
                        event_name,
                        source_url,
                    ),
                },
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data["ok"] is True

            # Selected-matchup integrity from response payload
            assert data["selected_matchup_fighter_a"] == fighter_a
            assert data["selected_matchup_fighter_b"] == fighter_b
            assert data["selected_matchup_event"] == event_name
            assert data["selected_matchup_id"]

            # Route/template diagnostics
            assert data["renderer_route_used"] == "template_pack_asset_renderer"
            assert data["renderer_profile"].startswith("premium_template_pack_v29")
            assert data["template_pack_root"] == DEFAULT_TEMPLATE_PACK_ROOT
            assert data["template_pack_asset_backed"] is True
            assert data["jbalia_layout_applied"] is True

            # Output freshness and file metadata
            assert data["generation_request_id"]
            assert data["output_path"]
            assert data["output_filename"]
            assert "_premium_" in data["output_filename"]
            assert data["output_filename"].endswith(".pdf")
            assert data["pdf_open_url"].endswith(data["output_filename"])
            assert data["generated_at"]
            assert data["file_modified_at"]
            assert isinstance(data["file_size_bytes"], int) and data["file_size_bytes"] > 0

            # Content and stale/fallback guards
            assert data["page_count"] == 24
            assert data["selected_matchup_matches_pdf_text"] is True
            assert data["stale_file_reused"] is False
            scan = data["text_scan_forbidden_markers"]
            assert scan["any_forbidden_found"] is False
            for marker in FORBIDDEN:
                assert scan["marker_hits"][marker] is False

            # Safe open route must return the exact generated file
            open_response = client.get(
                OPEN_ROUTE,
                query_string={"filename": data["output_filename"]},
            )
            assert open_response.status_code == 200

            _assert_governance_false(data)
            rows.append(data)

        # Library route must list the exact fresh generated filenames
        library = client.get(LIBRARY_ROUTE)
        assert library.status_code == 200
        library_html = library.data.decode("utf-8")
        for row in rows:
            assert row["output_filename"] in library_html

    # Confirm files were actually written under configured output root
    for row in rows:
        assert Path(row["output_path"]).exists()
        assert str(Path(row["output_path"]).parent) == str(tmp_path)
