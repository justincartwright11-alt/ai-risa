from __future__ import annotations

import copy
import io
import inspect
import math as _math
import os
from pathlib import Path

from pypdf import PdfReader

from operator_dashboard import app as app_module
from operator_dashboard import button2_template_pack_asset_renderer_v1 as renderer


BATCH_ROUTE = "/api/button2/generate-selected-batch"


class DummyCanvas:
    def __init__(self):
        self.text_calls = []
        self.line_calls = []
        self.round_rect_calls = []

    def stringWidth(self, text, font_name, font_size):
        return len(str(text)) * float(font_size) * 0.45

    def setFont(self, *_args, **_kwargs):
        return None

    def drawString(self, x, y, text):
        self.text_calls.append({"kind": "drawString", "x": float(x), "y": float(y), "text": str(text)})

    def drawCentredString(self, x, y, text):
        self.text_calls.append({"kind": "drawCentredString", "x": float(x), "y": float(y), "text": str(text)})

    def drawRightString(self, x, y, text):
        self.text_calls.append({"kind": "drawRightString", "x": float(x), "y": float(y), "text": str(text)})

    def line(self, x1, y1, x2, y2):
        self.line_calls.append({"x1": float(x1), "y1": float(y1), "x2": float(x2), "y2": float(y2)})

    def roundRect(self, x, y, w, h, r, fill=0, stroke=1):
        self.round_rect_calls.append({"x": float(x), "y": float(y), "w": float(w), "h": float(h), "r": float(r), "fill": int(fill), "stroke": int(stroke)})

    def rect(self, *_args, **_kwargs):
        return None

    def beginPath(self):
        class _Path:
            def moveTo(self, *_args):
                return None

            def lineTo(self, *_args):
                return None

            def close(self):
                return None

        return _Path()

    def showPage(self):
        return None

    def __getattr__(self, _name):
        return lambda *args, **kwargs: None


class _ColorConst:
    def __init__(self, r=0.5, g=0.5, b=0.5):
        self.red = r
        self.green = g
        self.blue = b


class _Colors:
    def Color(self, r=0, g=0, b=0, alpha=1):
        return _ColorConst(r, g, b)


class FakeModule:
    PAGE_W = 600
    PAGE_H = 800
    SAFE_X = 36
    FOOTER_Y = 0
    GOLD = _ColorConst(0.83, 0.68, 0.21)
    GOLD2 = _ColorConst(0.90, 0.75, 0.30)
    PANEL = _ColorConst(0.10, 0.10, 0.10)
    PANEL2 = _ColorConst(0.12, 0.12, 0.12)
    PANEL_RED = _ColorConst(0.20, 0.05, 0.05)
    BLUE = _ColorConst(0.18, 0.45, 0.78)
    PANEL_BLUE = _ColorConst(0.10, 0.20, 0.35)
    SOFT = _ColorConst(0.6, 0.6, 0.6)
    WHITE = _ColorConst(1.0, 1.0, 1.0)
    RED = _ColorConst(0.78, 0.18, 0.18)
    RED_D = _ColorConst(0.58, 0.12, 0.12)
    BLUE_D = _ColorConst(0.12, 0.28, 0.50)
    BLACK = _ColorConst(0.0, 0.0, 0.0)
    MUTED = _ColorConst(0.5, 0.5, 0.5)
    colors = _Colors()
    math = _math

    def __init__(self):
        self.panel_calls = []
        self.para_calls = []
        self.calls = []

    def __getattr__(self, _name):
        return lambda *args, **kwargs: None

    def stat_card(self, c, x, y, w, h, *_args):
        self.panel_calls.append({"x": float(x), "y": float(y), "w": float(w), "h": float(h), "kind": "stat"})

    def page_base(self, *_args, **_kwargs):
        return None

    def panel(self, c, x, y, w, h, *args, **kwargs):
        title = args[0] if len(args) > 0 else kwargs.get("title")
        self.panel_calls.append({"x": float(x), "y": float(y), "w": float(w), "h": float(h), "title": title, "kind": "panel"})

    def set_font(self, c, font, size, color):
        self.calls.append((font, float(size), color))
        c.setFont(font, size)

    def para(self, c, text, x, y, w, h, **kwargs):
        self.para_calls.append({"text": str(text), "x": float(x), "y": float(y), "w": float(w), "h": float(h), "kwargs": dict(kwargs)})

    def target(self, *_args, **_kwargs):
        return None

    def method_bars(self, *_args, **_kwargs):
        return None

    def bars(self, *_args, **_kwargs):
        return None


SAMPLE_BLOCKS = {
    "_layout_safety": {},
    "fighter_a": "Max Holloway",
    "fighter_b": "Justin Gaethje",
    "confidence_band": "55%",
    "volatility": "42%",
    "summary": "Pressure-versus-structure headline.",
    "control_zone": "Max controls outcomes when first touch forces Justin to reset before second-phase counters.",
    "danger_zone": "Justin flips exchanges if Max exits square after first burst and gives free second entries.",
    "command_read": "Keep Max patient after first success and deny Justin direct reset reads.",
    "matchup_snapshot": "Model-derived instability versus structure read.",
    "event_name": "UFC 300",
    "event_date": "2026-07-12",
    "report_id": "ARISA-MAX-GAETHJE-001",
}


