from __future__ import annotations

import os
from pathlib import Path

from operator_dashboard import app as app_module
from operator_dashboard import button2_template_pack_asset_renderer_v1 as renderer
from operator_dashboard.test_button2_v29_template_final_delivery_visual_cleanup_v7 import (
    BATCH_ROUTE,
    _layout_safety_stub_v7,
    _preview,
    _queue_rows,
    _render_output,
    _run,
    _success_text_for_selected,
)


def _rectangles_overlap(a, b):
    return (
        a["x"] < b["x"] + b["w"]
        and a["x"] + a["w"] > b["x"]
        and a["y"] < b["y"] + b["h"]
        and a["y"] + a["h"] > b["y"]
    )


def _right_rail_panels(module):
    return [panel for panel in module.panel_calls if panel["x"] > (module.PAGE_W / 2)]


def test_page_2_fight_control_strip_and_lower_row_do_not_overlap():
    module, _canvas, blocks = _run(renderer._draw_executive)
    assert blocks["_layout_safety"].get("page_2_strip_collision_passed") is True
    assert blocks["_layout_safety"].get("page_2_lower_modules_no_strip_overlap_passed") is True

    strip_cards = [panel for panel in module.panel_calls if abs(panel["h"] - 35.0) < 0.2]
    lower_row_panels = [panel for panel in module.panel_calls if abs(panel["h"] - 80.0) < 0.2 and panel["y"] > 150]
    assert strip_cards, "Fight control strip cards were not found"
    assert lower_row_panels, "Lower row modules were not found"
    strip_bottom = max(card["y"] + card["h"] for card in strip_cards)
    assert min(panel["y"] for panel in lower_row_panels) >= strip_bottom + 8


def test_page_2_lower_modules_clear_footer_safe_zone():
    module, _canvas, blocks = _run(renderer._draw_executive)
    assert blocks["_layout_safety"].get("page_2_footer_safe_passed") is True
    footer_safe_zone_y = module.FOOTER_Y + renderer.FOOTER_SAFE_ZONE_Y
    lower_row_top = min(panel["y"] for panel in module.panel_calls if abs(panel["h"] - 80.0) < 0.2 and panel["y"] > 150)
    assert lower_row_top >= footer_safe_zone_y + 12


def test_page_2_lower_modules_center_as_one_row():
    module, _canvas, blocks = _run(renderer._draw_executive)
    cards = sorted(
        [panel for panel in module.panel_calls if abs(panel["h"] - 80.0) < 0.2 and panel["y"] > 150],
        key=lambda item: item["x"],
    )
    assert len(cards) == 3
    assert max(card["y"] for card in cards) - min(card["y"] for card in cards) < 1.0
    row_right = cards[-1]["x"] + cards[-1]["w"]
    assert row_right <= module.PAGE_W - 8
    assert blocks["_layout_safety"].get("page_2_strip_collision_passed") is True


def test_page_5_right_rail_panels_do_not_overlap():
    module, _canvas, blocks = _run(renderer._draw_fighter_architecture_radar)
    panels = _right_rail_panels(module)
    assert len(panels) >= 3
    for i, panel_a in enumerate(panels):
        for panel_b in panels[i + 1 :]:
            assert not _rectangles_overlap(panel_a, panel_b), f"Right rail panels overlapped: {panel_a} vs {panel_b}"
    assert blocks["_layout_safety"].get("page_5_side_panel_fit_passed") is True


def test_page_5_customer_meaning_heading_body_do_not_overlap():
    module, _canvas, blocks = _run(renderer._draw_fighter_architecture_radar)
    customer_panel = next(
        panel
        for panel in module.panel_calls
        if panel["x"] > (module.PAGE_W / 2) and panel["h"] >= 84 and panel["y"] > 150 and panel["y"] < 260
    )
    customer_para = next(item for item in module.para_calls if item["x"] > (module.PAGE_W / 2) and item["y"] > 150)
    assert customer_para["x"] >= customer_panel["x"] + 10
    assert customer_para["x"] + customer_para["w"] <= customer_panel["x"] + customer_panel["w"] - 10
    assert blocks["_layout_safety"].get("page_5_customer_meaning_rule_clear_passed") is True


def test_page_5_customer_meaning_rule_does_not_cross_body():
    module, _canvas, blocks = _run(renderer._draw_fighter_architecture_radar)
    assert blocks["_layout_safety"].get("page_5_customer_meaning_rule_clear_passed") is True
    assert blocks["_layout_safety"].get("page_5_customer_operator_fit_passed") is True


