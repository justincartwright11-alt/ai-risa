import inspect
import copy
import math as _math
import pytest
from operator_dashboard import button2_template_pack_asset_renderer_v1 as renderer


class DummyCanvas:
    def __init__(self):
        self.text_calls = []
        self.line_calls = []
        self.rect_calls = []
        self.round_rect_calls = []
        self.current_font = ("Helvetica", 8.0)
        self.page_count = 0

    def stringWidth(self, text, fontName, fontSize):
        return len(text) * fontSize * 0.45

    def setFont(self, name, size):
        self.current_font = (name, float(size))

    def drawString(self, x, y, text):
        self.text_calls.append({"kind": "drawString", "x": float(x), "y": float(y), "text": str(text)})

    def drawCentredString(self, x, y, text):
        self.text_calls.append({"kind": "drawCentredString", "x": float(x), "y": float(y), "text": str(text)})

    def drawRightString(self, x, y, text):
        self.text_calls.append({"kind": "drawRightString", "x": float(x), "y": float(y), "text": str(text)})

    def line(self, x1, y1, x2, y2):
        self.line_calls.append({"x1": float(x1), "y1": float(y1), "x2": float(x2), "y2": float(y2)})

    def rect(self, x, y, w, h, fill=0, stroke=1):
        self.rect_calls.append({"x": float(x), "y": float(y), "w": float(w), "h": float(h), "fill": int(fill), "stroke": int(stroke)})

    def roundRect(self, x, y, w, h, r, fill=0, stroke=1):
        self.round_rect_calls.append({"x": float(x), "y": float(y), "w": float(w), "h": float(h), "r": float(r), "fill": int(fill), "stroke": int(stroke)})

    def showPage(self):
        self.page_count += 1

    def beginPath(self):
        class _Path:
            def __init__(self):
                self.points = []

            def moveTo(self, x, y):
                self.points.append((float(x), float(y)))

            def lineTo(self, x, y):
                self.points.append((float(x), float(y)))

            def close(self):
                return None

            def __getattr__(self, name):
                return lambda *args, **kwargs: None
        return _Path()

    def __getattr__(self, name):
        return lambda *args, **kwargs: None


class _ColorConst:
    """Stub color constant with .red .green .blue float attributes."""
    def __init__(self, r=0.5, g=0.5, b=0.5):
        self.red = r
        self.green = g
        self.blue = b


class _Colors:
    def Color(self, r=0, g=0, b=0, alpha=1):
        return _ColorConst(r, g, b)
    def __call__(self, *args, **kwargs):
        return None
    def __getattr__(self, name):
        return lambda *args, **kwargs: None


