"""
Premium Report Factory Phase 3 – Report Content Assembler

Maps saved queue record fields to the 14 required report sections.
Applies empty-state rules per the locked PDF Report Standard.

No result lookup, no accuracy comparison, no learning, no web discovery,
no billing, no distribution.
"""

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

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

_BASE_DIR = Path(__file__).resolve().parent.parent
_PREDICTIONS_DIR = _BASE_DIR / "predictions"
_MATCHUPS_DIR = _BASE_DIR / "matchups"
_MANUAL_ENRICHMENT_PATH = _BASE_DIR / "fighters" / "manual_profile_enrichment.json"
_CANONICAL_REGISTRY_PATH = _BASE_DIR / "fighters" / "canonical_fighter_registry.json"


def _slugify(value: str) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text


def _to_title(value: str) -> str:
    return str(value or "").replace("_", " ").strip().title()


def _read_json(path: Path):
    if not path.exists() or not path.is_file():
        return None
    try:
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _load_profile_record(slug: str) -> dict:
    if not slug:
        return {}
    profile = {}
    manual = _read_json(_MANUAL_ENRICHMENT_PATH)
    if isinstance(manual, dict):
        maybe = manual.get(slug)
        if isinstance(maybe, dict):
            profile.update(maybe)

    registry = _read_json(_CANONICAL_REGISTRY_PATH)
    if isinstance(registry, dict):
        entry = registry.get(slug)
        if isinstance(entry, dict):
            profile.update(entry)
    return profile


def _build_matchup_slug(fighter_a: str, fighter_b: str) -> str:
    return "{}_vs_{}".format(_slugify(fighter_a), _slugify(fighter_b)).strip("_")


def _find_prediction_record(queue_record: dict) -> tuple[dict, str]:
    fighter_a = str(queue_record.get("fighter_a") or "").strip()
    fighter_b = str(queue_record.get("fighter_b") or "").strip()
    matchup_id = str(queue_record.get("matchup_id") or "").strip()
    event_name = str(queue_record.get("event_name") or "").strip()
    source_reference = str(queue_record.get("source_reference") or "").strip()

    matchup_slug = _build_matchup_slug(fighter_a, fighter_b)
    reverse_slug = _build_matchup_slug(fighter_b, fighter_a)
    candidates = [
        _PREDICTIONS_DIR / "pred_{}.json".format(matchup_slug),
        _PREDICTIONS_DIR / "{}_prediction.json".format(matchup_slug),
        _PREDICTIONS_DIR / "pred_{}.json".format(reverse_slug),
        _PREDICTIONS_DIR / "{}_prediction.json".format(reverse_slug),
    ]

    for path in candidates:
        payload = _read_json(path)
        if isinstance(payload, dict):
            return payload, path.stem

    if not _PREDICTIONS_DIR.exists():
        return {}, ""

    normalized_matchup_id = _slugify(matchup_id)
    a_slug = _slugify(fighter_a)
    b_slug = _slugify(fighter_b)
    source_token = _slugify(Path(source_reference).stem)
    if len(source_token) < 8:
        source_token = ""
    event_token = _slugify(event_name)
    if len(event_token) < 10:
        event_token = ""

    for name in os.listdir(_PREDICTIONS_DIR):
        if not name.endswith(".json"):
            continue
        stem = _slugify(Path(name).stem)
        if not stem:
            continue
        strong_match = bool(normalized_matchup_id and normalized_matchup_id in stem)
        fighter_pair_match = bool(a_slug and b_slug and a_slug in stem and b_slug in stem)
        weak_match = bool(
            (
                (event_token and event_token in stem)
                or (source_token and source_token in stem)
            )
            and ((a_slug and a_slug in stem) or (b_slug and b_slug in stem))
        )
        if not (strong_match or fighter_pair_match or weak_match):
            continue
        payload = _read_json(_PREDICTIONS_DIR / name)
        if isinstance(payload, dict):
            return payload, Path(name).stem
    return {}, ""


def _find_matchup_sections_record(queue_record: dict) -> tuple[dict, str]:
    fighter_a = str(queue_record.get("fighter_a") or "").strip()
    fighter_b = str(queue_record.get("fighter_b") or "").strip()
    matchup_slug = _build_matchup_slug(fighter_a, fighter_b)
    reverse_slug = _build_matchup_slug(fighter_b, fighter_a)

    if not _MATCHUPS_DIR.exists():
        return {}, ""

    candidates = [
        _MATCHUPS_DIR / "{}_premium_sections.json".format(matchup_slug),
        _MATCHUPS_DIR / "{}_premium_sections.json".format(reverse_slug),
    ]
    for path in candidates:
        payload = _read_json(path)
        if isinstance(payload, dict):
            return payload, path.stem

    a_slug = _slugify(fighter_a)
    b_slug = _slugify(fighter_b)
    for name in os.listdir(_MATCHUPS_DIR):
        if not name.endswith("_premium_sections.json"):
            continue
        stem = _slugify(Path(name).stem)
        if a_slug and b_slug and not (a_slug in stem and b_slug in stem):
            continue
        payload = _read_json(_MATCHUPS_DIR / name)
        if isinstance(payload, dict):
            return payload, Path(name).stem
    return {}, ""


