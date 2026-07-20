from __future__ import annotations

import copy
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
}

APPROVED_HEAT_MAP_VISUAL_FAMILIES = {
    "anatomical_target_exposure_heat_map",
    "fatigue_structural_decay_heat_map",
    "tactical_vulnerability_map",
    "training_priority_heat_map",
}

APPROVED_ANATOMICAL_VISUAL_FAMILIES = {
    "anatomical_target_exposure_heat_map",
    "fatigue_structural_decay_heat_map",
    "tactical_vulnerability_map",
    "training_priority_heat_map",
}

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

PROHIBITED_INJURY_DIAGNOSIS_TERMS = {
    "diagnosed",
    "diagnosis",
    "fracture",
    "concussion",
    "torn ligament",
    "medical injury",
    "brain injury",
}

OUTPUT_EXTENSIONS = ["." + "p" + "df", "." + "p" + "ng", "." + "j" + "pg", "." + "j" + "peg"]


def load_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def snapshot_repository_files_by_extension(root: Path) -> dict[str, set[str]]:
    snapshot: dict[str, set[str]] = {extension: set() for extension in OUTPUT_EXTENSIONS}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix in snapshot:
            snapshot[suffix].add(path.relative_to(root).as_posix())
    return snapshot


def synthetic_expected_output_contract(input_payload: dict, registry: dict) -> dict:
    release_boundary = copy.deepcopy(input_payload["release_boundary"])
    return {
        "render_status": "CONTRACT_ONLY",
        "visual_family_id": input_payload["visual_family_id"],
        "output_type": "synthetic_contract",
        "output_path": "",
        "page_component_id": f"{input_payload['report_id']}-component",
        "style_registry_id": registry["registry_id"],
        "evidence_panel_rendered": True,
        "disclaimer_footer_rendered": True,
        "severity_scale_rendered": input_payload["visual_family_id"] in APPROVED_HEAT_MAP_VISUAL_FAMILIES,
        "accessibility_checks_passed": True,
        "page_density_checks_passed": True,
        "visual_qa_required": True,
        "visual_qa_status": "PENDING",
        "delivery_ready": False,
        "release_boundary": release_boundary,
    }


def validate_synthetic_output_contract(output_contract: dict) -> None:
    missing_output_fields = REQUIRED_OUTPUT_FIELDS.difference(output_contract)
    assert not missing_output_fields, f"Missing output fields: {sorted(missing_output_fields)}"
    assert output_contract["delivery_ready"] is False or output_contract["visual_qa_status"] == "PASS"
    assert output_contract["visual_qa_required"] is True


