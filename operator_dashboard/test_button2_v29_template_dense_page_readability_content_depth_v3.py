from __future__ import annotations

import io
import os
from pathlib import Path

import pytest
from pypdf import PdfReader

from operator_dashboard import app as app_module
from operator_dashboard.button2_dossier_handoff_report_context_preview import build_button2_dossier_handoff_report_context_preview
from operator_dashboard import button2_template_pack_asset_renderer_v1 as renderer


BATCH_ROUTE = "/api/button2/generate-selected-batch"


@pytest.fixture
def client(tmp_path):
    os.environ["BUTTON2_PDF_OUTPUT_ROOT"] = str(tmp_path)
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as test_client:
        yield test_client


def _preview(
    fighter_a: str = "Callum Walsh",
    fighter_b: str = "Austin Williams",
    event_name: str = "Joshua vs Dubois",
    event_date: str = "2026-09-21",
    source_url: str = "https://www.matchroomboxing.com/events/joshua-vs-dubois",
):
    return {
        "selected_matchup": {
            "fighter_a": fighter_a,
            "fighter_b": fighter_b,
            "event_name": event_name,
            "event_date": event_date,
            "promotion": "Matchroom Boxing",
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


def _render_pdf_bytes_to_text(pdf_bytes: bytes):
    reader = PdfReader(io.BytesIO(pdf_bytes))
    return "\n".join((page.extract_text() or "") for page in reader.pages), len(reader.pages)


def _render_output(tmp_path):
    os.environ["BUTTON2_PDF_OUTPUT_ROOT"] = str(tmp_path)
    out = renderer.render_button2_template_pack_asset_pdf(_preview())
    pdf_path = tmp_path / "callum_walsh_vs_austin_williams_joshua_vs_dubois_premium_dense_page_v3.pdf"
    pdf_path.write_bytes(out["pdf_bytes"])
    text, page_count = _render_pdf_bytes_to_text(out["pdf_bytes"])
    return out, pdf_path, text, page_count


def _queue_rows():
    rows = app_module.load_button2_queue_readonly()
    assert rows, "canonical queue must exist for Button 2 tests"
    return rows


def _pick_ids(count=2):
    return [row["matchup_id"] for row in _queue_rows()[:count]]


def _success_text_for_selected(selected: dict):
    fighter_a = selected["fighter_a"]
    fighter_b = selected["fighter_b"]
    event_name = selected["event_name"]
    event_date = selected["event_date"]
    source_url = selected["source_url"]
    return (
        f"{fighter_a} vs {fighter_b}\n"
        f"Event: {event_name}\n"
        f"Event Date: {event_date}\n"
        f"Source: {source_url}\n"
        "Control Lens / Control Zone\n"
        f"{fighter_a} owns the preferred lane when the fight stays in crowded middle distance and {fighter_b} is forced to reset twice before he can plant his counters.\n"
        "Danger Lens / Danger Zone\n"
        f"{fighter_b} flips the fight if {fighter_a} chases after first success and leaves square exits for straight counters.\n"
        "Command Read / Collapse Trigger\n"
        f"Corner priority: keep {fighter_a} patient on the second phase and never give {fighter_b} a free reset.\n"
        + "\n".join(marker.upper() for marker in app_module._BUTTON2_REQUIRED_PREMIUM_MARKERS)
        + "\n"
        + "\n".join(f"{a.upper()} {b.upper()}" for a, b in app_module._BUTTON2_REQUIRED_PREMIUM_MARKER_ALTERNATIVES)
        + "\n"
        + "\n".join(marker.upper() for marker in app_module._BUTTON2_REQUIRED_V29_LAYOUT_MARKERS)
        + "\n"
    )


def test_operator_note_removed_from_customer_pdf_text(tmp_path):
    out, _pdf_path, text, _page_count = _render_output(tmp_path)
    lower = text.lower()
    assert "operator note" not in lower
    for marker in app_module._BUTTON2_DENSE_PAGE_SCAFFOLD_MARKERS:
        assert marker not in lower
    assert out.get("layout_safety", {}).get("operator_note_present") is False


def test_control_lens_contains_deep_matchup_specific_copy(tmp_path):
    out, _pdf_path, text, _page_count = _render_output(tmp_path)
    control = out.get("layout_safety", {}).get("lens_depth", {}).get("control", {})
    assert control.get("length", 0) >= 90
    assert control.get("mentions_selected_fighter") is True
    assert control.get("generic_placeholder") is False
    assert "Callum Walsh" in text


def test_danger_lens_contains_deep_matchup_specific_copy(tmp_path):
    out, _pdf_path, text, _page_count = _render_output(tmp_path)
    danger = out.get("layout_safety", {}).get("lens_depth", {}).get("danger", {})
    assert danger.get("length", 0) >= 90
    assert danger.get("mentions_selected_fighter") is True
    assert danger.get("generic_placeholder") is False
    assert "Austin Williams" in text


def test_command_read_contains_deep_matchup_specific_copy(tmp_path):
    out, _pdf_path, text, _page_count = _render_output(tmp_path)
    command = out.get("layout_safety", {}).get("lens_depth", {}).get("command", {})
    assert command.get("length", 0) >= 90
    assert command.get("mentions_selected_fighter") is True
    assert command.get("generic_placeholder") is False
    assert "Corner priority" in text


def test_page_6_tactical_edge_table_readable_and_no_operator_note(tmp_path):
    out, _pdf_path, text, _page_count = _render_output(tmp_path)
    page_info = out.get("layout_safety", {}).get("page_bounds", {}).get("6", {})
    assert page_info.get("overlap_detected") is False
    assert float(page_info.get("min_font_size", 0.0)) >= 8.8
    assert "Operator Note" not in text


def test_page_6_failure_consequence_visible(tmp_path):
    _out, _pdf_path, text, _page_count = _render_output(tmp_path)
    assert "Failure Consequence" in text
    assert "straight counter pockets" in text


def test_page_14_round_heading_body_no_overlap_geometry(tmp_path):
    out, _pdf_path, _text, _page_count = _render_output(tmp_path)
    safety = out.get("layout_safety", {})
    assert safety.get("round_heading_body_clear_passed") is True
    assert safety.get("page_bounds", {}).get("14", {}).get("overlap_detected") is False


def test_page_14_round_cards_centered_and_balanced(tmp_path):
    out, _pdf_path, text, _page_count = _render_output(tmp_path)
    assert out.get("layout_safety", {}).get("round_outlook_centered_passed") is True
    assert "INFO / RHYTHM TEST" in text
    assert "PRIMARY PRESSURE TEST" in text
    assert "DECISION STRESS POINT" in text


def test_page_16_scorecard_no_operator_note_and_readable_commentary(tmp_path):
    out, _pdf_path, text, _page_count = _render_output(tmp_path)
    safety = out.get("layout_safety", {})
    assert safety.get("scorecard_readability_passed") is True
    assert float(safety.get("page_bounds", {}).get("16", {}).get("min_font_size", 0.0)) >= 8.8
    assert "Operator Note" not in text
    assert "Scorecard Commentary" in text


def test_page_17_stoppage_no_operator_note_and_readable_risk_control(tmp_path):
    out, _pdf_path, text, _page_count = _render_output(tmp_path)
    safety = out.get("layout_safety", {})
    assert safety.get("stoppage_readability_passed") is True
    assert float(safety.get("page_bounds", {}).get("17", {}).get("min_font_size", 0.0)) >= 8.8
    assert "Operator Note" not in text
    assert "Risk Control" in text


def test_alternate_matchup_render_has_no_callum_austin_bleed_and_keeps_boxing_binding(tmp_path):
    preview = _preview(fighter_a="Ben Whittaker", fighter_b="Willy Hutchinson")
    out = renderer.render_button2_template_pack_asset_pdf(preview)
    text, _page_count = _render_pdf_bytes_to_text(out["pdf_bytes"])
    lower = text.lower()
    assert "austin williams" not in lower
    assert "walsh on the scoring beat" not in lower
    assert "promotion\nmatchroom boxing" in lower
    assert "sport\nboxing" in lower


def test_report_context_preview_preserves_promotion_for_live_batch_binding():
    result = build_button2_dossier_handoff_report_context_preview({
        "button2_ingest_preview_context": {
            "destination_marker": "button2_report_generation_preview",
            "context_kind": "button1_selected_matchup_handoff",
            "ingest_mode": "premium_template_selected_matchup",
            "template_renderer_profile": "premium_template_pack_v29",
            "selected_matchup_payload": {
                "fighter_a": "Ben Whittaker",
                "fighter_b": "Willy Hutchinson",
                "event_name": "Joshua vs Dubois",
                "event_date": "2026-09-21",
                "promotion": "Matchroom Boxing",
                "source_url": "https://www.matchroomboxing.com/events/joshua-vs-dubois",
                "source_type": "official",
            },
            "dossier_summary_preview": "Selected matchup handoff summary.",
        }
    })
    assert result["ok"] is True
    assert result["report_context_preview"]["selected_matchup"]["promotion"] == "Matchroom Boxing"


def test_visual_gate_blocks_customer_ready_when_operator_note_appears(monkeypatch, tmp_path):
    preview = _preview()
    out, pdf_path, text, page_count = _render_output(tmp_path)
    layout_safety = dict(out.get("layout_safety", {}))
    layout_safety["operator_note_present"] = True
    ok, violations = app_module._selected_matchup_passes_strict_pdf_quality_gate(
        preview["selected_matchup"],
        {"output_path": str(pdf_path), "output_filename": pdf_path.name, "report_id": "callum_walsh_vs_austin_williams_joshua_vs_dubois"},
        text + "\nOperator Note\n",
        page_count,
        layout_safety,
    )
    assert ok is False
    assert any(v.startswith("dense_page_scaffold_note_present:") or v == "dense_page_operator_note_reported_by_renderer" for v in violations)


def test_visual_gate_blocks_generic_lens_placeholder_copy(tmp_path):
    preview = _preview()
    out, pdf_path, text, page_count = _render_output(tmp_path)
    layout_safety = dict(out.get("layout_safety", {}))
    layout_safety["lens_depth"] = {
        "control": {"length": 40, "mentions_selected_fighter": False, "generic_placeholder": True, "overflow": False},
        "danger": {"length": 40, "mentions_selected_fighter": False, "generic_placeholder": True, "overflow": False},
        "command": {"length": 40, "mentions_selected_fighter": False, "generic_placeholder": True, "overflow": False},
    }
    layout_safety["dashboard_lens_depth_passed"] = False
    ok, violations = app_module._selected_matchup_passes_strict_pdf_quality_gate(
        preview["selected_matchup"],
        {"output_path": str(pdf_path), "output_filename": pdf_path.name, "report_id": "callum_walsh_vs_austin_williams_joshua_vs_dubois"},
        text + "\nwhere the fight is owned\n",
        page_count,
        layout_safety,
    )
    assert ok is False
    assert any(v.startswith("dense_page_generic_lens_placeholder_present:") or v == "dense_page_dashboard_lens_not_deep_enough" for v in violations)


def test_event_binding_gate_still_passes(tmp_path):
    preview = _preview()
    out, pdf_path, text, page_count = _render_output(tmp_path)
    ok, violations = app_module._selected_matchup_passes_strict_pdf_quality_gate(
        preview["selected_matchup"],
        {"output_path": str(pdf_path), "output_filename": pdf_path.name, "report_id": "callum_walsh_vs_austin_williams_joshua_vs_dubois"},
        text,
        page_count,
        out.get("layout_safety"),
    )
    assert ok is True
    assert "event_binding_incomplete_no_event_name" not in violations
    assert "event_binding_incomplete_no_event_date" not in violations


def test_sample_bleed_gate_still_passes(tmp_path):
    preview = _preview()
    out, pdf_path, text, page_count = _render_output(tmp_path)
    ok, violations = app_module._selected_matchup_passes_strict_pdf_quality_gate(
        preview["selected_matchup"],
        {"output_path": str(pdf_path), "output_filename": pdf_path.name, "report_id": "callum_walsh_vs_austin_williams_joshua_vs_dubois"},
        text,
        page_count,
        out.get("layout_safety"),
    )
    assert ok is True
    assert not any(value.startswith("template_sample_bleed_present:") for value in violations)


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
            "layout_safety": {
                    "logo_blend_ok": True,
                    "logo_black_tile_risk": False,
                "operator_note_present": False,
                "operator_note_absent_passed": True,
                "page_2_strip_collision_passed": True,
                "page_2_dashboard_fit_passed": True,
                "page_5_operator_use_fit_passed": True,
                "page_5_side_panel_fit_passed": True,
                "page_6_table_density_passed": True,
                "page_14_round_fit_passed": True,
                "page_14_round_outlook_fit_passed": True,
                "page_16_scorecard_fit_passed": True,
                "page_17_stoppage_fit_passed": True,
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
            },
            "delivery_performed": False,
            "external_api_delivery_performed": False,
            "queue_write_performed": False,
            "learning_apply_performed": False,
            "calibration_write_performed": False,
            "button3_mutation_performed": False,
        }

    monkeypatch.setattr(app_module, "generate_button2_report_render_gate_integration", _generate)
    monkeypatch.setattr(app_module, "_extract_pdf_text_and_page_count", lambda path: (text_by_path.get(str(path), ""), 24))
    data = app_module.app.test_client().post(BATCH_ROUTE, json={"operator_approval": True, "selected_matchup_ids": [row["matchup_id"] for row in rows]}).get_json()
    assert data["generated_count"] == 2
    assert all(result["content_gate_passed"] is True for result in data["results"] if result.get("ok"))


def test_governance_flags_remain_false(monkeypatch, tmp_path, client):
    os.environ["BUTTON2_PDF_OUTPUT_ROOT"] = str(tmp_path)
    rows = _queue_rows()[:1]
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
            "layout_safety": {
                    "logo_blend_ok": True,
                    "logo_black_tile_risk": False,
                "operator_note_present": False,
                "operator_note_absent_passed": True,
                "page_2_strip_collision_passed": True,
                "page_2_dashboard_fit_passed": True,
                "page_5_operator_use_fit_passed": True,
                "page_5_side_panel_fit_passed": True,
                "page_6_table_density_passed": True,
                "page_14_round_fit_passed": True,
                "page_14_round_outlook_fit_passed": True,
                "page_16_scorecard_fit_passed": True,
                "page_17_stoppage_fit_passed": True,
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
            },
            "delivery_performed": False,
            "external_api_delivery_performed": False,
            "queue_write_performed": False,
            "learning_apply_performed": False,
            "calibration_write_performed": False,
            "button3_mutation_performed": False,
        }

    monkeypatch.setattr(app_module, "generate_button2_report_render_gate_integration", _generate)
    monkeypatch.setattr(app_module, "_extract_pdf_text_and_page_count", lambda path: (text_by_path.get(str(path), ""), 24))
    data = client.post(BATCH_ROUTE, json={"operator_approval": True, "selected_matchup_ids": _pick_ids(1)}).get_json()
    assert data["delivery_performed"] is False
    assert data["external_api_delivery_performed"] is False
    assert data["queue_write_performed"] is False
    assert data["learning_apply_performed"] is False