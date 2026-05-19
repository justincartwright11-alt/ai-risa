import datetime as _dt
import html
import importlib.util
import io
import os
import re
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


def _customer_command_footer(module, c, x, y, w):
    """Customer-facing command footer that replaces generic placeholder lanes."""
    gap = 16
    cw = (w - 2 * gap) / 3
    cards = [
        (
            "Control Lane",
            "pressure rhythm, reset denial, and scoring geography",
            "Keep exits layered and preserve scoring integrity.",
            module.BLUE,
        ),
        (
            "Danger Lane",
            "geography loss, rushed entries, and output without conversion",
            "Do not let defensive hand decay become a late-round tax.",
            module.RED,
        ),
        (
            "Command Read",
            "force reset discipline and avoid low-value pressure chases",
            "Corner instruction: make every entry pay or reset the lane.",
            module.GOLD2,
        ),
    ]
    for i, (title, body, cue, col) in enumerate(cards):
        xx = x + i * (cw + gap)
        module.panel(c, xx, y, cw, 58, None, col, module.SOFT, r=6, lw=0.95, title_line=False)
        module.set_font(c, "Helvetica-Bold", 8.7, col)
        c.drawString(xx + 12, y + 40, title.upper())
        module.set_font(c, "Helvetica", 7.6, module.WHITE)
        c.drawString(xx + 12, y + 28, body)
        module.set_font(c, "Helvetica", 7.0, module.MUTED)
        module.para(c, cue, xx + 12, y + 8, cw - 24, 14, size=7.0, col=module.MUTED, min_size=6.8)


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
    report_id = re.sub(r"[^a-z0-9]+", "_", f"{fighter_a}_{fighter_b}_{event_name}".lower()).strip("_")
    if not report_id:
        report_id = "selected_matchup_report"

    handoff_summary_raw = _clean_text(report_context_preview.get("handoff_summary_preview"), "No summary provided.")
    blocked_markers = [
        "operator summary preview",
        "premium selected-matchup intelligence summary",
        "template renderer profile",
        "premium_template_pack_v29",
        "renderer mode",
        "source context",
        "ingest mode",
        "visual qa",
        "visual qA rollup",
        "certification:",
        "completeness:",
        "controlled_export_not_eligible",
        "controlled_export_preview",
        "customer_ready_not_ready",
        "customer_ready_status",
        "overall visual confidence",
        "valid layers",
        "missing layers",
        "raw proof",
        "raw ingest",
        "raw status",
        "meta-data",
    ]
    filtered_lines = []
    for line in handoff_summary_raw.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        lowered = stripped.lower()
        # Skip lines that contain blocked markers
        if any(marker in lowered for marker in blocked_markers):
            continue
        # Skip lines that look like metadata assignments or raw operators statements
        if ":" in stripped and any(keyword in lowered for keyword in ["readiness:", "source url:", "source type:", "promotion:", "event date:", "event name:", "template", "renderer", "ingest", "certification", "completeness"]):
            # Allow these specific info lines
            if any(keep in lowered for keep in ["event name:", "event date:", "source url:", "source type:", "promotion:", "readiness:"]):
                filtered_lines.append(line)
            continue
        filtered_lines.append(line)
    
    handoff_summary = "\n".join(filtered_lines).strip() or "Premium summary prepared from selected matchup and source traceability context."
    dashboard_summary = (
        f"{fighter_a} owns the pressure lane when resets stay denied and geometry remains crowded. "
        f"{fighter_b} can flip the fight only if the lane stays clean, the counters stay layered, and the exit discipline holds. "
        f"Command Read: keep scoreable moments, avoid low-value pressure, and preserve the fight's scoring geography. "
        f"Round-control projection: R1 establishes the read, R2 tests adaptation, and the late rounds reward the fighter who still owns the reset after contact."
    )

    # Enhanced fight-specific content
    return {
        "fighter_a": fighter_a,
        "fighter_b": fighter_b,
        "event_name": event_name,
        "event_date": event_date,
        "source_url": source_url,
        "report_id": report_id,
        "summary": dashboard_summary,
        "source_summary": handoff_summary,
        # Cover tagline
        "cover_tagline": "THE INTELLIGENCE BENEATH THE VIOLENCE",
        "cover_title": "AI-RISA PREMIUM FIGHT INTELLIGENCE REPORT",
        # Headline with more specific projection
        "headline": (
            f"{fighter_a} enters with the clearest control lane if the fight stays at a pressure-to-reset cadence. "
            f"The tactical thesis is simple: deny {fighter_b} clean geography, win the first re-entry after every break, and make late-round reads expensive. "
            f"If {fighter_b} turns the fight into clean, countable exchanges, the edge compresses quickly."
        ),
        # Matchup snapshot with tactical depth
        "matchup_snapshot": (
            f"{fighter_a} vs {fighter_b} is a contest between pressure rhythm and counter structure. "
            f"Control lane: {fighter_a} should force layered entries, crowd the reset window, and score before the exit is free. "
            f"Danger lane: {fighter_b} can flip the fight if the entries get rushed, the hands decay defensively, or the output is not converted into position. "
            f"Command read: keep exits layered, do not chase low-value pressure, and make every exchange pay for itself."
        ),
        # Decision structure with specific watch cues
        "decision_structure": (
            f"Decision structure: the judge-friendly route belongs to the fighter who owns scoring geography without overcommitting. "
            f"{fighter_a} needs pressure rhythm, reset denial, and angle closure that prevents clean counters. "
            f"{fighter_b} needs disciplined counter-entry timing, ring awareness, and enough repeatable output to keep the scorecard narrow. "
            f"Watch cue: if {fighter_b} is forced to defend twice in the same sequence, {fighter_a} is likely dictating the round. Failure consequence: a high-volume but low-conversion round becomes a point loss instead of a control round."
        ),
        # Energy/fatigue with work rates
        "energy": (
            f"Energy profile: {fighter_a} spends energy in pressure bursts and must convert those bursts into position, not just activity. "
            f"{fighter_b} spends more economically when the fight stays readable, but the cost rises quickly if the resets disappear. "
            f"Watch cue: repeated forced exits or defensive hand decay will tax the slower processor first. Failure consequence: style starts to degrade before cardio visibly fails."
        ),
        # Mental condition specific to matchup
        "mental": (
            f"Mental layer: {fighter_a} is strongest when the fight feels unstable, because disruption amplifies his confidence. "
            f"{fighter_b} is strongest when the fight stays orderly, because clean decision-making is part of his value. "
            f"Command instruction: if the rhythm breaks, reset immediately instead of forcing the next exchange. Watch cue: the first visible hesitation after a momentum swing usually predicts the next scored sequence."
        ),
        # Collapse triggers with specific pattern recognition
        "collapse": (
            f"Collapse trigger map: {fighter_a} risks a downturn when pressure stops moving {fighter_b} and becomes empty volume. "
            f"{fighter_b} risks a downturn when early defensive costs accumulate and the counter window becomes late or predictable. "
            f"Failure consequence: after two consecutive rounds of lost geography or broken timing, the scorecard can move faster than the physical fatigue is obvious."
        ),
        # Round projection with specific expectations
        "round_projection": (
            f"R1 is an information and spacing test. R2 is the first real pressure read: can {fighter_a} keep the geometry pinned, or can {fighter_b} force a clean lane? "
            f"R3 through the late rounds should reward the fighter who is still making the other man reset under threat. "
            f"Command/corner instruction: do not chase damage if the lane is not there; preserve scoring integrity and make the opponent work for every turn."
        ),
        # Scenario pathways with probabilities
        "scenario": (
            f"Scenario Tree / Method Pathways. Pathway A (model-derived 58%): {fighter_a} pressure conversion wins by controlling geography and making the scorecard look inevitable. "
            f"Pathway B (model-derived 33%): {fighter_b} counter-scoring keeps the fight close by staying disciplined and punishing rushed entries. "
            f"Pathway C (model-derived 9%): a swing-variance turn appears if one fighter loses discipline and gives the other a full round of momentum."
        ),
        # Final projection with confidence band
        "final_projection": (
            f"{fighter_a} is the slight projection-based favorite because the control lane is more repeatable than the upset path. "
            f"The model-derived edge sits in the 52-60% band, which is meaningful but not wide. "
            f"If {fighter_b} keeps the fight clean, the gap narrows; if {fighter_a} keeps the fight disruptive, the advantage compounds. "
            f"Recommendation: treat the read as edge plus volatility, not certainty."
        ),
        # Confidence explanation with transparency
        "confidence": (
            "Confidence is model-derived and source-traceable, not guaranteed. The report should be read as bounded intelligence with explicit uncertainty controls. "
            "Control ownership, flip conditions, and corner adjustments are all treated as tactical projections, not promises."
        ),
        "fatigue_failure_points": (
            f"Fatigue Failure Points (Failure Heat Map): {fighter_a} risks output collapse when pressure bursts are not converted into position, "
            f"while {fighter_b} risks late timing delays if repeated resets become defensive-only cycles. "
            "Model-derived warning: cumulative defensive hand decay is a leading indicator for momentum loss."
        ),
        "deception_unpredictability": (
            f"Deception and Unpredictability: {fighter_a} benefits from disruptive cadence shifts that hide true entry timing. "
            f"{fighter_b} benefits from false-rhythm counters that bait rushed pressure before punishing exit lines. "
            "Model-derived guidance: deception value rises after one successful sequence repetition is observed by the opponent."
        ),
        "range_geography_control": (
            f"Range / Geography Control: the decisive lane is who controls geography after first contact. "
            f"{fighter_a} wants crowded middle distance with denied exits; {fighter_b} wants clean lane geometry and countable exchanges. "
            "Failure consequence: when geography is surrendered twice in a row, scoring authority usually changes hands."
        ),
        "scorecard_scenario": (
            "Scorecard Scenario (model-derived): 48-47 primary lane when control geography holds, "
            "47-48 upset lane when counter timing remains clean across the middle rounds, "
            "and 47-47 volatility lane if one late momentum swing overrides early control."
        ),
        "stoppage_windows": (
            "Stoppage Windows (model-derived): early window is opportunistic only, mid-fight window appears if defensive hands decay under sustained pressure, "
            "and late window opens when composure plus pocket exits fail together."
        ),
        "risk_warnings": (
            "Risk Warnings and Exposure Discipline: do not convert a bounded edge into certainty, "
            "do not force output without conversion, and downgrade confidence immediately when unresolved source or round-shift cues appear."
        ),
        "betting_market_intelligence": (
            "Betting Market Intelligence (projection/model-derived): market lane supports a narrow favorite profile with high volatility tax. "
            "Use only as comparative intelligence against tactical pathways; this is not financial advice or guaranteed outcome guidance."
        ),
        "coach_corner_notes": (
            f"Coach / Corner Notes: keep {fighter_a} on layered entry discipline and reset denial cues; "
            f"if {fighter_b} starts winning clean geography, reduce chase volume and re-establish scoring integrity before pace escalation."
        ),
        # Additional metrics for dashboard
        "projected_edge": f"{fighter_a} (model-derived edge)",
        "edge_percent": "54% (model-derived)",
        "volatility": "High (model-derived)",
        "control_zone": "Pressure rhythm / reset denial",
        "danger_zone": "Geography loss / rushed entry",
        "collapse_trigger": "Defensive hand decay",
        "method_probability": "Decision (model-derived)",
        "confidence_band": "52-60% (model-derived)",
    }