def test_page_5_operator_use_rows_fit_inside_panel():
    module, _canvas, blocks = _run(renderer._draw_fighter_architecture_radar)
    operator_panel = next(
        panel
        for panel in module.panel_calls
        if panel["x"] > (module.PAGE_W / 2) and panel["h"] >= 110 and panel["y"] < 150
    )
    operator_texts = [text for text in _canvas.text_calls if text["kind"] == "drawString" and text["x"] > operator_panel["x"]]
    assert operator_texts, "Operator-use text was not rendered"
    assert max(text["x"] for text in operator_texts) <= operator_panel["x"] + operator_panel["w"] - 10
    assert blocks["_layout_safety"].get("page_5_operator_use_fit_passed") is True


def test_page_5_long_fighter_names_do_not_break_right_rail():
    module, _canvas, blocks = _run(
        renderer._draw_fighter_architecture_radar,
        {
            "fighter_a": "Tyrone Spong",
            "fighter_b": "Lancelot Proton de la Chapelle",
            "matchup_snapshot": "Long-name stress test for right rail panel fit.",
            "customer_meaning": "Customer meaning copy is stable under long fighter names.",
        },
    )
    assert blocks["_layout_safety"].get("page_5_side_panel_fit_passed") is True
    assert blocks["_layout_safety"].get("page_5_customer_operator_fit_passed") is True
    assert blocks["_layout_safety"].get("page_5_side_panel_text_clear_passed") is True
    panels = _right_rail_panels(module)
    assert all(panel["x"] + panel["w"] <= module.PAGE_W - module.SAFE_X + 0.5 for panel in panels)


def test_page_16_scorecard_rows_still_clear_rules():
    module, _canvas, blocks = _run(renderer._draw_scorecard_scenario)
    assert blocks["_layout_safety"].get("page_16_scorecard_integration_passed") is True
    assert blocks["_layout_safety"].get("page_16_scorecard_commentary_centered_passed") is True


def test_page_17_lower_cards_still_centered():
    module, _canvas, blocks = _run(renderer._draw_method_probability_chart)
    assert blocks["_layout_safety"].get("page_17_mechanism_risk_centered_passed") is True


def test_final_gate_blocks_page_2_strip_collision(tmp_path):
    preview = _preview()
    out, pdf_path, text, page_count = _render_output(tmp_path)
    layout_safety = dict(out.get("layout_safety", {}))
    layout_safety["page_2_strip_collision_passed"] = False
    layout_safety["page_2_lower_modules_no_strip_overlap_passed"] = False
    fight_id = app_module._build_fight_id_from_selected_matchup(preview["selected_matchup"])
    ok, violations = app_module._selected_matchup_passes_strict_pdf_quality_gate(
        preview["selected_matchup"],
        {"output_path": str(pdf_path), "output_filename": f"{fight_id}.pdf", "report_id": fight_id},
        text,
        page_count,
        layout_safety,
    )
    assert ok is False
    assert "page_2_lower_modules_no_strip_overlap_passed" in violations
    assert "visual_gate_status:v29_final_delivery_microfit_failed" in violations


def test_final_gate_blocks_page_5_right_rail_collision(tmp_path):
    preview = _preview()
    out, pdf_path, text, page_count = _render_output(tmp_path)
    layout_safety = dict(out.get("layout_safety", {}))
    layout_safety["page_5_side_panel_fit_passed"] = False
    layout_safety["page_5_customer_operator_fit_passed"] = False
    fight_id = app_module._build_fight_id_from_selected_matchup(preview["selected_matchup"])
    ok, violations = app_module._selected_matchup_passes_strict_pdf_quality_gate(
        preview["selected_matchup"],
        {"output_path": str(pdf_path), "output_filename": f"{fight_id}.pdf", "report_id": fight_id},
        text,
        page_count,
        layout_safety,
    )
    assert ok is False
    assert "page_5_side_panel_fit_passed" in violations
    assert "final_delivery_fit_polish_failed:page_5_customer_operator_fit_passed" in violations


def test_event_binding_gate_still_passes(tmp_path):
    preview = _preview()
    out, pdf_path, text, page_count = _render_output(tmp_path)
    layout_safety = dict(out.get("layout_safety", {}))
    fight_id = app_module._build_fight_id_from_selected_matchup(preview["selected_matchup"])
    ok, violations = app_module._selected_matchup_passes_strict_pdf_quality_gate(
        preview["selected_matchup"],
        {"output_path": str(pdf_path), "output_filename": f"{fight_id}.pdf", "report_id": fight_id},
        text,
        page_count,
        layout_safety,
    )
    assert ok is True
    assert "event_binding_incomplete_no_event_name" not in violations
    assert "event_binding_incomplete_no_event_date" not in violations
    assert "event_binding_unknown_event_in_pdf" not in violations


