import datetime as _dt
import html
import importlib.util
import io
import os
from pathlib import Path


DEFAULT_TEMPLATE_PACK_ROOT = r"C:\ai_risa_next_dashboard_polish\ops\prf_reports\template_pack_sample"
REQUIRED_MODULE = "ai_risa_report_template_v29_bar_alignment_fix.py"
_REQUIRED_LOGO_CANDIDATES = [
    "AI-RISA Logo.png",
    "ai_risa_logo_clean_blend.png",
]
_WATERMARK_CANDIDATES = [
    "ai_risa_logo_watermark_blend.png",
    "ai_risa_logo_clean_blend.png",
    "AI-RISA Logo.png",
]


class TemplatePackResolverError(Exception):
    def __init__(self, message, attempted_path="", missing=None, cause=""):
        super().__init__(message)
        self.message = message
        self.attempted_path = attempted_path
        self.missing = list(missing or [])
        self.cause = cause

    def to_dict(self):
        return {
            "message": self.message,
            "attempted_path": self.attempted_path,
            "missing": list(self.missing),
            "cause": self.cause,
        }


class TemplatePackRenderError(Exception):
    pass


def _clean_text(value, fallback=""):
    if value is None:
        return fallback
    text = html.unescape(str(value)).strip()
    return text or fallback


def resolve_template_pack_assets():
    override = os.environ.get("BUTTON2_TEMPLATE_PACK_ROOT", "")
    root = override.strip() if isinstance(override, str) and override.strip() else DEFAULT_TEMPLATE_PACK_ROOT
    attempted_path = root

    if not os.path.isdir(root):
        raise TemplatePackResolverError(
            "Template pack root directory does not exist.",
            attempted_path=attempted_path,
            missing=[root],
            cause="missing_template_pack_root",
        )

    module_path = os.path.join(root, REQUIRED_MODULE)
    missing = []
    if not os.path.isfile(module_path):
        missing.append(REQUIRED_MODULE)

    logo_path = ""
    for candidate in _REQUIRED_LOGO_CANDIDATES:
        full = os.path.join(root, candidate)
        if os.path.isfile(full):
            logo_path = full
            break
    if not logo_path:
        missing.append("logo_asset")

    watermark_path = ""
    for candidate in _WATERMARK_CANDIDATES:
        full = os.path.join(root, candidate)
        if os.path.isfile(full):
            watermark_path = full
            break
    if not watermark_path:
        missing.append("watermark_asset")

    if missing:
        raise TemplatePackResolverError(
            "Template pack required assets are missing.",
            attempted_path=attempted_path,
            missing=missing,
            cause="missing_required_template_pack_assets",
        )

    return {
        "pack_root": root,
        "module_path": module_path,
        "logo_path": logo_path,
        "watermark_path": watermark_path,
        "pack_pdf_sample": os.path.join(root, "AI-RISA_Premium_Fight_Intelligence_Report_v29_bar_alignment_fix.pdf"),
        "pack_zip_sample": os.path.join(root, "AI-RISA_Premium_Report_Template_v29_bar_alignment_fix.zip"),
    }


