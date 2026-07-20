from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest


REGISTRY_PATH = Path(__file__).resolve().parent / "visual_intelligence" / "button2_premium_pdf_visual_style_registry_v1.json"

REQUIRED_TOP_LEVEL_FIELDS = {
    "schema_version",
    "registry_id",
    "registry_scope",
    "release_boundary",
    "color_tokens",
    "typography_tokens",
    "border_tokens",
    "spacing_tokens",
    "severity_scales",
    "fighter_identity_tokens",
    "visual_family_ids",
    "evidence_panel_tokens",
    "disclaimer_footer_tokens",
    "page_density_rules",
    "overload_prohibitions",
    "accessibility_rules",
    "prohibited_states",
}

REQUIRED_CORE_INTERFACE_COLORS = {
    "midnight_black": "#0A0A0A",
    "combat_gold": "#D4AF37",
    "steel_grey": "#2E2E2E",
}

REQUIRED_FIGHTER_IDENTITY_COLORS = {
    "fighter_a_identity_blue",
    "fighter_b_identity_red",
    "neutral_identity_grey",
    "shared_information_gold",
}

REQUIRED_SEVERITY_COLORS = {
    "severity_very_low",
    "severity_low",
    "severity_moderate",
    "severity_high",
    "severity_very_high",
    "severity_critical",
}

REQUIRED_TYPOGRAPHY_ROLES = {
    "report_title",
    "section_title",
    "panel_title",
    "chart_axis_label",
    "table_header",
    "table_body",
    "score_number_large",
    "score_number_medium",
    "evidence_label",
    "disclaimer_text",
    "footnote_text",
}

REQUIRED_BORDER_TOKENS = {
    "outer_report_frame",
    "hero_visual_frame",
    "chart_panel_frame",
    "evidence_panel_frame",
    "insight_panel_frame",
    "score_table_frame",
    "callout_box_frame",
    "warning_box_frame",
}

REQUIRED_SPACING_TOKENS = {
    "page_margin",
    "panel_gap",
    "title_to_content_gap",
    "chart_padding",
    "table_cell_padding",
    "callout_line_clearance",
    "footer_clearance",
    "minimum_mobile_text_size",
    "minimum_print_text_size",
}

REQUIRED_VISUAL_FAMILY_IDS = {
    "anatomical_target_exposure_heat_map",
    "fatigue_structural_decay_heat_map",
    "tactical_vulnerability_map",
    "fighter_architecture_radar",
    "tactical_edge_bar_chart",
    "round_control_projection_line_graph",
    "scenario_method_pathway_tree",
    "ring_geography_pressure_map",
    "decision_structure_map",
    "pace_energy_fatigue_curve",
    "training_priority_heat_map",
    "scorecard_probability_table",
    "button3_result_comparison_visual",
}

REQUIRED_VISUAL_FAMILY_FIELDS = {
    "visual_family_id",
    "purpose",
    "anatomical_treatment_allowed",
    "requires_severity_scale",
    "requires_evidence_panel",
    "requires_disclaimer_footer",
}

REQUIRED_EVIDENCE_PANEL_FIELDS = {
    "analysis_id",
    "report_version",
    "data_basis",
    "sample_size",
    "source_quality",
    "observed_vs_modelled",
    "confidence_score",
    "uncertainty_flags",
    "limitation_note",
    "operator_review_status",
}

REQUIRED_DISCLAIMER_VARIANTS = {
    "tactical_non_medical",
    "projected_modelled_estimate",
    "internal_draft_only",
    "result_comparison_verified",
}

REQUIRED_PROHIBITED_STATES = {
    "customer_release_authorized=true",
    "public_publishing_authorized=true",
    "production_launch_authorized=true",
    "automated_delivery_authorized=true",
    "learning_activation_authorized=true",
    "visual_family_id without evidence panel rules",
    "heat map without severity scale",
    "anatomical heat map without non-medical disclaimer",
    "red used as Fighter B identity where it conflicts with risk meaning",
    "unlabeled heat colours",
    "PDF visual marked delivery-ready without visual QA gate",
}