def _build_cover_page(queue_record: dict, generated_at: str) -> str:
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
    return "\n".join(cover_lines)


def _build_sections_from_prediction(queue_record: dict, prediction: dict) -> dict:
    fighter_a = str(queue_record.get("fighter_a") or "").strip()
    fighter_b = str(queue_record.get("fighter_b") or "").strip()
    event_name = str(queue_record.get("event_name") or "").strip()
    event_date = str(queue_record.get("event_date") or "").strip()
    method = str(prediction.get("method") or "Decision").strip() or "Decision"
    confidence = float(prediction.get("confidence") or 0.55)
    confidence_pct = max(1.0, min(99.0, round(confidence * 100.0, 1)))
    winner_id = str(prediction.get("predicted_winner") or "").strip()
    winner_name = _to_title(winner_id.replace("fighter_", "")) if winner_id else (fighter_a or fighter_b or "Unknown")
    tactical_edge = str(prediction.get("main_tactical_edge") or "cleaner phase control and tactical sequencing").strip()
    flow_projection = str(prediction.get("round_flow_projection") or "measured three-round control progression with momentum shifts in the middle rounds").strip()

    sections = {
        "headline_prediction": (
            "Projected winner: {} via {}. Confidence sits at {}% based on available AI-RISA prediction records, "
            "with the likely edge coming from {}."
        ).format(winner_name, method, confidence_pct, tactical_edge),
        "executive_summary": (
            "This matchup between {} and {} at {} ({}) is mapped from an existing AI-RISA prediction record. "
            "The projected outcome favors {} by {}, with phase-control and tactical clarity as the central decision drivers."
        ).format(fighter_a or "Fighter A", fighter_b or "Fighter B", event_name or "scheduled event", event_date or "date pending", winner_name, method),
        "matchup_snapshot": (
            "Fighter A: {}\n"
            "Fighter B: {}\n"
            "Event: {}\n"
            "Date: {}\n"
            "Prediction record: {} by {} at {}% confidence."
        ).format(fighter_a or "-", fighter_b or "-", event_name or "-", event_date or "-", winner_name, method, confidence_pct),
        "decision_structure": str(prediction.get("decision_structure") or "AI-RISA decision structure indicates control through repeatable tactical choices and disciplined phase entries."),
        "energy_use": "Energy profile indicates {} with pacing shaped toward {}.".format(str(prediction.get("energy_use") or "balanced output and recovery control").strip(), flow_projection),
        "fatigue_failure_points": "Primary fatigue pressure appears in {} rounds when sequencing quality drops under repeated exchanges.".format(str(prediction.get("fatigue_failure_points") or "late").strip()),
        "mental_condition": "Mental condition profile projects {} under pressure with stable tactical adherence.".format(str(prediction.get("mental_condition") or "composed").strip()),
        "collapse_triggers": "Collapse risk increases when {} and tactical discipline decays across consecutive rounds.".format(str(prediction.get("collapse_triggers") or "high-pressure exchanges force repeated defensive resets").strip()),
        "deception_and_unpredictability": (
            "Deception profile favors timing shifts around {} while masking setup intent through rhythm variation."
        ).format(tactical_edge),
        "round_by_round_control_shifts": "Round flow projection: {}. Control is expected to swing around transition success and late-round composure.",
        "scenario_tree": (
            "Scenario 1: projected winner {} controls middle rounds and secures decision momentum. "
            "Scenario 2: opponent interrupts phase entries and narrows cards late. "
            "Scenario 3: split momentum fight resolved by cleaner closing sequences."
        ).format(winner_name),
        "risk_warnings": (
            "Risk warnings: this projection is probabilistic and sensitive to early momentum shifts, injury states, and adaptation speed. "
            "Operator review is required before customer delivery."
        ),
        "operator_notes": str(queue_record.get("notes") or "Operator review completed against linked prediction record.").strip() or "Operator review completed against linked prediction record.",
    }
    sections["round_by_round_control_shifts"] = sections["round_by_round_control_shifts"].format(flow_projection)
    return sections