def test_sample_bleed_gate_still_passes(tmp_path):
    preview = _preview()
    out, pdf_path, text, page_count = _render_output(tmp_path)
    layout_safety = dict(out.get("layout_safety", {}))
    layout_safety["dashboard_lens_depth_passed"] = True
    fight_id = app_module._build_fight_id_from_selected_matchup(preview["selected_matchup"])
    ok, violations = app_module._selected_matchup_passes_strict_pdf_quality_gate(
        preview["selected_matchup"],
        {"output_path": str(pdf_path), "output_filename": f"{fight_id}.pdf", "report_id": fight_id},
        text,
        page_count,
        layout_safety,
    )
    assert ok is True
    assert not any(v.startswith("template_sample_bleed_present:") for v in violations)


def test_bulk_generation_contract_still_passes(monkeypatch, tmp_path):
    os.environ["BUTTON2_PDF_OUTPUT_ROOT"] = str(tmp_path)
    rows = _queue_rows()[:2]
    monkeypatch.setattr(app_module, "load_button2_queue_readonly", lambda: rows)
    text_by_path = {}

    def _generate(payload):
        out_path = tmp_path / payload["output_filename_override"]
        selected = payload.get("ingest_payload", {}).get("selected_matchup_payload", {})
        out_path.write_bytes(b"%PDF-1.4\n")
        text_by_path[str(out_path)] = _success_text_for_selected(selected)
        return {
            "ok": True,
            "output_path": str(out_path),
            "output_filename": payload["output_filename_override"],
            "report_id": Path(payload["output_filename_override"]).stem,
            "renderer_route_used": "template_pack_asset_renderer",
            "renderer_profile": "premium_template_pack_v29_layout_parity_rebuild_v1",
            "template_pack_asset_backed": True,
            "layout_safety": _layout_safety_stub_v7(),
            "delivery_performed": False,
            "external_api_delivery_performed": False,
            "queue_write_performed": False,
            "learning_apply_performed": False,
            "calibration_write_performed": False,
            "button3_mutation_performed": False,
        }

    monkeypatch.setattr(app_module, "generate_button2_report_render_gate_integration", _generate)
    monkeypatch.setattr(app_module, "_extract_pdf_text_and_page_count", lambda path: (text_by_path.get(str(path), ""), 24))

    with app_module.app.test_client() as client:
        data = client.post(BATCH_ROUTE, json={"operator_approval": True, "selected_matchup_ids": [row["matchup_id"] for row in rows]}).get_json()

    assert data["generated_count"] == 2
    assert all(result["content_gate_passed"] is True for result in data["results"] if result.get("ok"))


def test_governance_flags_remain_false(monkeypatch, tmp_path):
    os.environ["BUTTON2_PDF_OUTPUT_ROOT"] = str(tmp_path)
    rows = _queue_rows()[:1]
    monkeypatch.setattr(app_module, "load_button2_queue_readonly", lambda: rows)
    text_by_path = {}

    def _generate(payload):
        out_path = tmp_path / payload["output_filename_override"]
        out_path.write_bytes(b"%PDF-1.4\n")
        selected = payload.get("ingest_payload", {}).get("selected_matchup_payload", {})
        text_by_path[str(out_path)] = _success_text_for_selected(selected)
        return {
            "ok": True,
            "output_path": str(out_path),
            "output_filename": payload["output_filename_override"],
            "report_id": Path(payload["output_filename_override"]).stem,
            "renderer_route_used": "template_pack_asset_renderer",
            "renderer_profile": "premium_template_pack_v29_layout_parity_rebuild_v1",
            "template_pack_asset_backed": True,
            "layout_safety": _layout_safety_stub_v7(),
            "delivery_performed": False,
            "external_api_delivery_performed": False,
            "queue_write_performed": False,
            "learning_apply_performed": False,
            "calibration_write_performed": False,
            "button3_mutation_performed": False,
        }

    monkeypatch.setattr(app_module, "generate_button2_report_render_gate_integration", _generate)
    monkeypatch.setattr(app_module, "_extract_pdf_text_and_page_count", lambda path: (text_by_path.get(str(path), ""), 24))

    with app_module.app.test_client() as client:
        data = client.post(BATCH_ROUTE, json={"operator_approval": True, "selected_matchup_ids": [rows[0]["matchup_id"]]}).get_json()

    row = next(r for r in data["results"] if r.get("ok"))
    assert data["generated_count"] == 1
    assert row["customer_ready"] is True
    assert row["visual_gate_status"] == "premium_template_confirmed"
    assert data["delivery_performed"] is False
    assert data["external_api_delivery_performed"] is False
    assert data["queue_write_performed"] is False
    assert data["learning_apply_performed"] is False
    assert data["calibration_write_performed"] is False
    assert data["button3_mutation_performed"] is False