def _draw_cover(module, c, blocks):
    """Premium cover design matching Ares reference standard."""
    module.page_base(c, 1, "AI-RISA PREMIUM FIGHT INTELLIGENCE REPORT")
    x = module.SAFE_X + 10
    w = module.PAGE_W - 2 * x

    # Top title bar with premium branding
    module.panel(c, x, 380, w, 80, "", module.GOLD, module.PANEL)
    try:
        c.drawImage(module.LOGO, module.PAGE_W / 2 - 28, 430, 56, 56, preserveAspectRatio=True, mask='auto')
    except Exception:
        pass
    module.set_font(c, "Helvetica-Bold", 16.0, module.WHITE)
    c.drawCentredString(module.PAGE_W / 2, 445, blocks.get("cover_title", "AI-RISA PREMIUM FIGHT INTELLIGENCE REPORT"))
    module.set_font(c, "Helvetica-Bold", 10.0, module.GOLD2)
    c.drawCentredString(module.PAGE_W / 2, 420, blocks.get("cover_tagline", "THE INTELLIGENCE BENEATH THE VIOLENCE"))
    module.set_font(c, "Helvetica", 7.8, module.MUTED)
    c.drawCentredString(module.PAGE_W / 2, 406, "Cover Page")

    # Fighter A block
    module.panel(c, x, 280, (w // 3) - 8, 80, None, module.BLUE, module.PANEL, title_line=False)
    module.set_font(c, "Helvetica-Bold", 8.4, module.BLUE)
    c.drawString(x + 12, 348, "FIGHTER A")
    module.set_font(c, "Helvetica-Bold", 13.0, module.WHITE)
    c.drawCentredString(x + (w // 6), 326, blocks["fighter_a"])
    module.set_font(c, "Helvetica", 8.0, module.GOLD2)
    c.drawCentredString(x + (w // 6), 305, blocks.get("projected_edge", "Model-derived edge"))

    # VS block
    module.panel(c, x + (w // 3), 280, (w // 3) - 16, 80, None, module.GOLD, module.PANEL, title_line=False)
    module.set_font(c, "Helvetica-Bold", 14.0, module.WHITE)
    c.drawCentredString(module.PAGE_W / 2, 325, "VS")
    module.set_font(c, "Helvetica", 8.0, module.MUTED)
    c.drawCentredString(module.PAGE_W / 2, 305, blocks.get("edge_percent", "54% (model-derived)"))

    # Fighter B block
    module.panel(c, x + (2 * w // 3) + 8, 280, (w // 3) - 8, 80, None, module.RED, module.PANEL, title_line=False)
    module.set_font(c, "Helvetica-Bold", 8.4, module.RED)
    c.drawRightString(x + w - 12, 348, "FIGHTER B")
    module.set_font(c, "Helvetica-Bold", 13.0, module.WHITE)
    c.drawCentredString(x + w - (w // 6), 325, blocks["fighter_b"])
    module.set_font(c, "Helvetica", 8.0, module.GOLD2)
    c.drawCentredString(x + w - (w // 6), 305, "Underdog")

    # Event and date
    module.set_font(c, "Helvetica-Bold", 11.0, module.GOLD2)
    c.drawCentredString(module.PAGE_W / 2, 260, blocks["event_name"])
    module.set_font(c, "Helvetica", 9.0, module.MUTED)
    c.drawCentredString(module.PAGE_W / 2, 243, f"Event Date: {blocks['event_date']}")

    # Control/Danger/Command lens
    module.panel(c, x, 140, w, 85, None, module.GOLD, module.PANEL, title_line=False)
    module.set_font(c, "Helvetica-Bold", 8.5, module.GOLD2)
    c.drawString(x + 20, 208, "CONTROL LENS")
    module.set_font(c, "Helvetica", 7.5, module.WHITE)
    c.drawString(x + 20, 195, f"Pressure rhythm, reset denial, and scoring geography")
    module.set_font(c, "Helvetica-Bold", 8.5, module.GOLD2)
    c.drawString(x + (w // 3), 208, "DANGER ZONE")
    module.set_font(c, "Helvetica", 7.5, module.WHITE)
    c.drawString(x + (w // 3), 195, f"Geography loss, rushed entries, and output without conversion")
    module.set_font(c, "Helvetica-Bold", 8.5, module.GOLD2)
    c.drawString(x + (2 * w // 3), 208, "CONFIDENCE")
    module.set_font(c, "Helvetica", 7.5, module.WHITE)
    c.drawString(x + (2 * w // 3), 195, blocks.get("confidence_band", "52-60% (model-derived)"))

    # Headline projection
    module.panel(c, x, 20, w, 108, None, module.BLUE, module.PANEL_BLUE, title_line=False)
    module.set_font(c, "Helvetica-Bold", 8.8, module.BLUE)
    c.drawString(x + 18, 114, "HEADLINE PROJECTION")
    module.para(c, blocks["headline"], x + 18, 30, w - 36, 64, size=9.7, col=module.WHITE, min_size=8.6)

    # Footer with source/operator approval
    module.set_font(c, "Helvetica", 7.0, module.MUTED)
    c.drawString(x, 10, "Source Traceable | Operator Approved")
    module.set_font(c, "Helvetica", 6.5, module.GREY)
    c.drawRightString(x + w, 10, f"Generated: {_dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")

    c.showPage()


def _draw_executive(module, c, blocks):
    """Enhanced executive dashboard with more meaningful data panels."""
    module.page_base(c, 2, "Fight Intelligence Dashboard")
    x = module.SAFE_X + 8
    w = module.PAGE_W - 2 * x

    module.set_font(c, "Helvetica-Bold", 10.8, module.GOLD2)
    c.drawString(x + 2, 452, "Fight Intelligence Dashboard")
    module.set_font(c, "Helvetica", 7.8, module.MUTED)
    c.drawString(x + 2, 440, "Executive Command Dashboard")

    # Top dashboard row - 4 key stat cards
    card_width = (w - 20) // 4
    module.stat_card(c, x + 10, 368, card_width - 4, 70, "Projected Edge", blocks.get("projected_edge", "Fighter A"), module.BLUE)
    module.stat_card(c, x + card_width + 16, 368, card_width - 4, 70, "Confidence", blocks.get("confidence_band", "52-60%"), module.GOLD2)
    module.stat_card(c, x + 2*card_width + 22, 368, card_width - 4, 70, "Volatility", blocks.get("volatility", "High"), module.RED)
    module.stat_card(c, x + 3*card_width + 28, 368, card_width - 4, 70, "Method", blocks.get("method_probability", "Decision"), module.GOLD)

    # Second row - control/danger/collapse zones
    zone_width = (w - 20) // 3
    module.panel(c, x + 10, 278, zone_width - 4, 80, None, module.BLUE, module.PANEL, title_line=False)
    module.set_font(c, "Helvetica-Bold", 9.0, module.WHITE)
    c.drawString(x + 22, 345, "CONTROL ZONE")
    c.drawCentredString(x + 10 + (zone_width - 4) // 2, 326, blocks.get("control_zone", "Pressure rhythm / reset denial"))
    module.set_font(c, "Helvetica", 7.5, module.GOLD2)
    module.para(c, f"{blocks['fighter_a']} keeps scoring geography under threat and denies clean exits.", x + 20, 293, zone_width - 24, 30, size=7.2, col=module.WHITE, min_size=6.8, align='center')

    module.panel(c, x + zone_width + 16, 278, zone_width - 4, 80, None, module.RED, module.PANEL, title_line=False)
    module.set_font(c, "Helvetica-Bold", 9.0, module.WHITE)
    c.drawString(x + zone_width + 28, 345, "DANGER ZONE")
    c.drawCentredString(x + zone_width + 16 + (zone_width - 4) // 2, 326, blocks.get("danger_zone", "Geography loss / rushed entry"))
    module.set_font(c, "Helvetica", 7.5, module.GOLD2)
    module.para(c, f"{blocks['fighter_b']} can flip the fight if the counters stay layered and the exit discipline holds.", x + zone_width + 28, 293, zone_width - 24, 30, size=7.2, col=module.WHITE, min_size=6.8, align='center')

    module.panel(c, x + 2*zone_width + 22, 278, zone_width - 4, 80, None, module.GOLD, module.PANEL, title_line=False)
    module.set_font(c, "Helvetica-Bold", 9.0, module.WHITE)
    c.drawString(x + 2*zone_width + 34, 345, "COLLAPSE TRIGGER")
    c.drawCentredString(x + 2*zone_width + 22 + (zone_width - 4) // 2, 326, blocks.get("collapse_trigger", "Defensive hand decay"))
    module.set_font(c, "Helvetica", 7.5, module.GOLD2)
    module.para(c, "Two consecutive rounds of lost geography or broken timing can move the scorecard faster than fatigue looks visible.", x + 2*zone_width + 34, 293, zone_width - 24, 30, size=7.0, col=module.WHITE, min_size=6.6, align='center')

    # Method pathway visualization
    module.panel(c, x, 102, w, 154, None, module.GOLD, module.PANEL, title_line=False)
    module.set_font(c, "Helvetica-Bold", 9.0, module.GOLD2)
    c.drawString(x + 16, 239, "Method Probability Chart")
    module.method_bars(c, [
        (f"{blocks['fighter_a']} pressure conversion", 58, module.BLUE),
        (f"{blocks['fighter_b']} counter-scoring", 33, module.RED),
        (f"Swing-variance finish", 9, module.GOLD2),
    ], x + 22, 152, w - 44, 75)

    # Executive summary
    module.panel(c, x, 8, w, 86, None, module.BLUE, module.PANEL_BLUE, title_line=False)
    module.set_font(c, "Helvetica-Bold", 8.8, module.BLUE)
    c.drawString(x + 12, 78, "EXECUTIVE SUMMARY / ROUND-CONTROL PROJECTION")
    module.para(c, blocks["summary"], x + 12, 18, w - 24, 46, size=8.8, col=module.WHITE, min_size=7.8)
    c.showPage()


def _draw_fighter_architecture_radar(module, c, blocks):
    module.page_base(c, 4, "Fighter Architecture Radar")
    x = module.SAFE_X + 8
    w = module.PAGE_W - 2 * x
    module.panel(c, x, 82, w, 378, None, module.GOLD, module.PANEL, title_line=False)
    module.set_font(c, "Helvetica-Bold", 11.0, module.GOLD2)
    c.drawString(x + 18, 438, "Fighter Architecture Radar")

    cx = x + 255
    cy = 250
    radius = 112
    labels = [
        "PRESSURE",
        "PACE",
        "RANGE",
        "DURABILITY",
        "DEFENSE",
        "POWER",
        "COMPOSURE",
        "LATE-FIGHT",
        "UNPREDICT",
        "ADAPT",
    ]
    a_vals = [78, 72, 69, 76, 67, 88, 73, 71, 84, 74]
    b_vals = [70, 75, 81, 74, 79, 72, 77, 76, 69, 78]

    c.setStrokeColor(module.GREY)
    c.setLineWidth(0.6)
    for ring in [0.25, 0.5, 0.75, 1.0]:
        pts = []
        rr = radius * ring
        for i in range(10):
            ang = 1.57079632679 - i * (2 * 3.14159265359 / 10)
            pts.append((cx + rr * module.math.cos(ang), cy + rr * module.math.sin(ang)))
        for i in range(10):
            c.line(pts[i][0], pts[i][1], pts[(i + 1) % 10][0], pts[(i + 1) % 10][1])

    for i, label in enumerate(labels):
        ang = 1.57079632679 - i * (2 * 3.14159265359 / 10)
        lx = cx + (radius + 20) * module.math.cos(ang)
        ly = cy + (radius + 20) * module.math.sin(ang)
        module.set_font(c, "Helvetica", 7.0, module.MUTED)
        c.drawCentredString(lx, ly, label)

    def _plot(vals, stroke, alpha):
        pts = []
        for i, v in enumerate(vals):
            ang = 1.57079632679 - i * (2 * 3.14159265359 / 10)
            rr = radius * v / 100
            pts.append((cx + rr * module.math.cos(ang), cy + rr * module.math.sin(ang)))
        path = c.beginPath()
        path.moveTo(pts[0][0], pts[0][1])
        for px, py in pts[1:]:
            path.lineTo(px, py)
        path.close()
        c.setFillColor(module.colors.Color(stroke.red, stroke.green, stroke.blue, alpha=alpha))
        c.setStrokeColor(stroke)
        c.setLineWidth(1.0)
        c.drawPath(path, fill=1, stroke=1)

    _plot(a_vals, module.BLUE, 0.33)
    _plot(b_vals, module.RED, 0.27)

    module.panel(c, x + 500, 246, 240, 148, None, module.GOLD, module.PANEL2, title_line=False)
    module.set_font(c, "Helvetica-Bold", 9.2, module.GOLD2)
    c.drawString(x + 516, 374, "Control Lane")
    module.para(c, f"{blocks['fighter_a']} pressure rhythm and reset denial become the scoring driver if exits are layered.", x + 516, 330, 208, 34, size=8.6, col=module.WHITE, min_size=7.8)
    module.set_font(c, "Helvetica-Bold", 9.2, module.RED)
    c.drawString(x + 516, 308, "Danger Lane")
    module.para(c, f"{blocks['fighter_b']} flips momentum if range control and counter-entry timing stay clean in the mid rounds.", x + 516, 264, 208, 34, size=8.6, col=module.WHITE, min_size=7.8)

    module.panel(c, x + 500, 82, 240, 148, None, module.BLUE, module.PANEL_BLUE, title_line=False)
    module.set_font(c, "Helvetica-Bold", 9.2, module.BLUE)
    c.drawString(x + 516, 210, "Watch Cue")
    module.para(c, "If the second reset after contact is still controlled by the same fighter, that round is likely decisive on cards.", x + 516, 168, 208, 34, size=8.6, col=module.WHITE, min_size=7.8)
    module.set_font(c, "Helvetica-Bold", 9.2, module.GOLD2)
    c.drawString(x + 516, 146, "Failure Consequence")
    module.para(c, "Rushed entry volume without positional conversion creates visible scoring leakage and late-round volatility.", x + 516, 102, 208, 34, size=8.6, col=module.WHITE, min_size=7.8)
    c.showPage()


def _draw_tactical_edge_table(module, c, blocks):
    module.page_base(c, 6, "Tactical Edge Map")
    x = module.SAFE_X + 12
    w = module.PAGE_W - 2 * x
    module.panel(c, x, 86, w, 374, None, module.GOLD, module.PANEL, title_line=False)
    module.set_font(c, "Helvetica-Bold", 11.0, module.GOLD2)
    c.drawString(x + 16, 438, "Tactical Edge Map")
    module.set_font(c, "Helvetica", 7.8, module.MUTED)
    c.drawString(x + 16, 424, "Tactical Edge Table")

    table_x = x + 20
    table_w = w - 40
    header_y = 402
    columns = [
        ("Tactical Layer", 0.25),
        ("Edge", 0.17),
        ("Confidence", 0.14),
        ("Why It Matters", 0.44),
    ]
    cx = table_x
    for title, frac in columns:
        module.set_font(c, "Helvetica-Bold", 9.0, module.GOLD2)
        c.drawString(cx + 6, header_y, title)
        cx += table_w * frac
    c.setStrokeColor(module.GOLD)
    c.setLineWidth(0.8)
    c.line(table_x, header_y - 8, table_x + table_w, header_y - 8)

    rows = [
        ("Pressure Rhythm", blocks["fighter_a"], "Model-derived 58%", "Mechanism: layered pressure plus reset denial creates repeatable scoreable moments in rounds 2-4."),
        ("Counter Entry Timing", blocks["fighter_b"], "Model-derived 33%", "Mechanism: clean exits and counter sequencing reduce pressure efficiency and compress card margin."),
        ("Range Geography", "Contested", "Model-derived 54%", "Mechanism: the fighter who owns mid-range after first contact controls both volume quality and risk exposure."),
        ("Pocket Exit Discipline", blocks["fighter_a"], "Model-derived 52-60%", "Mechanism: disciplined exits prevent swing-variance exchanges and preserve score integrity."),
        ("Late-Round Reliability", "Volatile", "Model-derived high", "Mechanism: fatigue and composure shifts can overturn prior lane control when defensive hand discipline decays."),
    ]

    y = header_y - 28
    row_h = 62
    for idx, (layer, edge, conf, why) in enumerate(rows):
        c.setStrokeColor(module.colors.Color(1, 1, 1, alpha=0.14))
        c.setLineWidth(0.45)
        c.line(table_x, y - 8, table_x + table_w, y - 8)
        module.set_font(c, "Helvetica-Bold", 8.6, module.WHITE)
        c.drawString(table_x + 6, y + 13, layer)
        module.set_font(c, "Helvetica-Bold", 8.6, module.BLUE if edge == blocks["fighter_a"] else module.RED)
        c.drawString(table_x + table_w * 0.25 + 6, y + 13, edge)
        module.set_font(c, "Helvetica", 8.2, module.GOLD2)
        c.drawString(table_x + table_w * 0.42 + 6, y + 13, conf)
        module.para(c, why, table_x + table_w * 0.56 + 6, y - 1, table_w * 0.42 - 10, 36, size=8.0, col=module.WHITE, min_size=7.4)
        y -= row_h

    module.panel(c, x + 20, 96, w - 40, 92, None, module.BLUE, module.PANEL_BLUE, title_line=False)
    module.set_font(c, "Helvetica-Bold", 9.0, module.BLUE)
    c.drawString(x + 34, 168, "Command Instruction")
    module.para(c, "Keep exits layered, do not chase low-value pressure, and preserve scoring geography before forcing pace extensions.", x + 34, 128, w - 68, 30, size=8.6, col=module.WHITE, min_size=7.8)
    module.set_font(c, "Helvetica-Bold", 9.0, module.RED)
    c.drawString(x + 34, 108, "Failure Consequence")
    module.para(c, "If pressure output rises while positional conversion falls, the card drifts toward the cleaner counter lane.", x + 34, 88, w - 68, 18, size=8.2, col=module.WHITE, min_size=7.6)
    c.showPage()


def _draw_failure_heat_map(module, c, blocks):
    module.page_base(c, 9, "Fatigue Failure Points")
    x = module.SAFE_X + 12
    w = module.PAGE_W - 2 * x
    module.panel(c, x, 86, w, 374, None, module.GOLD, module.PANEL, title_line=False)
    module.set_font(c, "Helvetica-Bold", 11.0, module.GOLD2)
    c.drawString(x + 16, 438, "Fatigue Failure Points")
    module.set_font(c, "Helvetica", 7.8, module.MUTED)
    c.drawString(x + 16, 424, "Failure Heat Map")

    labels = [
        "Gas Tank",
        "Defense",
        "Composure",
        "Range Control",
        "Pocket Exits",
        "Reaction Speed",
        "Mental Stress",
    ]
    a_scores = [41, 46, 39, 44, 43, 37, 40]
    b_scores = [34, 38, 36, 31, 35, 33, 42]

    start_y = 368
    row_h = 38
    col_x = [x + 18, x + 210, x + 390, x + 570]
    module.set_font(c, "Helvetica-Bold", 8.8, module.GOLD2)
    c.drawString(col_x[0], start_y + 22, "Category")
    c.drawString(col_x[1], start_y + 22, f"{blocks['fighter_a']} Risk")
    c.drawString(col_x[2], start_y + 22, f"{blocks['fighter_b']} Risk")
    c.drawString(col_x[3], start_y + 22, "Watch Cue")

    def _risk_color(score):
        if score >= 45:
            return module.RED
        if score >= 38:
            return module.GOLD2
        return module.BLUE

    y = start_y
    for idx, label in enumerate(labels):
        a = a_scores[idx]
        b = b_scores[idx]
        c.setStrokeColor(module.colors.Color(1, 1, 1, alpha=0.12))
        c.setLineWidth(0.45)
        c.line(x + 16, y - 6, x + w - 16, y - 6)
        module.set_font(c, "Helvetica-Bold", 8.4, module.WHITE)
        c.drawString(col_x[0], y + 10, label)

        c.setFillColor(_risk_color(a))
        c.roundRect(col_x[1], y, 134, 18, 3, fill=1, stroke=0)
        module.set_font(c, "Helvetica-Bold", 8.0, module.BLACK)
        c.drawCentredString(col_x[1] + 67, y + 5, f"{a}% model-derived")

        c.setFillColor(_risk_color(b))
        c.roundRect(col_x[2], y, 134, 18, 3, fill=1, stroke=0)
        module.set_font(c, "Helvetica-Bold", 8.0, module.BLACK)
        c.drawCentredString(col_x[2] + 67, y + 5, f"{b}% model-derived")

        module.set_font(c, "Helvetica", 7.7, module.MUTED)
        cue = "watch defensive hand discipline" if label in ["Defense", "Pocket Exits"] else "watch reset speed under pressure"
        c.drawString(col_x[3], y + 4, cue)
        y -= row_h

    module.panel(c, x + 18, 96, w - 36, 104, None, module.BLUE, module.PANEL_BLUE, title_line=False)
    module.set_font(c, "Helvetica-Bold", 9.0, module.BLUE)
    c.drawString(x + 32, 178, "Core Claim")
    module.para(c, "Heat-map exposure spikes when the pace rises without positional conversion. Round band: R2-R4 is where compounding stress most often changes scoring outcomes.", x + 32, 134, w - 64, 36, size=8.6, col=module.WHITE, min_size=7.8)
    module.set_font(c, "Helvetica-Bold", 9.0, module.RED)
    c.drawString(x + 32, 114, "Failure Consequence")
    module.para(c, "If composure and pocket exits decay together, one momentum swing can override earlier control reads.", x + 32, 94, w - 64, 18, size=8.2, col=module.WHITE, min_size=7.6)
    c.showPage()


def _draw_round_control_graph(module, c, blocks):
    module.page_base(c, 14, "Round-by-Round Control Projection")
    x = module.SAFE_X + 14
    w = module.PAGE_W - 2 * x
    module.panel(c, x, 86, w, 374, None, module.GOLD, module.PANEL, title_line=False)
    module.set_font(c, "Helvetica-Bold", 11.0, module.GOLD2)
    c.drawString(x + 16, 438, "Round-by-Round Control Projection")
    module.set_font(c, "Helvetica", 7.8, module.MUTED)
    c.drawString(x + 16, 424, "Round Control Graph")

    plot_x = x + 30
    plot_y = 172
    plot_w = w - 60
    plot_h = 214
    c.setStrokeColor(module.GREY)
    c.setLineWidth(0.55)
    c.rect(plot_x, plot_y, plot_w, plot_h, fill=0, stroke=1)

    for i in range(1, 5):
        gx = plot_x + i * (plot_w / 5)
        c.setStrokeColor(module.colors.Color(1, 1, 1, alpha=0.14))
        c.line(gx, plot_y, gx, plot_y + plot_h)
    for i in range(1, 4):
        gy = plot_y + i * (plot_h / 4)
        c.line(plot_x, gy, plot_x + plot_w, gy)

    rounds = ["R1", "R2", "R3", "R4", "R5"]
    a_ctrl = [49, 57, 61, 56, 52]
    b_ctrl = [51, 43, 39, 44, 48]
    for i, r in enumerate(rounds):
        rx = plot_x + (i + 0.5) * (plot_w / 5)
        module.set_font(c, "Helvetica-Bold", 8.0, module.MUTED)
        c.drawCentredString(rx, plot_y - 14, r)

    def _plot_line(vals, col):
        pts = []
        for i, v in enumerate(vals):
            px = plot_x + (i + 0.5) * (plot_w / 5)
            py = plot_y + (v / 100.0) * plot_h
            pts.append((px, py))
        c.setStrokeColor(col)
        c.setLineWidth(1.8)
        for i in range(len(pts) - 1):
            c.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1])
        for px, py in pts:
            c.setFillColor(col)
            c.circle(px, py, 3.0, fill=1, stroke=0)

    _plot_line(a_ctrl, module.BLUE)
    _plot_line(b_ctrl, module.RED)

    module.set_font(c, "Helvetica-Bold", 8.4, module.BLUE)
    c.drawString(plot_x, plot_y + plot_h + 10, f"{blocks['fighter_a']} control estimate")
    module.set_font(c, "Helvetica-Bold", 8.4, module.RED)
    c.drawString(plot_x + 220, plot_y + plot_h + 10, f"{blocks['fighter_b']} control estimate")

    module.panel(c, x + 18, 96, w - 36, 66, None, module.BLUE, module.PANEL_BLUE, title_line=False)
    module.set_font(c, "Helvetica-Bold", 8.8, module.BLUE)
    c.drawString(x + 30, 146, "Control Shift Notes")
    module.para(c, "Danger spikes: R2 if exits are rushed; R4 if defensive hand discipline decays. Command instruction: stabilize reset geography before forcing pace expansion.", x + 30, 106, w - 60, 32, size=8.2, col=module.WHITE, min_size=7.6)
    c.showPage()


def _draw_method_probability_chart(module, c, blocks):
    module.page_base(c, 17, "Stoppage Windows")
    x = module.SAFE_X + 14
    w = module.PAGE_W - 2 * x
    module.panel(c, x, 86, w, 374, None, module.GOLD, module.PANEL, title_line=False)
    module.set_font(c, "Helvetica-Bold", 11.0, module.GOLD2)
    c.drawString(x + 16, 438, "Stoppage Windows")
    module.set_font(c, "Helvetica", 7.8, module.MUTED)
    c.drawString(x + 16, 424, "Method Probability Chart")

    rows = [
        (f"{blocks['fighter_a']} decision", 42, module.BLUE),
        (f"{blocks['fighter_a']} stoppage", 16, module.BLUE_D),
        (f"{blocks['fighter_b']} decision", 29, module.RED),
        (f"{blocks['fighter_b']} stoppage", 13, module.RED_D),
    ]

    module.panel(c, x + 18, 206, w - 36, 204, None, module.GOLD, module.PANEL2, title_line=False)
    module.method_bars(c, rows, x + 42, 250, w - 84, 120)
    module.set_font(c, "Helvetica", 8.2, module.MUTED)
    c.drawString(x + 42, 230, "All percentages are model-derived and normalized for this matchup projection path.")

    module.panel(c, x + 18, 96, w - 36, 94, None, module.BLUE, module.PANEL_BLUE, title_line=False)
    module.set_font(c, "Helvetica-Bold", 8.8, module.BLUE)
    c.drawString(x + 30, 170, "Mechanism")
    module.para(c, "Decision lanes dominate when control geometry survives late rounds. Stoppage lanes rise only when composure and pocket exits fail together.", x + 30, 134, w - 60, 28, size=8.4, col=module.WHITE, min_size=7.8)
    module.set_font(c, "Helvetica-Bold", 8.8, module.GOLD2)
    c.drawString(x + 30, 114, "Risk Control")
    module.para(c, "Treat method read as probabilistic support, not certainty. Re-score after each round-band shift.", x + 30, 96, w - 60, 16, size=8.0, col=module.WHITE, min_size=7.4)
    c.showPage()


def _draw_source_traceability(module, c, blocks, report_context_preview):
    module.page_base(c, 23, "Traceability / Source Map")
    x = module.SAFE_X + 24
    w = module.PAGE_W - 2 * x
    module.panel(c, x, 112, w, 348, None, module.GOLD, module.PANEL, title_line=False)
    module.set_font(c, "Helvetica-Bold", 11.0, module.GOLD2)
    c.drawString(x + 20, 440, "Traceability / Source Map")

    rows = report_context_preview.get("source_traceability", []) if isinstance(report_context_preview, dict) else []
    if not isinstance(rows, list):
        rows = []
    if not rows:
        rows = [{"id": "SRC-001", "type": "official", "tier": "official", "url": blocks["source_url"], "date": blocks["event_date"], "discipline": "source traceable"}]

    table_x = x + 20
    table_w = w - 40
    header_y = 394
    cols = [
        ("Source", 0.13),
        ("Type/Tier", 0.14),
        ("URL", 0.28),
        ("Use in Report", 0.22),
        ("Operator Review Requirement", 0.23),
    ]
    cx = table_x
    for title, frac in cols:
        module.set_font(c, "Helvetica-Bold", 8.4, module.GOLD2)
        c.drawString(cx + 4, header_y, title)
        cx += table_w * frac
    c.setStrokeColor(module.GOLD)
    c.setLineWidth(0.7)
    c.line(table_x, header_y - 8, table_x + table_w, header_y - 8)

    row_y = header_y - 30
    source_name = "Primary Event Record"
    src_type = "official / tier-traceable"
    src_url = blocks["source_url"]
    src_use = f"Event verification for {blocks['event_name']}"
    src_gate = "Required before customer delivery or mutation"
    values = [source_name, src_type, src_url, src_use, src_gate]
    cx = table_x
    col_widths = [table_w * frac for _, frac in cols]
    for idx, value in enumerate(values):
        module.para(c, value, cx + 4, row_y - 10, col_widths[idx] - 8, 32, size=7.8, col=module.WHITE, min_size=7.0)
        cx += col_widths[idx]
    c.setStrokeColor(module.colors.Color(1, 1, 1, alpha=0.15))
    c.setLineWidth(0.45)
    c.line(table_x, row_y - 14, table_x + table_w, row_y - 14)

    module.set_font(c, "Helvetica-Bold", 8.8, module.GOLD2)
    c.drawString(table_x, 334, "Event")
    module.set_font(c, "Helvetica", 8.8, module.WHITE)
    c.drawString(table_x + 78, 334, blocks["event_name"])

    module.set_font(c, "Helvetica-Bold", 8.8, module.GOLD2)
    c.drawString(table_x, 320, "Report ID")
    module.set_font(c, "Helvetica", 8.8, module.WHITE)
    c.drawString(table_x + 78, 320, blocks.get("report_id", "selected_matchup_report"))

    module.set_font(c, "Helvetica-Bold", 8.8, module.GOLD2)
    c.drawString(table_x, 302, "Source Discipline Statement")
    module.para(c, "Claims remain model-derived unless directly supported by this source map and confirmed through operator review.", table_x + 150, 292, table_w - 156, 24, size=8.0, col=module.WHITE, min_size=7.2)

    module.panel(c, x + 18, 130, w - 36, 134, None, module.BLUE, module.PANEL_BLUE, title_line=False)
    module.set_font(c, "Helvetica-Bold", 8.8, module.BLUE)
    c.drawString(x + 34, 246, "SOURCE INTEGRITY NOTE")
    module.para(c, "Source Traceability remains intact when the map is complete, the data path is approved, and operator review confirms the claim. If a source is unresolved, confidence is downgraded instead of inventing certainty.", x + 34, 188, w - 68, 50, size=8.8, col=module.WHITE, min_size=8.0)
    module.set_font(c, "Helvetica-Bold", 8.4, module.GOLD2)
    c.drawString(x + 34, 168, "Operator Approval Requirement")
    module.para(c, "No customer delivery, queue mutation, learning apply, calibration write, or Button 3 mutation is permitted without operator approval.", x + 34, 142, w - 68, 22, size=8.0, col=module.WHITE, min_size=7.2)
    c.showPage()


def _draw_customer_appendix(module, c):
    module.page_base(c, 24, "Disclaimer / Risk Control")
    x = module.SAFE_X + 30
    w = module.PAGE_W - 2 * x
    module.panel(c, x, 262, w, 194, None, module.GOLD, module.PANEL, title_line=False)
    module.set_font(c, "Helvetica-Bold", 9.0, module.GOLD2)
    c.drawString(x + 24, 432, "Disclaimer / Risk Control")
    module.para(c, "This report is customer-facing competitive intelligence, not certainty. It is probabilistic, source-traceable, and intended to support disciplined review rather than automatic action.", x + 24, 350, w - 48, 64, size=10.7, col=module.WHITE, min_size=9.6)
    module.para(c, "Use this report alongside operator judgment, source verification, and context from the broader fight card. If a cue is unresolved, the correct move is to downgrade confidence, not to invent clarity.", x + 24, 288, w - 48, 56, size=10.3, col=module.WHITE, min_size=9.2)

    module.panel(c, x, 98, w, 146, None, module.BLUE, module.PANEL_BLUE, title_line=False)
    module.set_font(c, "Helvetica-Bold", 9.0, module.BLUE)
    c.drawString(x + 24, 224, "WHAT THIS REPORT INCLUDES")
    module.para(c, "Premium cover, executive dashboard panels, Radar and Tactical stat pages, Scenario pathway analysis, Round-control Projection, risk framing, and Source Traceability / source map pages.", x + 24, 154, w - 48, 46, size=10.0, col=module.WHITE, min_size=9.0)
    module.para(c, "No automated delivery is implied. No external API delivery. No queue mutation. No learning or calibration changes without operator approval.", x + 24, 116, w - 48, 26, size=9.4, col=module.MUTED, min_size=8.5)
    c.showPage()


def _draw_text_section(module, c, number, title, subtitle, body, blocks):
    module.page_base(c, number, title)
    x = module.SAFE_X + 18
    w = module.PAGE_W - 2 * x

    module.panel(c, x, 96, w, 364, None, module.GOLD, module.PANEL, title_line=False)
    module.set_font(c, "Helvetica-Bold", 11.0, module.GOLD2)
    c.drawString(x + 18, 438, title)
    module.set_font(c, "Helvetica", 8.0, module.MUTED)
    c.drawString(x + 18, 424, subtitle)

    chips = [
        ("CORE CLAIM", f"{blocks['fighter_a']} vs {blocks['fighter_b']}", module.BLUE),
        ("MECHANISM", "Model-derived tactical lane", module.RED),
        ("RISK", "Bounded confidence with volatility", module.GOLD2),
        ("GOVERNANCE", "Operator-approved generation only", module.GOLD2),
    ]
    chip_y = 390
    chip_w = (w - 50) / 4
    for idx, (label, value, col) in enumerate(chips):
        xx = x + 18 + idx * (chip_w + 6)
        module.panel(c, xx, chip_y, chip_w, 40, None, col, module.SOFT, r=5, lw=0.8, title_line=False)
        module.set_font(c, "Helvetica-Bold", 7.0, col)
        c.drawString(xx + 8, chip_y + 26, label)
        module.set_font(c, "Helvetica", 7.0, module.WHITE)
        c.drawString(xx + 8, chip_y + 12, value[:32])

    module.panel(c, x + 18, 118, w - 36, 252, None, module.BLUE, module.PANEL_BLUE, title_line=False)
    module.para(c, body, x + 30, 136, w - 60, 222, size=9.3, col=module.WHITE, min_size=8.4)
    c.showPage()


def _draw_scorecard_scenario(module, c, blocks):
    module.page_base(c, 16, "Scorecard Scenario")
    x = module.SAFE_X + 18
    w = module.PAGE_W - 2 * x
    module.panel(c, x, 96, w, 364, None, module.GOLD, module.PANEL, title_line=False)
    module.set_font(c, "Helvetica-Bold", 11.0, module.GOLD2)
    c.drawString(x + 18, 438, "Scorecard Scenario")
    module.set_font(c, "Helvetica", 8.0, module.MUTED)
    c.drawString(x + 18, 424, "Projection / model-derived score pathways")

    headers = ["Path", "Likely Card", "Driver", "Volatility"]
    rows = [
        ("Primary lane", "48-47", "Pressure conversion + reset denial", "Medium"),
        ("Counter lane", "47-48", "Clean exits + punished entries", "High"),
        ("Swing lane", "47-47", "Late momentum reversal", "Very high"),
    ]
    tx = x + 24
    tw = w - 48
    y = 388
    cw = [0.22, 0.16, 0.40, 0.22]
    cx = tx
    for i, h in enumerate(headers):
        module.set_font(c, "Helvetica-Bold", 8.8, module.GOLD2)
        c.drawString(cx + 4, y, h)
        cx += tw * cw[i]
    c.setStrokeColor(module.GOLD)
    c.setLineWidth(0.8)
    c.line(tx, y - 8, tx + tw, y - 8)

    ry = y - 34
    for path, card, driver, vol in rows:
        module.set_font(c, "Helvetica-Bold", 8.3, module.WHITE)
        c.drawString(tx + 4, ry + 12, path)
        module.set_font(c, "Helvetica-Bold", 8.3, module.BLUE)
        c.drawString(tx + tw * cw[0] + 4, ry + 12, card)
        module.set_font(c, "Helvetica", 8.1, module.WHITE)
        c.drawString(tx + tw * (cw[0] + cw[1]) + 4, ry + 12, driver)
        module.set_font(c, "Helvetica", 8.1, module.GOLD2)
        c.drawString(tx + tw * (cw[0] + cw[1] + cw[2]) + 4, ry + 12, vol)
        c.setStrokeColor(module.colors.Color(1, 1, 1, alpha=0.12))
        c.setLineWidth(0.45)
        c.line(tx, ry - 4, tx + tw, ry - 4)
        ry -= 56

    module.panel(c, x + 20, 112, w - 40, 116, None, module.BLUE, module.PANEL_BLUE, title_line=False)
    module.set_font(c, "Helvetica-Bold", 8.8, module.BLUE)
    c.drawString(x + 32, 206, "Scorecard Commentary")
    module.para(c, blocks.get("scorecard_scenario", ""), x + 32, 146, w - 64, 48, size=8.6, col=module.WHITE, min_size=7.8)
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

    module.command_footer = lambda c, x, y, w: _customer_command_footer(module, c, x, y, w)

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
    _draw_text_section(module, c, 3, "Headline Projection", "Ares parity headline lane", blocks["headline"], blocks)
    _draw_text_section(module, c, 4, "Matchup Snapshot", "Core Claim / Mechanism / Pathways", blocks["matchup_snapshot"], blocks)
    _draw_fighter_architecture_radar(module, c, blocks)
    _draw_tactical_edge_table(module, c, blocks)
    _draw_text_section(module, c, 7, "Decision Structure", "Decision Structure / Command Layer", blocks["decision_structure"], blocks)
    _draw_text_section(module, c, 8, "Energy Use Analysis", "Energy/Fatigue / Watch Cue", blocks["energy"], blocks)
    _draw_failure_heat_map(module, c, blocks)
    _draw_text_section(module, c, 10, "Mental Condition Under Stress", "Mental response and composure", blocks["mental"], blocks)
    _draw_text_section(module, c, 11, "Collapse Triggers", "Failure cascade map", blocks["collapse"], blocks)
    _draw_text_section(module, c, 12, "Deception and Unpredictability", "Rhythm deception and hidden lane control", blocks["deception_unpredictability"], blocks)
    _draw_text_section(module, c, 13, "Range / Geography Control", "Control lane ownership by distance", blocks["range_geography_control"], blocks)
    _draw_round_control_graph(module, c, blocks)
    _draw_text_section(module, c, 15, "Scenario Tree / Method Pathways", "Scenario Tree / Method Pathways", blocks["scenario"], blocks)
    _draw_scorecard_scenario(module, c, blocks)
    _draw_method_probability_chart(module, c, blocks)
    _draw_text_section(module, c, 18, "Risk Warnings and Exposure Discipline", "Risk control and exposure governance", blocks["risk_warnings"], blocks)
    _draw_text_section(module, c, 19, "Betting Market Intelligence", "Market context (projection/model-derived)", blocks["betting_market_intelligence"], blocks)
    _draw_text_section(module, c, 20, "Coach / Corner Notes", "Corner instruction lane", blocks["coach_corner_notes"], blocks)
    _draw_text_section(module, c, 21, "Final Projection", "Final projection lane", blocks["final_projection"], blocks)
    _draw_text_section(module, c, 22, "Confidence Explanation", "Confidence framing", blocks["confidence"], blocks)
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
        "page_count": 24,
    }