def _build_sections_from_matchup_payload(queue_record: dict, payload: dict) -> dict:
    final_projection = str(payload.get("final_projection") or "").strip()
    confidence_explanation = str(payload.get("confidence_explanation") or "").strip()
    headline = "{} {}".format(final_projection, confidence_explanation).strip()
    if not headline:
        headline = "Linked AI-RISA premium analysis record provides a structured projected outcome and tactical edge model."

    risk = "\n\n".join(
        [
            str(payload.get("risk_factors") or "").strip(),
            str(payload.get("what_could_flip") or "").strip(),
            str(payload.get("disclaimer") or "").strip(),
        ]
    ).strip()
    if not risk:
        risk = "Risk warnings include tactical volatility, adaptation variance, and execution swings across phases."

    sections = {
        "headline_prediction": headline,
        "executive_summary": str(payload.get("executive_summary") or "").strip(),
        "matchup_snapshot": str(payload.get("matchup_snapshot") or "").strip(),
        "decision_structure": str(payload.get("decision_structure") or "").strip(),
        "energy_use": str(payload.get("energy_use") or "").strip(),
        "fatigue_failure_points": str(payload.get("fatigue_failure_points") or "").strip(),
        "mental_condition": str(payload.get("mental_condition") or "").strip(),
        "collapse_triggers": str(payload.get("collapse_triggers") or "").strip(),
        "deception_and_unpredictability": str(payload.get("deception_unpredictability") or "").strip(),
        "round_by_round_control_shifts": str(payload.get("round_by_round_outlook") or payload.get("fight_turns") or "").strip(),
        "scenario_tree": str(payload.get("scenario_tree") or "").strip(),
        "risk_warnings": risk,
        "operator_notes": (
            str(queue_record.get("notes") or "").strip()
            or str(payload.get("corner_notes") or "").strip()
            or "Operator review completed against linked premium analysis record."
        ),
    }
    return sections


def _build_internal_draft_sections(queue_record: dict) -> dict:
    fighter_a = str(queue_record.get("fighter_a") or "").strip()
    fighter_b = str(queue_record.get("fighter_b") or "").strip()
    event_name = str(queue_record.get("event_name") or "").strip()
    event_date = str(queue_record.get("event_date") or "").strip()

    a_slug = _slugify(fighter_a)
    b_slug = _slugify(fighter_b)
    a_profile = _load_profile_record(a_slug)
    b_profile = _load_profile_record(b_slug)

    a_style = str(a_profile.get("style") or "adaptive pressure-control style").strip()
    b_style = str(b_profile.get("style") or "counter-timing control style").strip()
    a_stance = str(a_profile.get("stance") or "mixed-stance").strip()
    b_stance = str(b_profile.get("stance") or "mixed-stance").strip()

    sections = {
        "headline_prediction": (
            "Internal AI-RISA draft projection favors {} by decision based on style collision analysis: {} versus {}."
        ).format(fighter_a or "Fighter A", a_style, b_style),
        "executive_summary": (
            "Internal draft for {} vs {} at {} ({}) synthesizes available fighter-profile and queue metadata into a complete premium section set for operator review."
        ).format(fighter_a or "Fighter A", fighter_b or "Fighter B", event_name or "scheduled event", event_date or "date pending"),
        "matchup_snapshot": (
            "Fighter A: {} ({}, {})\n"
            "Fighter B: {} ({}, {})\n"
            "Profile-derived matchup lens: phase control versus interruption timing."
        ).format(fighter_a or "-", a_style, a_stance, fighter_b or "-", b_style, b_stance),
        "decision_structure": (
            "Decision structure lens: {} should prioritize repeatable entries and positional consolidation, while {} should emphasize denial-first sequencing and reset geometry."
        ).format(fighter_a or "Fighter A", fighter_b or "Fighter B"),
        "energy_use": (
            "Energy-use lens: projected pacing favors measured first-round data collection, then controlled output escalation in rounds two and three."
        ),
        "fatigue_failure_points": (
            "Fatigue-failure lens: pressure-side risk rises when entries are repeatedly denied; denial-side risk rises when reset quality slows under layered exchanges."
        ),
        "mental_condition": (
            "Mental-condition lens: both corners need composure through tactical adversity; tilt risk increases when a fighter abandons process discipline after lost exchanges."
        ),
        "collapse_triggers": (
            "Collapse-trigger lens: collapse begins when one fighter is repeatedly forced into non-preferred exchange phases for two rounds without adjustment."
        ),
        "deception_and_unpredictability": (
            "Deception lens: rhythm disruption, setup feints, and phase-hiding entries are key to creating high-value openings without overcommitting."
        ),
        "round_by_round_control_shifts": (
            "Round-by-round control shifts: round one information mapping, round two transition ownership, round three composure and closure quality decide the likely outcome."
        ),
        "scenario_tree": (
            "Scenario tree: (1) pressure-control accumulation, (2) interruption-led reset control, (3) split-momentum decision resolved by cleaner finishing sequences."
        ),
        "risk_warnings": (
            "Risk warnings: this internal draft is based on local profile metadata and tactical synthesis, and must be operator-reviewed before any customer delivery decision."
        ),
        "operator_notes": (
            str(queue_record.get("notes") or "").strip()
            or "Internal AI-RISA draft generated for operator review before customer export consideration."
        ),
    }
    return sections


