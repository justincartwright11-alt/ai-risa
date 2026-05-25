from __future__ import annotations

import os
from pathlib import Path

from operator_dashboard import app as app_module
from operator_dashboard import button2_template_pack_asset_renderer_v1 as renderer
from operator_dashboard.test_button2_v29_template_final_delivery_fit_polish_v6 import (
    BATCH_ROUTE,
    DummyCanvas,
    FakeModule,
    _preview,
    _queue_rows,
    _render_output,
    _run,
    _success_text_for_selected,
)


def _layout_safety_stub_v7():
    return {
        "logo_blend_ok": True,
        "logo_black_tile_risk": False,
        "operator_note_present": False,
        "operator_note_absent_passed": True,
        "page_2_strip_collision_passed": True,
        "page_2_dashboard_fit_passed": True,
        "page_2_lower_modules_fit_passed": True,
        "page_2_lower_row_centered_passed": True,
        "page_5_operator_use_fit_passed": True,
        "page_5_side_panel_fit_passed": True,
        "page_5_customer_operator_fit_passed": True,
        "page_5_side_panel_text_clear_passed": True,
        "page_6_table_density_passed": True,
        "page_6_tactical_command_centered_passed": True,
        "page_14_round_fit_passed": True,
        "page_14_round_outlook_fit_passed": True,
        "page_14_round_balance_passed": True,
        "page_14_round_outlook_balanced_passed": True,
        "page_16_scorecard_fit_passed": True,
        "page_16_scorecard_integration_passed": True,
        "page_16_scorecard_commentary_centered_passed": True,
        "page_17_stoppage_fit_passed": True,
        "page_17_stoppage_rhythm_passed": True,
        "page_17_mechanism_risk_centered_passed": True,
        "dashboard_lens_depth_passed": True,
        "round_heading_body_clear_passed": True,
        "readable_min_font_passed": True,
        "footer_safe_zone_passed": True,
        "tactical_edge_overlap_passed": True,
        "scorecard_readability_passed": True,
        "stoppage_readability_passed": True,
        "round_outlook_centered_passed": True,
        "footer_safe_zone_pages": {"6": {"safe": True}, "16": {"safe": True}, "17": {"safe": True}},
        "page_bounds": {
            "6": {"overlap_detected": False, "min_font_size": 8.8},
            "14": {"overlap_detected": False, "min_font_size": 8.6},
            "16": {"overlap_detected": False, "min_font_size": 8.8},
            "17": {"overlap_detected": False, "min_font_size": 8.8},
        },
        "lens_depth": {
            "control": {"length": 120, "mentions_selected_fighter": True, "generic_placeholder": False, "overflow": False},
            "danger": {"length": 120, "mentions_selected_fighter": True, "generic_placeholder": False, "overflow": False},
            "command": {"length": 120, "mentions_selected_fighter": True, "generic_placeholder": False, "overflow": False},
        },
        "source_map": {"rows_separated": True, "source_url_statement_separated": True},
    }


def test_page_2_lower_row_modules_are_centered_and_fit():
    module, _canvas, blocks = _run(renderer._draw_executive)
    cards = sorted(
        [p for p in module.panel_calls if abs(p["y"] - 52.0) < 0.2 and abs(p["h"] - 84.0) < 0.2],
        key=lambda item: item["x"],
    )
    assert len(cards) == 3
    left_edge = cards[0]["x"]
    right_edge = cards[-1]["x"] + cards[-1]["w"]
    assert abs(((left_edge + right_edge) / 2) - (module.PAGE_W / 2)) <= 2.5
    assert blocks["_layout_safety"].get("page_2_lower_row_centered_passed") is True
    assert blocks["_layout_safety"].get("page_2_lower_modules_fit_passed") is True


def test_page_2_round_control_projection_shows_all_three_rounds():
    _module, canvas, blocks = _run(renderer._draw_executive)
    round_tokens = {"R1", "R2", "R3"}
    drawn = {item["text"] for item in canvas.text_calls if item["kind"] == "drawCentredString" and item["text"] in round_tokens}
    assert drawn == round_tokens
    assert blocks["_layout_safety"].get("page_2_lower_row_centered_passed") is True