def load_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def validate_registry_contract(registry: dict) -> None:
    missing_top_level = REQUIRED_TOP_LEVEL_FIELDS.difference(registry)
    assert not missing_top_level, f"Missing top-level fields: {sorted(missing_top_level)}"

    release_boundary = registry["release_boundary"]
    assert release_boundary["release_scope_decision"] == "INTERNAL_ONLY"
    assert release_boundary["customer_release_authorized"] is False
    assert release_boundary["public_publishing_authorized"] is False
    assert release_boundary["production_launch_authorized"] is False
    assert release_boundary["automated_delivery_authorized"] is False
    assert release_boundary["learning_activation_authorized"] is False

    color_tokens = registry["color_tokens"]
    assert "core_interface_colors" in color_tokens
    assert "fighter_identity_colors" in color_tokens
    assert "severity_colors" in color_tokens

    core_interface_colors = color_tokens["core_interface_colors"]
    for color_name, expected_value in REQUIRED_CORE_INTERFACE_COLORS.items():
        assert color_name in core_interface_colors
        assert core_interface_colors[color_name]["value"] == expected_value

    assert color_tokens["red_primary_meaning"] == "severity_risk_exposure_failure_before_fighter_identity"

    fighter_identity_colors = color_tokens["fighter_identity_colors"]
    assert REQUIRED_FIGHTER_IDENTITY_COLORS.issubset(fighter_identity_colors)

    severity_colors = color_tokens["severity_colors"]
    assert REQUIRED_SEVERITY_COLORS.issubset(severity_colors)

    typography_tokens = registry["typography_tokens"]
    assert REQUIRED_TYPOGRAPHY_ROLES.issubset(typography_tokens)
    for role_name in REQUIRED_TYPOGRAPHY_ROLES:
        role = typography_tokens[role_name]
        assert "purpose" in role
        assert "relative_size" in role
        assert "weight" in role
        assert "readability_rule" in role

    border_tokens = registry["border_tokens"]
    assert REQUIRED_BORDER_TOKENS.issubset(border_tokens)

    spacing_tokens = registry["spacing_tokens"]
    assert REQUIRED_SPACING_TOKENS.issubset(spacing_tokens)

    severity_scale = registry["severity_scales"]["default_0_100_scale"]
    assert severity_scale["very_low"]["range"] == [0, 20]
    assert severity_scale["low"]["range"] == [21, 40]
    assert severity_scale["moderate"]["range"] == [41, 60]
    assert severity_scale["high"]["range"] == [61, 80]
    assert severity_scale["very_high"]["range"] == [81, 100]

    visual_families = registry["visual_family_ids"]
    assert isinstance(visual_families, list)
    family_by_id = {}
    for family in visual_families:
        missing_family_fields = REQUIRED_VISUAL_FAMILY_FIELDS.difference(family)
        assert not missing_family_fields, f"Missing visual_family_fields: {sorted(missing_family_fields)}"
        family_by_id[family["visual_family_id"]] = family

        if family["visual_family_id"].endswith("_heat_map"):
            assert family["requires_severity_scale"] is True
            assert family["requires_evidence_panel"] is True
            assert family["requires_disclaimer_footer"] is True

        if family["visual_family_id"] in {
            "anatomical_target_exposure_heat_map",
            "fatigue_structural_decay_heat_map",
            "training_priority_heat_map",
        }:
            assert family["anatomical_treatment_allowed"] is True
            assert family["requires_disclaimer_footer"] is True

    missing_families = REQUIRED_VISUAL_FAMILY_IDS.difference(family_by_id)
    assert not missing_families, f"Missing visual_family_ids: {sorted(missing_families)}"

    evidence_panel_tokens = registry["evidence_panel_tokens"]
    required_fields = evidence_panel_tokens.get("required_fields", [])
    assert REQUIRED_EVIDENCE_PANEL_FIELDS.issubset(required_fields)
    assert evidence_panel_tokens["panel_rule"] == "every_visual_family_requires_a_matching_evidence_panel"

    disclaimer_footer_tokens = registry["disclaimer_footer_tokens"]
    footer_variants = disclaimer_footer_tokens.get("footer_variants", [])
    assert REQUIRED_DISCLAIMER_VARIANTS.issubset(footer_variants)
    assert disclaimer_footer_tokens["anatomical_required_wording"] == "TACTICAL ANALYSIS — NOT A MEDICAL DIAGNOSIS"

    page_density_rules = registry["page_density_rules"]
    assert page_density_rules["max_level_1_hero_visuals_per_page"] == 1
    assert page_density_rules["max_level_2_analytical_visuals_per_page"] == 1
    assert page_density_rules["max_level_3_evidence_panels_per_page"] == 3
    assert page_density_rules["dense_master_dashboard_allowed_only_for_summary_page"] is True
    assert page_density_rules["mobile_readability_required"] is True
    assert page_density_rules["print_readability_required"] is True

    accessibility_rules = registry["accessibility_rules"]
    assert accessibility_rules["no_colour_only_meaning"] is True
    assert accessibility_rules["severity_requires_label_and_colour"] is True
    assert accessibility_rules["important_scores_require_numeric_value"] is True
    assert accessibility_rules["fighter_identity_requires_name_label"] is True
    assert accessibility_rules["callout_text_must_remain_readable"] is True
    assert accessibility_rules["charts_must_avoid_overflow_and_clipping"] is True
    assert accessibility_rules["table_numbers_must_not_sit_on_glowing_backgrounds"] is True

    prohibited_states = registry["prohibited_states"]
    assert isinstance(prohibited_states, list)
    missing_prohibited_states = REQUIRED_PROHIBITED_STATES.difference(prohibited_states)
    assert not missing_prohibited_states, f"Missing prohibited_states: {sorted(missing_prohibited_states)}"

    assert any(state == "PDF visual marked delivery-ready without visual QA gate" for state in prohibited_states)