class FakeModule:
    PAGE_W = 600
    PAGE_H = 800
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
    FOOTER_Y = 0
    SAFE_X = 36
    SAFE_Y = 36
    SAFE_W = 528
    SAFE_H = 720
    FOOTER_RESERVED_HEIGHT = 36
    w = 600
    h = 800
    MIN_BODY_FONT_SIZE = 8.0
    MIN_LABEL_FONT_SIZE = 8.0
    MIN_COMMENTARY_FONT_SIZE = 8.0
    colors = _Colors()
    math = _math

    def __getattr__(self, name):
        return lambda *args, **kwargs: None

    def __init__(self):
        self.calls = []
        self.panel_calls = []
        self.font_calls = []
        self.para_calls = []
        self.shape_calls = []

    def stat_card(self, c, x, y, w, h, title, short, color, desc):
        self.calls.append(("stat_card", x, y, w, h, title, short, color, desc))

    def page_base(self, c, page, title):
        self.calls.append(("page_base", page, title))

    def panel(self, c, x, y, w, h, *args, **kwargs):
        self.calls.append(("panel", x, y, w, h))
        title = args[0] if len(args) > 0 else kwargs.get("title")
        border = args[1] if len(args) > 1 else kwargs.get("border")
        fill = args[2] if len(args) > 2 else kwargs.get("fill")
        self.panel_calls.append(
            {
                "x": float(x),
                "y": float(y),
                "w": float(w),
                "h": float(h),
                "title": title,
                "border": border,
                "fill": fill,
            }
        )

    def set_font(self, c, font, size, color):
        self.calls.append(("set_font", font, size, color))
        self.font_calls.append({"font": font, "size": float(size), "color": color})
        c.setFont(font, size)

    def para(self, c, text, x, y, w, h, **kwargs):
        self.calls.append(("para", text, x, y, w, h))
        self.para_calls.append({"text": str(text), "x": float(x), "y": float(y), "w": float(w), "h": float(h), "kwargs": dict(kwargs)})

    def drawString(self, c, x, y, text):
        self.calls.append(("drawString", x, y, text))

    def line(self, c, x1, y1, x2, y2):
        self.calls.append(("line", x1, y1, x2, y2))
        self.shape_calls.append({"kind": "line", "x1": float(x1), "y1": float(y1), "x2": float(x2), "y2": float(y2)})

    def rect(self, c, x, y, w, h):
        self.calls.append(("rect", x, y, w, h))
        self.shape_calls.append({"kind": "rect", "x": float(x), "y": float(y), "w": float(w), "h": float(h)})

    def fill(self, c, color):
        self.calls.append(("fill", color))

    def target(self, c, x, y, r, color):
        self.calls.append(("target", x, y, r, color))

    def method_bars(self, c, bars, x, y, w, h):
        self.calls.append(("method_bars", x, y, w, h))

    def bars(self, c, bars, x, y, w, h):
        self.calls.append(("bars", x, y, w, h))


SAMPLE_BLOCKS = {
    "_layout_safety": {},
    "fighter_a": "Anthony Joshua",
    "fighter_b": "Daniel Dubois",
    "confidence_band": "55%",
    "volatility": "42%",
    "summary": "Joshua controls distance and applies early pressure.",
    "control_zone": "Joshua owns mid-range and denies reset.",
    "danger_zone": "Dubois lands a clean right and forces a reset.",
    "command_read": "Break Joshua structure in rounds 3-6.",
    "operator_use": "CONTROL: Keep structure | DANGER: Avoid reset | FLIP: Win late rounds",
}


def _run(fn):
    module = FakeModule()
    c = DummyCanvas()
    blocks = copy.deepcopy(SAMPLE_BLOCKS)
    blocks["_layout_safety"] = {}
    params = inspect.signature(fn).parameters
    args = [module, c, blocks]
    while len(args) < len(params):
        args.append(0)
    fn(*args[:len(params)])
    return module, c, blocks


def _visual_layout_safe(layout_safety):
    footer_pages = layout_safety.get("footer_safe_zone_pages", {}) if isinstance(layout_safety, dict) else {}
    footer_safe = all(bool(info.get("safe")) for info in footer_pages.values()) if footer_pages else False
    source_map = layout_safety.get("source_map", {}) if isinstance(layout_safety, dict) else {}
    source_safe = bool(source_map.get("rows_separated", False)) and bool(source_map.get("source_url_statement_separated", False))
    return bool(
        layout_safety.get("logo_blend_ok", False)
        and not layout_safety.get("logo_black_tile_risk", False)
        and not layout_safety.get("operator_note_present", False)
        and bool(layout_safety.get("operator_note_absent_passed", True))
        and bool(layout_safety.get("dashboard_lens_depth_passed", False))
        and bool(layout_safety.get("round_heading_body_clear_passed", False))
        and footer_safe
        and source_safe
        and bool(layout_safety.get("readable_min_font_passed", True))
        and bool(layout_safety.get("round_outlook_centered_passed", True))
        and bool(layout_safety.get("tactical_edge_overlap_passed", True))
        and bool(layout_safety.get("scorecard_readability_passed", True))
        and bool(layout_safety.get("stoppage_readability_passed", True))
    )


