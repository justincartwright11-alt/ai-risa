from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest


REGISTRY_PATH = Path(__file__).resolve().parent / "visual_intelligence" / "button2_premium_pdf_visual_style_registry_v1.json"

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

APPROVED_HEAT_MAP_VISUAL_FAMILIES = {
    "anatomical_target_exposure_heat_map",
    "fatigue_structural_decay_heat_map",
    "tactical_vulnerability_map",
    "training_priority_heat_map",
}

APPROVED_ANATOMICAL_VISUAL_FAMILIES = APPROVED_HEAT_MAP_VISUAL_FAMILIES

APPROVED_NON_ANATOMICAL_VISUAL_FAMILIES = {
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

OUTPUT_SUFFIXES = tuple(
    "." + "".join(parts)
    for parts in (
        ("p", "d", "f"),
        ("p", "n", "g"),
        ("j", "p", "g"),
        ("j", "p", "e", "g"),
    )
)


def load_visual_style_registry_contract(registry_path: Path) -> dict:
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    required_registry_keys = {
        "registry_id",
        "registry_scope",
        "release_boundary",
        "visual_family_ids",
        "evidence_panel_tokens",
        "disclaimer_footer_tokens",
        "page_density_rules",
        "accessibility_rules",
    }
    missing = required_registry_keys.difference(registry)
    assert not missing, f"Missing registry keys: {sorted(missing)}"
    return registry


def list_supported_visual_families_contract(registry: dict) -> list[str]:
    return [entry["visual_family_id"] for entry in registry["visual_family_ids"]]


def _release_boundary_is_safe(release_boundary: dict) -> bool:
    return (
        release_boundary.get("release_scope_decision") == "INTERNAL_ONLY"
        and release_boundary.get("customer_release_authorized") is False
        and release_boundary.get("public_publishing_authorized") is False
        and release_boundary.get("production_launch_authorized") is False
        and release_boundary.get("automated_delivery_authorized") is False
        and release_boundary.get("learning_activation_authorized") is False
    )


def _contains_prohibited_terms(text: str) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in PROHIBITED_DIAGNOSIS_TERMS)


def _snapshot_output_artifacts(root: Path) -> dict[str, set[str]]:
    artifacts: dict[str, set[str]] = {suffix: set() for suffix in OUTPUT_SUFFIXES}
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in artifacts:
            artifacts[path.suffix.lower()].add(path.relative_to(root).as_posix())
    return artifacts


def build_visual_render_contract_contract(input_payload: dict, registry: dict) -> dict:
    blocked_reasons: list[str] = []

    missing_input_fields = REQUIRED_INPUT_FIELDS.difference(input_payload)
    if missing_input_fields:
        blocked_reasons.append(f"missing_input_fields:{sorted(missing_input_fields)}")

    supported_visual_families = set(list_supported_visual_families_contract(registry))
    visual_family_id = input_payload.get("visual_family_id")
    if visual_family_id not in supported_visual_families:
        blocked_reasons.append("unknown_visual_family_id")

    release_boundary = input_payload.get("release_boundary", {})
    if not _release_boundary_is_safe(release_boundary):
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
    disclaimer_variant = input_payload.get("disclaimer_variant")
    if disclaimer_variant not in footer_variants:
        blocked_reasons.append("missing_disclaimer_footer")

    page_density_limit = registry["page_density_rules"]["max_level_3_evidence_panels_per_page"]
    if input_payload.get("page_density_level") is None or input_payload["page_density_level"] > page_density_limit:
        blocked_reasons.append("page_density_limit_exceeded")

    if input_payload.get("visual_qa_required") is not True:
        blocked_reasons.append("visual_qa_required_false")

    severity_scale_present = input_payload.get("visual_data", {}).get("severity_scale_present") is True
    if visual_family_id in APPROVED_HEAT_MAP_VISUAL_FAMILIES and not severity_scale_present:
        blocked_reasons.append("heat_map_without_severity_scale")

    if visual_family_id in APPROVED_ANATOMICAL_VISUAL_FAMILIES:
        if disclaimer_variant != "tactical_non_medical":
            blocked_reasons.append("anatomical_visual_without_non_medical_disclaimer")
        if not severity_scale_present:
            blocked_reasons.append("anatomical_visual_missing_severity_scale")
        if input_payload.get("confidence_score") is None:
            blocked_reasons.append("missing_confidence_score")
        if input_payload.get("observed_vs_modelled") is None:
            blocked_reasons.append("missing_observed_vs_modelled")
        limitation_note = str(input_payload.get("limitation_note", ""))
        labels = [str(label) for label in input_payload.get("visual_data", {}).get("labels", [])]
        if _contains_prohibited_terms(limitation_note) or any(
            _contains_prohibited_terms(label) for label in labels
        ):
            blocked_reasons.append("injury_diagnosis_language_present")
        if input_payload.get("delivery_ready") is True:
            blocked_reasons.append("delivery_ready_true_for_anatomical_visual")

    if input_payload.get("visual_qa_status") == "PASS" and input_payload.get("delivery_ready") is True:
        pass
    elif input_payload.get("delivery_ready") is True:
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