def test_button2_visual_style_registry_loads_as_json() -> None:
    registry = load_registry()
    assert isinstance(registry, dict)


def test_button2_visual_style_registry_has_required_top_level_fields() -> None:
    registry = load_registry()
    missing = REQUIRED_TOP_LEVEL_FIELDS.difference(registry)
    assert not missing


def test_button2_visual_style_registry_preserves_internal_only_release_boundary() -> None:
    registry = load_registry()
    validate_registry_contract(registry)


def test_button2_visual_style_registry_has_required_color_token_groups() -> None:
    registry = load_registry()
    validate_registry_contract(registry)
    color_tokens = registry["color_tokens"]
    assert "core_interface_colors" in color_tokens
    assert "fighter_identity_colors" in color_tokens
    assert "severity_colors" in color_tokens


def test_button2_visual_style_registry_has_required_core_interface_colors() -> None:
    registry = load_registry()
    validate_registry_contract(registry)
    core_interface_colors = registry["color_tokens"]["core_interface_colors"]
    for color_name, expected_value in REQUIRED_CORE_INTERFACE_COLORS.items():
        assert core_interface_colors[color_name]["value"] == expected_value


def test_button2_visual_style_registry_preserves_red_primary_meaning_rule() -> None:
    registry = load_registry()
    validate_registry_contract(registry)
    assert registry["color_tokens"]["red_primary_meaning"] == "severity_risk_exposure_failure_before_fighter_identity"


def test_button2_visual_style_registry_has_required_typography_tokens() -> None:
    registry = load_registry()
    validate_registry_contract(registry)
    typography_tokens = registry["typography_tokens"]
    for role_name in REQUIRED_TYPOGRAPHY_ROLES:
        role = typography_tokens[role_name]
        assert "purpose" in role
        assert "relative_size" in role
        assert "weight" in role
        assert "readability_rule" in role


def test_button2_visual_style_registry_has_required_border_tokens() -> None:
    registry = load_registry()
    validate_registry_contract(registry)
    border_tokens = registry["border_tokens"]
    assert REQUIRED_BORDER_TOKENS.issubset(border_tokens)


def test_button2_visual_style_registry_has_required_spacing_tokens() -> None:
    registry = load_registry()
    validate_registry_contract(registry)
    spacing_tokens = registry["spacing_tokens"]
    assert REQUIRED_SPACING_TOKENS.issubset(spacing_tokens)


def test_button2_visual_style_registry_has_default_0_100_severity_scale() -> None:
    registry = load_registry()
    validate_registry_contract(registry)
    severity_scale = registry["severity_scales"]["default_0_100_scale"]
    assert severity_scale["very_low"]["range"] == [0, 20]
    assert severity_scale["low"]["range"] == [21, 40]
    assert severity_scale["moderate"]["range"] == [41, 60]
    assert severity_scale["high"]["range"] == [61, 80]
    assert severity_scale["very_high"]["range"] == [81, 100]


def test_button2_visual_style_registry_has_required_visual_family_ids() -> None:
    registry = load_registry()
    validate_registry_contract(registry)
    family_ids = {entry["visual_family_id"] for entry in registry["visual_family_ids"]}
    assert REQUIRED_VISUAL_FAMILY_IDS.issubset(family_ids)