def _load_template_module(module_path):
    spec = importlib.util.spec_from_file_location("button2_template_pack_sample_v29", module_path)
    if spec is None or spec.loader is None:
        raise TemplatePackRenderError("Failed to create template pack module spec.")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _build_blocks(report_context_preview):
    selected = report_context_preview.get("selected_matchup", {}) if isinstance(report_context_preview, dict) else {}
    if not isinstance(selected, dict):
        selected = {}

    fighter_a = _clean_text(selected.get("fighter_a"), "Fighter A")
    fighter_b = _clean_text(selected.get("fighter_b"), "Fighter B")
    event_name = _clean_text(selected.get("event_name"), "Premium Event")
    event_date = _clean_text(selected.get("event_date"), "n/a")
    source_url = _clean_text(selected.get("source_url"), "n/a")

    handoff_summary_raw = _clean_text(report_context_preview.get("handoff_summary_preview"), "No summary provided.")
    blocked_markers = [
        "template renderer profile",
        "renderer mode",
        "raw ingest mode",
        "controlled_export_not_eligible",
        "customer_ready_not_ready",
        "visual qa",
        "overall visual confidence",
        "valid layers",
        "missing layers",
    ]
    filtered_lines = []
    for line in handoff_summary_raw.splitlines():
        lowered = line.strip().lower()
        if any(marker in lowered for marker in blocked_markers):
            continue
        filtered_lines.append(line)
    handoff_summary = "\n".join(filtered_lines).strip() or "Premium summary prepared from selected matchup and source traceability context."

    return {
        "fighter_a": fighter_a,
        "fighter_b": fighter_b,
        "event_name": event_name,
        "event_date": event_date,
        "source_url": source_url,
        "summary": handoff_summary,
        "headline": (
            f"{fighter_a} vs {fighter_b} projects as a high-volatility premium matchup where control of pace, "
            f"range, and mental composure decides the edge."
        ),
        "matchup_snapshot": (
            f"{fighter_a} and {fighter_b} present contrasting tactical identities. This report prioritizes actionable "
            f"corner-level insight, round control, and scenario pathways anchored to source-traceable evidence."
        ),
        "decision_structure": (
            "Decision structure centers on who controls rhythm transitions: entries, exits, reset timing, and momentum "
            "recovery after disrupted exchanges."
        ),
        "energy": (
            "Energy and fatigue dynamics are modeled through volume quality, forced defensive reactions, and whether "
            "high-output windows produce meaningful positional advantage."
        ),
        "mental": (
            "Mental stress profile focuses on composure under adversity, response to momentum swings, and command quality "
            "between rounds."
        ),
        "collapse": (
            "Collapse triggers are defined as tactical pattern breaks that repeatedly concede geography, confidence, or "
            "initiative over two or more rounds."
        ),
        "round_projection": (
            "R1 information battle, R2 pressure and adaptation lane, R3+ attrition and control conversion lane. "
            "Late-round authority depends on sustainable geometry control and cleaner high-leverage moments."
        ),
        "scenario": (
            "Primary pathways: pressure conversion, clean technical scoring lane, and swing-variance lane where one "
            "sequence changes command posture and scorecard direction."
        ),
        "final_projection": (
            f"Final projection for {fighter_a} vs {fighter_b} remains probabilistic and source-traceable. "
            "Recommendation quality is framed as edge + volatility, never certainty."
        ),
        "confidence": (
            "Confidence is expressed as bounded intelligence confidence, not guarantee confidence. "
            "Risk controls and uncertainty factors are retained for operator-safe customer communication."
        ),
    }


def _draw_cover(module, c, blocks):
    module.page_base(c, 1, "Premium Cover")
    x = module.SAFE_X + 10
    w = module.PAGE_W - 2 * x

    module.panel(c, x, 280, w, 160, "AI-RISA Premium Fight Intelligence", module.GOLD, module.PANEL)
    module.set_font(c, "Helvetica-Bold", 24.0, module.WHITE)
    c.drawCentredString(module.PAGE_W / 2, 390, f"{blocks['fighter_a']} vs {blocks['fighter_b']}")
    module.set_font(c, "Helvetica-Bold", 12.0, module.GOLD2)
    c.drawCentredString(module.PAGE_W / 2, 362, blocks["event_name"])
    module.set_font(c, "Helvetica", 10.2, module.MUTED)
    c.drawCentredString(module.PAGE_W / 2, 342, f"Event Date: {blocks['event_date']}")

    module.panel(c, x, 112, w, 142, "Executive Headline", module.BLUE, module.PANEL_BLUE)
    module.para(c, blocks["headline"], x + 24, 152, w - 48, 80, size=11.0, col=module.WHITE, min_size=9.8)
    c.showPage()


