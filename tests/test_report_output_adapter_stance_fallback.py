from ai_risa_report_output_adapter import map_engine_output_to_report


def _build_engine_output(stance_a=None, stance_b=None):
    fighter_a_profile = {
        "name": "Alpha Fighter",
        "style": "Grappler",
    }
    fighter_b_profile = {
        "name": "Bravo Fighter",
        "style": "Striker",
    }
    if stance_a is not None:
        fighter_a_profile["stance"] = stance_a
    if stance_b is not None:
        fighter_b_profile["stance"] = stance_b

    return {
        "predicted_winner_id": "fighter_alpha_fighter",
        "confidence": 0.61,
        "method": "decision",
        "round": "full",
        "event_date": "2026-04-27",
        "promotion": "UFC",
        "sport": "mma",
        "fight_id": "alpha_fighter_vs_bravo_fighter",
        "fighter_a_id": "fighter_alpha_fighter",
        "fighter_b_id": "fighter_bravo_fighter",
        "fighter_a_profile": fighter_a_profile,
        "fighter_b_profile": fighter_b_profile,
        "debug_metrics": {
            "signal_gap": 0.2,
            "stoppage_propensity": 0.2,
            "round_finish_tendency": 0.2,
        },
    }


def _section_map(report):
    return {s["id"]: str(s.get("content") or "") for s in report.get("sections", [])}


def test_missing_or_noncanonical_stance_never_emits_unknown_in_required_sections():
    report = map_engine_output_to_report(
        _build_engine_output(stance_a=None, stance_b="spinning pressure entry")
    )
    sections = _section_map(report)
    targeted = [
        "executive_summary",
        "matchup_snapshot",
        "tactical_edges",
        "deception_unpredictability",
    ]

    for sid in targeted:
        text = sections[sid].lower()
        assert "unknown" not in text
        assert "unlisted stance" in text


def test_canonical_stance_values_pass_through():
    report = map_engine_output_to_report(
        _build_engine_output(stance_a="orthodox", stance_b="southpaw")
    )
    sections = _section_map(report)

    assert "orthodox" in sections["matchup_snapshot"].lower()
    assert "southpaw" in sections["matchup_snapshot"].lower()
    assert "unlisted stance" not in sections["executive_summary"].lower()
