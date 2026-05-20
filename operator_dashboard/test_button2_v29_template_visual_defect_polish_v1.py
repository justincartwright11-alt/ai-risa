from __future__ import annotations

import io
import os
from pathlib import Path

import pytest
from pypdf import PdfReader

from operator_dashboard import app as app_module
from operator_dashboard import button2_template_pack_asset_renderer_v1 as renderer


BATCH_ROUTE = "/api/button2/generate-selected-batch"


def _preview(
    fighter_a: str = "Bo Nickal",
    fighter_b: str = "Cody Brundage",
    event_name: str = "UFC 300",
    event_date: str = "2026-07-12",
    source_url: str = "https://www.ufc.com/event/ufc-300",
):
    return {
        "selected_matchup": {
            "fighter_a": fighter_a,
            "fighter_b": fighter_b,
            "event_name": event_name,
            "event_date": event_date,
            "promotion": "UFC",
            "source_url": source_url,
            "source_type": "official",
        },
        "handoff_summary_preview": "Selected matchup handoff summary.",
        "source_traceability": [
            {
                "source_url": source_url,
                "source_type": "official",
                "source_date": event_date,
            }
        ],
    }


def _extract_text(pdf_bytes: bytes):
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = "\n".join((page.extract_text() or "") for page in reader.pages)
    return text, len(reader.pages)


def _premium_text_for(selected: dict):
    return (
        f"{selected['fighter_a']} vs {selected['fighter_b']}\n"
        f"Event: {selected['event_name']}\n"
        f"Event Date: {selected['event_date']}\n"
        f"Source: {selected['source_url']}\n"
        "PREMIUM FIGHT\n"
        "INTELLIGENCE REPORT\n"
        "THE INTELLIGENCE BENEATH THE VIOLENCE\n"
        "02 | EXECUTIVE COMMAND DASHBOARD\n"
        "CONTROL ZONE\n"
        "DANGER ZONE\n"
        "COLLAPSE TRIGGER\n"
        "FIGHT CONTROL INTELLIGENCE STRIP\n"
        "ROUND CONTROL PROJECTION\n"
        "METHOD PROBABILITY\n"
        "RISK CONTROL\n"
        "05 | FIGHTER ARCHITECTURE RADAR\n"
        "PAGE 05\n"
        "FATIGUE FAILURE POINTS\n"
        "FAILURE RAIL\n"
        "SIGNAL\n"
        "LATE RISK\n"
        "14 | ROUND-BY-ROUND CONTROL PROJECTION\n"
        "15 | SCENARIO TREE / METHOD PATHWAYS\n"
        "23 | TRACEABILITY / SOURCE MAP\n"
        "SOURCE CHAIN\n"
        "FIGHT ID\n"
        "EVENT DATE\n"
        "SPORT\n"
        "PROMOTION\n"
        "REPORT ID\n"
        "SOURCE DISCIPLINE STATEMENT\n"
        "24 | DISCLAIMER / RISK CONTROL\n"
        "NO GUARANTEE\n"
        "NO FINANCIAL ADVICE\n"
        "COMBAT RISK\n"
        "NEVER OVER-WAGER\n"
        "EXECUTIVE COMMAND DASHBOARD\n"
        "FIGHTER ARCHITECTURE RADAR\n"
        "TACTICAL EDGE MAP\n"
        "SCENARIO TREE / METHOD PATHWAYS\n"
        "TRACEABILITY / SOURCE MAP\n"
        "DISCLAIMER / RISK CONTROL\n"
    )


def _queue_rows():
    return [
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
    ]


def test_logo_uses_blended_asset_not_black_tile():
    out = renderer.render_button2_template_pack_asset_pdf(_preview())
    safety = out.get("layout_safety", {})
    asset = str(safety.get("logo_asset") or "").lower()
    assert safety.get("logo_blend_ok") is True
    assert safety.get("logo_black_tile_risk") is False
    assert any(name in asset for name in ["clean_blend", "watermark_blend", "ai-risa logo.png"])


def test_bottom_risk_cards_do_not_use_footer_collision_y_positions():
    out = renderer.render_button2_template_pack_asset_pdf(_preview())
    safety = out.get("layout_safety", {})
    footer_pages = safety.get("footer_safe_zone_pages", {})
    for key in ("6", "16", "17"):
        page_info = footer_pages.get(key, {})
        assert page_info.get("safe") is True
        assert float(page_info.get("card_min_y", 0.0)) >= float(page_info.get("safe_zone_y", 9999.0))


