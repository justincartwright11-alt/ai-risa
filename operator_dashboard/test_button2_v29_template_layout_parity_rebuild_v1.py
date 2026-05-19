from __future__ import annotations

import io
import json
import os
import zipfile
from pathlib import Path

from pypdf import PdfReader

from operator_dashboard import app as app_module
from operator_dashboard import button2_template_pack_asset_renderer_v1 as renderer


BATCH_ROUTE = "/api/button2/generate-selected-batch"


def _preview(event_name: str = "UFC 300", event_date: str = "2026-07-12"):
    return {
        "selected_matchup": {
            "fighter_a": "Alex Pereira",
            "fighter_b": "Jiri Prochazka",
            "event_name": event_name,
            "event_date": event_date,
            "promotion": "UFC",
            "source_url": "https://www.ufc.com/event/ufc-300",
            "source_type": "official",
        },
        "handoff_summary_preview": "Selected matchup handoff summary.",
        "source_traceability": [
            {
                "source_url": "https://www.ufc.com/event/ufc-300",
                "source_type": "official",
                "source_date": event_date,
            }
        ],
    }


def _extract_text(pdf_bytes: bytes):
    r = PdfReader(io.BytesIO(pdf_bytes))
    txt = "\n".join((p.extract_text() or "") for p in r.pages)
    return txt, len(r.pages)


def test_v29_template_zip_assets_detected():
    assets = renderer.resolve_template_pack_assets()
    assert Path(assets["pack_zip_sample"]).is_file()
    with zipfile.ZipFile(assets["pack_zip_sample"], "r") as z:
        names = set(z.namelist())
    assert "AI-RISA_Premium_Fight_Intelligence_Report_v29_bar_alignment_fix.pdf" in names
    assert "ai_risa_report_template_v29_bar_alignment_fix.py" in names


def test_v29_template_script_is_read_as_layout_contract():
    assets = renderer.resolve_template_pack_assets()
    script_path = Path(assets["module_path"])
    text = script_path.read_text(encoding="utf-8")
    assert "def cover(c):" in text
    assert "def executive(c):" in text
    assert "def radar(c):" in text
    assert "def trace_page(c):" in text
    assert "def disclaimer_page(c):" in text


def test_cover_layout_matches_v29_contract():
    out = renderer.render_button2_template_pack_asset_pdf(_preview())
    text, pages = _extract_text(out["pdf_bytes"])
    low = text.lower()
    assert pages == 24
    assert "premium fight" in low
    assert "intelligence report" in low
    assert "the intelligence beneath the violence" in low
    assert "vs" in low


def test_dashboard_layout_matches_v29_contract():
    out = renderer.render_button2_template_pack_asset_pdf(_preview())
    text, _ = _extract_text(out["pdf_bytes"])
    low = text.lower()
    assert "02 | executive command dashboard" in low
    assert "headline prediction" in low
    assert "fight control intelligence strip" in low
    assert "method probability" in low
    assert "risk control" in low


def test_radar_page_uses_page_05_not_page_04():
    out = renderer.render_button2_template_pack_asset_pdf(_preview())
    text, _ = _extract_text(out["pdf_bytes"])
    low = text.lower()
    assert "05 | fighter architecture radar" in low
    assert "page 05" in low


def test_generated_report_has_v29_cover_markers():
    out = renderer.render_button2_template_pack_asset_pdf(_preview())
    text, _ = _extract_text(out["pdf_bytes"])
    low = text.lower()
    assert "executive command dashboard" in low
    assert "fighter architecture radar" in low
    assert "tactical edge map" in low


def test_generated_report_rejects_plain_cover_layout():
    selected = {
        "fighter_a": "alex pereira",
        "fighter_b": "jiri prochazka",
        "event_name": "ufc 300",
        "event_date": "2026-07-12",
        "source_url": "https://www.ufc.com/event/ufc-300",
    }
    fake_text = "main narrative\nplain boxes\npage 24"
    ok, violations = app_module._selected_matchup_passes_strict_pdf_quality_gate(
        selected,
        {"output_path": __file__, "output_filename": "alex_pereira_vs_jiri_prochazka_ufc_300.pdf", "report_id": "alex_pereira_jiri_prochazka_ufc_300"},
        fake_text,
        24,
    )
    assert ok is False
    assert any(v.startswith("v29_layout_") for v in violations)


def test_generated_report_rejects_unknown_event():
    selected = {
        "fighter_a": "alex pereira",
        "fighter_b": "jiri prochazka",
        "event_name": "ufc 300",
        "event_date": "2026-07-12",
        "source_url": "https://www.ufc.com/event/ufc-300",
    }
    fake_text = "unknown event | n/a | customer ready"
    ok, violations = app_module._selected_matchup_passes_strict_pdf_quality_gate(
        selected,
        {"output_path": __file__, "output_filename": "alex_pereira_vs_jiri_prochazka_ufc_300.pdf", "report_id": "alex_pereira_jiri_prochazka_ufc_300"},
        fake_text,
        24,
    )
    assert ok is False
    assert "event_binding_unknown_event_in_pdf" in violations


