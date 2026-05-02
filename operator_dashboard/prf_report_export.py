"""
Premium Report Factory Phase 3 – PDF Export Helper

Writes the assembled report sections to a PDF file using fpdf2.
Output folder: ops/prf_reports/

No result lookup, no accuracy comparison, no learning, no web discovery,
no billing, no distribution, no auto-send.
"""

import os
import re
from datetime import datetime, timezone


_INVALID_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|]+')
_VISUAL_LAYOUT_FLAG = "AI_RISA_PRF_VISUAL_INTELLIGENCE_LAYOUT"
_FLAG_TRUE_VALUES = {"1", "true", "yes", "on"}

SECTION_DISPLAY_NAMES = {
    "cover_page": "1. Cover Page",
    "headline_prediction": "2. Headline Prediction",
    "executive_summary": "3. Executive Summary",
    "matchup_snapshot": "4. Matchup Snapshot",
    "decision_structure": "5. Decision Structure",
    "energy_use": "6. Energy Use and Gas Tank Projection",
    "fatigue_failure_points": "7. Fatigue Failure Points",
    "mental_condition": "8. Mental Condition",
    "collapse_triggers": "9. Collapse Triggers",
    "deception_and_unpredictability": "10. Deception and Unpredictability",
    "round_by_round_control_shifts": "11. Round-by-Round Control Shifts",
    "scenario_tree": "12. Scenario Tree / Method Pathways",
    "risk_warnings": "13. Risk Warnings",
    "operator_notes": "14. Operator Notes",
}

LEGACY_SECTION_ORDER = [
    "cover_page", "headline_prediction", "executive_summary", "matchup_snapshot",
    "decision_structure", "energy_use", "fatigue_failure_points", "mental_condition",
    "collapse_triggers", "deception_and_unpredictability", "round_by_round_control_shifts",
    "scenario_tree", "risk_warnings", "operator_notes",
]

VISUAL_LAYOUT_SECTION_GROUPS = [
    ("Executive Intelligence", ["headline_prediction", "executive_summary", "risk_warnings"]),
    (
        "Combat Dynamics",
        [
            "matchup_snapshot",
            "decision_structure",
            "energy_use",
            "fatigue_failure_points",
            "mental_condition",
            "collapse_triggers",
            "deception_and_unpredictability",
        ],
    ),
    ("Scenario and Control", ["round_by_round_control_shifts", "scenario_tree", "operator_notes"]),
]


def _sanitize_filename_component(value: str) -> str:
    """Normalize user-derived filename parts so Windows paths remain valid."""
    sanitized = _INVALID_FILENAME_CHARS.sub("_", str(value or "").strip())
    sanitized = re.sub(r"\s+", "_", sanitized)
    sanitized = sanitized.strip(" ._")
    return sanitized or "unknown"


def _visual_layout_enabled() -> bool:
    value = str(os.getenv(_VISUAL_LAYOUT_FLAG, "")).strip().lower()
    return value in _FLAG_TRUE_VALUES


def _safe_pdf_text(value: str) -> str:
    return str(value or "").encode("latin-1", errors="replace").decode("latin-1")


def _normalize_block_text(value: str, fallback: str = "Section content unavailable.") -> str:
    normalized = str(value or "").strip()
    return normalized or fallback


def _render_block_title(pdf, title: str, subtitle: str = "") -> None:
    pdf.set_text_color(24, 36, 56)
    pdf.set_font("Helvetica", "B", 14)
    pdf.multi_cell(pdf.epw, 8, _safe_pdf_text(title))
    if subtitle:
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(90, 99, 110)
        pdf.multi_cell(pdf.epw, 5, _safe_pdf_text(subtitle))
    pdf.ln(2)


def _render_body_copy(pdf, text: str, font_size: int = 10, line_height: int = 6) -> None:
    pdf.set_font("Helvetica", "", font_size)
    pdf.set_text_color(35, 41, 49)
    for line in _normalize_block_text(text).split("\n"):
        pdf.multi_cell(pdf.epw, line_height, _safe_pdf_text(line))
    pdf.ln(2)


def _render_status_badge(pdf, label: str, fill_color: tuple[int, int, int], text_color: tuple[int, int, int]) -> None:
    pdf.set_fill_color(*fill_color)
    pdf.set_text_color(*text_color)
    pdf.set_font("Helvetica", "B", 9)
    pdf.multi_cell(pdf.epw, 7, _safe_pdf_text(label), align="C", fill=True)
    pdf.ln(1)