def test_page_6_footer_safe_zone_preserved():
    out = renderer.render_button2_template_pack_asset_pdf(_preview())
    page_info = out.get("layout_safety", {}).get("footer_safe_zone_pages", {}).get("6", {})
    assert page_info.get("safe") is True


def test_page_16_footer_safe_zone_preserved():
    out = renderer.render_button2_template_pack_asset_pdf(_preview())
    page_info = out.get("layout_safety", {}).get("footer_safe_zone_pages", {}).get("16", {})
    assert page_info.get("safe") is True


def test_page_17_footer_safe_zone_preserved():
    out = renderer.render_button2_template_pack_asset_pdf(_preview())
    page_info = out.get("layout_safety", {}).get("footer_safe_zone_pages", {}).get("17", {})
    assert page_info.get("safe") is True


def test_source_map_rows_are_vertically_separated():
    out = renderer.render_button2_template_pack_asset_pdf(_preview())
    source_map = out.get("layout_safety", {}).get("source_map", {})
    assert source_map.get("rows_separated") is True


def test_source_map_long_report_id_wraps_or_fits():
    out = renderer.render_button2_template_pack_asset_pdf(
        _preview(
            fighter_a="Maximillian Alexander Holloway The Third",
            fighter_b="Justin Xavier Gaethje The Highlight",
            event_name="Ultimate Championship Long Form Event Name For Layout Stress Validation",
        )
    )
    source_map = out.get("layout_safety", {}).get("source_map", {})
    rows = source_map.get("rows", [])
    report_rows = [r for r in rows if r.get("label") == "REPORT ID"]
    assert report_rows
    assert report_rows[0].get("line_count", 1) >= 1
    assert source_map.get("rows_separated") is True


def test_source_url_row_does_not_overlap_source_statement():
    out = renderer.render_button2_template_pack_asset_pdf(
        _preview(source_url="https://www.ufc.com/event/ufc-300/very/long/path/that/tests/source/url/wrapping/safety/for/page/23")
    )
    source_map = out.get("layout_safety", {}).get("source_map", {})
    assert source_map.get("source_url_statement_separated") is True


def test_visual_defect_gate_blocks_customer_ready_when_layout_safety_fails(monkeypatch, tmp_path):
    os.environ["BUTTON2_PDF_OUTPUT_ROOT"] = str(tmp_path)
    row = _queue_rows()[0]
    monkeypatch.setattr(app_module, "load_button2_queue_readonly", lambda: [row])

    out_path = tmp_path / "bo_nickal_vs_cody_brundage.pdf"
    out_path.write_bytes(b"%PDF-1.4\n")
    premium_text = _premium_text_for({
        "fighter_a": row["fighter_a"],
        "fighter_b": row["fighter_b"],
        "event_name": row["event_name"],
        "event_date": row["event_date"],
        "source_url": row["source_url"],
    })

    monkeypatch.setattr(app_module, "_extract_pdf_text_and_page_count", lambda _p: (premium_text, 24))
    monkeypatch.setattr(
        app_module,
        "generate_button2_report_render_gate_integration",
        lambda _payload: {
            "ok": True,
            "output_path": str(out_path),
            "output_filename": "bo_nickal_vs_cody_brundage_ufc_300.pdf",
            "report_id": "bo_nickal_vs_cody_brundage_ufc_300",
            "renderer_route_used": "template_pack_asset_renderer",
            "renderer_profile": "premium_template_pack_v29_layout_parity_rebuild_v1",
            "template_pack_asset_backed": True,
            "layout_safety": {
                "logo_blend_ok": False,
                "logo_black_tile_risk": True,
                "footer_safe_zone_pages": {
                    "6": {"safe": False},
                    "16": {"safe": False},
                    "17": {"safe": False},
                },
                "source_map": {
                    "rows_separated": False,
                    "source_url_statement_separated": False,
                },
            },
            "delivery_performed": False,
            "external_api_delivery_performed": False,
            "queue_write_performed": False,
            "learning_apply_performed": False,
            "calibration_write_performed": False,
            "button3_mutation_performed": False,
        },
    )

    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as client:
        resp = client.post(BATCH_ROUTE, json={"operator_approval": True, "selected_matchup_ids": [row["matchup_id"]]})
        data = resp.get_json()

    assert resp.status_code == 200
    assert data["results"][0]["customer_ready"] is False
    assert data["results"][0]["visual_gate_status"] == "v29_visual_defect_failed"