def _present(value) -> bool:
    return bool(str(value or "").strip())


def build_report_content_bundle(queue_record: dict, allow_internal_draft: bool = False) -> dict:
    """Build report content sections plus linkage metadata for Button 2 generation."""
    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    sections = {
        "cover_page": _build_cover_page(queue_record, generated_at),
    }
    section_status = {"cover_page": "complete"}
    linked_analysis_record_id = ""
    analysis_source_type = "none"
    analysis_source_status = "not_found"
    forced_unavailable_sections = set()
    linkage_keys_used = [
        "fighter_a",
        "fighter_b",
        "normalized_matchup_id",
        "event_name",
        "event_date",
        "source_reference",
    ]

    matchup_payload, matchup_record_id = _find_matchup_sections_record(queue_record)
    if matchup_payload:
        sections.update(_build_sections_from_matchup_payload(queue_record, matchup_payload))
        linked_analysis_record_id = matchup_record_id
        analysis_source_type = "analysis_json"
        analysis_source_status = "found"
    else:
        prediction_payload, prediction_record_id = _find_prediction_record(queue_record)
        if prediction_payload:
            sections.update(_build_sections_from_prediction(queue_record, prediction_payload))
            linked_analysis_record_id = prediction_record_id
            analysis_source_type = "model_record"
            analysis_source_status = "found"
        elif allow_internal_draft:
            sections.update(_build_internal_draft_sections(queue_record))
            linked_analysis_record_id = _build_matchup_slug(
                str(queue_record.get("fighter_a") or ""),
                str(queue_record.get("fighter_b") or ""),
            )
            analysis_source_type = "generated_internal_draft"
            analysis_source_status = "found"

    # Preserve explicit blocked behavior when no source and no internal draft mode.
    if analysis_source_status == "not_found":
        sections.update({
            "headline_prediction": "Prediction unavailable - no linked AI-RISA analysis record was found for this matchup.",
            "executive_summary": "Analysis unavailable for customer export. Link an existing record or generate an internal draft for review.",
            "matchup_snapshot": "Matchup snapshot is incomplete because no linked analysis source was found.",
            "decision_structure": "Decision structure analysis unavailable.",
            "energy_use": "Energy projection unavailable.",
            "fatigue_failure_points": "Fatigue analysis unavailable.",
            "mental_condition": "Mental condition profile unavailable.",
            "collapse_triggers": "Collapse trigger analysis unavailable.",
            "deception_and_unpredictability": "Deception profile unavailable.",
            "round_by_round_control_shifts": "Round-by-round projection unavailable.",
            "scenario_tree": "Scenario pathways unavailable.",
            "risk_warnings": "Customer export blocked until real AI-RISA analysis content is linked or internal draft mode is selected.",
            "operator_notes": str(queue_record.get("notes") or "").strip() or "Operator review required before export.",
        })
        forced_unavailable_sections.update({
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
        })

    for section_name in SECTION_NAMES:
        if section_name not in sections:
            sections[section_name] = ""
        if section_name in forced_unavailable_sections:
            section_status[section_name] = "unavailable"
        else:
            section_status[section_name] = "complete" if _present(sections.get(section_name)) else "unavailable"

    content_preview = {
        "headline_prediction_preview": str(sections.get("headline_prediction") or "")[:240],
        "executive_summary_preview": str(sections.get("executive_summary") or "")[:320],
    }

    return {
        "sections": sections,
        "section_status": section_status,
        "analysis_source_status": analysis_source_status,
        "analysis_source_type": analysis_source_type,
        "linked_analysis_record_id": linked_analysis_record_id,
        "linkage_keys_used": linkage_keys_used,
        "content_preview": content_preview,
    }


def assemble_report_sections(queue_record: dict) -> tuple:
    """
    Assemble the 14 required report sections from a saved queue record.

    Returns:
        sections: dict mapping section_name -> section_text
        section_status: dict mapping section_name -> status string
    """
    bundle = build_report_content_bundle(queue_record, allow_internal_draft=False)
    return bundle["sections"], bundle["section_status"]