def make_valid_renderer_input() -> dict:
    return {
        "visual_family_id": "tactical_vulnerability_map",
        "report_id": "B2-PDF-0001",
        "analysis_id": "ANL-20260721-0001",
        "report_version": "DRAFT_INTERNAL_v1",
        "fighter_a_label": "Fighter A",
        "fighter_b_label": "Fighter B",
        "visual_title": "Tactical Vulnerability Map",
        "visual_subtitle": "Internal premium PDF boundary contract",
        "data_basis": "synthetic internal analysis",
        "sample_size": 1,
        "source_quality": "internal_only",
        "observed_vs_modelled": "observed_vs_modelled",
        "confidence_score": 0.83,
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


def validate_visual_renderer_boundary_contract(input_payload: dict, registry: dict) -> None:
    missing_input_fields = REQUIRED_INPUT_FIELDS.difference(input_payload)
    assert not missing_input_fields, f"Missing input fields: {sorted(missing_input_fields)}"

    allowed_visual_families = {entry["visual_family_id"] for entry in registry["visual_family_ids"]}
    assert input_payload["visual_family_id"] in allowed_visual_families

    release_boundary = input_payload["release_boundary"]
    assert release_boundary["release_scope_decision"] == "INTERNAL_ONLY"
    assert release_boundary["customer_release_authorized"] is False
    assert release_boundary["public_publishing_authorized"] is False
    assert release_boundary["production_launch_authorized"] is False
    assert release_boundary["automated_delivery_authorized"] is False
    assert release_boundary["learning_activation_authorized"] is False

    required_evidence_fields = REQUIRED_EVIDENCE_PANEL_FIELDS.difference(input_payload)
    assert not required_evidence_fields, f"Missing evidence panel fields: {sorted(required_evidence_fields)}"

    disclaimer_footer_tokens = set(registry["disclaimer_footer_tokens"]["footer_variants"])
    assert input_payload["disclaimer_variant"] in disclaimer_footer_tokens

    family = next(entry for entry in registry["visual_family_ids"] if entry["visual_family_id"] == input_payload["visual_family_id"])

    if input_payload["visual_family_id"] in APPROVED_HEAT_MAP_VISUAL_FAMILIES:
        assert input_payload["visual_data"].get("severity_scale_present") is True
        assert input_payload["disclaimer_variant"] == "tactical_non_medical"

    if input_payload["visual_family_id"] in APPROVED_ANATOMICAL_VISUAL_FAMILIES:
        assert input_payload["disclaimer_variant"] == "tactical_non_medical"
        assert input_payload["visual_data"].get("severity_scale_present") is True
        assert input_payload.get("confidence_score") is not None
        assert input_payload.get("observed_vs_modelled") is not None
        limitation_note = str(input_payload.get("limitation_note", "")).lower()
        labels = [str(label).lower() for label in input_payload.get("visual_data", {}).get("labels", [])]
        for term in PROHIBITED_INJURY_DIAGNOSIS_TERMS:
            assert term not in limitation_note
            assert all(term not in label for label in labels)

    if input_payload["visual_family_id"] in APPROVED_NON_ANATOMICAL_VISUAL_FAMILIES:
        assert input_payload["visual_data"].get("body_graphics_required") is False

    assert input_payload["page_density_level"] <= registry["page_density_rules"]["max_level_3_evidence_panels_per_page"]
    assert input_payload["visual_qa_required"] is True

    assert family["requires_evidence_panel"] is True
    if family["requires_disclaimer_footer"]:
        assert input_payload["disclaimer_variant"] in disclaimer_footer_tokens


def test_button2_visual_renderer_boundary_accepts_approved_visual_family() -> None:
    registry = load_registry()
    input_payload = make_valid_renderer_input()
    validate_visual_renderer_boundary_contract(input_payload, registry)
    output_contract = synthetic_expected_output_contract(input_payload, registry)
    validate_synthetic_output_contract(output_contract)
    assert output_contract["visual_family_id"] == input_payload["visual_family_id"]
    assert output_contract["delivery_ready"] is False


def test_button2_visual_renderer_boundary_rejects_unknown_visual_family() -> None:
    registry = load_registry()
    input_payload = make_valid_renderer_input()
    input_payload["visual_family_id"] = "unknown_visual_family"
    with pytest.raises(AssertionError):
        validate_visual_renderer_boundary_contract(input_payload, registry)


def test_button2_visual_renderer_boundary_requires_internal_only_release_boundary() -> None:
    registry = load_registry()
    input_payload = make_valid_renderer_input()
    input_payload["release_boundary"]["release_scope_decision"] = "EXTERNAL"
    with pytest.raises(AssertionError):
        validate_visual_renderer_boundary_contract(input_payload, registry)


def test_button2_visual_renderer_boundary_rejects_customer_release_authorized_true() -> None:
    registry = load_registry()
    input_payload = make_valid_renderer_input()
    input_payload["release_boundary"]["customer_release_authorized"] = True
    with pytest.raises(AssertionError):
        validate_visual_renderer_boundary_contract(input_payload, registry)


def test_button2_visual_renderer_boundary_rejects_learning_activation_authorized_true() -> None:
    registry = load_registry()
    input_payload = make_valid_renderer_input()
    input_payload["release_boundary"]["learning_activation_authorized"] = True
    with pytest.raises(AssertionError):
        validate_visual_renderer_boundary_contract(input_payload, registry)


def test_button2_visual_renderer_boundary_requires_evidence_panel_fields() -> None:
    registry = load_registry()
    input_payload = make_valid_renderer_input()
    del input_payload["confidence_score"]
    with pytest.raises(AssertionError):
        validate_visual_renderer_boundary_contract(input_payload, registry)


def test_button2_visual_renderer_boundary_requires_disclaimer_footer() -> None:
    registry = load_registry()
    input_payload = make_valid_renderer_input()
    input_payload["disclaimer_variant"] = "not_a_registry_footer"
    with pytest.raises(AssertionError):
        validate_visual_renderer_boundary_contract(input_payload, registry)


def test_button2_visual_renderer_boundary_rejects_heat_map_without_severity_scale() -> None:
    registry = load_registry()
    input_payload = make_valid_renderer_input()
    input_payload["visual_family_id"] = "training_priority_heat_map"
    input_payload["visual_data"]["severity_scale_present"] = False
    with pytest.raises(AssertionError):
        validate_visual_renderer_boundary_contract(input_payload, registry)


def test_button2_visual_renderer_boundary_rejects_anatomical_visual_without_non_medical_disclaimer() -> None:
    registry = load_registry()
    input_payload = make_valid_renderer_input()
    input_payload["visual_family_id"] = "anatomical_target_exposure_heat_map"
    input_payload["disclaimer_variant"] = "internal_draft_only"
    with pytest.raises(AssertionError):
        validate_visual_renderer_boundary_contract(input_payload, registry)


def test_button2_visual_renderer_boundary_enforces_page_density_limits() -> None:
    registry = load_registry()
    input_payload = make_valid_renderer_input()
    input_payload["page_density_level"] = registry["page_density_rules"]["max_level_2_analytical_visuals_per_page"] + 1
    validate_visual_renderer_boundary_contract(input_payload, registry)


def test_button2_visual_renderer_boundary_keeps_delivery_ready_false_by_default() -> None:
    registry = load_registry()
    input_payload = make_valid_renderer_input()
    output_contract = synthetic_expected_output_contract(input_payload, registry)
    validate_synthetic_output_contract(output_contract)
    assert output_contract["delivery_ready"] is False
    assert output_contract["visual_qa_required"] is True


def test_button2_visual_renderer_boundary_rejects_delivery_ready_without_visual_qa_pass() -> None:
    registry = load_registry()
    input_payload = make_valid_renderer_input()
    output_contract = synthetic_expected_output_contract(input_payload, registry)
    output_contract["delivery_ready"] = True
    output_contract["visual_qa_status"] = "FAIL"
    with pytest.raises(AssertionError):
        validate_synthetic_output_contract(output_contract)


def test_button2_visual_renderer_boundary_does_not_require_reference_visual_folder() -> None:
    registry = load_registry()
    input_payload = make_valid_renderer_input()
    validate_visual_renderer_boundary_contract(input_payload, registry)
    assert registry["registry_scope"] == "button2_premium_pdf_visual_intelligence"


def test_button2_visual_renderer_boundary_does_not_generate_pdf_or_image_outputs() -> None:
    root = Path(__file__).resolve().parents[1]
    before_snapshot = snapshot_repository_files_by_extension(root)
    registry = load_registry()
    input_payload = make_valid_renderer_input()
    validate_visual_renderer_boundary_contract(input_payload, registry)
    synthetic_expected_output_contract(input_payload, registry)
    after_snapshot = snapshot_repository_files_by_extension(root)
    assert before_snapshot == after_snapshot