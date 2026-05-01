"""
Premium Report Factory Phase 3 – Report Content Assembler

Maps saved queue record fields to the 14 required report sections.
Applies empty-state rules per the locked PDF Report Standard.

No result lookup, no accuracy comparison, no learning, no web discovery,
no billing, no distribution.
"""

from datetime import datetime, timezone

SECTION_NAMES = [
    "cover_page",
    "headline_prediction",
    "executive_summary",
    "matchup_snapshot",
    "decision_structure",
    "energy_use",
    "fatigue_failure_points",
    "mental_condition",
    "collapse_triggers",
    "deception_and_unpredictability",
    "round_by_round_control_shifts",
    "scenario_tree",
    "risk_warnings",
    "operator_notes",
]


def _present(value) -> bool:
    return bool(str(value or "").strip())


def assemble_report_sections(queue_record: dict) -> tuple:
    """
    Assemble the 14 required report sections from a saved queue record.

    Returns:
        sections: dict mapping section_name -> section_text
        section_status: dict mapping section_name -> status string
    """
    fighter_a = str(queue_record.get("fighter_a") or "").strip()
    fighter_b = str(queue_record.get("fighter_b") or "").strip()
    event_name = str(queue_record.get("event_name") or "").strip()
    event_date = str(queue_record.get("event_date") or "").strip()
    promotion = str(queue_record.get("promotion") or "").strip()
    location = str(queue_record.get("location") or "").strip()
    weight_class = str(queue_record.get("weight_class") or "").strip()
    ruleset = str(queue_record.get("ruleset") or "").strip()
    source_reference = str(queue_record.get("source_reference") or "").strip()
    operator_notes_text = str(queue_record.get("notes") or "").strip()

    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    sections = {}
    section_status = {}

    # 1. Cover Page — always populated from queue record
    cover_lines = [
        "AI-RISA Premium Report Factory",
        "Report Type: Premium Report",
        "",
        "Event: {}".format(event_name or "-"),
        "Date: {}".format(event_date or "-"),
        "Promotion: {}".format(promotion or "-"),
        "Location: {}".format(location or "-"),
        "Weight Class: {}".format(weight_class or "-"),
        "Ruleset: {}".format(ruleset or "-"),
        "",
        "Matchup: {} vs {}".format(fighter_a or "-", fighter_b or "-"),
        "",
        "Generated: {}".format(generated_at),
        "Source Reference: {}".format(source_reference or "-"),
    ]
    if operator_notes_text:
        cover_lines += ["", "Operator Notes: {}".format(operator_notes_text)]
    sections["cover_page"] = "\n".join(cover_lines)
    section_status["cover_page"] = "complete"

    # 2. Headline Prediction — no prediction engine in Phase 3
    sections["headline_prediction"] = (
        "Prediction unavailable — insufficient data for this matchup. "
        "No prediction model data is available for Phase 3 report generation."
    )
    section_status["headline_prediction"] = "unavailable"

    # 3. Executive Summary
    if _present(fighter_a) and _present(fighter_b) and _present(event_name):
        sections["executive_summary"] = (
            "This premium report covers the scheduled matchup between {} and {} "
            "at {}. "
            "Full analytical data is not available for automated generation in Phase 3. "
            "Section content will be enriched in future report generations as prediction model data becomes available. "
            "All sections are present per the AI-RISA report standard.".format(
                fighter_a, fighter_b, event_name
            )
        )
        section_status["executive_summary"] = "partial"
    else:
        sections["executive_summary"] = "Executive summary unavailable — insufficient matchup data."
        section_status["executive_summary"] = "unavailable"

    # 4. Matchup Snapshot
    snapshot_lines = [
        "Fighter A: {}".format(fighter_a or "—"),
        "Fighter B: {}".format(fighter_b or "—"),
        "Weight Class: {}".format(weight_class or "—"),
        "Ruleset: {}".format(ruleset or "—"),
        "",
        "Head-to-head comparison:",
        "  Reach: - vs -",
        "  Stance: - vs -",
        "  Win method distribution: unavailable",
    ]
    sections["matchup_snapshot"] = "\n".join(snapshot_lines)
    if _present(fighter_a) and _present(fighter_b):
        section_status["matchup_snapshot"] = "partial"
    else:
        section_status["matchup_snapshot"] = "unavailable"

    # 5. Decision Structure
    sections["decision_structure"] = "Decision structure analysis unavailable."
    section_status["decision_structure"] = "unavailable"

    # 6. Energy Use and Gas Tank Projection
    sections["energy_use"] = "Energy projection unavailable."
    section_status["energy_use"] = "unavailable"

    # 7. Fatigue Failure Points
    sections["fatigue_failure_points"] = "Fatigue analysis unavailable."
    section_status["fatigue_failure_points"] = "unavailable"

    # 8. Mental Condition
    sections["mental_condition"] = "Mental condition profile unavailable."
    section_status["mental_condition"] = "unavailable"

    # 9. Collapse Triggers
    sections["collapse_triggers"] = "Collapse trigger analysis unavailable."
    section_status["collapse_triggers"] = "unavailable"

    # 10. Deception and Unpredictability
    sections["deception_and_unpredictability"] = "Deception profile unavailable."
    section_status["deception_and_unpredictability"] = "unavailable"

    # 11. Round-by-Round Control Shifts
    sections["round_by_round_control_shifts"] = "Round-by-round projection unavailable."
    section_status["round_by_round_control_shifts"] = "unavailable"

    # 12. Scenario Tree / Method Pathways
    sections["scenario_tree"] = "Scenario pathways unavailable."
    section_status["scenario_tree"] = "unavailable"

    # 13. Risk Warnings — always rendered with minimum content
    risk_lines = [
        "Standard prediction caveats apply. See operator notes.",
        "",
        "Limitations:",
        "- This report is generated from queue metadata only. No live prediction model data was used.",
        "- Section content accuracy is limited to available structured fields in the saved queue record.",
        "- Analytical sections will be enriched in future report versions.",
        "- Do not rely on this report as the sole input for any decision.",
    ]
    sections["risk_warnings"] = "\n".join(risk_lines)
    section_status["risk_warnings"] = "complete"

    # 14. Operator Notes
    if operator_notes_text:
        sections["operator_notes"] = operator_notes_text
        section_status["operator_notes"] = "complete"
    else:
        sections["operator_notes"] = "No operator notes recorded."
        section_status["operator_notes"] = "complete"

    return sections, section_status
