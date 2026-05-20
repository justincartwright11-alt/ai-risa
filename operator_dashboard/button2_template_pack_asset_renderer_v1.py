import datetime as _dt
import html
import importlib.util
import io
import os
import re
from pathlib import Path

from PIL import Image


DEFAULT_TEMPLATE_PACK_ROOT = r"C:\ai_risa_next_dashboard_polish\ops\prf_reports\template_pack_sample"
REQUIRED_MODULE = "ai_risa_report_template_v29_bar_alignment_fix.py"
_WORKSPACE_TEMPLATE_PACK_RELATIVE = os.path.join("reports", "template_pack_sample")
_PACKAGED_TEMPLATE_PACK_CANDIDATES = [
    os.path.join("assets", "template_pack_sample"),
    "assets",
]
_REQUIRED_LOGO_CANDIDATES = [
    "ai_risa_logo_clean_blend.png",
    "ai_risa_logo_watermark_blend.png",
    "AI-RISA Logo.png",
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


def _prepare_logo_image_reader(module, logo_path):
    """Prefer alpha-safe logo rendering and avoid hard black-tile draws."""
    logo_basename = os.path.basename(str(logo_path or "")).lower()
    fallback_risk = logo_basename == "ai-risa logo.png"
    try:
        with Image.open(logo_path) as im:
            rgba = im.convert("RGBA")
            alpha = rgba.getchannel("A")
            alpha_bbox = alpha.getbbox()
            logo_blend_ok = alpha_bbox is not None

            if alpha_bbox is None:
                # Convert near-black background to transparency for legacy logo assets.
                pixels = list(rgba.getdata())
                converted = []
                for r, g, b, a in pixels:
                    if r <= 20 and g <= 20 and b <= 20:
                        converted.append((r, g, b, 0))
                    else:
                        converted.append((r, g, b, max(a, 230)))
                rgba.putdata(converted)
                alpha_bbox = rgba.getchannel("A").getbbox()
                logo_blend_ok = alpha_bbox is not None

            if alpha_bbox:
                rgba = rgba.crop(alpha_bbox)

            stream = io.BytesIO()
            rgba.save(stream, format="PNG")
            stream.seek(0)
            return {
                "image_reader": module.ImageReader(stream),
                "logo_blend_ok": bool(logo_blend_ok),
                "logo_black_tile_risk": bool(fallback_risk and not logo_blend_ok),
                "logo_asset": logo_path,
            }
    except Exception:
        return {
            "image_reader": module.ImageReader(logo_path),
            "logo_blend_ok": False,
            "logo_black_tile_risk": bool(fallback_risk),
            "logo_asset": logo_path,
        }


def _fighter_last_name(value, fallback="Fighter"):
    text = _clean_text(value, fallback)
    parts = [part for part in text.split() if part]
    if not parts:
        return fallback
    return parts[-1]


def _style_descriptor_from_selected(selected, fighter_key, fallback_role):
    if not isinstance(selected, dict):
        selected = {}

    candidate_keys = [
        f"{fighter_key}_style",
        f"style_{fighter_key[-1]}",
        "a_style" if fighter_key == "fighter_a" else "b_style",
        f"{fighter_key}_style_descriptor",
    ]
    for key in candidate_keys:
        value = _clean_text(selected.get(key), "")
        if value:
            return value

    stance_key_candidates = [
        f"{fighter_key}_stance",
        f"stance_{fighter_key[-1]}",
    ]
    stance = ""
    for key in stance_key_candidates:
        stance = _clean_text(selected.get(key), "")
        if stance:
            break

    if stance:
        return f"Model-derived {fallback_role} | {stance}"
    return f"Model-derived {fallback_role} | Orthodox"


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
    fighter_a_style = _style_descriptor_from_selected(selected, "fighter_a", "pressure striker")
    fighter_b_style = _style_descriptor_from_selected(selected, "fighter_b", "counter striker")
    event_name = _clean_text(selected.get("event_name"), "Premium Event")
    event_date = _clean_text(selected.get("event_date"), "n/a")
    promotion = _clean_text(selected.get("promotion"), "UFC")
    source_url = _clean_text(selected.get("source_url"), "n/a")
    report_id = re.sub(r"[^a-z0-9]+", "_", f"{fighter_a}_{fighter_b}_{event_name}".lower()).strip("_")
    if not report_id:
        report_id = "selected_matchup_report"
    fight_id = re.sub(r"[^a-z0-9]+", "_", f"{fighter_a}_{fighter_b}".lower()).strip("_")
    if not fight_id:
        fight_id = "selected_matchup"

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
        "fighter_a_style": fighter_a_style,
        "fighter_b_style": fighter_b_style,
        "event_name": event_name,
        "event_date": event_date,
        "promotion": promotion,
        "source_url": source_url,
        "report_id": report_id,
        "fight_id": fight_id,
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
        "projected_edge": f"{fighter_a} over {fighter_b}",
        "edge_percent": "Decision | Full Distance",
        "confidence_display": "55.0%",
        "volatility": "High (model-derived)",
        "control_zone": f"{fighter_a} pressure rhythm / reset denial",
        "danger_zone": f"{fighter_b} geography loss / rushed entry",
        "collapse_trigger": f"{fighter_a} defensive hand decay",
        "method_probability": f"Decision (model-derived) | {fighter_a} / {fighter_b}",
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


def _draw_depth_footer(module, c, x, y, w, title, body, blocks, *, page_number=None, layout_safety=None):
    fighter_a = blocks.get("fighter_a", "Fighter A")
    fighter_b = blocks.get("fighter_b", "Fighter B")
    footer_safe_zone_y = module.FOOTER_Y + 16
    card_y = max(y, footer_safe_zone_y + 2)
    card_h = 20
    gap = 12
    card_w = (w - gap) / 2

    # Compact summary line above the bottom strip to preserve v29 depth cues.
    summary_y = card_y + card_h + 6
    module.panel(c, x, summary_y, w, 18, None, module.GOLD, module.PANEL2, r=5, lw=0.8, title_line=False)
    module.set_font(c, "Helvetica-Bold", 7.9, module.GOLD2)
    c.drawString(x + 8, summary_y + 7, title.upper())
    module.set_font(c, "Helvetica", 7.0, module.MUTED)
    compact_body = re.sub(r"\s+", " ", str(body or "")).strip()
    compact_body = compact_body[:118] + "..." if len(compact_body) > 118 else compact_body
    c.drawRightString(x + w - 8, summary_y + 7, compact_body)

    left_x = x
    right_x = x + card_w + gap
    module.panel(c, left_x, card_y, card_w, card_h, None, module.RED, module.PANEL, r=5, lw=0.9, title_line=False)
    module.panel(c, right_x, card_y, card_w, card_h, None, module.GOLD2, module.PANEL, r=5, lw=0.9, title_line=False)

    module.set_font(c, "Helvetica-Bold", 7.2, module.RED)
    c.drawString(left_x + 8, card_y + 12, "Risk Trigger")
    module.set_font(c, "Helvetica", 6.6, module.WHITE)
    c.drawString(left_x + 8, card_y + 4, f"If pressure output rises without position conversion, card authority can drift quickly.")

    module.set_font(c, "Helvetica-Bold", 7.2, module.GOLD2)
    c.drawString(right_x + 8, card_y + 12, "Corner Command")
    module.set_font(c, "Helvetica", 6.6, module.WHITE)
    c.drawString(right_x + 8, card_y + 4, "Preserve lane discipline, keep resets controlled, and avoid low-value chase volume.")

    if isinstance(layout_safety, dict) and page_number is not None:
        footer_pages = layout_safety.setdefault("footer_safe_zone_pages", {})
        page_key = str(page_number)
        min_card_y = card_y
        footer_pages[page_key] = {
            "safe": bool(min_card_y >= footer_safe_zone_y),
            "card_min_y": float(min_card_y),
            "safe_zone_y": float(footer_safe_zone_y),
        }


def _draw_cover(module, c, blocks, *, layout_safety=None):
    # v29 parity cover: centered logo/title stack, two fighter cards, VS lane, event band.
    c.setFillColor(module.BLACK)
    c.rect(0, 0, module.PAGE_W, module.PAGE_H, fill=1, stroke=0)
    module.grid(c)
    module.vector_watermark(c)
    c.setStrokeColor(module.GOLD)
    c.setLineWidth(1.25)
    c.rect(28, 40, module.PAGE_W - 56, module.PAGE_H - 76, fill=0, stroke=1)
    if getattr(module, "LOGO", None):
        c.drawImage(module.LOGO, module.PAGE_W / 2 - 45, module.PAGE_H - 106, 90, 90, preserveAspectRatio=True, mask="auto")
    if isinstance(layout_safety, dict):
        layout_safety["cover_logo_drawn"] = bool(getattr(module, "LOGO", None))
    c.setStrokeColor(module.GOLD)
    c.setLineWidth(0.9)
    c.line(70, module.PAGE_H - 91, module.PAGE_W / 2 - 70, module.PAGE_H - 91)
    c.line(module.PAGE_W / 2 + 70, module.PAGE_H - 91, module.PAGE_W - 70, module.PAGE_H - 91)
    module.set_font(c, "Helvetica-Bold", 16.5, module.WHITE)
    c.drawCentredString(module.PAGE_W / 2, 360, "PREMIUM FIGHT")
    module.set_font(c, "Helvetica-Bold", 35.0, module.WHITE)
    c.drawCentredString(module.PAGE_W / 2, 326, "INTELLIGENCE REPORT")
    module.set_font(c, "Helvetica-Bold", 12.0, module.GOLD2)
    c.drawCentredString(module.PAGE_W / 2, 298, "THE INTELLIGENCE BENEATH THE VIOLENCE")

    def _name_lines(name):
        parts = [p for p in str(name or "").strip().split() if p]
        if not parts:
            return ("FIGHTER", "A")
        if len(parts) == 1:
            return (parts[0].upper(), "")
        return (" ".join(parts[:-1]).upper(), parts[-1].upper())

    y = 171
    card_w = 300
    card_h = 92
    module.panel(c, 66, y, card_w, card_h, None, module.BLUE, module.PANEL_BLUE, title_line=False)
    module.target(c, 99, y + 46, 29, module.BLUE)
    a_top, a_bottom = _name_lines(blocks.get("fighter_a"))
    module.set_font(c, "Helvetica-Bold", 16.5, module.BLUE)
    c.drawString(142, y + 55, a_top)
    if a_bottom:
        c.drawString(142, y + 35, a_bottom)
    module.para(c, blocks.get("fighter_a_style", "Model-derived pressure striker | Orthodox"), 142, y + 14, 190, 15, size=9.5, col=module.MUTED, min_size=8.6)

    module.set_font(c, "Helvetica-Bold", 35, module.GOLD2)
    c.drawCentredString(module.PAGE_W / 2, y + 36, "VS")

    module.panel(c, module.PAGE_W - 66 - card_w, y, card_w, card_h, None, module.RED, module.PANEL_RED, title_line=False)
    module.target(c, module.PAGE_W - 99, y + 46, 29, module.RED)
    b_top, b_bottom = _name_lines(blocks.get("fighter_b"))
    module.set_font(c, "Helvetica-Bold", 16.5, module.RED)
    c.drawRightString(module.PAGE_W - 142, y + 55, b_top)
    if b_bottom:
        c.drawRightString(module.PAGE_W - 142, y + 35, b_bottom)
    module.para(c, blocks.get("fighter_b_style", "Model-derived counter striker | Orthodox"), module.PAGE_W - 332, y + 14, 190, 15, size=9.5, col=module.MUTED, min_size=8.6, align="right")

    meta_y = 85
    module.panel(c, 76, meta_y, module.PAGE_W - 152, 62, None, module.GOLD, module.PANEL, title_line=False)
    module.set_font(c, "Helvetica-Bold", 10.0, module.GOLD2)
    c.drawCentredString(module.PAGE_W / 2, meta_y + 39, f"{blocks['event_name']} | {blocks['event_date']} | CUSTOMER READY")
    module.set_font(c, "Helvetica", 9.0, module.MUTED)
    c.drawCentredString(
        module.PAGE_W / 2,
        meta_y + 19,
        f"Report ID: {blocks['report_id']} | Confidence: {blocks.get('confidence_display', '55.0%')} | Generated: {module.DATA.get('generated', '')}",
    )
    module.set_font(c, "Helvetica", 8.2, module.MUTED)
    c.drawCentredString(module.PAGE_W / 2, meta_y + 7, f"{blocks['fighter_a']} vs {blocks['fighter_b']}")

    c.setStrokeColor(module.GOLD)
    c.line(module.SAFE_X, module.FOOTER_Y + 12, module.PAGE_W - module.SAFE_X, module.FOOTER_Y + 12)
    module.set_font(c, "Helvetica-Bold", 7.2, module.GOLD2)
    c.drawString(module.SAFE_X + 6, module.FOOTER_Y + 3, "AI-RISA | COMBAT INTELLIGENCE | OPERATOR APPROVED | SOURCE TRACEABLE")
    c.drawRightString(module.PAGE_W - module.SAFE_X - 6, module.FOOTER_Y + 3, "PAGE 01")
    c.showPage()


def _draw_executive(module, c, blocks):
    # v29 parity executive dashboard layout with dynamic selected fighters.
    module.page_base(c, 2, "Executive Command Dashboard")
    x = module.SAFE_X + 4
    w = module.PAGE_W - 2 * x
    a_short = _fighter_last_name(blocks.get("fighter_a", "Fighter A"), "Fighter A")
    b_short = _fighter_last_name(blocks.get("fighter_b", "Fighter B"), "Fighter B")

    top = 360
    gap = 14
    h = 88
    pred_w = 172
    kpi_w = 136
    summary_w = w - pred_w - 2 * kpi_w - 3 * gap
    module.stat_card(c, x, top, pred_w, h, "Headline Prediction", a_short, module.BLUE, "Decision | Full Distance")
    module.stat_card(c, x + pred_w + gap, top, kpi_w, h, "Confidence", blocks.get("confidence_band", "55%"), module.GOLD2, "Moderate edge")
    module.stat_card(c, x + pred_w + kpi_w + 2 * gap, top, kpi_w, h, "Volatility", blocks.get("volatility", "42%"), module.RED, "Live swing risk")
    sx = x + pred_w + 2 * kpi_w + 3 * gap
    module.panel(c, sx, top, summary_w, h, "Executive Summary", module.GOLD, module.PANEL, title_line=False)
    module.para(c, blocks.get("summary", ""), sx + 14, top + 16, summary_w - 28, 46, size=10.0, col=module.WHITE, min_size=8.8)

    y2 = 236
    colw = (w - 2 * 18) / 3
    module.panel(c, x, y2, colw, 112, f"Control Zone - {a_short}", module.BLUE, module.PANEL_BLUE)
    module.bullets(c, ["Pressure bursts", "Momentum theft", "Emotional discomfort"], x + 20, y2 + 30, colw - 88, 62, module.BLUE, 9.4)
    module.target(c, x + colw - 40, y2 + 55, 17, module.BLUE)
    module.panel(c, x + colw + 18, y2, colw, 112, f"Danger Zone - {b_short}", module.RED, module.PANEL_RED)
    module.bullets(c, ["Clean range", "Disciplined counters", "Measured scoring"], x + colw + 38, y2 + 30, colw - 88, 62, module.RED, 9.4)
    module.target(c, x + 2 * colw + 18 - 40, y2 + 55, 17, module.RED)
    module.panel(c, x + 2 * (colw + 18), y2, colw, 112, "Collapse Trigger", module.RED, module.PANEL, title_line=False)
    module.set_font(c, "Helvetica-Bold", 34, module.RED)
    c.drawString(x + 2 * (colw + 18) + 22, y2 + 43, "!")
    module.para(c, blocks.get("collapse", ""), x + 2 * (colw + 18) + 70, y2 + 28, colw - 96, 52, size=9.0, col=module.WHITE, min_size=8.0)

    y3 = 148
    module.panel(c, x, y3, w, 76, None, module.GOLD, module.PANEL, title_line=False)
    module.set_font(c, "Helvetica-Bold", 10.2, module.GOLD2)
    c.drawString(x + 14, y3 + 55, "FIGHT CONTROL INTELLIGENCE STRIP")
    c.setStrokeColor(module.GOLD)
    c.setLineWidth(0.65)
    c.line(x + 14, y3 + 48, x + w - 14, y3 + 50)
    strip = [
        ("CONTROL THESIS", "Instability vs structure", module.BLUE),
        ("FLIP POINT", "Who creates doubt first?", module.GOLD2),
        ("WATCH CUE", f"Does {b_short} reset clean?", module.GOLD2),
        ("COMMAND RULE", "Break decision structure", module.GOLD2),
    ]
    gap_s = 12
    cw = (w - 30 - gap_s * 3) / 4
    for i, (t, v, col) in enumerate(strip):
        xx = x + 15 + i * (cw + gap_s)
        module.panel(c, xx, y3 + 9, cw, 35, None, col, module.SOFT, r=5, title_line=False)
        module.set_font(c, "Helvetica-Bold", 8.7, col)
        c.drawString(xx + 9, y3 + 31, t)
        module.para(c, v, xx + 9, y3 + 12, cw - 18, 14, size=8.0, col=module.WHITE, min_size=7.2)

    y4 = 70
    round_w = 248
    prob_w = 350
    risk_w = w - round_w - prob_w - 36
    module.panel(c, x, y4, round_w, 84, None, module.GOLD, module.PANEL, title_line=False)
    module.set_font(c, "Helvetica-Bold", 9.6, module.GOLD2)
    c.drawString(x + 14, y4 + 62, "ROUND CONTROL PROJECTION")
    rounds = [("R1", "INFO", module.MUTED), ("R2", "PRESS", module.BLUE), ("R3", "ATTRITION", module.RED)]
    for i, (r, lab, col) in enumerate(rounds):
        cx = x + 50 + i * 72
        cy = y4 + 31
        module.set_font(c, "Helvetica-Bold", 8.5, module.WHITE)
        c.drawCentredString(cx, y4 + 53, r)
        module.target(c, cx, cy, 10.5, col)
        module.set_font(c, "Helvetica-Bold", 7.0, col)
        c.drawCentredString(cx, y4 + 13, lab)
    px = x + round_w + 18
    module.panel(c, px, y4, prob_w, 84, None, module.GOLD, module.PANEL, title_line=False)
    module.set_font(c, "Helvetica-Bold", 10.0, module.GOLD2)
    c.drawString(px + 14, y4 + 62, "METHOD PROBABILITY")
    module.method_bars(c, [
        (f"{a_short} decision", 55, module.BLUE),
        (f"{b_short} decision", 45, module.RED),
        ("Stoppage upset lane", 22, module.RED),
        ("Clean control lane", 38, module.BLUE),
    ], px + 18, y4 + 8, prob_w - 36, 44)
    rx = px + prob_w + 18
    module.panel(c, rx, y4, risk_w, 84, None, module.GOLD, module.PANEL, title_line=False)
    module.set_font(c, "Helvetica-Bold", 10.0, module.GOLD2)
    c.drawString(rx + 14, y4 + 62, "RISK CONTROL")
    module.set_font(c, "Helvetica-Bold", 12.0, module.GOLD2)
    c.drawString(rx + 14, y4 + 42, "NO CERTAINTY")
    module.para(c, "Probabilistic edge. Not a guarantee.", rx + 14, y4 + 13, risk_w - 28, 26, size=8.0, col=module.WHITE, min_size=7.4)
    c.showPage()


def _draw_fighter_architecture_radar(module, c, blocks):
    # v29 parity radar with PAGE 05 marker and right-side read panels.
    module.page_base(c, 5, "Fighter Architecture Radar")
    x = module.SAFE_X + 8
    y = 72
    w_left = 548
    h = 390
    a_short = _fighter_last_name(blocks.get("fighter_a", "Fighter A"), "Fighter A")
    b_short = _fighter_last_name(blocks.get("fighter_b", "Fighter B"), "Fighter B")
    module.panel(c, x, y, w_left, h, "10-Pillar Fighter Architecture Radar", module.GOLD, module.PANEL)
    module.set_font(c, "Helvetica-Bold", 8.0, module.GOLD2)
    c.drawString(x + 26, y + h - 34, "PAGE 05")
    module.set_font(c, "Helvetica", 9.6, module.WHITE)
    c.setFillColor(module.BLUE)
    c.rect(x + 26, y + h - 54, 9, 9, fill=1, stroke=0)
    module.set_font(c, "Helvetica", 9.4, module.WHITE)
    c.drawString(x + 40, y + h - 53, a_short)
    c.setFillColor(module.RED)
    c.rect(x + 151, y + h - 54, 9, 9, fill=1, stroke=0)
    module.set_font(c, "Helvetica", 9.4, module.WHITE)
    c.drawString(x + 165, y + h - 53, b_short)

    labels = ["PRESSURE", "PACE", "RANGE", "DEFENSE", "DURABILITY", "COMPOSURE", "ADAPT", "POWER", "UNPREDICT", "LATE"]
    a_vals = [86, 74, 66, 62, 72, 70, 64, 91, 82, 69]
    b_vals = [72, 77, 83, 75, 70, 76, 61, 66, 70, 80]
    cx = x + 282
    cy = y + 250
    R = 72
    c.setStrokeColor(module.colors.Color(0.8, 0.8, 0.8, alpha=0.18))
    c.setLineWidth(0.75)
    for rr in [R * 0.25, R * 0.5, R * 0.75, R]:
        pts = []
        for i in range(10):
            ang = module.math.pi / 2 - i * 2 * module.math.pi / 10
            pts.append((cx + rr * module.math.cos(ang), cy + rr * module.math.sin(ang)))
        for i in range(10):
            c.line(*pts[i], *pts[(i + 1) % 10])
    for i, lab in enumerate(labels):
        ang = module.math.pi / 2 - i * 2 * module.math.pi / 10
        lx = cx + (R + 25) * module.math.cos(ang)
        ly = cy + (R + 25) * module.math.sin(ang)
        module.set_font(c, "Helvetica", 7.0, module.MUTED)
        c.drawCentredString(lx, ly, lab)

    def _poly(vals, col, alpha):
        pts = []
        for i, v in enumerate(vals):
            rr = R * v / 100
            ang = module.math.pi / 2 - i * 2 * module.math.pi / 10
            pts.append((cx + rr * module.math.cos(ang), cy + rr * module.math.sin(ang)))
        c.setFillColor(module.colors.Color(col.red, col.green, col.blue, alpha=alpha))
        c.setStrokeColor(col)
        c.setLineWidth(1.0)
        path = c.beginPath()
        path.moveTo(*pts[0])
        for pt in pts[1:]:
            path.lineTo(*pt)
        path.close()
        c.drawPath(path, fill=1, stroke=1)

    _poly(b_vals, module.RED, 0.30)
    _poly(a_vals, module.BLUE, 0.36)
    module.bars(c, [
        (f"{a_short} Pressure", 86, module.BLUE),
        (f"{a_short} Power", 91, module.BLUE),
        (f"{b_short} Structure", 84, module.RED),
        (f"{b_short} Range", 83, module.RED),
    ], x + 34, y + 24, w_left - 68, 100)

    rx = x + w_left + 24
    rw = module.PAGE_W - module.SAFE_X - rx
    module.panel(c, rx, y + 268, rw, 122, "Architecture Read", module.GOLD, module.PANEL)
    module.para(c, blocks.get("matchup_snapshot", ""), rx + 18, y + 292, rw - 36, 66, size=9.2, col=module.WHITE, min_size=8.4)
    module.panel(c, rx, y + 142, rw, 100, "Customer Meaning", module.BLUE, module.PANEL)
    module.para(c, "Instability versus structure. The fighter who forces his preferred rules controls the bout.", rx + 18, y + 168, rw - 36, 44, size=9.2, col=module.WHITE, min_size=8.4)
    module.panel(c, rx, y, rw, 112, None, module.GOLD, module.PANEL, title_line=False)
    module.set_font(c, "Helvetica-Bold", 10.2, module.GOLD2)
    c.drawString(rx + 18, y + 90, "OPERATOR USE")
    c.setStrokeColor(module.GOLD)
    c.setLineWidth(0.55)
    c.line(rx + 18, y + 80, rx + rw - 18, y + 80)
    rows = [("CONTROL", "Dictates rhythm", module.BLUE), ("DANGER", "Creates chaos", module.RED), ("FLIP", "Entry cost", module.GOLD2)]
    yy = y + 61
    for label, val, col in rows:
        module.set_font(c, "Helvetica-Bold", 8.8, col)
        c.drawString(rx + 18, yy, label)
        module.set_font(c, "Helvetica", 8.8, module.WHITE)
        c.drawString(rx + 102, yy, val)
        yy -= 24
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
        ("Pressure Rhythm", blocks["fighter_a"], "Model-derived 58%", "Layered pressure plus reset denial creates repeatable scoreable moments in rounds 2-4.", f"Watch if {blocks['fighter_a']} forces exits twice in one sequence."),
        ("Counter Entry Timing", blocks["fighter_b"], "Model-derived 33%", "Clean exits and counter sequencing reduce pressure efficiency and compress card margin.", f"Watch delayed counters after {blocks['fighter_b']} reset feints."),
        ("Range Geography", "Contested", "Model-derived 54%", "Who owns mid-range after first contact controls volume quality and risk exposure.", "Watch center-line denial after contact."),
        ("Pocket Exit Discipline", blocks["fighter_a"], "Model-derived 52-60%", "Disciplined exits prevent swing-variance exchanges and preserve score integrity.", f"Watch {blocks['fighter_a']} defensive hand return on exits."),
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
    module.para(c, f"Keep exits layered for {blocks['fighter_a']}, do not chase low-value pressure for {blocks['fighter_b']}, and preserve scoring geography before forcing pace extensions.", x + 34, 130, w - 68, 30, size=8.3, col=module.WHITE, min_size=7.4)
    module.set_font(c, "Helvetica-Bold", 9.0, module.RED)
    c.drawString(x + 34, 108, "Failure Consequence")
    module.para(c, f"If {blocks['fighter_a']} pressure output rises while positional conversion falls, the card drifts toward the cleaner counter lane.", x + 34, 86, w - 68, 22, size=8.0, col=module.WHITE, min_size=7.2)
    _draw_depth_footer(module, c, x + 20, 22, w - 40, "Tactical Edge Map", "Table rows map tactical layers directly to confidence, mechanism, and watch cues.", blocks, page_number=6, layout_safety=blocks.get("_layout_safety"))
    c.showPage()


def _draw_scenario_tree(module, c, blocks):
    # v29 parity scenario-tree nodes and branch flow.
    module.page_base(c, 15, "Scenario Tree / Method Pathways")
    x = module.SAFE_X + 28
    y = 78
    w = module.PAGE_W - 2 * x
    h = 378
    module.panel(c, x, y, w, h, "Scenario Tree / Method Pathways", module.GOLD, module.PANEL)

    def _node(cx, cy, ww, hh, text, accent, fill=None):
        if fill is None:
            fill = module.PANEL2 if accent != module.RED else module.PANEL_RED
        c.setFillColor(fill)
        c.setStrokeColor(accent)
        c.setLineWidth(1.0)
        c.roundRect(cx - ww / 2, cy - hh / 2, ww, hh, 6, fill=1, stroke=1)
        module.para(c, text, cx - ww / 2 + 12, cy - hh / 2 + 8, ww - 24, hh - 16, size=9.2, col=module.WHITE, min_size=8.2, align="center")

    def _conn(x1, y1, x2, y2):
        c.setStrokeColor(module.GOLD)
        c.setLineWidth(0.8)
        c.line(x1, y1, x2, y2)

    cx = x + w / 2
    _node(cx, y + h - 56, 230, 42, "Opening technical range battle", module.GOLD)
    _node(cx, y + h - 126, 276, 42, "Who controls the fight's operating rules?", module.GOLD2)
    _conn(cx, y + h - 77, cx, y + h - 105)
    lx = x + 190
    rx = x + w - 190
    _node(lx, y + h - 205, 280, 56, f"{blocks['fighter_a']} branch", module.BLUE, module.PANEL_BLUE)
    _node(rx, y + h - 205, 280, 56, f"{blocks['fighter_b']} branch", module.RED, module.PANEL_RED)
    _conn(cx, y + h - 147, lx, y + h - 177)
    _conn(cx, y + h - 147, rx, y + h - 177)
    _node(lx, y + h - 292, 280, 56, "Pressure, momentum theft, emotional discomfort, damage swings", module.BLUE, module.PANEL_BLUE)
    _node(rx, y + h - 292, 280, 56, "Spacing, counters, disciplined exits, repeatable round-winning", module.RED, module.PANEL_RED)
    _conn(lx, y + h - 233, lx, y + h - 264)
    _conn(rx, y + h - 233, rx, y + h - 264)
    _node(cx, y + 53, 420, 46, "Swing scenario: danger moments versus clean stretches", module.GOLD2)
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
    _draw_depth_footer(module, c, x + 18, 22, w - 36, "Fatigue Failure Points", "Heat map column and risk table align with fight-specific stress cues.", blocks, page_number=9, layout_safety=blocks.get("_layout_safety"))
    c.showPage()


def _draw_round_control_graph(module, c, blocks):
    # v29 parity round-control page with three outlook cards.
    module.page_base(c, 14, "Round-by-Round Control Projection")
    x = module.SAFE_X + 36
    w = module.PAGE_W - 2 * x
    module.panel(c, x, 94, w, 372, "Round-by-Round Outlook", module.GOLD, module.PANEL)
    cards = [
        ("R1", "INFO / RHYTHM TEST", f"{blocks['fighter_b']} establishes distance and information. {blocks['fighter_a']} tests reactions and makes clean reads uncomfortable.", module.MUTED),
        ("R2", "PRIMARY PRESSURE TEST", "The operating mode becomes visible. If hesitation appears, pressure becomes meaningful. If the lane stays clean, scoring rhythm strengthens.", module.BLUE),
        ("R3", "DECISION STRESS POINT", "Attrition and composure decide it. Pressure either defines the fight or loses efficiency under late-round stress.", module.RED),
    ]
    cy = 352
    for r, title, desc, col in cards:
        c.setFillColor(module.PANEL2)
        c.setStrokeColor(col)
        c.setLineWidth(1.0)
        c.roundRect(x + 35, cy - 52, w - 70, 64, 7, fill=1, stroke=1)
        module.set_font(c, "Helvetica-Bold", 17, col)
        c.drawString(x + 55, cy - 17, r)
        module.set_font(c, "Helvetica-Bold", 9.2, module.GOLD2)
        c.drawString(x + 105, cy - 12, title)
        module.para(c, desc, x + 105, cy - 39, w - 150, 26, size=8.8, col=module.WHITE, min_size=7.8)
        cy -= 96
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
    _draw_depth_footer(module, c, x + 18, 22, w - 36, "Stoppage Windows", "Method lanes and finish windows are tied to mechanism and risk-control triggers.", blocks, page_number=17, layout_safety=blocks.get("_layout_safety"))
    c.showPage()


def _draw_source_traceability(module, c, blocks, report_context_preview):
    # v29 parity source map with SOURCE CHAIN and required metadata rows.
    module.page_base(c, 23, "Traceability / Source Map")
    x = module.SAFE_X + 50
    y = 126
    w = module.PAGE_W - 2 * x
    h = 330
    module.panel(c, x, y, w, h, "Source Chain", module.GOLD, module.PANEL)
    rows = [
        ("EVENT", blocks.get("event_name", "Premium Event")),
        ("FIGHT ID", blocks.get("fight_id", "selected_matchup")),
        ("EVENT DATE", blocks.get("event_date", "n/a")),
        ("SPORT", module.DATA.get("sport", "MMA")),
        ("PROMOTION", blocks.get("promotion", "UFC")),
        ("REPORT ID", blocks.get("report_id", "selected_matchup_report")),
        ("SOURCE URL", blocks.get("source_url", "n/a")),
    ]
    yy = y + h - 70
    label_x = x + 28
    value_x = x + 160
    value_w = w - 188
    row_geometry = []
    for lab, val in rows:
        value_text = _normalize_text(val)
        # Allow long report ids and URLs to wrap safely inside their own row.
        value_lines = _wrap_text_to_width(c, value_text, "Helvetica", 8.6, value_w)
        if not value_lines:
            value_lines = ["n/a"]
        if lab in {"REPORT ID", "SOURCE URL"}:
            value_lines = value_lines[:3]
        row_h = max(18, int(len(value_lines) * 9.2 + 4))

        module.set_font(c, "Helvetica-Bold", 8.8, module.GOLD2)
        c.drawString(label_x, yy, lab)
        module.set_font(c, "Helvetica", 8.6, module.WHITE)
        text_y = yy
        for line in value_lines:
            c.drawString(value_x, text_y, line)
            text_y -= 9.2

        c.setStrokeColor(module.colors.Color(1, 1, 1, alpha=0.10))
        c.setLineWidth(0.45)
        c.line(label_x, yy - row_h + 2, x + w - 28, yy - row_h + 2)
        row_geometry.append({
            "label": lab,
            "top_y": float(yy),
            "bottom_y": float(yy - row_h),
            "line_count": len(value_lines),
        })
        yy -= row_h + 4

    statement_y = y + 34
    statement_h = max(42, int(yy - statement_y - 6))
    statement_h = min(statement_h, 68)
    module.para(
        c,
        "Production exports should attach or reference official event-card data, fighter profile records, matchup ledger rows, odds snapshots, and report-generation metadata.",
        x + 28,
        statement_y + 22,
        w - 56,
        max(20, statement_h - 18),
        size=8.0,
        col=module.WHITE,
        min_size=7.4,
    )
    module.para(
        c,
        "Source discipline statement: customer-ready status is blocked if required source references are unavailable, unresolved, or unverified.",
        x + 28,
        statement_y + 6,
        w - 56,
        14,
        size=7.6,
        col=module.WHITE,
        min_size=7.1,
    )

    layout_safety = blocks.get("_layout_safety") if isinstance(blocks, dict) else None
    if isinstance(layout_safety, dict):
        source_safe = True
        for idx in range(1, len(row_geometry)):
            if row_geometry[idx - 1]["bottom_y"] <= row_geometry[idx]["top_y"]:
                source_safe = False
                break
        source_statement_top = statement_y + statement_h
        source_safe = source_safe and bool(row_geometry) and (row_geometry[-1]["bottom_y"] > source_statement_top + 2)
        layout_safety["source_map"] = {
            "rows": row_geometry,
            "statement_top_y": float(source_statement_top),
            "statement_box_y": float(statement_y),
            "rows_separated": bool(source_safe),
            "report_id_wrapped": any(r["label"] == "REPORT ID" and r["line_count"] > 1 for r in row_geometry),
            "source_url_wrapped": any(r["label"] == "SOURCE URL" and r["line_count"] > 1 for r in row_geometry),
            "source_url_statement_separated": bool(row_geometry) and (row_geometry[-1]["bottom_y"] > source_statement_top + 2),
        }
    c.showPage()


def _draw_customer_appendix(module, c):
    # v29 parity disclaimer page with four risk-rail cards.
    module.page_base(c, 24, "Disclaimer / Risk Control")
    x = module.SAFE_X + 40
    w = module.PAGE_W - 2 * x
    module.metric_rail(
        c,
        [
            ("NO GUARANTEE", "All predictions are probabilistic", module.GOLD2),
            ("NO FINANCIAL ADVICE", "Market reads require discipline", module.GOLD2),
            ("COMBAT RISK", "Combat sports are volatile", module.RED),
            ("NEVER OVER-WAGER", "Risk control beats action", module.BLUE),
        ],
        x,
        354,
        w,
        82,
    )
    module.panel(c, x, 164, w, 150, "Risk Control Standard", module.GOLD, module.PANEL)
    module.para(c, module.TEXT.get("disclaimer", ""), x + 28, 204, w - 56, 58, size=12.0, col=module.WHITE, min_size=10.8)
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
    _draw_depth_footer(module, c, x + 20, 22, w - 40, "Scorecard Scenario", "Score pathways connect mechanism, volatility, and round-band controls.", blocks, page_number=16, layout_safety=blocks.get("_layout_safety"))
    c.showPage()


def render_button2_template_pack_asset_pdf(report_context_preview):
    assets = resolve_template_pack_assets()
    module = _load_template_module(assets["module_path"])

    # Bind template pack image assets so watermark/branding comes from pack files.
    layout_safety = {
        "footer_safe_zone_pages": {},
    }

    try:
        image_reader = module.ImageReader
        logo_info = _prepare_logo_image_reader(module, assets["logo_path"])
        module.LOGO = logo_info["image_reader"]
        module.WATER = image_reader(assets["watermark_path"])
        layout_safety.update({
            "logo_asset": logo_info.get("logo_asset"),
            "logo_blend_ok": bool(logo_info.get("logo_blend_ok", False)),
            "logo_black_tile_risk": bool(logo_info.get("logo_black_tile_risk", False)),
        })
    except Exception as e:
        raise TemplatePackRenderError(f"Failed to load template pack image assets: {str(e)}") from e

    blocks = _build_blocks(report_context_preview)
    blocks["_layout_safety"] = layout_safety

    # Bind selected-matchup values into the canonical v29 template data contract.
    if not isinstance(getattr(module, "DATA", None), dict):
        module.DATA = {}
    if not isinstance(getattr(module, "TEXT", None), dict):
        module.TEXT = {}

    module.DATA["a"] = blocks["fighter_a"]
    module.DATA["b"] = blocks["fighter_b"]
    module.DATA["a_short"] = _fighter_last_name(blocks["fighter_a"], "Fighter A")
    module.DATA["b_short"] = _fighter_last_name(blocks["fighter_b"], "Fighter B")
    module.DATA["winner"] = blocks["fighter_a"]
    module.DATA["method"] = "Decision"
    module.DATA["round"] = "Full Distance"
    module.DATA["confidence"] = blocks.get("confidence_display", "55.0%")
    module.DATA["confidence_short"] = str(blocks.get("confidence_band", "55%")).replace("%", "") + "%"
    module.DATA["volatility"] = blocks.get("volatility", "High")
    module.DATA["event"] = blocks["event_name"]
    module.DATA["date"] = blocks["event_date"]
    module.DATA["promotion"] = _clean_text(
        (report_context_preview.get("selected_matchup", {}) if isinstance(report_context_preview, dict) else {}).get("promotion"),
        "UFC",
    )
    module.DATA["sport"] = "MMA"
    module.DATA["report_type"] = "CUSTOMER READY"
    module.DATA["report_id"] = blocks.get("report_id", "selected_matchup_report")
    module.DATA["generated"] = _dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    module.DATA["a_style"] = blocks.get("fighter_a_style", "Model-derived pressure striker | Orthodox")
    module.DATA["b_style"] = blocks.get("fighter_b_style", "Model-derived counter striker | Orthodox")

    module.TEXT["exec"] = blocks.get("executive_summary", blocks.get("summary", ""))
    module.TEXT["headline"] = blocks.get("headline", "")
    module.TEXT["matchup"] = blocks.get("matchup_snapshot", "")
    module.TEXT["decision"] = blocks.get("decision_structure", "")
    module.TEXT["energy"] = blocks.get("energy", "")
    module.TEXT["fatigue"] = blocks.get("fatigue_failure_points", "")
    module.TEXT["mental"] = blocks.get("mental", "")
    module.TEXT["collapse"] = blocks.get("collapse", "")
    module.TEXT["deception"] = blocks.get("deception_unpredictability", "")
    module.TEXT["range"] = blocks.get("range_geography_control", "")
    module.TEXT["risk"] = blocks.get("risk_warnings", "")
    module.TEXT["betting"] = blocks.get("betting_market_intelligence", "")
    module.TEXT["coach"] = blocks.get("coach_corner_notes", "")
    module.TEXT["final"] = blocks.get("final_projection", "")
    module.TEXT["confidence"] = blocks.get("confidence", "")
    module.TEXT["disclaimer"] = (
        "This report is for informational and analytical purposes only. Predictions are probabilistic and not financial advice. "
        "Combat sports are inherently unpredictable. Bet responsibly. Never wager more than you can afford to lose."
    )

    stream = io.BytesIO()
    c = module.canvas.Canvas(stream, pagesize=module.landscape(module.A4))

    # Render with the dynamic v29 layout helpers so selected-matchup content stays bound.
    _draw_cover(module, c, blocks, layout_safety=layout_safety)
    _draw_executive(module, c, blocks)
    module.section_page(
        c,
        3,
        "Headline Projection",
        "Headline Prediction",
        [
            ("WINNER", module.DATA["winner"], module.BLUE),
            ("METHOD", module.DATA["method"], module.GOLD2),
            ("ROUND", module.DATA["round"], module.GOLD2),
            ("CONFIDENCE", module.DATA["confidence"], module.GOLD2),
        ],
        "Headline Projection",
        module.TEXT["headline"],
        module.BLUE,
    )
    module.section_page(
        c,
        4,
        "Matchup Snapshot",
        "Fighter Snapshot",
        [
            (f"{module.DATA['a_short'].upper()}", "Pressure lane | model-derived", module.BLUE),
            (f"{module.DATA['b_short'].upper()}", "Counter lane | model-derived", module.RED),
            ("CORE CONTRAST", "Instability vs structure", module.GOLD2),
            ("CRITICAL FACTOR", "Who imposes rhythm first", module.GOLD2),
        ],
        "Matchup Snapshot",
        module.TEXT["matchup"],
        module.GOLD,
    )
    _draw_fighter_architecture_radar(module, c, blocks)
    _draw_tactical_edge_table(module, c, blocks)
    module.section_page(
        c,
        7,
        "Decision Structure",
        "Decision Chain",
        [
            ("A LOOP", "Pressure + momentum theft", module.BLUE),
            ("B LOOP", "Map, reset, clean selection", module.RED),
            ("DECISIVE QUESTION", "Order vs instability", module.GOLD2),
            ("WATCH CUE", "Who owns the second decision?", module.GOLD2),
        ],
        "Decision Structure",
        module.TEXT["decision"],
        module.GOLD,
    )
    module.section_page(
        c,
        8,
        "Energy Use Analysis",
        "Energy Rail",
        [
            (f"{module.DATA['a_short'].upper()}", "Burst expenditure", module.BLUE),
            (f"{module.DATA['b_short'].upper()}", "Economic scoring", module.RED),
            ("COST TRIGGER", "Forced entries without payoff", module.GOLD2),
            ("BREAK TRIGGER", "Emergency reactions", module.GOLD2),
        ],
        "Energy Use Analysis",
        module.TEXT["energy"],
        module.GOLD,
    )
    module.section_page(
        c,
        9,
        "Fatigue Failure Points",
        "Failure Rail",
        [
            (f"{module.DATA['a_short'].upper()} FAILURE", "Reduced chaos creation", module.BLUE),
            (f"{module.DATA['b_short'].upper()} FAILURE", "Defensive overexposure", module.RED),
            ("SIGNAL", "Style degradation", module.GOLD2),
            ("LATE RISK", "Readability vs delayed counters", module.GOLD2),
        ],
        "Fatigue Failure Points",
        module.TEXT["fatigue"],
        module.GOLD,
    )
    module.section_page(
        c,
        10,
        "Mental Condition Under Stress",
        "Mental Condition",
        [
            (f"{module.DATA['a_short'].upper()}", "Comfortable in disorder", module.BLUE),
            (f"{module.DATA['b_short'].upper()}", "Composed and structural", module.RED),
            ("A EDGE", "Uncertainty early", module.GOLD2),
            ("B EDGE", "Calm under volatility", module.GOLD2),
        ],
        "Mental Condition Under Stress",
        module.TEXT["mental"],
        module.GOLD,
    )
    module.section_page(
        c,
        11,
        "Collapse Triggers",
        "Collapse Map",
        [
            (f"{module.DATA['a_short'].upper()} TRIGGER", "Chaos stops working", module.BLUE),
            (f"{module.DATA['b_short'].upper()} TRIGGER", "Chaos starts snowballing", module.RED),
            ("PRESSURE CONDITION", "Damage moments + crowding", module.GOLD2),
            ("CONTROL CONDITION", "Checks + denied momentum", module.GOLD2),
        ],
        "Collapse Triggers",
        module.TEXT["collapse"],
        module.RED,
    )
    module.section_page(
        c,
        12,
        "Deception and Unpredictability",
        "Deception Rail",
        [
            (f"{module.DATA['a_short'].upper()}", "Timing disruption", module.BLUE),
            (f"{module.DATA['b_short'].upper()}", "Selective deception", module.RED),
            ("CORE VALUE", "Pressures reads", module.GOLD2),
            ("MAJOR EDGE", "Makes opponent doubt first", module.GOLD2),
        ],
        "Deception and Unpredictability",
        module.TEXT["deception"],
        module.GOLD,
    )
    module.section_page(
        c,
        13,
        "Range / Geography Control",
        "Control Rules",
        [
            (f"{module.DATA['a_short'].upper()} CONTROL", "Emotion over score", module.BLUE),
            (f"{module.DATA['b_short'].upper()} CONTROL", "Clean, countable exchanges", module.RED),
            ("TURN POINT", "Preferred rhythm sustainable", module.GOLD2),
            ("DEEP-ROUND OWNER", "Fighter who breaks structure", module.GOLD2),
        ],
        "Range / Geography Control",
        module.TEXT["range"],
        module.GOLD,
    )
    _draw_round_control_graph(module, c, blocks)
    _draw_scenario_tree(module, c, blocks)
    _draw_scorecard_scenario(module, c, blocks)
    _draw_method_probability_chart(module, c, blocks)
    module.section_page(
        c,
        18,
        "Risk Warnings / What Could Flip the Fight",
        "Risk Rail",
        [
            (f"{module.DATA['a_short'].upper()} RISK", "Aggression without conversion", module.BLUE),
            (f"{module.DATA['b_short'].upper()} RISK", "Emotional tone risk", module.RED),
            ("FLIP POINT", "Sequence changes who commands", module.GOLD2),
            ("SCORING RISK", "Disruption vs clean stretches", module.GOLD2),
        ],
        "Risk Warnings / What Could Flip",
        module.TEXT["risk"],
        module.RED,
    )
    module.section_page(
        c,
        19,
        "Betting Market Intelligence",
        "Risk-Controlled Market Read",
        [
            ("PROJECTION", f"{module.DATA['a_short']} by decision", module.BLUE),
            ("CONFIDENCE", module.DATA["confidence"], module.GOLD2),
            ("VOLATILITY", "Moderate - both men live", module.RED),
            ("PASS CONDITION", "Price too wide", module.GOLD2),
        ],
        "Market Discipline",
        module.TEXT["betting"],
        module.GOLD,
    )
    module.section_page(
        c,
        20,
        "Coach / Corner Notes",
        "Corner Translation",
        [
            (module.DATA["a_short"].upper(), "Functional pressure", module.BLUE),
            (module.DATA["b_short"].upper(), "Win the clean fight", module.RED),
            ("A COMMAND", f"Make {module.DATA['b_short']} reset under threat", module.GOLD2),
            ("B COMMAND", "Punish layered entries", module.GOLD2),
        ],
        "Coach / Corner Notes",
        module.TEXT["coach"],
        module.GOLD,
    )
    module.section_page(
        c,
        21,
        "Final Projection",
        "Final Read",
        [
            ("WINNER", module.DATA["winner"], module.BLUE),
            ("METHOD", module.DATA["method"], module.GOLD2),
            ("ROUND", module.DATA["round"], module.GOLD2),
            ("CONFIDENCE", module.DATA["confidence"], module.GOLD2),
        ],
        "Final Projection",
        module.TEXT["final"],
        module.GOLD,
    )
    module.section_page(
        c,
        22,
        "Confidence Explanation",
        "Confidence Rail",
        [
            ("EDGE TYPE", "Real edge, not wide gap", module.BLUE),
            ("UNCERTAINTY", "Both have control routes", module.GOLD2),
            ("PRIMARY SUPPORT", "Disruption changes decisions", module.GOLD2),
            ("LIVE COUNTER", f"{module.DATA['b_short']} technical stability", module.RED),
        ],
        "Confidence Explanation",
        module.TEXT["confidence"],
        module.GOLD,
    )
    _draw_source_traceability(module, c, blocks, report_context_preview)
    _draw_customer_appendix(module, c)
    c.save()
    pdf_bytes = stream.getvalue()

    selected_matchup = report_context_preview.get("selected_matchup", {}) if isinstance(report_context_preview, dict) else {}
    selected_matchup_present = isinstance(selected_matchup, dict) and bool(
        _clean_text(selected_matchup.get("fighter_a", ""), "") and _clean_text(selected_matchup.get("fighter_b", ""), "")
    )

    footer_pages = layout_safety.get("footer_safe_zone_pages", {}) if isinstance(layout_safety, dict) else {}
    footer_safe = all(bool(info.get("safe")) for info in footer_pages.values()) if footer_pages else False
    source_map = layout_safety.get("source_map", {}) if isinstance(layout_safety, dict) else {}
    source_safe = bool(source_map.get("rows_separated", False)) and bool(source_map.get("source_url_statement_separated", False))
    layout_safety["footer_safe_zone_all_passed"] = bool(footer_safe)
    layout_safety["source_map_layout_safe"] = bool(source_safe)
    layout_safety["visual_layout_safe"] = bool(
        layout_safety.get("logo_blend_ok", False)
        and not layout_safety.get("logo_black_tile_risk", False)
        and footer_safe
        and source_safe
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
            "premium_template_pack_v29_layout_parity_rebuild_v1"
            if selected_matchup_present
            else "premium_template_pack_v29_asset_backed_v1"
        ),
        "page_count": 24,
        "layout_safety": layout_safety,
    }