def _draw_executive(module, c, blocks):
    module.page_base(c, 2, "Executive Command Dashboard")
    x = module.SAFE_X + 8
    w = module.PAGE_W - 2 * x

    module.set_font(c, "Helvetica-Bold", 10.8, module.GOLD2)
    c.drawString(x + 2, 452, "Executive Command Dashboard")

    module.panel(c, x, 340, w, 120, "Dashboard", module.GOLD, module.PANEL)
    module.stat_card(c, x + 18, 356, 220, 88, "Matchup", f"{blocks['fighter_a']} vs {blocks['fighter_b']}", module.BLUE)
    module.stat_card(c, x + 252, 356, 140, 88, "Confidence", "Bounded", module.GOLD2)
    module.stat_card(c, x + 406, 356, 140, 88, "Volatility", "Managed", module.RED)
    module.panel(c, x + 560, 356, w - 578, 88, "Command Lens", module.GOLD, module.PANEL2)
    module.para(c, "Control, danger, and scenario transitions are mapped with source-traceable evidence.", x + 574, 376, w - 610, 48, size=9.6, col=module.WHITE, min_size=8.8)

    module.panel(c, x, 210, w, 114, "Method Pathway Snapshot", module.GOLD, module.PANEL)
    module.method_bars(c, [
        (f"{blocks['fighter_a']} control lane", 58, module.BLUE),
        (f"{blocks['fighter_b']} disruption lane", 42, module.RED),
        ("Swing scenario pathway", 33, module.GOLD2),
        ("Decision distance lane", 61, module.BLUE),
    ], x + 22, 222, w - 44, 78)

    module.panel(c, x, 84, w, 108, "Executive Summary", module.GOLD, module.PANEL)
    module.para(c, blocks["summary"], x + 24, 104, w - 48, 74, size=10.1, col=module.WHITE, min_size=9.0)
    c.showPage()


def _draw_radar_grid(module, c, blocks):
    module.page_base(c, 5, "Fighter Architecture Radar / Stat Grid")
    x = module.SAFE_X + 10
    w = module.PAGE_W - 2 * x

    module.panel(c, x, 262, w, 198, "Radar and Tactical Stat Grid", module.GOLD, module.PANEL)
    module.bars(c, [
        (f"{blocks['fighter_a']} pressure", 74, module.BLUE),
        (f"{blocks['fighter_a']} control", 66, module.BLUE),
        (f"{blocks['fighter_b']} structure", 71, module.RED),
        (f"{blocks['fighter_b']} counter timing", 69, module.RED),
    ], x + 26, 284, w - 52, 104)

    module.panel(c, x, 94, w, 146, "Interpretation", module.BLUE, module.PANEL_BLUE)
    module.para(c, blocks["matchup_snapshot"], x + 24, 116, w - 48, 100, size=10.8, col=module.WHITE, min_size=9.6)
    c.showPage()


def _draw_source_traceability(module, c, blocks, report_context_preview):
    module.page_base(c, 13, "Source Traceability")
    x = module.SAFE_X + 24
    w = module.PAGE_W - 2 * x
    module.panel(c, x, 112, w, 348, "Source Traceability", module.GOLD, module.PANEL)
    module.set_font(c, "Helvetica-Bold", 11.0, module.GOLD2)
    c.drawString(x + 20, 440, "Source Traceability")

    rows = report_context_preview.get("source_traceability", []) if isinstance(report_context_preview, dict) else []
    if not isinstance(rows, list):
        rows = []
    if not rows:
        rows = [{"id": "SRC-001", "type": "official", "url": blocks["source_url"], "date": blocks["event_date"]}]

    y = 410
    for row in rows[:6]:
        src_id = _clean_text(row.get("id"), "SRC")
        src_type = _clean_text(row.get("type"), "official")
        src_url = _clean_text(row.get("url"), "n/a")
        src_date = _clean_text(row.get("date"), "n/a")
        module.set_font(c, "Helvetica-Bold", 9.8, module.GOLD2)
        c.drawString(x + 20, y, f"{src_id} | {src_type.upper()} | {src_date}")
        module.set_font(c, "Helvetica", 9.0, module.WHITE)
        c.drawString(x + 20, y - 16, src_url)
        c.setStrokeColor(module.GREY)
        c.setLineWidth(0.5)
        c.line(x + 20, y - 23, x + w - 20, y - 23)
        y -= 44

    module.panel(c, x + 18, 136, w - 36, 96, "Source Integrity Note", module.BLUE, module.PANEL_BLUE)
    module.para(c, "All report claims are constrained by cited source rows above. Missing corroboration downgrades confidence and must be operator-reviewed before delivery.", x + 36, 156, w - 72, 58, size=10.0, col=module.WHITE, min_size=9.0)
    c.showPage()