def _run(fn, blocks_override=None):
    module = FakeModule()
    canvas = DummyCanvas()
    blocks = copy.deepcopy(SAMPLE_BLOCKS)
    if isinstance(blocks_override, dict):
        blocks.update(copy.deepcopy(blocks_override))
    blocks["_layout_safety"] = {
        "logo_blend_ok": True,
        "logo_black_tile_risk": False,
        "source_map": {"rows_separated": True, "source_url_statement_separated": True},
        "dashboard_lens_depth_passed": True,
        "round_heading_body_clear_passed": True,
    }
    params = inspect.signature(fn).parameters
    args = [module, canvas, blocks]
    while len(args) < len(params):
        args.append(0)
    fn(*args[: len(params)])
    return module, canvas, blocks


def _preview():
    return {
        "selected_matchup": {
            "fighter_a": "Max Holloway",
            "fighter_b": "Justin Gaethje",
            "event_name": "UFC 300",
            "event_date": "2026-07-12",
            "promotion": "UFC",
            "source_url": "https://www.ufc.com/event/ufc-300",
            "source_type": "official",
        }
    }


def _render_output(tmp_path):
    os.environ["BUTTON2_PDF_OUTPUT_ROOT"] = str(tmp_path)
    out = renderer.render_button2_template_pack_asset_pdf(_preview())
    pdf_path = tmp_path / "max_holloway_vs_justin_gaethje_v6_test.pdf"
    pdf_path.write_bytes(out["pdf_bytes"])
    reader = PdfReader(io.BytesIO(out["pdf_bytes"]))
    text = "\n".join((page.extract_text() or "") for page in reader.pages)
    return out, pdf_path, text, len(reader.pages)


def _queue_rows():
    rows = app_module.load_button2_queue_readonly()
    assert rows, "canonical queue rows required"
    return rows


def _success_text_for_selected(selected):
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
        + "\n".join(app_module._BUTTON2_REQUIRED_PREMIUM_MARKERS)
        + "\n"
        + "\n".join(f"{a} {b}" for a, b in app_module._BUTTON2_REQUIRED_PREMIUM_MARKER_ALTERNATIVES)
        + "\n"
        + "\n".join(app_module._BUTTON2_REQUIRED_V29_LAYOUT_MARKERS)
        + "\n"
    )


