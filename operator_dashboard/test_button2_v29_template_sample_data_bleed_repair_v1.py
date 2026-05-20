from __future__ import annotations

import io
import os
from pathlib import Path

from pypdf import PdfReader

from operator_dashboard import app as app_module
from operator_dashboard import button2_template_pack_asset_renderer_v1 as renderer


BATCH_ROUTE = "/api/button2/generate-selected-batch"


def _preview(event_name: str = "UFC 304", event_date: str = "2026-07-27"):
    return {
        "selected_matchup": {
            "fighter_a": "Sean Strickland",
            "fighter_b": "Dricus du Plessis",
            "event_name": event_name,
            "event_date": event_date,
            "promotion": "UFC",
            "source_url": "https://www.ufc.com/event/ufc-304",
            "source_type": "official",
        },
        "handoff_summary_preview": "Selected matchup handoff summary.",
        "source_traceability": [
            {
                "source_url": "https://www.ufc.com/event/ufc-304",
                "source_type": "official",
                "source_date": event_date,
            }
        ],
    }


def _page_texts(pdf_bytes: bytes):
    reader = PdfReader(io.BytesIO(pdf_bytes))
    return [(page.extract_text() or "").lower() for page in reader.pages]


def _render_texts():
    return _page_texts(renderer.render_button2_template_pack_asset_pdf(_preview())["pdf_bytes"])


def _queue_rows():
    return [
        {
            "matchup_id": "ufc_304_sean_strickland_dricus_du_plessis",
            "event_id": "ufc_304",
            "event_name": "UFC 304",
            "event_date": "2026-07-27",
            "promotion": "UFC",
            "fighter_a": "Sean Strickland",
            "fighter_b": "Dricus du Plessis",
            "weight_class": "Middleweight",
            "bout_order": 1,
            "source_url": "https://www.ufc.com/event/ufc-304",
            "source_type": "official",
            "provenance_status": "source_backed_ready",
            "button2_readiness_status": "ready_for_button2_generation",
            "report_ready_status": "ready_for_button2_generation",
            "customer_ready_possible": True,
            "blocked_reason": "",
            "selected_for_button2": True,
        },
        {
            "matchup_id": "ufc_300_bo_nickal_vs_cody_brundage",
            "event_id": "ufc_300",
            "event_name": "UFC 300",
            "event_date": "2026-07-12",
            "promotion": "UFC",
            "fighter_a": "Bo Nickal",
            "fighter_b": "Cody Brundage",
            "weight_class": "Middleweight",
            "bout_order": 4,
            "source_url": "https://www.ufc.com/event/ufc-300",
            "source_type": "official",
            "provenance_status": "source_backed_ready",
            "button2_readiness_status": "ready_for_button2_generation",
            "report_ready_status": "ready_for_button2_generation",
            "customer_ready_possible": True,
            "blocked_reason": "",
            "selected_for_button2": True,
        },
    ]


def _post_generate(client, selected_ids):
    return client.post(
        BATCH_ROUTE,
        json={"operator_approval": True, "selected_matchup_ids": selected_ids},
    )


def _real_generator(monkeypatch, tmp_path):
    calls = []

    def _generate(payload):
        calls.append(payload)
        ingest_payload = payload["ingest_payload"]
        report_context_preview = {
            "selected_matchup": ingest_payload.get("selected_matchup_payload", {}),
            "handoff_summary_preview": ingest_payload.get("dossier_summary_preview", "Selected matchup handoff summary."),
            "source_traceability": ingest_payload.get("source_traceability_sources", []),
        }
        pdf = renderer.render_button2_template_pack_asset_pdf(report_context_preview)
        out_name = payload["output_filename_override"]
        out_path = Path(tmp_path) / out_name
        out_path.write_bytes(pdf["pdf_bytes"])
        return {
            "ok": True,
            "output_path": str(out_path),
            "output_filename": out_name,
            "report_id": payload["fight_id"],
            "renderer_route_used": "template_pack_asset_renderer",
            "renderer_profile": pdf["renderer_profile"],
            "template_pack_asset_backed": True,
            "delivery_performed": False,
            "external_api_delivery_performed": False,
            "queue_write_performed": False,
            "learning_apply_performed": False,
            "calibration_write_performed": False,
            "button3_mutation_performed": False,
        }

    monkeypatch.setattr(app_module, "generate_button2_report_render_gate_integration", _generate)
    return calls


def test_cover_uses_selected_fighters_not_v29_sample_names():
    texts = _render_texts()
    page = texts[0]
    assert "sean strickland" in page
    assert "dricus du plessis" in page
    assert "bahram rajabzadeh" not in page
    assert "donovan wisse" not in page