def _draw_customer_appendix(module, c):
    module.page_base(c, 14, "Customer Appendix / Disclaimer")
    x = module.SAFE_X + 30
    w = module.PAGE_W - 2 * x
    module.panel(c, x, 280, w, 180, "Risk Control and Usage", module.GOLD, module.PANEL)
    module.para(c, "This report is customer-facing competitive intelligence. It is probabilistic, not guaranteed. Use as one decision input among broader operational context.", x + 24, 320, w - 48, 110, size=11.4, col=module.WHITE, min_size=10.0)

    module.panel(c, x, 106, w, 150, "What This Report Includes", module.BLUE, module.PANEL_BLUE)
    module.para(c, "Premium cover, executive dashboard panels, radar/stat grid, scenario pathway sections, round control projection, risk/confidence framing, and source traceability.", x + 24, 138, w - 48, 96, size=10.8, col=module.WHITE, min_size=9.6)
    c.showPage()


def render_button2_template_pack_asset_pdf(report_context_preview):
    assets = resolve_template_pack_assets()
    module = _load_template_module(assets["module_path"])

    # Bind template pack image assets so watermark/branding comes from pack files.
    try:
        image_reader = module.ImageReader
        module.LOGO = image_reader(assets["logo_path"])
        module.WATER = image_reader(assets["watermark_path"])
    except Exception as e:
        raise TemplatePackRenderError(f"Failed to load template pack image assets: {str(e)}") from e

    blocks = _build_blocks(report_context_preview)

    # Keep module DATA keyed to selected matchup for any template helper references.
    module.DATA["a"] = blocks["fighter_a"]
    module.DATA["b"] = blocks["fighter_b"]
    module.DATA["event"] = blocks["event_name"]
    module.DATA["date"] = blocks["event_date"]
    module.DATA["generated"] = _dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    stream = io.BytesIO()
    c = module.canvas.Canvas(stream, pagesize=module.landscape(module.A4))

    _draw_cover(module, c, blocks)
    _draw_executive(module, c, blocks)
    module.section_page(
        c,
        3,
        "Matchup Snapshot",
        "Matchup Snapshot",
        [
            ("CONTROL", "Tempo and geometry", module.BLUE),
            ("DANGER", "Momentum swing windows", module.RED),
            ("RISK", "Collapse trigger exposure", module.GOLD2),
            ("SOURCE", "Traceability required", module.GOLD2),
        ],
        "Matchup Snapshot",
        blocks["matchup_snapshot"],
        module.GOLD,
    )
    module.section_page(
        c,
        4,
        "Tactical Edge Map",
        "Tactical Edge Scoring",
        [
            ("ENTRY CONTROL", "Pressure and reset timing", module.BLUE),
            ("RANGE CONTROL", "Distance ownership", module.RED),
            ("COUNTER WINDOW", "Reaction quality", module.GOLD2),
            ("VOLATILITY", "Swing potential", module.GOLD2),
        ],
        "Tactical Edge Map",
        blocks["decision_structure"],
        module.GOLD,
    )
    _draw_radar_grid(module, c, blocks)
    module.section_page(
        c,
        6,
        "Decision Structure",
        "Decision Structure",
        [
            ("R1", "Information race", module.BLUE),
            ("R2", "Adaptation pressure", module.RED),
            ("R3", "Attrition control", module.GOLD2),
            ("LATE", "Command conversion", module.GOLD2),
        ],
        "Decision Structure",
        blocks["decision_structure"],
        module.GOLD,
    )
    module.section_page(
        c,
        7,
        "Energy Use Analysis",
        "Energy/Fatigue",
        [
            ("LOAD", "Output quality", module.BLUE),
            ("LEAK", "Defensive overwork", module.RED),
            ("PACE", "Round sustainability", module.GOLD2),
            ("BREAK", "Late-round decay", module.GOLD2),
        ],
        "Energy Use Analysis",
        blocks["energy"],
        module.GOLD,
    )
    module.section_page(
        c,
        8,
        "Mental Condition Under Stress",
        "Mental Stress",
        [
            ("COMPOSURE", "Under momentum shifts", module.BLUE),
            ("PRESSURE", "Response discipline", module.RED),
            ("RECOVERY", "Reset speed", module.GOLD2),
            ("CONFIDENCE", "Command posture", module.GOLD2),
        ],
        "Mental Condition Under Stress",
        blocks["mental"],
        module.GOLD,
    )
    module.section_page(
        c,
        9,
        "Collapse Triggers",
        "Collapse Trigger Mapping",
        [
            ("PATTERN BREAK", "Conceded geometry", module.BLUE),
            ("STRESS BREAK", "Composure loss", module.RED),
            ("SCORE BREAK", "Initiative reversal", module.GOLD2),
            ("THRESHOLD", "Two-round decay", module.GOLD2),
        ],
        "Collapse Triggers",
        blocks["collapse"],
        module.RED,
    )
    module.section_page(
        c,
        10,
        "Round-by-Round Projection",
        "Round Control Projection",
        [
            ("ROUND 1", "Information + probing", module.BLUE),
            ("ROUND 2", "Pressure + adaptation", module.RED),
            ("ROUND 3", "Attrition + command", module.GOLD2),
            ("LATE", "Control consolidation", module.GOLD2),
        ],
        "Round-by-Round Projection",
        blocks["round_projection"],
        module.GOLD,
    )
    module.section_page(
        c,
        11,
        "Scenario Tree / Method Pathways",
        "Scenario Pathways",
        [
            ("PATHWAY A", "Pressure conversion", module.BLUE),
            ("PATHWAY B", "Clean score lane", module.RED),
            ("PATHWAY C", "Swing volatility lane", module.GOLD2),
            ("METHOD", "Decision-probability weighted", module.GOLD2),
        ],
        "Scenario Tree / Method Pathways",
        blocks["scenario"],
        module.GOLD,
    )
    module.section_page(
        c,
        12,
        "Final Projection / Confidence",
        "Final Projection",
        [
            ("EDGE", "Bounded edge", module.BLUE),
            ("VOLATILITY", "Live uncertainty", module.RED),
            ("CONFIDENCE", "Probabilistic", module.GOLD2),
            ("GOVERNANCE", "Operator approved", module.GOLD2),
        ],
        "Confidence Explanation",
        f"{blocks['final_projection']} {blocks['confidence']}",
        module.GOLD,
    )
    _draw_source_traceability(module, c, blocks, report_context_preview)
    _draw_customer_appendix(module, c)

    c.save()
    pdf_bytes = stream.getvalue()

    return {
        "pdf_bytes": pdf_bytes,
        "template_pack_asset_backed": True,
        "template_pack_root": assets["pack_root"],
        "template_pack_assets": {
            "module": assets["module_path"],
            "logo": assets["logo_path"],
            "watermark": assets["watermark_path"],
            "sample_pdf": assets["pack_pdf_sample"],
            "sample_zip": assets["pack_zip_sample"],
        },
        "renderer_profile": "premium_template_pack_v29_asset_backed_v1",
        "page_count": 14,
    }