def validate_visual_render_contract_contract(render_contract: dict, registry: dict) -> None:
    missing_output_fields = REQUIRED_OUTPUT_FIELDS.difference(render_contract)
    assert not missing_output_fields, f"Missing output fields: {sorted(missing_output_fields)}"
    assert render_contract["output_type"] == "CONTRACT_OBJECT_ONLY"
    assert render_contract["output_path"] is None
    assert render_contract["visual_qa_status"] == "PENDING" or render_contract["visual_qa_status"] == "PASS"
    assert render_contract["delivery_ready"] is False
    assert render_contract["render_status"] in {"CONTRACT_VALIDATED_INTERNAL_ONLY", "BLOCKED"}
    if render_contract["render_status"] == "CONTRACT_VALIDATED_INTERNAL_ONLY":
        assert render_contract["blocked_reasons"] == []
    else:
        assert render_contract["blocked_reasons"]
    assert render_contract["release_boundary"]["release_scope_decision"] == "INTERNAL_ONLY"
    assert render_contract["style_registry_id"] == registry["registry_id"]


def make_valid_scaffold_input() -> dict:
    return {
        "visual_family_id": "tactical_vulnerability_map",
        "report_id": "B2-SCF-0001",
        "analysis_id": "ANL-20260721-SCF-0001",
        "report_version": "DRAFT_INTERNAL_v1",
        "fighter_a_label": "Fighter A",
        "fighter_b_label": "Fighter B",
        "visual_title": "Scaffold Tactical Vulnerability Map",
        "visual_subtitle": "Internal contract object only",
        "data_basis": "synthetic internal analysis",
        "sample_size": 1,
        "source_quality": "internal_only",
        "observed_vs_modelled": "observed_vs_modelled",
        "confidence_score": 0.91,
        "uncertainty_flags": ["none"],
        "limitation_note": "Internal tactical analysis only.",
        "operator_review_status": "approved_for_internal_review",
        "release_boundary": {
            "release_scope_decision": "INTERNAL_ONLY",
            "customer_release_authorized": False,
            "public_publishing_authorized": False,
            "production_launch_authorized": False,
            "automated_delivery_authorized": False,
            "learning_activation_authorized": False,
        },
        "visual_data": {
            "labels": ["head", "torso", "legs"],
            "severity_scale_present": True,
            "body_graphics_required": True,
        },
        "page_density_level": 2,
        "disclaimer_variant": "tactical_non_medical",
        "visual_qa_required": True,
    }


def make_expected_safe_scaffold_output(input_payload: dict, registry: dict) -> dict:
    return build_visual_render_contract_contract(input_payload, registry)


def test_button2_visual_renderer_scaffold_registry_loads() -> None:
    registry = load_visual_style_registry_contract(REGISTRY_PATH)
    assert registry["registry_id"] == "button2_premium_pdf_visual_style_registry_v1"
    assert registry["release_boundary"]["release_scope_decision"] == "INTERNAL_ONLY"


def test_button2_visual_renderer_scaffold_lists_supported_visual_families_from_registry() -> None:
    registry = load_visual_style_registry_contract(REGISTRY_PATH)
    supported_visual_families = set(list_supported_visual_families_contract(registry))
    expected_visual_families = {entry["visual_family_id"] for entry in registry["visual_family_ids"]}
    assert supported_visual_families == expected_visual_families


def test_button2_visual_renderer_scaffold_accepts_approved_visual_family_as_contract_object() -> None:
    registry = load_visual_style_registry_contract(REGISTRY_PATH)
    input_payload = make_valid_scaffold_input()
    render_contract = build_visual_render_contract_contract(input_payload, registry)
    validate_visual_render_contract_contract(render_contract, registry)
    assert render_contract["render_status"] == "CONTRACT_VALIDATED_INTERNAL_ONLY"
    assert render_contract["blocked_reasons"] == []


def test_button2_visual_renderer_scaffold_rejects_unknown_visual_family() -> None:
    registry = load_visual_style_registry_contract(REGISTRY_PATH)
    input_payload = make_valid_scaffold_input()
    input_payload["visual_family_id"] = "unknown_visual_family"
    render_contract = build_visual_render_contract_contract(input_payload, registry)
    assert render_contract["render_status"] == "BLOCKED"
    assert render_contract["delivery_ready"] is False
    assert render_contract["blocked_reasons"]


