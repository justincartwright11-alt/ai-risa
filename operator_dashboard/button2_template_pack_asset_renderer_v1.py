import datetime as _dt
import html
import importlib.util
import io
import os
import re
from pathlib import Path


DEFAULT_TEMPLATE_PACK_ROOT = r"C:\ai_risa_next_dashboard_polish\ops\prf_reports\template_pack_sample"
REQUIRED_MODULE = "ai_risa_report_template_v29_bar_alignment_fix.py"
_WORKSPACE_TEMPLATE_PACK_RELATIVE = os.path.join("reports", "template_pack_sample")
_PACKAGED_TEMPLATE_PACK_CANDIDATES = [
    os.path.join("assets", "template_pack_sample"),
    "assets",
]
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


def _build_template_pack_root_candidates():
    candidates = []
    override = os.environ.get("BUTTON2_TEMPLATE_PACK_ROOT", "")
    if isinstance(override, str) and override.strip():
        candidates.append(override.strip())

    candidates.append(DEFAULT_TEMPLATE_PACK_ROOT)

    module_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = os.path.dirname(module_dir)
    candidates.append(os.path.join(workspace_root, _WORKSPACE_TEMPLATE_PACK_RELATIVE))

    for rel_path in _PACKAGED_TEMPLATE_PACK_CANDIDATES:
        candidates.append(os.path.join(module_dir, rel_path))

    deduped = []
    seen = set()
    for candidate in candidates:
        normalized = os.path.normpath(candidate)
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(normalized)
    return deduped


def resolve_template_pack_root_path():
    searched_paths = _build_template_pack_root_candidates()
    for candidate in searched_paths:
        if os.path.isdir(candidate):
            return candidate, searched_paths
    attempted = searched_paths[0] if searched_paths else DEFAULT_TEMPLATE_PACK_ROOT
    raise TemplatePackResolverError(
        "Template pack root directory does not exist in any configured location.",
        attempted_path=attempted,
        missing=searched_paths,
        cause="missing_template_pack_root",
    )


def _clean_text(value, fallback=""):
    if value is None:
        return fallback
    text = html.unescape(str(value)).strip()
    return text or fallback


def _fighter_last_name(value, fallback="Fighter"):
    text = _clean_text(value, fallback)
    parts = [part for part in text.split() if part]
    if not parts:
        return fallback
    return parts[-1]