def test_page_5_customer_meaning_text_not_crossed_by_divider():
    module, canvas, blocks = _run(renderer._draw_fighter_architecture_radar)
    customer_panel = next(
        panel for panel in module.panel_calls if abs(panel["y"] - 250.0) < 0.2 and abs(panel["h"] - 88.0) < 0.2
    )
    customer_para = next(item for item in module.para_calls if str(item["text"]).startswith("Instability versus structure"))
    divider_y = customer_panel["y"] + customer_panel["h"] - 28
    assert customer_para["x"] >= customer_panel["x"] + 10
    assert customer_para["y"] + 20 < divider_y
    assert blocks["_layout_safety"].get("page_5_side_panel_text_clear_passed") is True


def test_page_5_side_panel_text_has_safe_padding():
    module, _canvas, blocks = _run(renderer._draw_fighter_architecture_radar)
    customer_panel = next(
        panel for panel in module.panel_calls if abs(panel["y"] - 250.0) < 0.2 and abs(panel["h"] - 88.0) < 0.2
    )
    customer_para = next(item for item in module.para_calls if str(item["text"]).startswith("Instability versus structure"))
    assert customer_para["x"] - customer_panel["x"] >= 8
    assert customer_para["y"] - customer_panel["y"] >= 8
    assert blocks["_layout_safety"].get("page_5_side_panel_text_clear_passed") is True


def test_page_6_tactical_command_panel_centered():
    module, _canvas, blocks = _run(renderer._draw_tactical_edge_table)
    outer = next(panel for panel in module.panel_calls if abs(panel["y"] - 94.0) < 0.2 and abs(panel["h"] - 84.0) < 0.2 and panel["w"] > 300)
    assert abs((outer["x"] + (outer["w"] / 2)) - (module.PAGE_W / 2)) <= 2.5
    inner_cards = sorted(
        [panel for panel in module.panel_calls if abs(panel["y"] - 104.0) < 0.2 and abs(panel["h"] - 64.0) < 0.2],
        key=lambda panel: panel["x"],
    )
    assert len(inner_cards) == 2
    assert abs(inner_cards[0]["w"] - inner_cards[1]["w"]) <= 0.2
    assert blocks["_layout_safety"].get("page_6_tactical_command_centered_passed") is True


def test_page_14_round_outlook_balanced():
    module, canvas, blocks = _run(renderer._draw_round_control_graph, {"fighter_a": "Maximillian Alexander Holloway", "fighter_b": "Justin Xavier Gaethje"})
    round_labels = [item for item in canvas.text_calls if item["kind"] == "drawCentredString" and item["text"] in {"R1", "R2", "R3"}]
    assert len(round_labels) == 3
    assert blocks["_layout_safety"].get("page_14_round_outlook_balanced_passed") is True
    assert blocks["_layout_safety"].get("page_14_round_balance_passed") is True


def test_page_16_scorecard_commentary_centered_and_integrated():
    module, _canvas, blocks = _run(renderer._draw_scorecard_scenario)
    commentary = next(panel for panel in module.panel_calls if abs(panel["y"] - 176.0) < 0.2 and abs(panel["h"] - 92.0) < 0.2)
    table = next(panel for panel in module.panel_calls if abs(panel["y"] - 96.0) < 0.2 and abs(panel["h"] - 364.0) < 0.2)
    assert abs((commentary["x"] + commentary["w"] / 2) - (table["x"] + table["w"] / 2)) <= 1.5
    assert blocks["_layout_safety"].get("page_16_scorecard_commentary_centered_passed") is True
    assert blocks["_layout_safety"].get("page_16_scorecard_integration_passed") is True


def test_page_17_mechanism_and_risk_control_boxes_centered():
    module, _canvas, blocks = _run(renderer._draw_method_probability_chart)
    cards = sorted(
        [panel for panel in module.panel_calls if abs(panel["y"] - 92.0) < 0.2 and abs(panel["h"] - 82.0) < 0.2],
        key=lambda panel: panel["x"],
    )
    assert len(cards) == 2
    group_center = ((cards[0]["x"] + (cards[0]["w"] / 2)) + (cards[1]["x"] + (cards[1]["w"] / 2))) / 2
    assert abs(group_center - (module.PAGE_W / 2)) <= 2.5
    assert abs(cards[0]["w"] - cards[1]["w"]) <= 0.2
    assert blocks["_layout_safety"].get("page_17_mechanism_risk_centered_passed") is True