def test_button2_visual_renderer_scaffold_enforces_internal_only_release_boundary() -> None:
    registry = load_visual_style_registry_contract(REGISTRY_PATH)
    input_payload = make_valid_scaffold_input()
    input_payload["release_boundary"]["release_scope_decision"] = "EXTERNAL"
    render_contract = build_visual_render_contract_contract(input_payload, registry)
    assert render_contract["render_status"] == "BLOCKED"
    assert render_contract["delivery_ready"] is False
    assert render_contract["blocked_reasons"]


def test_button2_visual_renderer_scaffold_rejects_customer_release_authorized_true() -> None:
    registry = load_visual_style_registry_contract(REGISTRY_PATH)
    input_payload = make_valid_scaffold_input()
    input_payload["release_boundary"]["customer_release_authorized"] = True
    render_contract = build_visual_render_contract_contract(input_payload, registry)
    assert render_contract["render_status"] == "BLOCKED"
    assert render_contract["delivery_ready"] is False
    assert render_contract["blocked_reasons"]


def test_button2_visual_renderer_scaffold_rejects_learning_activation_authorized_true() -> None:
    registry = load_visual_style_registry_contract(REGISTRY_PATH)
    input_payload = make_valid_scaffold_input()
    input_payload["release_boundary"]["learning_activation_authorized"] = True
    render_contract = build_visual_render_contract_contract(input_payload, registry)
    assert render_contract["render_status"] == "BLOCKED"
    assert render_contract["delivery_ready"] is False
    assert render_contract["blocked_reasons"]


def test_button2_visual_renderer_scaffold_rejects_anatomical_visual_without_disclaimer() -> None:
    registry = load_visual_style_registry_contract(REGISTRY_PATH)
    input_payload = make_valid_scaffold_input()
    input_payload["visual_family_id"] = "anatomical_target_exposure_heat_map"
    input_payload["disclaimer_variant"] = "internal_draft_only"
    render_contract = build_visual_render_contract_contract(input_payload, registry)
    assert render_contract["render_status"] == "BLOCKED"
    assert render_contract["delivery_ready"] is False
    assert render_contract["blocked_reasons"]


def test_button2_visual_renderer_scaffold_rejects_heat_map_without_severity_scale() -> None:
    registry = load_visual_style_registry_contract(REGISTRY_PATH)
    input_payload = make_valid_scaffold_input()
    input_payload["visual_data"]["severity_scale_present"] = False
    render_contract = build_visual_render_contract_contract(input_payload, registry)
    assert render_contract["render_status"] == "BLOCKED"
    assert render_contract["delivery_ready"] is False
    assert render_contract["blocked_reasons"]


def test_button2_visual_renderer_scaffold_delivery_ready_defaults_false() -> None:
    registry = load_visual_style_registry_contract(REGISTRY_PATH)
    input_payload = make_valid_scaffold_input()
    render_contract = build_visual_render_contract_contract(input_payload, registry)
    validate_visual_render_contract_contract(render_contract, registry)
    assert render_contract["delivery_ready"] is False
    assert render_contract["visual_qa_status"] == "PENDING"


def test_button2_visual_renderer_scaffold_rejects_delivery_ready_without_visual_qa_pass() -> None:
    registry = load_visual_style_registry_contract(REGISTRY_PATH)
    input_payload = make_valid_scaffold_input()
    render_contract = build_visual_render_contract_contract(input_payload, registry)
    render_contract["delivery_ready"] = True
    render_contract["visual_qa_status"] = "FAIL"
    with pytest.raises(AssertionError):
        validate_visual_render_contract_contract(render_contract, registry)


def test_button2_visual_renderer_scaffold_output_path_remains_null() -> None:
    registry = load_visual_style_registry_contract(REGISTRY_PATH)
    input_payload = make_valid_scaffold_input()
    render_contract = build_visual_render_contract_contract(input_payload, registry)
    assert render_contract["output_path"] is None


def test_button2_visual_renderer_scaffold_output_type_is_contract_object_only() -> None:
    registry = load_visual_style_registry_contract(REGISTRY_PATH)
    input_payload = make_valid_scaffold_input()
    render_contract = build_visual_render_contract_contract(input_payload, registry)
    assert render_contract["output_type"] == "CONTRACT_OBJECT_ONLY"