@pytest.mark.parametrize("fn, expect_marker", [
    (renderer._draw_executive, "page_2_strip_collision_passed"),
    (renderer._draw_fighter_architecture_radar, "page_5_operator_use_fit_passed"),
    (renderer._draw_tactical_edge_table, "page_6_table_density_passed"),
    (renderer._draw_round_control_graph, "page_14_round_fit_passed"),
    (renderer._draw_scorecard_scenario, "page_16_scorecard_fit_passed"),
    (renderer._draw_method_probability_chart, "page_17_stoppage_fit_passed"),
])
def test_fit_flow_marker_set(fn, expect_marker):
    module, _, blocks = _run(fn)
    assert blocks["_layout_safety"].get(expect_marker) is True, f"Marker {expect_marker!r} not set in _layout_safety for {fn.__name__}"
    assert module.calls, f"No geometry calls recorded for {fn.__name__}"


def test_page_2_strip_zone_no_collision_with_lower_modules():
    module, _, blocks = _run(renderer._draw_executive)
    assert blocks["_layout_safety"].get("page_2_strip_collision_passed") is True

    lower_modules = [p for p in module.panel_calls if abs(p["h"] - 84.0) < 0.01 and p["y"] <= 80.0]
    strip_cards = [p for p in module.panel_calls if abs(p["y"] - 159.0) < 0.01 and abs(p["h"] - 35.0) < 0.01]
    assert len(lower_modules) == 3
    assert len(strip_cards) == 4

    upper_of_lower = max(p["y"] + p["h"] for p in lower_modules)
    lower_of_strip = min(p["y"] for p in strip_cards)
    assert lower_of_strip >= upper_of_lower


def test_page_5_operator_use_rows_stay_inside_panel_bounds():
    module, canvas, blocks = _run(renderer._draw_fighter_architecture_radar)
    assert blocks["_layout_safety"].get("page_5_operator_use_fit_passed") is True

    operator_panels = [p for p in module.panel_calls if abs(p["y"] - 72.0) < 0.01 and abs(p["h"] - 112.0) < 0.01]
    assert len(operator_panels) == 1
    op_panel = operator_panels[0]

    assert any("OPERATOR USE" in t["text"] for t in canvas.text_calls)

    value_draws = [
        t for t in canvas.text_calls
        if t["kind"] == "drawString"
        and (op_panel["x"] + 80) <= t["x"] <= (op_panel["x"] + op_panel["w"] - 6)
        and (op_panel["y"] + 8) <= t["y"] <= (op_panel["y"] + op_panel["h"] - 8)
    ]
    assert len(value_draws) >= 3


def test_page_6_table_density_within_bounds_and_metadata_populated():
    module, _, blocks = _run(renderer._draw_tactical_edge_table)
    safety = blocks["_layout_safety"]

    assert safety.get("page_6_table_density_passed") is True
    assert safety.get("tactical_edge_overlap_passed") is True
    assert safety.get("readable_min_font_passed") is True
    assert safety.get("dense_page_layout_safe") is True
    assert safety.get("footer_safe_zone_pages", {}).get("6", {}).get("safe") is True

    page_bounds = safety.get("page_bounds", {}).get("6", {})
    assert page_bounds.get("overlap_detected") is False
    assert float(page_bounds.get("min_font_size", 0.0)) >= renderer.MIN_TABLE_FONT_SIZE

    command_panels = [p for p in module.panel_calls if abs(p["y"] - 94.0) < 0.01 and abs(p["h"] - 74.0) < 0.01]
    assert len(command_panels) == 1


def test_page_14_round_cards_are_centered_and_balanced():
    _, canvas, blocks = _run(renderer._draw_round_control_graph)
    assert blocks["_layout_safety"].get("page_14_round_fit_passed") is True
    assert blocks["_layout_safety"].get("round_outlook_centered_passed") is True

    cards = [r for r in canvas.round_rect_calls if abs(r["y"] - 186.0) < 0.01 and abs(r["h"] - 152.0) < 0.01]
    assert len(cards) == 3

    cards = sorted(cards, key=lambda r: r["x"])
    gap_left = cards[1]["x"] - (cards[0]["x"] + cards[0]["w"])
    gap_right = cards[2]["x"] - (cards[1]["x"] + cards[1]["w"])
    assert pytest.approx(cards[0]["w"], abs=0.01) == cards[1]["w"]
    assert pytest.approx(cards[1]["w"], abs=0.01) == cards[2]["w"]
    assert pytest.approx(gap_left, abs=0.01) == gap_right