def _render_key_value_line(pdf, label: str, value: str) -> None:
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(44, 62, 80)
    pdf.write(5, _safe_pdf_text(label + ": "))
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(60, 68, 75)
    pdf.multi_cell(pdf.epw, 5, _safe_pdf_text(value))


def _render_section_card(pdf, section_key: str, content: str) -> None:
    pdf.set_draw_color(210, 216, 224)
    pdf.set_fill_color(248, 249, 251)
    pdf.set_line_width(0.2)
    start_x = pdf.get_x()
    start_y = pdf.get_y()

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(18, 43, 58)
    pdf.multi_cell(pdf.epw, 7, _safe_pdf_text(SECTION_DISPLAY_NAMES.get(section_key, section_key)), fill=True)
    pdf.set_x(start_x)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(35, 41, 49)
    for line in _normalize_block_text(content).split("\n"):
        pdf.multi_cell(pdf.epw, 5, _safe_pdf_text(line), fill=True)
        pdf.set_x(start_x)

    end_y = pdf.get_y()
    pdf.rect(start_x, start_y, pdf.epw, max(end_y - start_y, 12))
    pdf.ln(2)


def _render_visual_cover(pdf, report_obj: dict, sections: dict, is_draft_only: bool) -> None:
    fighter_a = str(report_obj.get("fighter_a") or "").strip()
    fighter_b = str(report_obj.get("fighter_b") or "").strip()
    quality_status = str(report_obj.get("report_quality_status") or "generated").strip() or "generated"
    event_name = str(report_obj.get("event_name") or report_obj.get("event_id") or "Unknown Event").strip()
    generated_at = str(report_obj.get("generated_at") or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")).strip()
    approval_state = "Approved" if bool(report_obj.get("operator_approval_state")) else "Not Approved"
    analysis_source_type = str(report_obj.get("analysis_source_type") or "unknown").strip() or "unknown"

    pdf.set_fill_color(20, 32, 48)
    pdf.set_text_color(255, 255, 255)
    pdf.rect(0, 0, 210, 60, style="F")
    pdf.set_y(14)
    pdf.set_font("Helvetica", "B", 20)
    pdf.multi_cell(pdf.epw, 10, _safe_pdf_text("AI-RISA Premium Report"), align="C")
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(pdf.epw, 7, _safe_pdf_text("Premium Cover"), align="C")
    pdf.ln(4)

    matchup_label = "{} vs {}".format(fighter_a, fighter_b) if fighter_a and fighter_b else "Matchup Report"
    pdf.set_text_color(24, 36, 56)
    pdf.set_font("Helvetica", "B", 16)
    pdf.multi_cell(pdf.epw, 9, _safe_pdf_text(matchup_label), align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(90, 99, 110)
    pdf.multi_cell(pdf.epw, 6, _safe_pdf_text(event_name), align="C")
    pdf.ln(3)

    badge_fill = (143, 36, 36) if is_draft_only else (24, 94, 65)
    badge_text = "DRAFT ONLY - NOT CUSTOMER READY" if is_draft_only else "QUALITY STATUS: {}".format(quality_status.upper())
    _render_status_badge(pdf, badge_text, badge_fill, (255, 255, 255))
    _render_key_value_line(pdf, "Operator Approval", approval_state)
    _render_key_value_line(pdf, "Analysis Source", analysis_source_type)
    _render_key_value_line(pdf, "Generated At", generated_at)
    pdf.ln(2)
    _render_block_title(pdf, "Cover Summary")
    _render_body_copy(pdf, str(sections.get("cover_page") or ""))


def _render_traceability_appendix(pdf, report_obj: dict) -> None:
    _render_block_title(pdf, "Traceability Appendix", "Deterministic section provenance and combat metadata")

    populated_sections = report_obj.get("populated_sections") or []
    missing_engine_outputs = report_obj.get("missing_engine_outputs") or []
    section_source_map = report_obj.get("section_source_map") or {}

    _render_block_title(pdf, "Populated Sections")
    _render_body_copy(pdf, "\n".join(populated_sections) if populated_sections else "No populated sections recorded.")

    _render_block_title(pdf, "Missing Engine Outputs")
    _render_body_copy(pdf, "\n".join(missing_engine_outputs) if missing_engine_outputs else "No missing engine outputs recorded.")

    _render_block_title(pdf, "Section Source Map")
    if section_source_map:
        rendered_lines = []
        for section_name in sorted(section_source_map):
            section_meta = section_source_map.get(section_name) or {}
            source_type = str(section_meta.get("source_type") or "unknown").strip() or "unknown"
            contributing_engines = section_meta.get("contributing_engines") or []
            rendered_lines.append(
                "{} -> {} -> {}".format(
                    section_name,
                    source_type,
                    ", ".join(str(engine) for engine in contributing_engines) or "none",
                )
            )
        _render_body_copy(pdf, "\n".join(rendered_lines))
    else:
        _render_body_copy(pdf, "No section source map recorded.")


def _render_visual_pdf_report(pdf, report_obj: dict, sections: dict, is_draft_only: bool) -> None:
    _render_visual_cover(pdf, report_obj, sections, is_draft_only)

    for page_title, section_keys in VISUAL_LAYOUT_SECTION_GROUPS:
        pdf.add_page()
        _render_block_title(pdf, page_title)
        for section_key in section_keys:
            _render_section_card(pdf, section_key, str(sections.get(section_key) or ""))

    pdf.add_page()
    _render_traceability_appendix(pdf, report_obj)


def _render_legacy_pdf_report(pdf, sections: dict) -> None:
    for section_key in LEGACY_SECTION_ORDER:
        display_name = SECTION_DISPLAY_NAMES.get(section_key, section_key)
        content = str(sections.get(section_key) or "Section content unavailable.")

        pdf.set_font("Helvetica", "B", 11)
        pdf.multi_cell(pdf.epw, 8, _safe_pdf_text(display_name))

        pdf.set_font("Helvetica", "", 10)
        for line in content.split("\n"):
            pdf.multi_cell(pdf.epw, 6, _safe_pdf_text(line))
        pdf.ln(3)


def build_report_filename(event_id: str, matchup_id: str) -> str:
    """Deterministic PDF filename per the locked export rules."""
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    safe_event_id = _sanitize_filename_component(event_id)
    safe_matchup_id = _sanitize_filename_component(matchup_id)
    return "ai_risa_premium_report_{}_{}_{}.pdf".format(safe_event_id, safe_matchup_id, date_str)


def write_pdf_report(report_obj: dict, sections: dict, reports_dir: str) -> dict:
    """
    Render the structured report to a PDF file using fpdf2.

    Returns:
        { ok, file_path, file_name, error }
    """
    event_id = str(report_obj.get("event_id") or "unknown").strip()
    matchup_id = str(report_obj.get("matchup_id") or "unknown").strip()
    fighter_a = str(report_obj.get("fighter_a") or "").strip()
    fighter_b = str(report_obj.get("fighter_b") or "").strip()
    is_draft_only = str(report_obj.get("report_quality_status") or "").strip() == "draft_only"

    file_name = build_report_filename(event_id, matchup_id)
    file_path = os.path.join(reports_dir, file_name)

    try:
        os.makedirs(reports_dir, exist_ok=True)
        from fpdf import FPDF

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        if _visual_layout_enabled():
            _render_visual_pdf_report(pdf, report_obj, sections, is_draft_only)
        else:
            pdf.set_font("Helvetica", "B", 16)
            pdf.multi_cell(pdf.epw, 10, _safe_pdf_text("AI-RISA Premium Report"), align="C")
            pdf.set_font("Helvetica", "", 12)
            matchup_label = "{} vs {}".format(fighter_a, fighter_b) if fighter_a and fighter_b else "Matchup Report"
            pdf.multi_cell(pdf.epw, 8, _safe_pdf_text(matchup_label), align="C")
            if is_draft_only:
                pdf.set_text_color(150, 30, 30)
                pdf.set_font("Helvetica", "B", 11)
                pdf.multi_cell(pdf.epw, 8, _safe_pdf_text("DRAFT ONLY - NOT CUSTOMER READY"), align="C")
                pdf.set_text_color(0, 0, 0)
                pdf.set_font("Helvetica", "", 12)
            pdf.ln(4)
            _render_legacy_pdf_report(pdf, sections)

        # Footer
        generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        pdf.set_font("Helvetica", "I", 8)
        footer_text = "AI-RISA Premium Report Factory - Generated: {}".format(generated_at)
        if is_draft_only:
            footer_text += " | DRAFT ONLY - NOT CUSTOMER READY"
        pdf.multi_cell(pdf.epw, 6, _safe_pdf_text(footer_text), align="C")

        pdf.output(file_path)

        return {
            "ok": True,
            "file_path": file_path,
            "file_name": file_name,
            "error": None,
        }

    except Exception as exc:
        return {
            "ok": False,
            "file_path": None,
            "file_name": file_name,
            "error": str(exc),
        }