def test_generated_report_rejects_template_sample_fighter_bleed():
    selected = {
        "fighter_a": "alex pereira",
        "fighter_b": "jiri prochazka",
        "event_name": "ufc 300",
        "event_date": "2026-07-12",
        "source_url": "https://www.ufc.com/event/ufc-300",
    }
    fake_text = "bahram rajabzadeh vs donovan wisse"
    ok, violations = app_module._selected_matchup_passes_strict_pdf_quality_gate(
        selected,
        {"output_path": __file__, "output_filename": "alex_pereira_vs_jiri_prochazka_ufc_300.pdf", "report_id": "alex_pereira_jiri_prochazka_ufc_300"},
        fake_text,
        24,
    )
    assert ok is False
    assert any(v.startswith("stale_pair_present:") for v in violations)


def test_customer_ready_false_when_v29_layout_gate_fails(monkeypatch, tmp_path):
    os.environ["BUTTON2_PDF_OUTPUT_ROOT"] = str(tmp_path)

    row = {
        "matchup_id": "ufc_300_alex_pereira_vs_jiri_prochazka",
        "event_name": "UFC 300",
        "event_date": "2026-07-12",
        "promotion": "UFC",
        "fighter_a": "Alex Pereira",
        "fighter_b": "Jiri Prochazka",
        "source_url": "https://www.ufc.com/event/ufc-300",
        "source_type": "official",
        "button2_readiness_status": "ready_for_button2_generation",
        "report_ready_status": "ready_for_button2_generation",
        "selected_for_button2": True,
    }
    monkeypatch.setattr(app_module, "load_button2_queue_readonly", lambda: [row])

    out_path = tmp_path / "test.pdf"
    out_path.write_bytes(b"%PDF-1.4\n")

    monkeypatch.setattr(
        app_module,
        "generate_button2_report_render_gate_integration",
        lambda _p: {
            "ok": True,
            "output_path": str(out_path),
            "output_filename": "alex_pereira_vs_jiri_prochazka_ufc_300.pdf",
            "report_id": "alex_pereira_jiri_prochazka_ufc_300",
            "renderer_route_used": "template_pack_asset_renderer",
            "renderer_profile": "premium_template_pack_v29_layout_parity_rebuild_v1",
            "template_pack_asset_backed": True,
            "delivery_performed": False,
            "external_api_delivery_performed": False,
            "queue_write_performed": False,
            "learning_apply_performed": False,
            "calibration_write_performed": False,
            "button3_mutation_performed": False,
        },
    )
    monkeypatch.setattr(app_module, "_extract_pdf_text_and_page_count", lambda _p: ("main narrative", 24))

    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as client:
        resp = client.post(BATCH_ROUTE, json={"operator_approval": True, "selected_matchup_ids": [row["matchup_id"]]})
        data = resp.get_json()

    assert data["results"][0]["customer_ready"] is False
    assert data["results"][0]["visual_gate_status"] == "v29_template_layout_parity_failed"