def test_page_16_scorecard_commentary_aligns_with_commentary_panel():
    module, _, blocks = _run(renderer._draw_scorecard_scenario)
    safety = blocks["_layout_safety"]
    assert safety.get("page_16_scorecard_fit_passed") is True
    assert safety.get("scorecard_readability_passed") is True

    commentary_panels = [p for p in module.panel_calls if abs(p["y"] - 94.0) < 0.01 and abs(p["h"] - 76.0) < 0.01]
    assert len(commentary_panels) == 1
    panel = commentary_panels[0]

    commentary_blocks = [p for p in module.para_calls if "premium 48-47 lane" in p["text"]]
    assert len(commentary_blocks) == 1
    para = commentary_blocks[0]

    assert para["x"] >= panel["x"]
    assert para["y"] >= panel["y"]
    assert para["x"] + para["w"] <= panel["x"] + panel["w"]
    assert para["y"] + para["h"] <= panel["y"] + panel["h"]
    assert safety.get("page_bounds", {}).get("16", {}).get("overlap_detected") is False


def test_page_17_stoppage_panels_are_balanced():
    module, _, blocks = _run(renderer._draw_method_probability_chart)
    safety = blocks["_layout_safety"]
    assert safety.get("page_17_stoppage_fit_passed") is True
    assert safety.get("stoppage_readability_passed") is True

    lower_panels = [p for p in module.panel_calls if abs(p["y"] - 88.0) < 0.01 and abs(p["h"] - 76.0) < 0.01]
    assert len(lower_panels) == 2
    lower_panels = sorted(lower_panels, key=lambda p: p["x"])

    left, right = lower_panels
    gap = right["x"] - (left["x"] + left["w"])
    assert pytest.approx(left["w"], abs=0.01) == right["w"]
    assert pytest.approx(gap, abs=0.01) == 12.0


def test_gate_metadata_reports_fit_flow_pass_and_fail_states():
    module = FakeModule()
    canvas = DummyCanvas()
    blocks = copy.deepcopy(SAMPLE_BLOCKS)
    blocks["control_zone"] = (
        "Anthony Joshua pins Daniel Dubois behind the first touch, exits on angle, and keeps the scoring lane "
        "stable through each reset."
    )
    blocks["danger_zone"] = (
        "Daniel Dubois flips momentum when Anthony Joshua squares after contact and leaves a clean second-phase "
        "counter lane before reset."
    )
    blocks["command_read"] = (
        "Anthony Joshua must force Daniel Dubois to reset twice before re-entry and deny free center-line counters "
        "during late-round stress."
    )
    blocks["_layout_safety"] = {
        "logo_blend_ok": True,
        "logo_black_tile_risk": False,
        "source_map": {
            "rows_separated": True,
            "source_url_statement_separated": True,
        },
    }

    renderer._draw_executive(module, canvas, blocks)
    renderer._draw_fighter_architecture_radar(module, canvas, blocks)
    renderer._draw_tactical_edge_table(module, canvas, blocks)
    renderer._draw_round_control_graph(module, canvas, blocks)
    renderer._draw_scorecard_scenario(module, canvas, blocks)
    renderer._draw_method_probability_chart(module, canvas, blocks)

    safety = blocks["_layout_safety"]
    # Lens-depth pass/fail belongs to content-depth tests; this test validates fit/flow gate aggregation.
    safety["dashboard_lens_depth_passed"] = True
    assert _visual_layout_safe(safety) is True

    fail_safety = copy.deepcopy(safety)
    fail_safety["scorecard_readability_passed"] = False
    assert _visual_layout_safe(fail_safety) is False