def test_final_visual_gate_blocks_page_5_divider_text_collision(tmp_path):
    preview = _preview()
    out, pdf_path, text, page_count = _render_output(tmp_path)
    layout_safety = dict(out.get("layout_safety", {}))
    for key in [
        "page_2_footer_safe_passed",
        "page_2_round_control_projection_fit_passed",
        "page_2_lower_modules_no_strip_overlap_passed",
        "page_2_round_control_no_lens_overlap_passed",
        "page_2_method_probability_no_lens_overlap_passed",
        "page_2_risk_control_no_lens_overlap_passed",
        "page_2_analysis_modules_no_strip_overlap_passed",
        "page_2_footer_safe_zone_passed",
        "page_2_dashboard_no_visual_overlap_passed",
        "page_2_dashboard_fit_passed",
        "page_2_lower_modules_fit_passed",
        "page_5_architecture_read_text_fit_passed",
        "page_5_customer_meaning_heading_clear_passed",
        "page_5_customer_meaning_body_clear_passed",
        "page_5_customer_panel_below_architecture_panel_passed",
        "page_5_operator_panel_below_customer_panel_passed",
        "page_5_customer_operator_fit_passed",
        "page_5_side_panel_fit_passed",
        "page_5_right_rail_no_text_overlap_passed",
        "page_5_right_rail_no_box_overlap_passed",
        "page_5_customer_meaning_rule_clear_passed",
        "page_5_architecture_customer_no_overlap_passed",
        "page_5_operator_use_fit_passed",
        "page_5_customer_panel_inside_radar_band_passed",
        "page_16_scorecard_row_rule_clear_passed",
        "page_16_commentary_centered_passed",
        "page_17_lower_cards_centered_passed",
    ]:
        layout_safety[key] = True
    layout_safety["page_5_side_panel_text_clear_passed"] = False
    ok, violations = app_module._selected_matchup_passes_strict_pdf_quality_gate(
        preview["selected_matchup"],
        {"output_path": str(pdf_path), "output_filename": "max_holloway_vs_justin_gaethje_ufc_300_premium_test.pdf", "report_id": "max_holloway_vs_justin_gaethje_ufc_300"},
        text,
        page_count,
        layout_safety,
    )
    assert ok is False
    assert "final_delivery_visual_cleanup_failed:page_5_side_panel_text_clear_passed" in violations
    assert "visual_gate_status:v29_final_delivery_microfit_failed" in violations


def test_final_visual_gate_blocks_page_2_lower_row_failure(tmp_path):
    preview = _preview()
    out, pdf_path, text, page_count = _render_output(tmp_path)
    layout_safety = dict(out.get("layout_safety", {}))
    for key in [
        "page_2_footer_safe_passed",
        "page_2_round_control_projection_fit_passed",
        "page_2_lower_modules_no_strip_overlap_passed",
        "page_2_round_control_no_lens_overlap_passed",
        "page_2_method_probability_no_lens_overlap_passed",
        "page_2_risk_control_no_lens_overlap_passed",
        "page_2_analysis_modules_no_strip_overlap_passed",
        "page_2_footer_safe_zone_passed",
        "page_2_dashboard_no_visual_overlap_passed",
        "page_2_dashboard_fit_passed",
        "page_2_lower_modules_fit_passed",
        "page_5_architecture_read_text_fit_passed",
        "page_5_customer_meaning_heading_clear_passed",
        "page_5_customer_meaning_body_clear_passed",
        "page_5_customer_panel_below_architecture_panel_passed",
        "page_5_operator_panel_below_customer_panel_passed",
        "page_5_customer_operator_fit_passed",
        "page_5_side_panel_fit_passed",
        "page_5_right_rail_no_text_overlap_passed",
        "page_5_right_rail_no_box_overlap_passed",
        "page_5_customer_meaning_rule_clear_passed",
        "page_5_architecture_customer_no_overlap_passed",
        "page_5_operator_use_fit_passed",
        "page_5_customer_panel_inside_radar_band_passed",
        "page_16_scorecard_row_rule_clear_passed",
        "page_16_commentary_centered_passed",
        "page_17_lower_cards_centered_passed",
    ]:
        layout_safety[key] = True
    layout_safety["page_2_lower_row_centered_passed"] = False
    layout_safety["page_2_lower_modules_fit_passed"] = False
    ok, violations = app_module._selected_matchup_passes_strict_pdf_quality_gate(
        preview["selected_matchup"],
        {"output_path": str(pdf_path), "output_filename": "max_holloway_vs_justin_gaethje_ufc_300_premium_test.pdf", "report_id": "max_holloway_vs_justin_gaethje_ufc_300"},
        text,
        page_count,
        layout_safety,
    )
    assert ok is False
    assert "final_delivery_visual_cleanup_failed:page_2_lower_row_centered_passed" in violations
    assert "final_delivery_fit_polish_failed:page_2_lower_modules_fit_passed" in violations