def test_button2_visual_style_registry_visual_families_define_required_controls() -> None:
    registry = load_registry()
    validate_registry_contract(registry)
    for entry in registry["visual_family_ids"]:
        assert REQUIRED_VISUAL_FAMILY_FIELDS.issubset(entry)


def test_button2_visual_style_registry_has_required_evidence_panel_tokens() -> None:
    registry = load_registry()
    validate_registry_contract(registry)
    required_fields = set(registry["evidence_panel_tokens"]["required_fields"])
    assert REQUIRED_EVIDENCE_PANEL_FIELDS.issubset(required_fields)


def test_button2_visual_style_registry_has_required_disclaimer_footer_variants() -> None:
    registry = load_registry()
    validate_registry_contract(registry)
    footer_variants = set(registry["disclaimer_footer_tokens"]["footer_variants"])
    assert REQUIRED_DISCLAIMER_VARIANTS.issubset(footer_variants)


def test_button2_visual_style_registry_preserves_page_density_rules() -> None:
    registry = load_registry()
    validate_registry_contract(registry)
    page_density_rules = registry["page_density_rules"]
    assert page_density_rules["max_level_1_hero_visuals_per_page"] == 1
    assert page_density_rules["max_level_2_analytical_visuals_per_page"] == 1
    assert page_density_rules["max_level_3_evidence_panels_per_page"] == 3
    assert page_density_rules["dense_master_dashboard_allowed_only_for_summary_page"] is True
    assert page_density_rules["mobile_readability_required"] is True
    assert page_density_rules["print_readability_required"] is True


def test_button2_visual_style_registry_preserves_accessibility_rules() -> None:
    registry = load_registry()
    validate_registry_contract(registry)
    accessibility_rules = registry["accessibility_rules"]
    assert accessibility_rules["no_colour_only_meaning"] is True
    assert accessibility_rules["severity_requires_label_and_colour"] is True
    assert accessibility_rules["important_scores_require_numeric_value"] is True
    assert accessibility_rules["fighter_identity_requires_name_label"] is True
    assert accessibility_rules["callout_text_must_remain_readable"] is True
    assert accessibility_rules["charts_must_avoid_overflow_and_clipping"] is True
    assert accessibility_rules["table_numbers_must_not_sit_on_glowing_backgrounds"] is True


def test_button2_visual_style_registry_lists_prohibited_states() -> None:
    registry = load_registry()
    validate_registry_contract(registry)
    prohibited_states = set(registry["prohibited_states"])
    assert REQUIRED_PROHIBITED_STATES.issubset(prohibited_states)


def test_button2_visual_style_registry_rejects_customer_release_authorized_true() -> None:
    registry = copy.deepcopy(load_registry())
    registry["release_boundary"]["customer_release_authorized"] = True
    with pytest.raises(AssertionError):
        validate_registry_contract(registry)


def test_button2_visual_style_registry_rejects_learning_activation_authorized_true() -> None:
    registry = copy.deepcopy(load_registry())
    registry["release_boundary"]["learning_activation_authorized"] = True
    with pytest.raises(AssertionError):
        validate_registry_contract(registry)


def test_button2_visual_style_registry_rejects_heat_map_without_severity_scale() -> None:
    registry = copy.deepcopy(load_registry())
    for family in registry["visual_family_ids"]:
        if family["visual_family_id"] == "anatomical_target_exposure_heat_map":
            family["requires_severity_scale"] = False
            break
    with pytest.raises(AssertionError):
        validate_registry_contract(registry)


def test_button2_visual_style_registry_rejects_anatomical_heat_map_without_non_medical_disclaimer() -> None:
    registry = copy.deepcopy(load_registry())
    registry["disclaimer_footer_tokens"]["anatomical_required_wording"] = "TACTICAL ANALYSIS ONLY"
    with pytest.raises(AssertionError):
        validate_registry_contract(registry)


def test_button2_visual_style_registry_rejects_delivery_ready_without_visual_qa_gate() -> None:
    registry = copy.deepcopy(load_registry())
    registry["prohibited_states"] = [
        state for state in registry["prohibited_states"] if state != "PDF visual marked delivery-ready without visual QA gate"
    ]
    with pytest.raises(AssertionError):
        validate_registry_contract(registry)