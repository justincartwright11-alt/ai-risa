"""
Premium Report Factory Phase 3 – PDF Export Helper

Writes the assembled report sections to a PDF file using fpdf2.
Output folder: ops/prf_reports/

No result lookup, no accuracy comparison, no learning, no web discovery,
no billing, no distribution, no auto-send.
"""

import os
from datetime import datetime, timezone


def build_report_filename(event_id: str, matchup_id: str) -> str:
    """Deterministic PDF filename per the locked export rules."""
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    return "ai_risa_premium_report_{}_{}_{}.pdf".format(event_id, matchup_id, date_str)


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

    file_name = build_report_filename(event_id, matchup_id)
    file_path = os.path.join(reports_dir, file_name)

    try:
        os.makedirs(reports_dir, exist_ok=True)
        from fpdf import FPDF

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        page_w = pdf.epw

        # Title block
        pdf.set_font("Helvetica", "B", 16)
        title_text = "AI-RISA Premium Report".encode("latin-1", errors="replace").decode("latin-1")
        pdf.multi_cell(page_w, 10, title_text, align="C")
        pdf.set_font("Helvetica", "", 12)
        matchup_label = "{} vs {}".format(fighter_a, fighter_b) if fighter_a and fighter_b else "Matchup Report"
        matchup_label = matchup_label.encode("latin-1", errors="replace").decode("latin-1")
        pdf.multi_cell(page_w, 8, matchup_label, align="C")
        pdf.ln(4)

        section_display_names = {
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

        section_order = [
            "cover_page", "headline_prediction", "executive_summary", "matchup_snapshot",
            "decision_structure", "energy_use", "fatigue_failure_points", "mental_condition",
            "collapse_triggers", "deception_and_unpredictability", "round_by_round_control_shifts",
            "scenario_tree", "risk_warnings", "operator_notes",
        ]

        for section_key in section_order:
            display_name = section_display_names.get(section_key, section_key)
            content = str(sections.get(section_key) or "Section content unavailable.")

            pdf.set_font("Helvetica", "B", 11)
            safe_display = display_name.encode("latin-1", errors="replace").decode("latin-1")
            pdf.multi_cell(page_w, 8, safe_display)

            pdf.set_font("Helvetica", "", 10)
            for line in content.split("\n"):
                safe_line = line.encode("latin-1", errors="replace").decode("latin-1")
                pdf.multi_cell(page_w, 6, safe_line)
            pdf.ln(3)

        # Footer
        generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        pdf.set_font("Helvetica", "I", 8)
        footer_text = "AI-RISA Premium Report Factory - Generated: {}".format(generated_at)
        footer_text = footer_text.encode("latin-1", errors="replace").decode("latin-1")
        pdf.multi_cell(page_w, 6, footer_text, align="C")

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