def test_event_binding_gate_still_passes(tmp_path):
    preview = _preview()
    out, pdf_path, text, page_count = _render_output(tmp_path)
    layout_safety = dict(out.get("layout_safety", {}))
    for key in [
        "page_2_footer_safe_passed",
        "page_2_round_control_projection_fit_passed",
        "page_2_lower_modules_no_strip_overlap_passed",
        "page_2_round_control_no_lens_overlap_passed",
        "page_2_method_probability_no_lens_overlap_passed",
        "page_2_risk_control_no_lens_overlap_passed",
        "page_2_analysis_modules_no_strip_overlap_passed",
        "page_2_footer_safe_zone_passed",
        "page_2_dashboard_no_visual_overlap_passed",
        "page_2_dashboard_fit_passed",
        "page_2_lower_modules_fit_passed",
        "page_5_architecture_read_text_fit_passed",
        "page_5_customer_meaning_heading_clear_passed",
        "page_5_customer_meaning_body_clear_passed",
        "page_5_customer_panel_below_architecture_panel_passed",
        "page_5_operator_panel_below_customer_panel_passed",
        "page_5_customer_operator_fit_passed",
        "page_5_side_panel_fit_passed",
        "page_5_right_rail_no_text_overlap_passed",
        "page_5_right_rail_no_box_overlap_passed",
        "page_5_customer_meaning_rule_clear_passed",
        "page_5_architecture_customer_no_overlap_passed",
        "page_5_operator_use_fit_passed",
        "page_5_customer_panel_inside_radar_band_passed",
        "page_16_scorecard_row_rule_clear_passed",
        "page_16_commentary_centered_passed",
        "page_17_lower_cards_centered_passed",
    ]:
        layout_safety[key] = True
    ok, violations = app_module._selected_matchup_passes_strict_pdf_quality_gate(
        preview["selected_matchup"],
        {"output_path": str(pdf_path), "output_filename": "max_holloway_vs_justin_gaethje_ufc_300_premium_test.pdf", "report_id": "max_holloway_vs_justin_gaethje_ufc_300"},
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
    for key in [
        "page_2_footer_safe_passed",
        "page_2_round_control_projection_fit_passed",
        "page_2_lower_modules_no_strip_overlap_passed",
        "page_2_round_control_no_lens_overlap_passed",
        "page_2_method_probability_no_lens_overlap_passed",
        "page_2_risk_control_no_lens_overlap_passed",
        "page_2_analysis_modules_no_strip_overlap_passed",
        "page_2_footer_safe_zone_passed",
        "page_2_dashboard_no_visual_overlap_passed",
        "page_2_dashboard_fit_passed",
        "page_2_lower_modules_fit_passed",
        "page_5_architecture_read_text_fit_passed",
        "page_5_customer_meaning_heading_clear_passed",
        "page_5_customer_meaning_body_clear_passed",
        "page_5_customer_panel_below_architecture_panel_passed",
        "page_5_operator_panel_below_customer_panel_passed",
        "page_5_customer_operator_fit_passed",
        "page_5_side_panel_fit_passed",
        "page_5_right_rail_no_text_overlap_passed",
        "page_5_right_rail_no_box_overlap_passed",
        "page_5_customer_meaning_rule_clear_passed",
        "page_5_architecture_customer_no_overlap_passed",
        "page_5_operator_use_fit_passed",
        "page_5_customer_panel_inside_radar_band_passed",
        "page_16_scorecard_row_rule_clear_passed",
        "page_16_commentary_centered_passed",
        "page_17_lower_cards_centered_passed",
    ]:
        layout_safety[key] = True
    layout_safety["dashboard_lens_depth_passed"] = True
    ok, violations = app_module._selected_matchup_passes_strict_pdf_quality_gate(
        preview["selected_matchup"],
        {"output_path": str(pdf_path), "output_filename": "max_holloway_vs_justin_gaethje_ufc_300_premium_test.pdf", "report_id": "max_holloway_vs_justin_gaethje_ufc_300"},
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

    row = next(result for result in data["results"] if result.get("ok"))
    assert data["generated_count"] == 1
    assert row["customer_ready"] is True
    assert row["visual_gate_status"] == "premium_template_confirmed"
    assert data["delivery_performed"] is False
    assert data["external_api_delivery_performed"] is False
    assert data["queue_write_performed"] is False
    assert data["learning_apply_performed"] is False
    assert data["calibration_write_performed"] is False
    assert data["button3_mutation_performed"] is False