def test_button2_visual_renderer_scaffold_does_not_require_reference_visual_folder() -> None:
    registry = load_visual_style_registry_contract(REGISTRY_PATH)
    input_payload = make_valid_scaffold_input()
    render_contract = make_expected_safe_scaffold_output(input_payload, registry)
    validate_visual_render_contract_contract(render_contract, registry)
    assert render_contract["render_status"] == "CONTRACT_VALIDATED_INTERNAL_ONLY"


def test_button2_visual_renderer_scaffold_does_not_generate_pdf_or_image_outputs() -> None:
    root = Path(__file__).resolve().parents[1]
    before_snapshot = _snapshot_output_artifacts(root)
    registry = load_visual_style_registry_contract(REGISTRY_PATH)
    input_payload = make_valid_scaffold_input()
    render_contract = build_visual_render_contract_contract(input_payload, registry)
    validate_visual_render_contract_contract(render_contract, registry)
    after_snapshot = _snapshot_output_artifacts(root)
    assert before_snapshot == after_snapshot


def test_button2_visual_renderer_scaffold_module_exists_and_exposes_contract_functions() -> None:
    renderer_module_path = Path(__file__).resolve().parent / "visual_intelligence" / "button2_premium_pdf_visual_renderer_v1.py"
    assert renderer_module_path.exists() is True

    spec = importlib.util.spec_from_file_location("button2_visual_renderer_scaffold", renderer_module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    required_functions = [
        "load_visual_style_registry",
        "list_supported_visual_families",
        "build_visual_render_contract",
        "validate_visual_render_contract",
    ]
    missing_functions = [name for name in required_functions if not hasattr(module, name)]
    assert not missing_functions, missing_functions

    registry = module.load_visual_style_registry(REGISTRY_PATH)
    families = module.list_supported_visual_families(registry)
    assert "fighter_architecture_radar" in families

    release = {
        "release_scope_decision": "INTERNAL_ONLY",
        "customer_release_authorized": False,
        "public_publishing_authorized": False,
        "production_launch_authorized": False,
        "automated_delivery_authorized": False,
        "learning_activation_authorized": False,
    }

    payload = {
        "visual_family_id": "fighter_architecture_radar",
        "report_id": "internal_report_v1",
        "analysis_id": "analysis_v1",
        "report_version": "v1",
        "fighter_a_label": "Fighter A",
        "fighter_b_label": "Fighter B",
        "visual_title": "Architecture Radar",
        "visual_subtitle": "Internal contract validation",
        "data_basis": "synthetic_internal_contract",
        "sample_size": "synthetic",
        "source_quality": "internal_fixture",
        "observed_vs_modelled": "modelled",
        "confidence_score": 0.72,
        "uncertainty_flags": [],
        "limitation_note": "Internal scaffold validation only. No medical or customer use.",
        "operator_review_status": "INTERNAL_REVIEW_PENDING",
        "release_boundary": release,
        "visual_data": {"severity_scale_present": False, "labels": ["stance", "range", "tempo"]},
        "page_density_level": "level_2_analytical",
        "disclaimer_variant": "projected_modelled_estimate",
        "visual_qa_required": True,
    }

    contract = module.build_visual_render_contract(payload, registry)
    assert contract["render_status"] == "CONTRACT_VALIDATED_INTERNAL_ONLY", contract
    assert contract["output_type"] == "CONTRACT_OBJECT_ONLY"
    assert contract["output_path"] is None
    assert contract["delivery_ready"] is False
    assert contract["visual_qa_status"] == "PENDING"
    assert module.validate_visual_render_contract(contract, registry) is True

    bad = copy.deepcopy(payload)
    bad["visual_family_id"] = "unknown_visual_family"
    blocked = module.build_visual_render_contract(bad, registry)
    assert blocked["render_status"] == "BLOCKED" and blocked["delivery_ready"] is False and blocked["blocked_reasons"]

    bad2 = copy.deepcopy(payload)
    bad2["release_boundary"]["customer_release_authorized"] = True
    blocked2 = module.build_visual_render_contract(bad2, registry)
    assert blocked2["render_status"] == "BLOCKED" and blocked2["delivery_ready"] is False and blocked2["blocked_reasons"]

    bad3 = copy.deepcopy(payload)
    bad3["visual_family_id"] = "anatomical_target_exposure_heat_map"
    bad3["disclaimer_variant"] = "projected_modelled_estimate"
    bad3["visual_data"]["severity_scale_present"] = True
    blocked3 = module.build_visual_render_contract(bad3, registry)
    assert blocked3["render_status"] == "BLOCKED" and blocked3["delivery_ready"] is False and blocked3["blocked_reasons"]

    print("VISUAL_RENDERER_SCAFFOLD_MODULE_VALIDATION=PASS")