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


def test_page_2_new_hard_band_markers_passed():
    module, _canvas, blocks = _run(renderer._draw_executive)
    assert blocks["_layout_safety"].get("page_2_round_control_no_lens_overlap_passed") is True
    assert blocks["_layout_safety"].get("page_2_method_probability_no_lens_overlap_passed") is True
    assert blocks["_layout_safety"].get("page_2_risk_control_no_lens_overlap_passed") is True
    assert blocks["_layout_safety"].get("page_2_analysis_modules_no_strip_overlap_passed") is True
    assert blocks["_layout_safety"].get("page_2_footer_safe_zone_passed") is True
    assert blocks["_layout_safety"].get("page_2_dashboard_no_visual_overlap_passed") is True


def test_page_5_new_right_rail_stack_and_read_fit_passed():
    module, _canvas, blocks = _run(renderer._draw_fighter_architecture_radar)
    assert blocks["_layout_safety"].get("page_5_architecture_read_text_fit_passed") is True
    assert blocks["_layout_safety"].get("page_5_customer_meaning_heading_clear_passed") is True
    assert blocks["_layout_safety"].get("page_5_customer_meaning_body_clear_passed") is True
    assert blocks["_layout_safety"].get("page_5_customer_panel_below_architecture_panel_passed") is True
    assert blocks["_layout_safety"].get("page_5_operator_panel_below_customer_panel_passed") is True
    assert blocks["_layout_safety"].get("page_5_right_rail_no_text_overlap_passed") is True
    assert blocks["_layout_safety"].get("page_5_right_rail_no_box_overlap_passed") is True


def test_strict_gate_rejects_page_2_footer_safe_zone_failure(tmp_path):
    preview = _preview()
    out, pdf_path, text, page_count = _render_output(tmp_path)
    out = dict(out)
    out["layout_safety"] = dict(out.get("layout_safety", {}))
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
        "page_5_architecture_read_text_fit_passed",
        "page_5_customer_meaning_heading_clear_passed",
        "page_5_customer_meaning_body_clear_passed",
        "page_5_customer_panel_below_architecture_panel_passed",
        "page_5_operator_panel_below_customer_panel_passed",
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
        out["layout_safety"][key] = True
    out["layout_safety"]["page_2_footer_safe_zone_passed"] = False
    fight_id = app_module._build_fight_id_from_selected_matchup(preview["selected_matchup"])

    ok, violations = app_module._selected_matchup_passes_strict_pdf_quality_gate(
        preview["selected_matchup"],
        {"output_path": str(pdf_path), "output_filename": f"{fight_id}.pdf", "report_id": fight_id},
        text,
        page_count,
        out,
    )

    assert ok is False
    assert "page_2_footer_safe_zone_passed" in violations
    assert "visual_gate_status:v29_final_delivery_right_rail_overlap_failed" in violations


def test_strict_gate_rejects_page_5_architecture_read_fit_failure(tmp_path):
    preview = _preview()
    out, pdf_path, text, page_count = _render_output(tmp_path)
    out = dict(out)
    out["layout_safety"] = dict(out.get("layout_safety", {}))
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
        "page_5_architecture_read_text_fit_passed",
        "page_5_customer_meaning_heading_clear_passed",
        "page_5_customer_meaning_body_clear_passed",
        "page_5_customer_panel_below_architecture_panel_passed",
        "page_5_operator_panel_below_customer_panel_passed",
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
        out["layout_safety"][key] = True
    out["layout_safety"]["page_5_architecture_read_text_fit_passed"] = False
    fight_id = app_module._build_fight_id_from_selected_matchup(preview["selected_matchup"])

    ok, violations = app_module._selected_matchup_passes_strict_pdf_quality_gate(
        preview["selected_matchup"],
        {"output_path": str(pdf_path), "output_filename": f"{fight_id}.pdf", "report_id": fight_id},
        text,
        page_count,
        out,
    )

    assert ok is False
    assert "page_5_architecture_read_text_fit_passed" in violations
    assert "visual_gate_status:v29_final_delivery_right_rail_overlap_failed" in violations


def test_strict_gate_passes_with_new_premium_text_markers(tmp_path):
    preview = _preview()
    out, pdf_path, text, page_count = _render_output(tmp_path)
    out = dict(out)
    out["layout_safety"] = dict(out.get("layout_safety", {}))
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
        "page_5_architecture_read_text_fit_passed",
        "page_5_customer_meaning_heading_clear_passed",
        "page_5_customer_meaning_body_clear_passed",
        "page_5_customer_panel_below_architecture_panel_passed",
        "page_5_operator_panel_below_customer_panel_passed",
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
        out["layout_safety"][key] = True
    fight_id = app_module._build_fight_id_from_selected_matchup(preview["selected_matchup"])

    ok, violations = app_module._selected_matchup_passes_strict_pdf_quality_gate(
        preview["selected_matchup"],
        {"output_path": str(pdf_path), "output_filename": f"{fight_id}.pdf", "report_id": fight_id},
        text,
        page_count,
        out,
    )

    assert ok is True
    assert not any(marker in violations for marker in [
        "tactical thesis",
        "control objective",
        "danger objective",
        "watch cue",
        "failure cue",
        "scoring consequence",
        "corner command",
        "customer meaning",
        "operator use",
        "uncertainty",
    ])


def test_bulk_generation_layout_gate_continues_to_pass(monkeypatch, tmp_path):
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
