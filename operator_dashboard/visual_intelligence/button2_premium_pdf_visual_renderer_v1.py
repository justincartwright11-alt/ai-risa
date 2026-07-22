from __future__ import annotations

import importlib.util
import json
from pathlib import Path


REQUIRED_INPUT_FIELDS = {
    "visual_family_id",
    "report_id",
    "analysis_id",
    "report_version",
    "fighter_a_label",
    "fighter_b_label",
    "visual_title",
    "visual_subtitle",
    "data_basis",
    "sample_size",
    "source_quality",
    "observed_vs_modelled",
    "confidence_score",
    "uncertainty_flags",
    "limitation_note",
    "operator_review_status",
    "release_boundary",
    "visual_data",
    "page_density_level",
    "disclaimer_variant",
    "visual_qa_required",
}

REQUIRED_OUTPUT_FIELDS = {
    "render_status",
    "visual_family_id",
    "output_type",
    "output_path",
    "page_component_id",
    "style_registry_id",
    "evidence_panel_rendered",
    "disclaimer_footer_rendered",
    "severity_scale_rendered",
    "accessibility_checks_passed",
    "page_density_checks_passed",
    "visual_qa_required",
    "visual_qa_status",
    "delivery_ready",
    "release_boundary",
    "blocked_reasons",
}

HEAT_MAP_VISUAL_FAMILIES = {
    "anatomical_target_exposure_heat_map",
    "fatigue_structural_decay_heat_map",
    "tactical_vulnerability_map",
    "training_priority_heat_map",
}

ANATOMICAL_VISUAL_FAMILIES = HEAT_MAP_VISUAL_FAMILIES

NON_ANATOMICAL_VISUAL_FAMILIES = {
    "fighter_architecture_radar",
    "tactical_edge_bar_chart",
    "round_control_projection_line_graph",
    "scenario_method_pathway_tree",
    "ring_geography_pressure_map",
    "decision_structure_map",
    "pace_energy_fatigue_curve",
    "scorecard_probability_table",
    "button3_result_comparison_visual",
}

PROHIBITED_DIAGNOSIS_TERMS = {
    "diagnosed",
    "diagnosis",
    "fracture",
    "concussion",
    "torn ligament",
    "medical injury",
    "brain injury",
}

PAGE_DENSITY_ALIASES = {
    "level_1_hero": 1,
    "level_2_analytical": 2,
    "level_3_evidence": 3,
}


def load_visual_style_registry(registry_path: Path | str) -> dict:
    registry_path = Path(registry_path)
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    required_keys = {
        "registry_id",
        "registry_scope",
        "release_boundary",
        "visual_family_ids",
        "evidence_panel_tokens",
        "disclaimer_footer_tokens",
        "page_density_rules",
        "accessibility_rules",
    }
    missing = required_keys.difference(registry)
    if missing:
        raise ValueError(f"Missing registry keys: {sorted(missing)}")
    return registry


def list_supported_visual_families(registry: dict) -> list[str]:
    return [entry["visual_family_id"] for entry in registry["visual_family_ids"]]


def _release_boundary_is_internal_only(release_boundary: dict) -> bool:
    return (
        release_boundary.get("release_scope_decision") == "INTERNAL_ONLY"
        and release_boundary.get("customer_release_authorized") is False
        and release_boundary.get("public_publishing_authorized") is False
        and release_boundary.get("production_launch_authorized") is False
        and release_boundary.get("automated_delivery_authorized") is False
        and release_boundary.get("learning_activation_authorized") is False
    )


def _contains_prohibited_diagnosis_language(value: object) -> bool:
    text = str(value).lower()
    return any(term in text for term in PROHIBITED_DIAGNOSIS_TERMS)


def _page_density_is_within_limit(page_density_level: object, limit: int) -> bool:
    if isinstance(page_density_level, (int, float)):
        return page_density_level <= limit
    if isinstance(page_density_level, str):
        normalized = PAGE_DENSITY_ALIASES.get(page_density_level)
        if normalized is not None:
            return normalized <= limit
        return True
    return False