def test_bulk_generation_contract_still_passes(monkeypatch, tmp_path):
    os.environ["BUTTON2_PDF_OUTPUT_ROOT"] = str(tmp_path)

    rows = [
        {
            "matchup_id": "ufc_300_alex_pereira_vs_jiri_prochazka",
            "event_name": "UFC 300",
            "event_date": "2026-07-12",
            "promotion": "UFC",
            "fighter_a": "Alex Pereira",
            "fighter_b": "Jiri Prochazka",
            "source_url": "https://www.ufc.com/event/ufc-300",
            "source_type": "official",
            "button2_readiness_status": "ready_for_button2_generation",
            "report_ready_status": "ready_for_button2_generation",
            "selected_for_button2": True,
        },
        {
            "matchup_id": "ufc_300_islam_makhachev_vs_dustin_poirier",
            "event_name": "UFC 300",
            "event_date": "2026-07-12",
            "promotion": "UFC",
            "fighter_a": "Islam Makhachev",
            "fighter_b": "Dustin Poirier",
            "source_url": "https://www.ufc.com/event/ufc-300",
            "source_type": "official",
            "button2_readiness_status": "ready_for_button2_generation",
            "report_ready_status": "ready_for_button2_generation",
            "selected_for_button2": True,
        },
    ]
    monkeypatch.setattr(app_module, "load_button2_queue_readonly", lambda: rows)

    def _gen(payload):
        out_path = tmp_path / (payload["output_filename_override"])
        out_path.write_bytes(b"%PDF-1.4\n")
        return {
            "ok": True,
            "output_path": str(out_path),
            "output_filename": payload["output_filename_override"],
            "report_id": payload["fight_id"],
            "renderer_route_used": "template_pack_asset_renderer",
            "renderer_profile": "premium_template_pack_v29_layout_parity_rebuild_v1",
            "template_pack_asset_backed": True,
            "delivery_performed": False,
            "external_api_delivery_performed": False,
            "queue_write_performed": False,
            "learning_apply_performed": False,
            "calibration_write_performed": False,
            "button3_mutation_performed": False,
        }

    monkeypatch.setattr(app_module, "generate_button2_report_render_gate_integration", _gen)
    monkeypatch.setattr(
        app_module,
        "_extract_pdf_text_and_page_count",
        lambda _p: (
            "premium fight intelligence report the intelligence beneath the violence "
            "02 | executive command dashboard 05 | fighter architecture radar page 05 "
            "14 | round-by-round control projection 15 | scenario tree / method pathways "
            "23 | traceability / source map 24 | disclaimer / risk control "
            "executive command dashboard fighter architecture radar tactical edge map "
            "traceability source map disclaimer risk control "
            "ufc 300 2026-07-12 https://www.ufc.com/event/ufc-300",
            24,
        ),
    )
    monkeypatch.setattr(app_module, "_scan_forbidden_markers", lambda _t: {"any_forbidden_found": False, "forbidden_hits": []})
    monkeypatch.setattr(app_module, "_selected_matchup_passes_strict_pdf_quality_gate", lambda *_a, **_k: (True, []))

    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as client:
        resp = client.post(
            BATCH_ROUTE,
            json={
                "operator_approval": True,
                "selected_matchup_ids": [r["matchup_id"] for r in rows],
            },
        )
        data = resp.get_json()

    assert data["ok"] is True
    assert data["generated_count"] == 2
    assert data["failed_count"] == 0


def test_governance_flags_remain_false(monkeypatch, tmp_path):
    os.environ["BUTTON2_PDF_OUTPUT_ROOT"] = str(tmp_path)

    row = {
        "matchup_id": "ufc_300_alex_pereira_vs_jiri_prochazka",
        "event_name": "UFC 300",
        "event_date": "2026-07-12",
        "promotion": "UFC",
        "fighter_a": "Alex Pereira",
        "fighter_b": "Jiri Prochazka",
        "source_url": "https://www.ufc.com/event/ufc-300",
        "source_type": "official",
        "button2_readiness_status": "ready_for_button2_generation",
        "report_ready_status": "ready_for_button2_generation",
        "selected_for_button2": True,
    }
    monkeypatch.setattr(app_module, "load_button2_queue_readonly", lambda: [row])

    def _gen(payload):
        out_path = tmp_path / payload["output_filename_override"]
        out_path.write_bytes(b"%PDF-1.4\n")
        return {
            "ok": True,
            "output_path": str(out_path),
            "output_filename": payload["output_filename_override"],
            "report_id": payload["fight_id"],
            "renderer_route_used": "template_pack_asset_renderer",
            "renderer_profile": "premium_template_pack_v29_layout_parity_rebuild_v1",
            "template_pack_asset_backed": True,
            "delivery_performed": False,
            "external_api_delivery_performed": False,
            "queue_write_performed": False,
            "learning_apply_performed": False,
            "calibration_write_performed": False,
            "button3_mutation_performed": False,
        }

    monkeypatch.setattr(app_module, "generate_button2_report_render_gate_integration", _gen)
    monkeypatch.setattr(
        app_module,
        "_extract_pdf_text_and_page_count",
        lambda _p: (
            "premium fight intelligence report the intelligence beneath the violence "
            "02 | executive command dashboard 05 | fighter architecture radar page 05 "
            "14 | round-by-round control projection 15 | scenario tree / method pathways "
            "23 | traceability / source map 24 | disclaimer / risk control "
            "executive command dashboard fighter architecture radar tactical edge map "
            "traceability source map disclaimer risk control "
            "ufc 300 2026-07-12 https://www.ufc.com/event/ufc-300",
            24,
        ),
    )
    monkeypatch.setattr(app_module, "_scan_forbidden_markers", lambda _t: {"any_forbidden_found": False, "forbidden_hits": []})
    monkeypatch.setattr(app_module, "_selected_matchup_passes_strict_pdf_quality_gate", lambda *_a, **_k: (True, []))

    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as client:
        resp = client.post(BATCH_ROUTE, json={"operator_approval": True, "selected_matchup_ids": [row["matchup_id"]]})
        data = resp.get_json()

    result = data["results"][0]
    assert result.get("delivery_performed", False) is False
    assert result.get("external_api_delivery_performed", False) is False
    assert result.get("learning_apply_performed", False) is False
    assert result.get("calibration_write_performed", False) is False
    assert result.get("button3_mutation_performed", False) is False