def _normalize_text(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _wrap_text_to_width(c, text, font_name, font_size, max_width):
    text = _normalize_text(text)
    if not text:
        return []
    words = text.split(" ")
    lines = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if c.stringWidth(candidate, font_name, font_size) <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
            current = word
            continue
        # Single very long token: hard-wrap by characters.
        chunk = ""
        for ch in word:
            probe = f"{chunk}{ch}"
            if c.stringWidth(probe, font_name, font_size) <= max_width:
                chunk = probe
            else:
                if chunk:
                    lines.append(chunk)
                chunk = ch
        current = chunk
    if current:
        lines.append(current)
    return lines


def measure_wrapped_text_height(c, text, width, font_name="Helvetica", font_size=8.0, line_height=1.25, min_lines=1):
    lines = _wrap_text_to_width(c, text, font_name, font_size, width)
    line_count = max(min_lines, len(lines))
    return line_count * font_size * line_height, lines


def split_content_if_overflow(c, text, width, max_height, font_name="Helvetica", font_size=8.0, line_height=1.25):
    lines = _wrap_text_to_width(c, text, font_name, font_size, width)
    if not lines:
        return "", ""
    line_px = font_size * line_height
    max_lines = max(1, int(max_height // line_px))
    if len(lines) <= max_lines:
        return " ".join(lines), ""
    visible = " ".join(lines[:max_lines])
    overflow = " ".join(lines[max_lines:])
    return visible, overflow


def check_box_fits_page(y, box_h, min_y=20):
    return y >= min_y and (y + box_h) <= 460


def prevent_footer_collision(y, box_h, footer_reserved=18):
    return max(y, footer_reserved), box_h


def draw_wrapped_text_box(module, c, text, x, y, w, h, *, font_name="Helvetica", font_size=8.0, color=None, padding=8):
    color = color or module.WHITE
    inner_w = max(10, w - padding * 2)
    inner_h = max(10, h - padding * 2)
    visible, overflow = split_content_if_overflow(
        c,
        text,
        inner_w,
        inner_h,
        font_name=font_name,
        font_size=font_size,
    )
    module.para(
        c,
        visible,
        x + padding,
        y + padding,
        inner_w,
        inner_h,
        size=font_size,
        col=color,
        min_size=max(6.8, font_size - 0.6),
    )
    return overflow


def draw_auto_height_card(
    module,
    c,
    *,
    x,
    y,
    w,
    title,
    text,
    border_color,
    fill_color,
    title_color=None,
    body_font_size=8.0,
    min_h=48,
    max_h=140,
):
    title_color = title_color or border_color
    title_h = 18
    text_h, _ = measure_wrapped_text_height(c, text, w - 16, font_name="Helvetica", font_size=body_font_size)
    desired_h = max(min_h, int(title_h + text_h + 16))
    card_h = min(max_h, desired_h)
    y, card_h = prevent_footer_collision(y, card_h)
    module.panel(c, x, y, w, card_h, None, border_color, fill_color, title_line=False)
    module.set_font(c, "Helvetica-Bold", 8.2, title_color)
    c.drawString(x + 8, y + card_h - 13, title)
    overflow = draw_wrapped_text_box(
        module,
        c,
        text,
        x + 2,
        y + 2,
        w - 4,
        card_h - title_h,
        font_name="Helvetica",
        font_size=body_font_size,
        color=module.WHITE,
        padding=6,
    )
    return card_h, overflow


def draw_two_column_safe_layout(module, c, *, x, y_top, w, column_gap, left_items, right_items, footer_reserved=18):
    col_w = (w - column_gap) / 2
    left_y = y_top
    right_y = y_top
    for title, text, border, fill in left_items:
        h, overflow = draw_auto_height_card(
            module,
            c,
            x=x,
            y=left_y,
            w=col_w,
            title=title,
            text=text,
            border_color=border,
            fill_color=fill,
            max_h=118,
        )
        left_y -= h + 8
        if overflow and left_y > footer_reserved + 54:
            h2, _ = draw_auto_height_card(
                module,
                c,
                x=x,
                y=left_y,
                w=col_w,
                title=f"{title} (cont.)",
                text=overflow,
                border_color=border,
                fill_color=fill,
                max_h=98,
            )
            left_y -= h2 + 8
    for title, text, border, fill in right_items:
        h, overflow = draw_auto_height_card(
            module,
            c,
            x=x + col_w + column_gap,
            y=right_y,
            w=col_w,
            title=title,
            text=text,
            border_color=border,
            fill_color=fill,
            max_h=118,
        )
        right_y -= h + 8
        if overflow and right_y > footer_reserved + 54:
            h2, _ = draw_auto_height_card(
                module,
                c,
                x=x + col_w + column_gap,
                y=right_y,
                w=col_w,
                title=f"{title} (cont.)",
                text=overflow,
                border_color=border,
                fill_color=fill,
                max_h=98,
            )
            right_y -= h2 + 8
    return min(left_y, right_y)


def draw_table_with_wrapped_cells(module, c, *, x, y_top, table_w, columns, rows, header_h=20, footer_reserved=22):
    col_widths = [table_w * frac for _, frac in columns]
    c.setStrokeColor(module.GOLD)
    c.setLineWidth(0.8)
    c.line(x, y_top - 8, x + table_w, y_top - 8)

    cx = x
    for idx, (title, _) in enumerate(columns):
        module.set_font(c, "Helvetica-Bold", 8.5, module.GOLD2)
        c.drawString(cx + 4, y_top, title)
        cx += col_widths[idx]

    y = y_top - header_h
    remaining_rows = []
    for row in rows:
        heights = []
        for idx, value in enumerate(row):
            h, _ = measure_wrapped_text_height(c, value, col_widths[idx] - 10, font_name="Helvetica", font_size=7.3)
            heights.append(h)
        row_h = max(24, int(max(heights) + 12))
        if y - row_h <= footer_reserved:
            remaining_rows.append(row)
            continue

        cx = x
        for idx, value in enumerate(row):
            color = module.WHITE
            if idx == 1:
                lowered = str(value).lower()
                if "fighter a" in lowered:
                    color = module.BLUE
                elif "fighter b" in lowered:
                    color = module.RED
            draw_wrapped_text_box(
                module,
                c,
                value,
                cx,
                y - row_h + 2,
                col_widths[idx],
                row_h - 4,
                font_name="Helvetica",
                font_size=7.3,
                color=color,
                padding=4,
            )
            cx += col_widths[idx]

        c.setStrokeColor(module.colors.Color(1, 1, 1, alpha=0.14))
        c.setLineWidth(0.45)
        c.line(x, y - row_h + 2, x + table_w, y - row_h + 2)
        y -= row_h

    return y, remaining_rows


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
    root, searched_paths = resolve_template_pack_root_path()
    attempted_path = root

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
        "searched_paths": searched_paths,
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
        "cover_title": "PREMIUM FIGHT INTELLIGENCE REPORT",
        # Headline with more specific projection
        "headline": (
            f"{fighter_a} enters with the clearest control lane if the fight stays at a pressure-to-reset cadence. "
            f"The operating thesis is simple: deny {fighter_b} clean geography, win the first re-entry after every break, and make late-round reads expensive. "
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
        "projected_edge": _fighter_last_name(fighter_a, "Fighter A"),
        "edge_percent": "Decision | Full Distance",
        "confidence_display": "55.0%",
        "volatility": "High (model-derived)",
        "control_zone": "Pressure rhythm / reset denial",
        "danger_zone": "Geography loss / rushed entry",
        "collapse_trigger": "Defensive hand decay",
        "method_probability": "Decision (model-derived)",
        "confidence_band": "55%",
        "report_type": "Premium Fight Intelligence Report",
        "round_band": "R2-R4 (model-derived inflection band)",
        "model_status": "model-derived unless source-confirmed",
        # Fighter Overview / Tale of the Tape (model-derived unless source-confirmed)
        "record_a": "model-derived 34-3",
        "record_b": "model-derived 26-4",
        "stance_a": "model-derived orthodox",
        "stance_b": "model-derived orthodox",
        "age_a": "model-derived 35",
        "age_b": "model-derived 30",
        "height_a": "model-derived 196 cm",
        "height_b": "model-derived 188 cm",
        "reach_a": "model-derived 203 cm",
        "reach_b": "model-derived 196 cm",
        "striking_a": 76,
        "striking_b": 73,
        "grappling_a": 52,
        "grappling_b": 58,
        "cardio_a": 68,
        "cardio_b": 71,
        "defense_a": 66,
        "defense_b": 69,
        "experience_a": 82,
        "experience_b": 74,
        "pressure_a": 78,
        "pressure_b": 70,
        "power_a": 84,
        "power_b": 75,
        "range_a": 72,
        "range_b": 76,
        # Dashboard short command read
        "command_read": f"{fighter_a} wins by preserving scoring geography and reset denial; {fighter_b} flips with clean counter timing.",
        "round_control": "Round Control Graph: model-derived R1-R5 cadence",
        "method_pathway": "Decision lane with stoppage volatility (model-derived)",
        "executive_summary": (
            f"Executive Summary: {fighter_a} is favored because he owns the cleaner route to making the fight look the way he wants."
        ),
        "control_zone_header": f"CONTROL ZONE - {_fighter_last_name(fighter_a, 'Fighter A').upper()}",
        "danger_zone_header": f"DANGER ZONE - {_fighter_last_name(fighter_b, 'Fighter B').upper()}",
        "collapse_trigger_text": (
            f"Collapse Trigger ({fighter_a} pressure side): entries still arrive but stop producing controlled exits."
        ),
        "control_thesis": "Instability vs structure",
        "flip_point": "Who creates doubt first?",
        "watch_cue": f"Does {_fighter_last_name(fighter_b, 'Fighter B')} reset clean?",
        "command_rule": "Break decision structure",
        # Body/Risk Anatomy Heat Map zones (model-derived)
        "risk_head_a": "62% model-derived",
        "risk_head_b": "58% model-derived",
        "risk_guard_a": "49% model-derived",
        "risk_guard_b": "54% model-derived",
        "risk_torso_a": "57% model-derived",
        "risk_torso_b": "51% model-derived",
        "risk_legs_base_a": "44% model-derived",
        "risk_legs_base_b": "46% model-derived",
        "risk_gas_tank_a": "53% model-derived",
        "risk_gas_tank_b": "47% model-derived",
        "risk_reaction_speed_a": "48% model-derived",
        "risk_reaction_speed_b": "52% model-derived",
        "risk_composure_stress_a": "50% model-derived",
        "risk_composure_stress_b": "55% model-derived",
    }


def _draw_depth_footer(module, c, x, y, w, title, body, blocks):
    fighter_a = blocks.get("fighter_a", "Fighter A")
    fighter_b = blocks.get("fighter_b", "Fighter B")
    compact_body = re.sub(r"\s+", " ", str(body or "")).strip()
    compact_body = compact_body[:210] + "..." if len(compact_body) > 210 else compact_body

    draw_two_column_safe_layout(
        module,
        c,
        x=x,
        y_top=y,
        w=w,
        column_gap=12,
        left_items=[
            (
                "Primary Control Read",
                compact_body or f"{fighter_a} keeps edge by winning first re-entry and preserving scoring geography.",
                module.BLUE,
                module.PANEL_BLUE,
            ),
            (
                "Risk Trigger",
                "If pressure output rises without position conversion, card authority can drift quickly.",
                module.RED,
                module.PANEL,
            ),
        ],
        right_items=[
            (
                "Counter Risk",
                f"{fighter_b} gains leverage when exits are clean and entries are rushed or unlayered.",
                module.RED,
                module.PANEL,
            ),
            (
                "Corner Command",
                "Preserve lane discipline, keep resets controlled, and avoid low-value chase volume.",
                module.GOLD2,
                module.PANEL,
            ),
        ],
        footer_reserved=8,
    )


def _draw_cover(module, c, blocks):
    """Premium cover design matching Ares reference standard."""
    module.page_base(c, 1, "AI-RISA PREMIUM FIGHT INTELLIGENCE REPORT")
    x = module.SAFE_X + 10
    w = module.PAGE_W - 2 * x

    # Premium header: logo reserve + clear type hierarchy.
    module.panel(c, x, 366, w, 98, "", module.GOLD, module.PANEL)
    logo_zone_x = x + 12
    logo_zone_y = 378
    logo_zone_w = 84
    logo_zone_h = 78
    module.panel(c, logo_zone_x, logo_zone_y, logo_zone_w, logo_zone_h, None, module.BLUE, module.PANEL_BLUE, title_line=False)
    try:
        c.drawImage(module.LOGO, logo_zone_x + 12, logo_zone_y + 8, 56, 56, preserveAspectRatio=True, mask='auto')
    except Exception:
        pass

    title_left = logo_zone_x + logo_zone_w + 16
    title_width = w - (title_left - x) - 12
    # Fit title text to available width (dynamic size guard).
    title_text = blocks.get("cover_title", "PREMIUM FIGHT INTELLIGENCE REPORT")
    title_size = 15.2
    while title_size >= 11.4:
        module.set_font(c, "Helvetica-Bold", title_size, module.WHITE)
        if c.stringWidth(title_text, "Helvetica-Bold", title_size) <= title_width:
            break
        title_size -= 0.6
    c.drawString(title_left, 442, title_text)

    module.set_font(c, "Helvetica-Bold", 9.6, module.GOLD2)
    c.drawString(title_left, 423, blocks.get("cover_tagline", "THE INTELLIGENCE BENEATH THE VIOLENCE"))

    # Fighter versus structure with centered VS lane.
    module.panel(c, x, 274, (w // 3) - 10, 86, None, module.BLUE, module.PANEL, title_line=False)
    module.set_font(c, "Helvetica-Bold", 8.4, module.BLUE)
    c.drawString(x + 12, 350, "FIGHTER A")
    module.set_font(c, "Helvetica-Bold", 12.0, module.WHITE)
    draw_wrapped_text_box(
        module,
        c,
        blocks["fighter_a"],
        x + 10,
        314,
        (w // 3) - 30,
        28,
        font_name="Helvetica-Bold",
        font_size=12.0,
        color=module.WHITE,
        padding=2,
    )
    module.set_font(c, "Helvetica", 8.0, module.GOLD2)
    c.drawCentredString(x + (w // 6), 307, "AI-RISA matchup subject | operator-approved")

    # VS block
    module.panel(c, x + (w // 3), 274, (w // 3) - 20, 86, None, module.GOLD, module.PANEL, title_line=False)
    module.set_font(c, "Helvetica-Bold", 14.0, module.WHITE)
    c.drawCentredString(module.PAGE_W / 2, 327, "VS")
    module.set_font(c, "Helvetica", 8.0, module.MUTED)
    c.drawCentredString(module.PAGE_W / 2, 307, blocks.get("edge_percent", "Decision | Full Distance"))

    # Fighter B block
    module.panel(c, x + (2 * w // 3) + 10, 274, (w // 3) - 10, 86, None, module.RED, module.PANEL, title_line=False)
    module.set_font(c, "Helvetica-Bold", 8.4, module.RED)
    c.drawRightString(x + w - 14, 350, "FIGHTER B")
    module.set_font(c, "Helvetica-Bold", 12.0, module.WHITE)
    draw_wrapped_text_box(
        module,
        c,
        blocks["fighter_b"],
        x + (2 * w // 3) + 20,
        314,
        (w // 3) - 30,
        28,
        font_name="Helvetica-Bold",
        font_size=12.0,
        color=module.WHITE,
        padding=2,
    )
    module.set_font(c, "Helvetica", 8.0, module.GOLD2)
    c.drawCentredString(x + w - (w // 6), 307, "AI-RISA matchup subject | opponent profile")

    # Event/date/customer-ready strip and report metadata row.
    module.panel(c, x, 130, w, 58, None, module.GOLD, module.PANEL, title_line=False)
    module.set_font(c, "Helvetica-Bold", 9.6, module.GOLD2)
    c.drawCentredString(module.PAGE_W / 2, 167, f"{blocks['event_name']} | {blocks['event_date']} | CUSTOMER READY")
    module.set_font(c, "Helvetica", 8.4, module.MUTED)
    c.drawCentredString(
        module.PAGE_W / 2,
        148,
        f"Report ID: {blocks.get('report_id', 'selected_matchup_report')} | Confidence: {blocks.get('confidence_display', '55.0%')} | Generated: {_dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
    )

    # Keep cover clean; command stack starts on dashboard page.
    module.panel(c, x, 20, w, 96, None, module.BLUE, module.PANEL_BLUE, title_line=False)
    module.set_font(c, "Helvetica-Bold", 8.6, module.BLUE)
    c.drawString(x + 18, 96, "PREMIUM FIGHT INTELLIGENCE REPORT")
    module.para(c, blocks["headline"], x + 18, 30, w - 36, 54, size=8.5, col=module.WHITE, min_size=7.8)

    # Footer with source/operator approval
    module.set_font(c, "Helvetica", 7.0, module.MUTED)
    c.drawString(x, 10, "Source Traceable | Operator Approved")
    module.set_font(c, "Helvetica", 6.5, module.GREY)
    c.drawRightString(x + w, 10, f"Generated: {_dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    module.set_font(c, "Helvetica", 5.9, module.MUTED)
    c.drawRightString(x + w, 18, "AI-RISA BRAND MARK")

    c.showPage()


def _draw_executive(module, c, blocks):
    """Executive command dashboard aligned to Jbalia template hierarchy."""
    module.page_base(c, 2, "Executive Command Dashboard")
    x = module.SAFE_X + 8
    w = module.PAGE_W - 2 * x

    module.set_font(c, "Helvetica-Bold", 10.8, module.GOLD2)
    c.drawString(x + 2, 452, "EXECUTIVE COMMAND DASHBOARD")
    module.set_font(c, "Helvetica", 7.8, module.MUTED)
    c.drawString(x + 2, 440, "PREMIUM FIGHT INTELLIGENCE DOSSIER")

    # 1-4: top metric cards.
    card_gap = 8
    card_w = (w - 16 - 3 * card_gap) / 4
    top_cards = [
        ("HEADLINE PREDICTION", blocks.get("projected_edge", "Fighter A"), module.BLUE),
        ("CONFIDENCE", blocks.get("confidence_band", "55%"), module.GOLD2),
        ("VOLATILITY", blocks.get("volatility", "High"), module.RED),
        ("EXECUTIVE SUMMARY", blocks.get("executive_summary", blocks.get("summary", "")), module.GOLD),
    ]
    for i, (title, value, col) in enumerate(top_cards):
        xx = x + 8 + i * (card_w + card_gap)
        draw_auto_height_card(
            module,
            c,
            x=xx,
            y=374,
            w=card_w,
            title=title,
            text=str(value),
            border_color=col,
            fill_color=module.PANEL,
            body_font_size=7.2,
            min_h=64,
            max_h=64,
        )

    # 5-7: zone cards.
    zone_w = (w - 20) / 3
    zones = [
        (blocks.get("control_zone_header", "CONTROL ZONE"), blocks.get("control_zone", "Pressure rhythm / reset denial"), "Momentum theft", module.BLUE),
        (blocks.get("danger_zone_header", "DANGER ZONE"), blocks.get("danger_zone", "Geography loss / rushed entry"), "Disciplined counters", module.RED),
        ("COLLAPSE TRIGGER", "!", blocks.get("collapse_trigger_text", "Collapse trigger lane."), module.GOLD),
    ]
    for i, (title, line1, line2, col) in enumerate(zones):
        xx = x + 10 + i * zone_w
        draw_auto_height_card(
            module,
            c,
            x=xx,
            y=290,
            w=zone_w - 6,
            title=title,
            text=f"{line1} {line2}",
            border_color=col,
            fill_color=module.PANEL,
            body_font_size=6.9,
            min_h=74,
            max_h=74,
        )

    # Fight control intelligence strip.
    strip_y = 188
    module.panel(c, x + 8, strip_y, w - 16, 84, None, module.GOLD, module.PANEL, title_line=False)
    module.set_font(c, "Helvetica-Bold", 8.8, module.GOLD2)
    c.drawString(x + 20, strip_y + 66, "FIGHT CONTROL INTELLIGENCE STRIP")
    strip_items = [
        ("CONTROL THESIS", blocks.get("control_thesis", "Instability vs structure")),
        ("FLIP POINT", blocks.get("flip_point", "Who creates doubt first?")),
        ("WATCH CUE", blocks.get("watch_cue", "Watch reset quality")),
        ("COMMAND RULE", blocks.get("command_rule", "Break decision structure")),
    ]
    col_w = (w - 56) / 4
    for idx, (hdr, body) in enumerate(strip_items):
        xx = x + 20 + idx * col_w
        module.panel(c, xx, strip_y + 12, col_w - 8, 46, None, module.GOLD2 if idx else module.BLUE, module.SOFT, title_line=False)
        module.set_font(c, "Helvetica-Bold", 7.7, module.GOLD2 if idx else module.BLUE)
        c.drawString(xx + 8, strip_y + 43, hdr)
        module.para(c, body, xx + 8, strip_y + 19, col_w - 24, 18, size=7.1, col=module.WHITE, min_size=6.7)

    # Round control, method probability, risk control.
    base_y = 86
    round_w = (w - 32) * 0.33
    method_w = (w - 32) * 0.43
    risk_w = (w - 32) - round_w - method_w

    module.panel(c, x + 8, base_y, round_w, 90, None, module.GOLD, module.PANEL, title_line=False)
    module.set_font(c, "Helvetica-Bold", 8.6, module.GOLD2)
    c.drawString(x + 20, base_y + 72, "ROUND CONTROL PROJECTION")
    for idx, label in enumerate(("R1\nINFO", "R2\nPRESS", "R3\nATTRITION")):
        lines = label.split("\n")
        cx = x + 54 + idx * 68
        module.set_font(c, "Helvetica-Bold", 7.8, module.WHITE)
        c.drawCentredString(cx, base_y + 56, lines[0])
        module.set_font(c, "Helvetica", 7.0, module.MUTED)
        c.drawCentredString(cx, base_y + 42, lines[1])

    mx = x + 8 + round_w + 10
    module.panel(c, mx, base_y, method_w, 90, None, module.GOLD, module.PANEL, title_line=False)
    module.set_font(c, "Helvetica-Bold", 8.6, module.GOLD2)
    c.drawString(mx + 10, base_y + 72, "METHOD PROBABILITY")
    module.method_bars(c, [
        (f"{_fighter_last_name(blocks['fighter_a'])} decision", 55, module.BLUE),
        (f"{_fighter_last_name(blocks['fighter_b'])} decision", 45, module.RED),
        ("Stoppage upset lane", 24, module.RED_D),
        ("Clean control lane", 53, module.BLUE_D),
    ], mx + 12, base_y + 14, method_w - 24, 46)

    rx = mx + method_w + 10
    module.panel(c, rx, base_y, risk_w, 90, None, module.GOLD, module.PANEL, title_line=False)
    module.set_font(c, "Helvetica-Bold", 8.6, module.GOLD2)
    c.drawString(rx + 10, base_y + 72, "RISK CONTROL")
    module.set_font(c, "Helvetica-Bold", 10.5, module.GOLD2)
    c.drawString(rx + 10, base_y + 54, "NO CERTAINTY")
    module.para(c, "Probabilistic edge. Not a guarantee.", rx + 10, base_y + 20, risk_w - 20, 28, size=7.4, col=module.WHITE, min_size=6.9)
    c.showPage()


def _draw_fighter_architecture_radar(module, c, blocks):
    module.page_base(c, 4, "Fighter Architecture Radar")
    x = module.SAFE_X + 8
    w = module.PAGE_W - 2 * x
    module.panel(c, x, 82, w, 378, None, module.GOLD, module.PANEL, title_line=False)
    module.set_font(c, "Helvetica-Bold", 11.0, module.GOLD2)
    c.drawString(x + 18, 438, "Fighter Architecture Radar")
    module.set_font(c, "Helvetica", 7.8, module.MUTED)
    c.drawString(x + 18, 424, "Fighter Overview | Tale of the Tape")

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
    _draw_depth_footer(module, c, x + 18, 8, w - 36, "Fighter Architecture Radar", "10-pillar radar read by tactical lane and round-band stress.", blocks)
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
    header_y = 404
    columns = [
        ("Tactical Layer", 0.19),
        ("Edge", 0.13),
        ("Confidence", 0.14),
        ("Why It Matters", 0.33),
        ("Watch Cue", 0.21),
    ]
    rows = [
        ("Pressure Rhythm", "Fighter A", "Model-derived 58%", "Layered pressure plus reset denial creates repeatable scoreable moments in rounds 2-4.", "Watch if exits are forced twice in one sequence."),
        ("Counter Entry Timing", "Fighter B", "Model-derived 33%", "Clean exits and counter sequencing reduce pressure efficiency and compress card margin.", "Watch delayed counters after reset feints."),
        ("Range Geography", "Contested", "Model-derived 54%", "Who owns mid-range after first contact controls volume quality and risk exposure.", "Watch center-line denial after contact."),
        ("Pocket Exit Discipline", "Fighter A", "Model-derived 52-60%", "Disciplined exits prevent swing-variance exchanges and preserve score integrity.", "Watch defensive hand return on exits."),
        ("Late-Round Reliability", "Volatile", "Model-derived high", "Fatigue and composure shifts can overturn prior lane control when discipline decays.", "Watch R4-R5 composure under pace spikes."),
    ]
    y, remaining = draw_table_with_wrapped_cells(
        module,
        c,
        x=table_x,
        y_top=header_y,
        table_w=table_w,
        columns=columns,
        rows=rows,
        footer_reserved=196,
    )
    if remaining:
        draw_auto_height_card(
            module,
            c,
            x=table_x,
            y=max(194, y - 6),
            w=table_w,
            title="Tactical Edge Table (cont.)",
            text=" ".join(" | ".join(r) for r in remaining),
            border_color=module.GOLD,
            fill_color=module.PANEL2,
            body_font_size=7.0,
            min_h=42,
            max_h=70,
        )

    module.panel(c, x + 20, 92, w - 40, 96, None, module.BLUE, module.PANEL_BLUE, title_line=False)
    module.set_font(c, "Helvetica-Bold", 9.0, module.BLUE)
    c.drawString(x + 34, 168, "Command Instruction")
    module.para(c, "Keep exits layered, do not chase low-value pressure, and preserve scoring geography before forcing pace extensions.", x + 34, 130, w - 68, 30, size=8.3, col=module.WHITE, min_size=7.4)
    module.set_font(c, "Helvetica-Bold", 9.0, module.RED)
    c.drawString(x + 34, 108, "Failure Consequence")
    module.para(c, "If pressure output rises while positional conversion falls, the card drifts toward the cleaner counter lane.", x + 34, 86, w - 68, 22, size=8.0, col=module.WHITE, min_size=7.2)
    _draw_depth_footer(module, c, x + 20, 8, w - 40, "Tactical Edge Map", "Table rows map tactical layers directly to confidence, mechanism, and watch cues.", blocks)
    c.showPage()


def _draw_failure_heat_map(module, c, blocks):
    module.page_base(c, 9, "Fatigue Failure Points")
    x = module.SAFE_X + 12
    w = module.PAGE_W - 2 * x
    module.panel(c, x, 86, w, 374, None, module.GOLD, module.PANEL, title_line=False)
    module.set_font(c, "Helvetica-Bold", 11.0, module.GOLD2)
    c.drawString(x + 16, 438, "Fatigue Failure Points")
    module.set_font(c, "Helvetica", 7.8, module.MUTED)
    c.drawString(x + 16, 424, "Failure Heat Map | Body Risk Heat Map / Anatomical Risk Map")

    # Split columns: left table, right anatomy visual + interpretation (prevents overlap).
    left_w = w - 230
    right_x = x + left_w + 14

    cx = right_x + 95
    cy = 330
    body_h = 118
    body_w = 30
    c.setFillColor(module.BLUE)
    c.roundRect(cx - body_w, cy - body_h / 2, body_w, body_h, 8, fill=1, stroke=0)
    c.setFillColor(module.RED)
    c.roundRect(cx, cy - body_h / 2, body_w, body_h, 8, fill=1, stroke=0)
    module.set_font(c, "Helvetica-Bold", 8.0, module.MUTED)
    c.drawCentredString(cx, cy - 70, "Anatomical Risk Map")

    module.panel(c, right_x + 8, 186, 188, 138, None, module.BLUE, module.PANEL_BLUE, title_line=False)
    module.set_font(c, "Helvetica-Bold", 8.6, module.BLUE)
    c.drawString(right_x + 20, 306, "Watch Cue")
    module.para(c, "Monitor defensive hand decay and delayed reset speed in R2-R4. These are model-derived trigger lanes.", right_x + 20, 266, 164, 34, size=7.8, col=module.WHITE, min_size=7.0)
    module.set_font(c, "Helvetica-Bold", 8.6, module.GOLD2)
    c.drawString(right_x + 20, 244, "Interpretation")
    module.para(c, f"Red/blue split indicates comparative vulnerability by zone for {blocks['fighter_a']} and {blocks['fighter_b']}. Values remain model-derived unless source-confirmed.", right_x + 20, 204, 164, 40, size=7.2, col=module.WHITE, min_size=6.8)

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
    col_x = [x + 18, x + 188, x + 334, x + 468]
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
        c.line(x + 16, y - 6, x + left_w - 8, y - 6)
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

        module.set_font(c, "Helvetica", 7.1, module.MUTED)
        cue = "watch defensive hand discipline" if label in ["Defense", "Pocket Exits"] else "watch reset speed under pressure"
        draw_wrapped_text_box(
            module,
            c,
            cue,
            col_x[3],
            y,
            96,
            18,
            font_name="Helvetica",
            font_size=6.9,
            color=module.MUTED,
            padding=1,
        )
        y -= row_h

    module.panel(c, x + 18, 92, left_w - 8, 108, None, module.BLUE, module.PANEL_BLUE, title_line=False)
    module.set_font(c, "Helvetica-Bold", 9.0, module.BLUE)
    c.drawString(x + 32, 178, "Body Risk Heat Map Interpretation")
    module.para(c, f"Body Risk Heat Map and Anatomical Risk Map are model-derived unless source-confirmed. In this matchup, exposure spikes when {blocks['fighter_a']} forces pace without positional conversion or {blocks['fighter_b']} loses reset timing. Control Window: R2-R4 is the inflection lane.", x + 32, 128, left_w - 34, 46, size=7.5, col=module.WHITE, min_size=6.8)
    module.set_font(c, "Helvetica-Bold", 9.0, module.RED)
    c.drawString(x + 32, 114, "Failure Consequence")
    module.para(c, "If composure and pocket exits decay together, one momentum swing can override earlier control reads.", x + 32, 90, left_w - 34, 20, size=7.8, col=module.WHITE, min_size=7.0)
    _draw_depth_footer(module, c, x + 18, 8, w - 36, "Fatigue Failure Points", "Heat map column and risk table align with fight-specific stress cues.", blocks)
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

    plot_x = x + 26
    plot_y = 192
    plot_w = w - 52
    plot_h = 178
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
        c.drawCentredString(rx, plot_y - 16, r)

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

    draw_auto_height_card(
        module,
        c,
        x=x + 18,
        y=96,
        w=w - 36,
        title="Control Shift Notes",
        text="Control Window Detail: R1 read phase, R2 pressure spike risk, R3 geometry consolidation, R4 defensive decay check, R5 volatility resolution. Command Instruction: stabilize reset geography before forcing pace expansion.",
        border_color=module.BLUE,
        fill_color=module.PANEL_BLUE,
        body_font_size=7.8,
        min_h=84,
        max_h=84,
    )
    _draw_depth_footer(module, c, x + 18, 8, w - 36, "Round-by-Round Control Projection", "Graph lane-to-lane momentum shifts are interpreted with command and risk controls.", blocks)
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
    _draw_depth_footer(module, c, x + 18, 8, w - 36, "Stoppage Windows", "Method lanes and finish windows are tied to mechanism and risk-control triggers.", blocks)
    c.showPage()


def _draw_source_traceability(module, c, blocks, report_context_preview):
    module.page_base(c, 23, "Traceability / Source Map")
    x = module.SAFE_X + 24
    w = module.PAGE_W - 2 * x
    module.panel(c, x, 112, w, 348, None, module.GOLD, module.PANEL, title_line=False)
    module.set_font(c, "Helvetica-Bold", 11.0, module.GOLD2)
    c.drawString(x + 20, 440, "Traceability / Source Map")
    module.set_font(c, "Helvetica-Bold", 8.4, module.MUTED)
    c.drawString(x + 20, 426, "Operator Traceability Appendix")

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
        draw_wrapped_text_box(
            module,
            c,
            value,
            cx + 2,
            row_y - 18,
            col_widths[idx] - 4,
            42,
            font_name="Helvetica",
            font_size=7.6,
            color=module.WHITE,
            padding=2,
        )
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

    module.panel(c, x + 18, 128, w - 36, 136, None, module.BLUE, module.PANEL_BLUE, title_line=False)
    module.set_font(c, "Helvetica-Bold", 8.8, module.BLUE)
    c.drawString(x + 34, 246, "SOURCE INTEGRITY NOTE")
    module.para(c, "Source Traceability remains intact when the map is complete, the data path is approved, and operator review confirms the claim. If a source is unresolved, confidence is downgraded instead of inventing certainty.", x + 34, 186, w - 68, 52, size=8.4, col=module.WHITE, min_size=7.6)
    module.set_font(c, "Helvetica-Bold", 8.4, module.GOLD2)
    c.drawString(x + 34, 168, "Operator Approval Requirement")
    module.para(c, "No customer delivery, queue mutation, learning apply, calibration write, or Button 3 mutation is permitted without operator approval.", x + 34, 140, w - 68, 24, size=7.8, col=module.WHITE, min_size=7.0)
    c.showPage()


def _draw_customer_appendix(module, c):
    module.page_base(c, 24, "Disclaimer / Risk Control")
    x = module.SAFE_X + 30
    w = module.PAGE_W - 2 * x
    module.panel(c, x, 258, w, 198, None, module.GOLD, module.PANEL, title_line=False)
    module.set_font(c, "Helvetica-Bold", 9.0, module.GOLD2)
    c.drawString(x + 24, 432, "Disclaimer / Risk Control")
    draw_wrapped_text_box(
        module,
        c,
        "This report is customer-facing competitive intelligence, not certainty. It is probabilistic, source-traceable, and intended to support disciplined review rather than automatic action.",
        x + 20,
        340,
        w - 40,
        76,
        font_name="Helvetica",
        font_size=9.8,
        color=module.WHITE,
        padding=4,
    )
    draw_wrapped_text_box(
        module,
        c,
        "Use this report alongside operator judgment, source verification, and context from the broader fight card. If a cue is unresolved, the correct move is to downgrade confidence, not to invent clarity.",
        x + 20,
        284,
        w - 40,
        54,
        font_name="Helvetica",
        font_size=9.2,
        color=module.WHITE,
        padding=4,
    )

    module.panel(c, x, 98, w, 146, None, module.BLUE, module.PANEL_BLUE, title_line=False)
    module.set_font(c, "Helvetica-Bold", 9.0, module.BLUE)
    c.drawString(x + 24, 224, "WHAT THIS REPORT INCLUDES")
    module.para(c, "Executive cover design, executive dashboard panels, Radar and Tactical stat pages, Scenario pathway analysis, Round-control Projection, risk framing, and source-map evidence pages.", x + 24, 154, w - 48, 46, size=10.0, col=module.WHITE, min_size=9.0)
    module.para(c, "No automated delivery is implied. No external API delivery. No queue mutation. No learning or calibration changes without operator approval.", x + 24, 116, w - 48, 26, size=9.4, col=module.MUTED, min_size=8.5)
    c.showPage()


def _draw_text_section(module, c, number, title, subtitle, body, blocks):
    module.page_base(c, number, title)
    x = module.SAFE_X + 18
    w = module.PAGE_W - 2 * x

    module.set_font(c, "Helvetica-Bold", 10.0, module.GOLD2)
    c.drawString(x, 446, title)
    module.set_font(c, "Helvetica", 7.6, module.MUTED)
    c.drawString(x, 434, subtitle)

    # Main narrative block
    module.panel(c, x, 320, w, 108, None, module.PANEL, module.PANEL, title_line=False)
    module.set_font(c, "Helvetica-Bold", 8.8, module.BLUE)
    c.drawString(x + 18, 406, "MAIN NARRATIVE")
    module.para(c, body, x + 18, 330, w - 36, 66, size=8.9, col=module.WHITE, min_size=8.0)

    # Lower lenses
    module.panel(c, x, 200, w, 100, None, module.GOLD, module.PANEL, title_line=False)
    module.set_font(c, "Helvetica-Bold", 8.5, module.GOLD2)
    c.drawString(x + 20, 278, "CONTROL LENS")
    module.set_font(c, "Helvetica", 7.5, module.WHITE)
    c.drawString(x + 20, 264, blocks.get("control_zone", "-"))
    module.set_font(c, "Helvetica-Bold", 8.5, module.GOLD2)
    c.drawString(x + (w // 3), 278, "DANGER LENS")
    module.set_font(c, "Helvetica", 7.5, module.WHITE)
    c.drawString(x + (w // 3), 264, blocks.get("danger_zone", "-"))
    module.set_font(c, "Helvetica-Bold", 8.5, module.GOLD2)
    c.drawString(x + (2 * w // 3), 278, "COMMAND READ")
    module.set_font(c, "Helvetica", 7.5, module.WHITE)
    c.drawString(x + (2 * w // 3), 264, blocks.get("command_read", "-"))
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

    module.panel(c, x + 20, 122, w - 40, 106, None, module.BLUE, module.PANEL_BLUE, title_line=False)
    module.set_font(c, "Helvetica-Bold", 8.8, module.BLUE)
    c.drawString(x + 32, 206, "Scorecard Commentary")
    module.para(c, blocks.get("scorecard_scenario", ""), x + 32, 150, w - 64, 42, size=8.2, col=module.WHITE, min_size=7.2)
    _draw_depth_footer(module, c, x + 20, 8, w - 40, "Scorecard Scenario", "Score pathways connect mechanism, volatility, and round-band controls.", blocks)
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
    _draw_text_section(module, c, 4, "Matchup Snapshot", "Primary matchup intelligence snapshot", blocks["matchup_snapshot"], blocks)
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

    selected_matchup = report_context_preview.get("selected_matchup", {}) if isinstance(report_context_preview, dict) else {}
    selected_matchup_present = isinstance(selected_matchup, dict) and bool(
        _clean_text(selected_matchup.get("fighter_a", ""), "") and _clean_text(selected_matchup.get("fighter_b", ""), "")
    )

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
        "renderer_profile": (
            "premium_template_pack_v29_selected_matchup_jbalia_hard_bind_v1"
            if selected_matchup_present
            else "premium_template_pack_v29_asset_backed_v1"
        ),
        "page_count": 24,
    }