def build_visual_render_contract(input_payload: dict, registry: dict) -> dict:
    blocked_reasons: list[str] = []
    supported_visual_families = set(list_supported_visual_families(registry))
    visual_family_id = input_payload.get("visual_family_id")
    release_boundary = input_payload.get("release_boundary", {})
    disclaimer_variant = input_payload.get("disclaimer_variant")
    visual_data = input_payload.get("visual_data", {})

    missing_input_fields = REQUIRED_INPUT_FIELDS.difference(input_payload)
    if missing_input_fields:
        blocked_reasons.append(f"missing_input_fields:{sorted(missing_input_fields)}")

    if visual_family_id not in supported_visual_families:
        blocked_reasons.append("unknown_visual_family_id")

    if not _release_boundary_is_internal_only(release_boundary):
        blocked_reasons.append("unsafe_release_boundary")

    required_evidence_fields = {
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
    missing_evidence_fields = required_evidence_fields.difference(input_payload)
    if missing_evidence_fields:
        blocked_reasons.append(f"missing_evidence_fields:{sorted(missing_evidence_fields)}")

    footer_variants = set(registry["disclaimer_footer_tokens"]["footer_variants"])
    if disclaimer_variant not in footer_variants:
        blocked_reasons.append("missing_disclaimer_footer")

    page_density_limit = registry["page_density_rules"]["max_level_3_evidence_panels_per_page"]
    page_density_level = input_payload.get("page_density_level")
    if page_density_level is None or not _page_density_is_within_limit(page_density_level, page_density_limit):
        blocked_reasons.append("page_density_limit_exceeded")

    if input_payload.get("visual_qa_required") is not True:
        blocked_reasons.append("visual_qa_required_false")

    severity_scale_present = visual_data.get("severity_scale_present") is True
    if visual_family_id in HEAT_MAP_VISUAL_FAMILIES and not severity_scale_present:
        blocked_reasons.append("heat_map_without_severity_scale")

    if visual_family_id in ANATOMICAL_VISUAL_FAMILIES:
        if disclaimer_variant != "tactical_non_medical":
            blocked_reasons.append("anatomical_visual_without_non_medical_disclaimer")
        if not severity_scale_present:
            blocked_reasons.append("anatomical_visual_missing_severity_scale")
        if input_payload.get("confidence_score") is None:
            blocked_reasons.append("missing_confidence_score")
        if input_payload.get("observed_vs_modelled") is None:
            blocked_reasons.append("missing_observed_vs_modelled")
        limitation_note = input_payload.get("limitation_note", "")
        labels = visual_data.get("labels", [])
        if _contains_prohibited_diagnosis_language(limitation_note) or any(
            _contains_prohibited_diagnosis_language(label) for label in labels
        ):
            blocked_reasons.append("injury_diagnosis_language_present")
        if input_payload.get("delivery_ready") is True:
            blocked_reasons.append("delivery_ready_true_for_anatomical_visual")

    if input_payload.get("delivery_ready") is True and input_payload.get("visual_qa_status") != "PASS":
        blocked_reasons.append("delivery_ready_without_visual_qa_pass")

    render_status = "CONTRACT_VALIDATED_INTERNAL_ONLY" if not blocked_reasons else "BLOCKED"
    return {
        "render_status": render_status,
        "visual_family_id": visual_family_id,
        "output_type": "CONTRACT_OBJECT_ONLY",
        "output_path": None,
        "page_component_id": f"{input_payload.get('report_id', 'unknown')}-component",
        "style_registry_id": registry["registry_id"],
        "evidence_panel_rendered": visual_family_id in supported_visual_families,
        "disclaimer_footer_rendered": disclaimer_variant in footer_variants,
        "severity_scale_rendered": severity_scale_present,
        "accessibility_checks_passed": render_status == "CONTRACT_VALIDATED_INTERNAL_ONLY",
        "page_density_checks_passed": render_status == "CONTRACT_VALIDATED_INTERNAL_ONLY",
        "visual_qa_required": input_payload.get("visual_qa_required", False),
        "visual_qa_status": "PENDING",
        "delivery_ready": False,
        "release_boundary": release_boundary,
        "blocked_reasons": blocked_reasons,
    }


def validate_visual_render_contract(render_contract: dict, registry: dict) -> None:
    missing_output_fields = REQUIRED_OUTPUT_FIELDS.difference(render_contract)
    if missing_output_fields:
        raise AssertionError(f"Missing output fields: {sorted(missing_output_fields)}")
    if render_contract["output_type"] != "CONTRACT_OBJECT_ONLY":
        raise AssertionError("output_type must be CONTRACT_OBJECT_ONLY")
    if render_contract["output_path"] is not None:
        raise AssertionError("output_path must remain null")
    if render_contract["visual_qa_status"] not in {"PENDING", "PASS"}:
        raise AssertionError("visual_qa_status must be PENDING or PASS")
    if render_contract["delivery_ready"] is not False:
        raise AssertionError("delivery_ready must be false")
    if render_contract["render_status"] not in {"CONTRACT_VALIDATED_INTERNAL_ONLY", "BLOCKED"}:
        raise AssertionError("render_status must be CONTRACT_VALIDATED_INTERNAL_ONLY or BLOCKED")
    if render_contract["render_status"] == "CONTRACT_VALIDATED_INTERNAL_ONLY" and render_contract["blocked_reasons"]:
        raise AssertionError("blocked_reasons must be empty for validated contracts")
    if render_contract["render_status"] == "BLOCKED" and not render_contract["blocked_reasons"]:
        raise AssertionError("blocked_reasons must be populated for blocked contracts")
    if render_contract["release_boundary"]["release_scope_decision"] != "INTERNAL_ONLY":
        raise AssertionError("release boundary must remain INTERNAL_ONLY")
    if render_contract["style_registry_id"] != registry["registry_id"]:
        raise AssertionError("style_registry_id must match the locked registry")
    return True


def _load_renderer_artifact_path_integration_module():
    module_path = Path(__file__).resolve().parent / "button2_premium_pdf_visual_renderer_artifact_path_integration_v1.py"
    spec = importlib.util.spec_from_file_location("button2_renderer_artifact_path_integration_v1", module_path)
    if spec is None or spec.loader is None:
        raise ImportError("Unable to load renderer artifact path integration module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_renderer_artifact_path_wiring_contract(render_contract, artifact_path_contract, qa_gate_output):
    integration_module = _load_renderer_artifact_path_integration_module()
    return integration_module.build_renderer_artifact_path_integration_contract(
        render_contract,
        artifact_path_contract,
        qa_gate_output,
    )