def test_sample_bleed_gate_still_passes_for_clean_selected_row(tmp_path):
    os.environ["BUTTON2_PDF_OUTPUT_ROOT"] = str(tmp_path)
    out_path = tmp_path / "bo_nickal_vs_cody_brundage_ufc_300.pdf"
    out_path.write_bytes(b"%PDF-1.4\n")
    selected = {
        "fighter_a": "Bo Nickal",
        "fighter_b": "Cody Brundage",
        "event_name": "UFC 300",
        "event_date": "2026-07-12",
        "source_url": "https://www.ufc.com/event/ufc-300",
    }
    fake_text = _premium_text_for(selected)
    ok, violations = app_module._selected_matchup_passes_strict_pdf_quality_gate(
        selected,
        {"output_path": str(out_path), "output_filename": "bo_nickal_vs_cody_brundage_ufc_300.pdf", "report_id": "bo_nickal_vs_cody_brundage_ufc_300"},
        fake_text,
        24,
        {
            "logo_blend_ok": True,
            "logo_black_tile_risk": False,
            "footer_safe_zone_pages": {
                "6": {"safe": True},
                "16": {"safe": True},
                "17": {"safe": True},
            },
            "source_map": {"rows_separated": True, "source_url_statement_separated": True},
        },
    )
    assert ok is True
    assert not any(str(v).startswith("template_sample_bleed_present:") for v in violations)


def test_event_binding_gate_still_passes_for_clean_selected_row(tmp_path):
    os.environ["BUTTON2_PDF_OUTPUT_ROOT"] = str(tmp_path)
    out_path = tmp_path / "sean_strickland_vs_dricus_du_plessis_ufc_304.pdf"
    out_path.write_bytes(b"%PDF-1.4\n")
    selected = {
        "fighter_a": "Sean Strickland",
        "fighter_b": "Dricus du Plessis",
        "event_name": "UFC 304",
        "event_date": "2026-07-27",
        "source_url": "https://www.ufc.com/event/ufc-304",
    }
    fake_text = _premium_text_for(selected)
    ok, violations = app_module._selected_matchup_passes_strict_pdf_quality_gate(
        selected,
        {"output_path": str(out_path), "output_filename": "sean_strickland_vs_dricus_du_plessis_ufc_304.pdf", "report_id": "sean_strickland_vs_dricus_du_plessis_ufc_304"},
        fake_text,
        24,
        {
            "logo_blend_ok": True,
            "logo_black_tile_risk": False,
            "footer_safe_zone_pages": {
                "6": {"safe": True},
                "16": {"safe": True},
                "17": {"safe": True},
            },
            "source_map": {"rows_separated": True, "source_url_statement_separated": True},
        },
    )
    assert ok is True
    assert "event_binding_incomplete_no_event_name" not in violations
    assert "event_binding_incomplete_no_event_date" not in violations


def test_bulk_generation_contract_still_passes(monkeypatch, tmp_path):
    os.environ["BUTTON2_PDF_OUTPUT_ROOT"] = str(tmp_path)
    rows = _queue_rows()
    monkeypatch.setattr(app_module, "load_button2_queue_readonly", lambda: rows)

    text_by_path = {}

    def _generate(payload):
        selected = payload["ingest_payload"]["selected_matchup_payload"]
        out_name = payload["output_filename_override"]
        out_path = Path(tmp_path) / out_name
        out_path.write_bytes(b"%PDF-1.4\n")
        text_by_path[str(out_path)] = _premium_text_for(selected)
        return {
            "ok": True,
            "output_path": str(out_path),
            "output_filename": out_name,
            "report_id": payload["fight_id"],
            "renderer_route_used": "template_pack_asset_renderer",
            "renderer_profile": "premium_template_pack_v29_layout_parity_rebuild_v1",
            "template_pack_asset_backed": True,
            "layout_safety": {
                "logo_blend_ok": True,
                "logo_black_tile_risk": False,
                "footer_safe_zone_pages": {
                    "6": {"safe": True},
                    "16": {"safe": True},
                    "17": {"safe": True},
                },
                "source_map": {"rows_separated": True, "source_url_statement_separated": True},
            },
            "delivery_performed": False,
            "external_api_delivery_performed": False,
            "queue_write_performed": False,
            "learning_apply_performed": False,
            "calibration_write_performed": False,
            "button3_mutation_performed": False,
        }

    monkeypatch.setattr(app_module, "generate_button2_report_render_gate_integration", _generate)
    monkeypatch.setattr(app_module, "_extract_pdf_text_and_page_count", lambda p: (text_by_path.get(str(p), ""), 24))

    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as client:
        resp = client.post(BATCH_ROUTE, json={
            "operator_approval": True,
            "selected_matchup_ids": [rows[0]["matchup_id"], rows[1]["matchup_id"]],
        })
        data = resp.get_json()

    assert resp.status_code == 200
    assert data["generated_count"] == 2
    assert data["failed_count"] == 0