def test_dashboard_uses_selected_fighters_not_v29_sample_names():
    texts = _render_texts()
    page = texts[1]
    assert "sean strickland" in page
    assert "dricus du plessis" in page
    assert "rajabzadeh owns disruption" not in page
    assert "wisse owns structure" not in page


def test_radar_uses_selected_fighters_not_v29_sample_names():
    texts = _render_texts()
    page = texts[4]
    assert "05 | fighter architecture radar" in page
    assert "sean strickland" in page
    assert "dricus du plessis" in page
    assert "rajabzadeh" not in page
    assert "wisse" not in page


def test_tactical_edge_uses_selected_fighters_not_v29_sample_names():
    texts = _render_texts()
    page = texts[5]
    assert "sean strickland" in page
    assert "dricus du plessis" in page
    assert "fighter a" not in page
    assert "fighter b" not in page


def test_round_projection_uses_selected_fighters_not_v29_sample_names():
    texts = _render_texts()
    page = texts[13]
    assert "14 | round-by-round control projection" in page
    assert "rajabzadeh" not in page
    assert "wisse" not in page


def test_scenario_tree_uses_selected_fighters_not_v29_sample_names():
    texts = _render_texts()
    page = texts[14]
    assert "scenario tree / method pathways" in page
    assert "sean strickland" in page
    assert "dricus du plessis" in page
    assert "rajabzadeh" not in page
    assert "wisse" not in page


def test_sample_bleed_gate_blocks_customer_ready():
    selected = {
        "fighter_a": "Sean Strickland",
        "fighter_b": "Dricus du Plessis",
        "event_name": "UFC 304",
        "event_date": "2026-07-27",
        "source_url": "https://www.ufc.com/event/ufc-304",
    }
    fake_text = "bahram rajabzadeh vs donovan wisse | aggressive power striker | technical counter striker"
    ok, violations = app_module._selected_matchup_passes_strict_pdf_quality_gate(
        selected,
        {"output_path": __file__, "output_filename": "sean_strickland_vs_dricus_du_plessis_ufc_304.pdf", "report_id": "sean_strickland_dricus_du_plessis_ufc_304"},
        fake_text,
        24,
    )
    assert ok is False
    assert any(v.startswith("template_sample_bleed_present:") for v in violations)


def test_selected_matchup_source_map_still_correct():
    texts = _render_texts()
    page = texts[22]
    assert "traceability / source map" in page
    assert "report id" in page
    assert "ufc 304" in page
    assert "2026-07-27" in page


def test_v29_layout_markers_still_present():
    texts = _render_texts()
    assert "premium fight" in texts[0]
    assert "02 | executive command dashboard" in texts[1]
    assert "05 | fighter architecture radar" in texts[4]
    assert "14 | round-by-round control projection" in texts[13]
    assert "15 | scenario tree / method pathways" in texts[14]
    assert "23 | traceability / source map" in texts[22]
    assert "24 | disclaimer / risk control" in texts[23]


def test_bulk_generation_contract_still_passes(monkeypatch, tmp_path):
    os.environ["BUTTON2_PDF_OUTPUT_ROOT"] = str(tmp_path)
    monkeypatch.setattr(app_module, "load_button2_queue_readonly", _queue_rows)
    calls = _real_generator(monkeypatch, tmp_path)

    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as client:
        resp = _post_generate(client, [
            "ufc_304_sean_strickland_dricus_du_plessis",
            "ufc_300_bo_nickal_vs_cody_brundage",
        ])
        data = resp.get_json()

    assert resp.status_code == 200
    assert data["generated_count"] == 2
    assert data["failed_count"] == 0
    assert len(calls) == 2


def test_governance_flags_remain_false(monkeypatch, tmp_path):
    os.environ["BUTTON2_PDF_OUTPUT_ROOT"] = str(tmp_path)
    monkeypatch.setattr(app_module, "load_button2_queue_readonly", _queue_rows)
    _real_generator(monkeypatch, tmp_path)

    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as client:
        resp = _post_generate(client, ["ufc_304_sean_strickland_dricus_du_plessis"])
        data = resp.get_json()

    result = data["results"][0]
    assert data["delivery_performed"] is False
    assert data["external_api_delivery_performed"] is False
    assert data["queue_write_performed"] is False
    assert data["learning_apply_performed"] is False
    assert data["calibration_write_performed"] is False
    assert data["button3_mutation_performed"] is False
    assert result["customer_ready"] is True
    assert result["visual_gate_status"] == "premium_template_confirmed"