def _layout_safety_stub():
    return {
        "logo_blend_ok": True,
        "logo_black_tile_risk": False,
        "operator_note_present": False,
        "operator_note_absent_passed": True,
        "page_2_strip_collision_passed": True,
        "page_2_dashboard_fit_passed": True,
        "page_2_lower_modules_fit_passed": True,
        "page_5_operator_use_fit_passed": True,
        "page_5_side_panel_fit_passed": True,
        "page_5_customer_operator_fit_passed": True,
        "page_6_table_density_passed": True,
        "page_14_round_fit_passed": True,
        "page_14_round_outlook_fit_passed": True,
        "page_14_round_balance_passed": True,
        "page_16_scorecard_fit_passed": True,
        "page_16_scorecard_integration_passed": True,
        "page_17_stoppage_fit_passed": True,
        "page_17_stoppage_rhythm_passed": True,
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


def test_page_2_round_control_projection_fits_all_three_rounds():
    _m, canvas, blocks = _run(renderer._draw_executive)
    round_tokens = {"R1", "R2", "R3"}
    drawn = {t["text"] for t in canvas.text_calls if t["kind"] == "drawCentredString" and t["text"] in round_tokens}
    assert drawn == round_tokens


def test_page_2_method_probability_labels_bars_values_fit():
    _m, _c, blocks = _run(renderer._draw_executive)
    # page_2_lower_modules_fit_passed and page_2_dashboard_fit_passed are now tested in v7 microfit suite


def test_page_2_risk_control_card_has_safe_width():
    module, _c, blocks = _run(renderer._draw_executive)
    candidates = [p for p in module.panel_calls if abs(p["y"] - 50.0) < 0.2 and abs(p["h"] - 80.0) < 0.2]
    assert len(candidates) > 0, "Risk Control card not found at new geometry"
    rightmost = sorted(candidates, key=lambda p: p["x"])[-1]
    assert rightmost["w"] >= 108


def test_page_5_customer_meaning_text_not_crossed_by_divider():
    _m, canvas, blocks = _run(renderer._draw_fighter_architecture_radar)
    divider = [line for line in canvas.line_calls if abs(line["y1"] - line["y2"]) < 0.001 and abs(line["y1"] - 310.0) < 2.0]
    row_text = [t["y"] for t in canvas.text_calls if t["kind"] == "drawString" and t["text"] in {"CONTROL", "DANGER", "FLIP"}]
    assert divider
    assert row_text
    assert max(row_text) < min(line["y1"] for line in divider)
    assert blocks["_layout_safety"].get("page_5_customer_operator_fit_passed") is True


def test_page_5_operator_use_text_fits_inside_panel():
    _m, _c, blocks = _run(renderer._draw_fighter_architecture_radar)
    assert blocks["_layout_safety"].get("page_5_operator_use_fit_passed") is True
    assert blocks["_layout_safety"].get("page_5_customer_operator_fit_passed") is True


def test_page_14_round_cards_balanced_for_long_names():
    _m, _c, blocks = _run(
        renderer._draw_round_control_graph,
        {
            "fighter_a": "Maximillian Alexander Holloway",
            "fighter_b": "Justin Xavier Gaethje",
        },
    )
    assert blocks["_layout_safety"].get("page_14_round_balance_passed") is True
    assert blocks["_layout_safety"].get("page_14_round_outlook_fit_passed") is True


def test_page_16_scorecard_commentary_centered_and_integrated():
    module, _c, blocks = _run(renderer._draw_scorecard_scenario)
    commentary = [p for p in module.panel_calls if abs(p["h"] - 92.0) < 0.5 and abs(p["y"] - 176.0) < 0.5]
    assert commentary
    assert blocks["_layout_safety"].get("page_16_scorecard_integration_passed") is True


def test_page_17_stoppage_chart_and_panels_have_balanced_spacing():
    _m, _c, blocks = _run(renderer._draw_method_probability_chart)
    assert blocks["_layout_safety"].get("page_17_stoppage_rhythm_passed") is True
    assert blocks["_layout_safety"].get("page_17_stoppage_fit_passed") is True


def test_final_delivery_gate_blocks_page_2_lower_module_clipping(tmp_path):
    preview = _preview()
    out, pdf_path, text, page_count = _render_output(tmp_path)
    layout_safety = dict(out.get("layout_safety", {}))
    layout_safety["page_2_lower_modules_fit_passed"] = False
    ok, violations = app_module._selected_matchup_passes_strict_pdf_quality_gate(
        preview["selected_matchup"],
        {"output_path": str(pdf_path), "output_filename": pdf_path.name, "report_id": "max_holloway_vs_justin_gaethje_ufc_300"},
        text,
        page_count,
        layout_safety,
    )
    assert ok is False
    assert "final_delivery_fit_polish_failed:page_2_lower_modules_fit_passed" in violations


def test_final_delivery_gate_blocks_page_5_text_divider_collision(tmp_path):
    preview = _preview()
    out, pdf_path, text, page_count = _render_output(tmp_path)
    layout_safety = dict(out.get("layout_safety", {}))
    layout_safety["page_5_customer_operator_fit_passed"] = False
    ok, violations = app_module._selected_matchup_passes_strict_pdf_quality_gate(
        preview["selected_matchup"],
        {"output_path": str(pdf_path), "output_filename": pdf_path.name, "report_id": "max_holloway_vs_justin_gaethje_ufc_300"},
        text,
        page_count,
        layout_safety,
    )
    assert ok is False
    assert "final_delivery_fit_polish_failed:page_5_customer_operator_fit_passed" in violations


def test_event_binding_gate_still_passes(tmp_path):
    preview = _preview()
    out, pdf_path, text, page_count = _render_output(tmp_path)
    layout_safety = dict(out.get("layout_safety", {}))
    ok, violations = app_module._selected_matchup_passes_strict_pdf_quality_gate(
        preview["selected_matchup"],
        {"output_path": str(pdf_path), "output_filename": pdf_path.name, "report_id": "max_holloway_vs_justin_gaethje_ufc_300"},
        text,
        page_count,
        layout_safety,
    )
    assert "event_binding_incomplete_no_event_name" not in violations
    assert "event_binding_incomplete_no_event_date" not in violations
    assert "event_binding_unknown_event_in_pdf" not in violations


def test_sample_bleed_gate_still_passes(tmp_path):
    preview = _preview()
    out, pdf_path, text, page_count = _render_output(tmp_path)
    layout_safety = dict(out.get("layout_safety", {}))
    layout_safety["dashboard_lens_depth_passed"] = True
    layout_safety["page_2_lower_modules_fit_passed"] = True
    layout_safety["page_5_customer_operator_fit_passed"] = True
    layout_safety["page_14_round_balance_passed"] = True
    layout_safety["page_16_scorecard_integration_passed"] = True
    layout_safety["page_17_stoppage_rhythm_passed"] = True
    ok, violations = app_module._selected_matchup_passes_strict_pdf_quality_gate(
        preview["selected_matchup"],
        {"output_path": str(pdf_path), "output_filename": pdf_path.name, "report_id": "max_holloway_vs_justin_gaethje_ufc_300"},
        text,
        page_count,
        layout_safety,
    )
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
            "layout_safety": _layout_safety_stub(),
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
            "layout_safety": _layout_safety_stub(),
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
