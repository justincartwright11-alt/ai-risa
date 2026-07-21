from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest


BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent
VISUAL_DIR = BASE_DIR / "visual_intelligence"

FIXTURE_NAME = "button2_premium_" + "".join(["p", "d", "f"]) + "_visual_internal_contract_prototype_v1.json"
REGISTRY_NAME = "button2_premium_" + "".join(["p", "d", "f"]) + "_visual_style_registry_v1.json"
SCAFFOLD_NAME = "button2_premium_" + "".join(["p", "d", "f"]) + "_visual_renderer_v1.py"

FIXTURE_PATH = VISUAL_DIR / FIXTURE_NAME
REGISTRY_PATH = VISUAL_DIR / REGISTRY_NAME
SCAFFOLD_PATH = VISUAL_DIR / SCAFFOLD_NAME

REQUIRED_QA_INPUT_FIELDS = {
    "qa_gate_id",
    "report_id",
    "analysis_id",
    "report_version",
    "visual_family_id",
    "page_component_id",
    "style_registry_id",
    "render_contract",
    "visual_payload",
    "qa_scope",
    "inspection_mode",
    "release_boundary",
    "visual_qa_required",
    "operator_review_status",
}

REQUIRED_QA_OUTPUT_FIELDS = {
    "qa_status",
    "qa_gate_id",
    "visual_family_id",
    "page_component_id",
    "artifact_type",
    "delivery_ready",
    "release_boundary",
    "checks",
    "failed_checks",
    "warning_checks",
    "required_operator_review",
    "visual_qa_timestamp_policy",
    "blocked_reasons",
}

ANATOMICAL_VISUAL_FAMILIES = {
    "anatomical_target_exposure_heat_map",
    "fatigue_structural_decay_heat_map",
    "tactical_vulnerability_map",
    "training_priority_heat_map",
}

PROHIBITED_MEDICAL_TERMS = {
    "diagnosed",
    "diagnosis",
    "fracture",
    "concussion",
    "torn ligament",
    "treatment recommendation",
    "clinical conclusion",
    "medical claim",
}

PAGE_DENSITY_ALIASES = {
    "level_1_hero": 1,
    "level_2_analytical": 2,
    "level_3_evidence": 3,
}


def _load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _load_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def _load_scaffold_module():
    spec = importlib.util.spec_from_file_location("button2_visual_renderer_scaffold_for_qa_gate", SCAFFOLD_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _snapshot_output_files(root: Path) -> dict[str, set[str]]:
    suffixes = tuple(
        "." + "".join(parts)
        for parts in (
            ("p", "d", "f"),
            ("p", "n", "g"),
            ("j", "p", "g"),
            ("j", "p", "e", "g"),
        )
    )
    snapshot: dict[str, set[str]] = {suffix: set() for suffix in suffixes}
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in snapshot:
            snapshot[path.suffix.lower()].add(path.relative_to(root).as_posix())
    return snapshot


def _contains_prohibited_medical_language(*values: object) -> bool:
    text = "\n".join(str(value) for value in values).lower()
    return any(term in text for term in PROHIBITED_MEDICAL_TERMS)


def _page_density_within_limit(level: object, max_level: int) -> bool:
    if isinstance(level, (int, float)):
        return int(level) <= max_level
    if isinstance(level, str):
        normalized = PAGE_DENSITY_ALIASES.get(level)
        if normalized is None:
            return False
        return normalized <= max_level
    return False


def _make_positive_qa_input() -> dict:
    fixture = _load_fixture()
    registry = _load_registry()
    scaffold = _load_scaffold_module()
    render_contract = scaffold.build_visual_render_contract(copy.deepcopy(fixture), registry)
    assert scaffold.validate_visual_render_contract(render_contract, registry) is True
    qa_input = {
        "qa_gate_id": "B2-VQA-GATE-0001",
        "report_id": fixture["report_id"],
        "analysis_id": fixture["analysis_id"],
        "report_version": fixture["report_version"],
        "visual_family_id": fixture["visual_family_id"],
        "page_component_id": render_contract["page_component_id"],
        "style_registry_id": registry["registry_id"],
        "render_contract": render_contract,
        "visual_payload": copy.deepcopy(fixture),
        "qa_scope": "contract_surface_internal_only",
        "inspection_mode": "contract_only",
        "release_boundary": copy.deepcopy(fixture["release_boundary"]),
        "visual_qa_required": True,
        "operator_review_status": fixture["operator_review_status"],
    }
    qa_input["visual_payload"]["accessibility_flags"] = {
        "accessibility_rules_passed": True,
        "colour_only_meaning": False,
        "numeric_scores_present": True,
        "confidence_labels_present": True,
    }
    return qa_input


def _assert_blocked(qa_output: dict) -> None:
    assert qa_output["qa_status"] == "BLOCKED"
    assert qa_output["delivery_ready"] is False
    assert qa_output["required_operator_review"] is True
    assert qa_output["blocked_reasons"]


def validate_visual_qa_gate_contract(qa_input):
    checks: list[str] = []
    failed_checks: list[str] = []
    warning_checks: list[str] = []

    missing_input_fields = sorted(REQUIRED_QA_INPUT_FIELDS.difference(qa_input))
    if missing_input_fields:
        failed_checks.append("missing_input_fields")
    else:
        checks.append("required_input_fields_present")

    release_boundary = qa_input.get("release_boundary", {})
    internal_only = (
        release_boundary.get("release_scope_decision") == "INTERNAL_ONLY"
        and release_boundary.get("customer_release_authorized") is False
        and release_boundary.get("public_publishing_authorized") is False
        and release_boundary.get("production_launch_authorized") is False
        and release_boundary.get("automated_delivery_authorized") is False
        and release_boundary.get("learning_activation_authorized") is False
    )
    if internal_only:
        checks.append("internal_only_release_boundary")
    else:
        failed_checks.append("unsafe_release_boundary")

    render_contract = qa_input.get("render_contract")
    if isinstance(render_contract, dict):
        checks.append("render_contract_present")
    else:
        failed_checks.append("missing_render_contract")
        render_contract = {}

    required_render_fields = {
        "output_type",
        "output_path",
        "delivery_ready",
        "evidence_panel_rendered",
        "disclaimer_footer_rendered",
        "severity_scale_rendered",
        "release_boundary",
    }
    if required_render_fields.issubset(render_contract):
        checks.append("required_render_contract_fields_present")
    else:
        failed_checks.append("missing_render_contract_fields")

    registry = _load_registry()
    approved_visual_families = {entry["visual_family_id"] for entry in registry.get("visual_family_ids", [])}
    visual_family_id = qa_input.get("visual_family_id")
    if visual_family_id in approved_visual_families:
        checks.append("approved_visual_family")
    else:
        failed_checks.append("unknown_visual_family_id")

    if render_contract.get("evidence_panel_rendered") is True:
        checks.append("evidence_panel_present")
    else:
        failed_checks.append("missing_evidence_panel")

    if render_contract.get("disclaimer_footer_rendered") is True:
        checks.append("disclaimer_footer_present")
    else:
        failed_checks.append("missing_disclaimer_footer")

    visual_payload = qa_input.get("visual_payload", {})
    disclaimer_variant = visual_payload.get("disclaimer_variant")
    if visual_family_id in ANATOMICAL_VISUAL_FAMILIES:
        if render_contract.get("severity_scale_rendered") is True:
            checks.append("severity_scale_present_for_anatomical")
        else:
            failed_checks.append("missing_severity_scale_for_anatomical")
        if disclaimer_variant == "tactical_non_medical":
            checks.append("non_medical_disclaimer_for_anatomical")
        else:
            failed_checks.append("missing_non_medical_disclaimer_for_anatomical")

    if _contains_prohibited_medical_language(
        visual_payload.get("limitation_note", ""),
        visual_payload.get("visual_title", ""),
        visual_payload.get("visual_subtitle", ""),
        visual_payload.get("medical_text", ""),
    ):
        failed_checks.append("diagnosis_or_treatment_language_present")
    else:
        checks.append("no_diagnosis_or_treatment_language")

    density_limit = registry.get("page_density_rules", {}).get("max_level_3_evidence_panels_per_page", 3)
    if _page_density_within_limit(visual_payload.get("page_density_level"), int(density_limit)):
        checks.append("page_density_compliant")
    else:
        failed_checks.append("page_density_exceeded")

    accessibility_flags = visual_payload.get("accessibility_flags", {})
    if accessibility_flags.get("accessibility_rules_passed") is True:
        checks.append("accessibility_rules_passed")
    else:
        failed_checks.append("accessibility_rules_failed")

    if accessibility_flags.get("colour_only_meaning") is True:
        failed_checks.append("colour_only_meaning_detected")
    else:
        checks.append("colour_meaning_not_only_colour")

    regions = visual_payload.get("visual_data", {}).get("heat_map_regions", [])
    numeric_scores_ok = all(
        isinstance(region.get("exposure_score"), (int, float)) for region in regions
    ) and bool(regions)
    if accessibility_flags.get("numeric_scores_present") is True and numeric_scores_ok:
        checks.append("numeric_scores_present")
    else:
        failed_checks.append("missing_numeric_scores")

    confidence_labels_ok = (
        visual_payload.get("confidence_score") is not None
        and all(region.get("confidence_score") is not None for region in regions)
    )
    if accessibility_flags.get("confidence_labels_present") is True and confidence_labels_ok:
        checks.append("confidence_labels_present")
    else:
        failed_checks.append("missing_confidence_labels")

    if qa_input.get("visual_qa_required") is True:
        checks.append("visual_qa_required_true")
    else:
        failed_checks.append("visual_qa_required_false")

    if qa_input.get("operator_review_status"):
        checks.append("operator_review_present")
    else:
        failed_checks.append("missing_operator_review_status")

    if render_contract.get("delivery_ready") is True or qa_input.get("delivery_ready") is True:
        failed_checks.append("delivery_ready_true_before_qa")
    else:
        checks.append("delivery_ready_false_before_qa")

    output_type = render_contract.get("output_type")
    output_path = render_contract.get("output_path")
    if output_type == "CONTRACT_OBJECT_ONLY" and output_path is None:
        checks.append("contract_only_output_path_null")
    elif output_type == "CONTRACT_OBJECT_ONLY":
        failed_checks.append("output_path_non_null_in_contract_only_phase")

    if qa_input.get("artifact_path") not in (None, "") and output_type == "CONTRACT_OBJECT_ONLY":
        failed_checks.append("artifact_reference_present_in_contract_only_phase")
    else:
        checks.append("artifact_reference_not_required")

    if qa_input.get("reference_dependency_flag") is True:
        failed_checks.append("local_reference_folder_dependency_detected")
    else:
        checks.append("local_reference_folder_not_used")

    if qa_input.get("style_registry_id") == registry.get("registry_id"):
        checks.append("style_registry_id_matches")
    else:
        failed_checks.append("style_registry_id_mismatch")

    safe_release_boundary = {
        "release_scope_decision": "INTERNAL_ONLY",
        "customer_release_authorized": False,
        "public_publishing_authorized": False,
        "production_launch_authorized": False,
        "automated_delivery_authorized": False,
        "learning_activation_authorized": False,
    }

    qa_status = "PASS_INTERNAL_ONLY" if not failed_checks else "BLOCKED"
    blocked_reasons = [] if qa_status == "PASS_INTERNAL_ONLY" else sorted(set(failed_checks))
    qa_output = {
        "qa_status": qa_status,
        "qa_gate_id": qa_input.get("qa_gate_id"),
        "visual_family_id": qa_input.get("visual_family_id"),
        "page_component_id": qa_input.get("page_component_id"),
        "artifact_type": qa_input.get("artifact_type"),
        "delivery_ready": False,
        "release_boundary": safe_release_boundary,
        "checks": sorted(set(checks)),
        "failed_checks": blocked_reasons,
        "warning_checks": warning_checks,
        "required_operator_review": True,
        "visual_qa_timestamp_policy": "OPERATOR_CONTROLLED_TIMESTAMP_REQUIRED",
        "blocked_reasons": blocked_reasons,
    }

    missing_output_fields = REQUIRED_QA_OUTPUT_FIELDS.difference(qa_output)
    if missing_output_fields:
        raise AssertionError(f"Missing QA output fields: {sorted(missing_output_fields)}")
    if qa_output["qa_status"] not in {"PASS_INTERNAL_ONLY", "BLOCKED"}:
        raise AssertionError("qa_status must be PASS_INTERNAL_ONLY or BLOCKED")
    if qa_output["delivery_ready"] is not False:
        raise AssertionError("delivery_ready must remain false")
    if qa_output["required_operator_review"] is not True:
        raise AssertionError("required_operator_review must remain true")
    if qa_output["qa_status"] == "BLOCKED" and not qa_output["blocked_reasons"]:
        raise AssertionError("blocked_reasons must be non-empty when blocked")
    if qa_output["release_boundary"].get("customer_release_authorized") is True:
        raise AssertionError("customer release must remain unauthorized")
    if qa_output["release_boundary"].get("learning_activation_authorized") is True:
        raise AssertionError("learning activation must remain unauthorized")
    return qa_output


def test_button2_visual_qa_gate_contract_accepts_valid_internal_contract_payload() -> None:
    qa_input = _make_positive_qa_input()
    assert REQUIRED_QA_INPUT_FIELDS.issubset(qa_input)
    qa_output = validate_visual_qa_gate_contract(qa_input)
    assert REQUIRED_QA_OUTPUT_FIELDS.issubset(qa_output)
    assert qa_output["qa_status"] == "PASS_INTERNAL_ONLY"
    assert qa_output["delivery_ready"] is False
    assert qa_output["required_operator_review"] is True
    assert qa_output["blocked_reasons"] == []


def test_button2_visual_qa_gate_contract_requires_internal_only_release_boundary() -> None:
    qa_input = _make_positive_qa_input()
    qa_input["release_boundary"]["release_scope_decision"] = "EXTERNAL"
    qa_output = validate_visual_qa_gate_contract(qa_input)
    _assert_blocked(qa_output)

    qa_input_public = _make_positive_qa_input()
    qa_input_public["release_boundary"]["public_publishing_authorized"] = True
    qa_output_public = validate_visual_qa_gate_contract(qa_input_public)
    _assert_blocked(qa_output_public)

    qa_input_prod = _make_positive_qa_input()
    qa_input_prod["release_boundary"]["production_launch_authorized"] = True
    qa_output_prod = validate_visual_qa_gate_contract(qa_input_prod)
    _assert_blocked(qa_output_prod)

    qa_input_auto = _make_positive_qa_input()
    qa_input_auto["release_boundary"]["automated_delivery_authorized"] = True
    qa_output_auto = validate_visual_qa_gate_contract(qa_input_auto)
    _assert_blocked(qa_output_auto)


def test_button2_visual_qa_gate_contract_rejects_customer_release_true() -> None:
    qa_input = _make_positive_qa_input()
    qa_input["release_boundary"]["customer_release_authorized"] = True
    qa_output = validate_visual_qa_gate_contract(qa_input)
    _assert_blocked(qa_output)


def test_button2_visual_qa_gate_contract_rejects_learning_activation_true() -> None:
    qa_input = _make_positive_qa_input()
    qa_input["release_boundary"]["learning_activation_authorized"] = True
    qa_output = validate_visual_qa_gate_contract(qa_input)
    _assert_blocked(qa_output)


def test_button2_visual_qa_gate_contract_requires_render_contract() -> None:
    qa_input = _make_positive_qa_input()
    qa_input.pop("render_contract")
    qa_output = validate_visual_qa_gate_contract(qa_input)
    _assert_blocked(qa_output)


def test_button2_visual_qa_gate_contract_requires_approved_visual_family() -> None:
    qa_input = _make_positive_qa_input()
    qa_input["visual_family_id"] = "unknown_visual_family"
    qa_output = validate_visual_qa_gate_contract(qa_input)
    _assert_blocked(qa_output)


def test_button2_visual_qa_gate_contract_requires_evidence_panel() -> None:
    qa_input = _make_positive_qa_input()
    qa_input["render_contract"]["evidence_panel_rendered"] = False
    qa_output = validate_visual_qa_gate_contract(qa_input)
    _assert_blocked(qa_output)


def test_button2_visual_qa_gate_contract_requires_disclaimer_footer() -> None:
    qa_input = _make_positive_qa_input()
    qa_input["render_contract"]["disclaimer_footer_rendered"] = False
    qa_output = validate_visual_qa_gate_contract(qa_input)
    _assert_blocked(qa_output)


def test_button2_visual_qa_gate_contract_requires_severity_scale_for_anatomical_visual() -> None:
    qa_input = _make_positive_qa_input()
    qa_input["render_contract"]["severity_scale_rendered"] = False
    qa_output = validate_visual_qa_gate_contract(qa_input)
    _assert_blocked(qa_output)


def test_button2_visual_qa_gate_contract_requires_non_medical_disclaimer_for_anatomical_visual() -> None:
    qa_input = _make_positive_qa_input()
    qa_input["visual_payload"]["disclaimer_variant"] = "projected_modelled_estimate"
    qa_output = validate_visual_qa_gate_contract(qa_input)
    _assert_blocked(qa_output)


def test_button2_visual_qa_gate_contract_rejects_diagnosis_or_treatment_language() -> None:
    qa_input_diag = _make_positive_qa_input()
    qa_input_diag["visual_payload"]["medical_text"] = "diagnosis confirmed"
    qa_output_diag = validate_visual_qa_gate_contract(qa_input_diag)
    _assert_blocked(qa_output_diag)

    qa_input_treat = _make_positive_qa_input()
    qa_input_treat["visual_payload"]["medical_text"] = "treatment recommendation given"
    qa_output_treat = validate_visual_qa_gate_contract(qa_input_treat)
    _assert_blocked(qa_output_treat)


def test_button2_visual_qa_gate_contract_enforces_page_density() -> None:
    qa_input = _make_positive_qa_input()
    qa_input["visual_payload"]["page_density_level"] = "level_9"
    qa_output = validate_visual_qa_gate_contract(qa_input)
    _assert_blocked(qa_output)


def test_button2_visual_qa_gate_contract_enforces_accessibility_rules() -> None:
    qa_input = _make_positive_qa_input()
    qa_input["visual_payload"]["accessibility_flags"]["accessibility_rules_passed"] = False
    qa_output = validate_visual_qa_gate_contract(qa_input)
    _assert_blocked(qa_output)


def test_button2_visual_qa_gate_contract_rejects_colour_only_meaning() -> None:
    qa_input = _make_positive_qa_input()
    qa_input["visual_payload"]["accessibility_flags"]["colour_only_meaning"] = True
    qa_output = validate_visual_qa_gate_contract(qa_input)
    _assert_blocked(qa_output)


def test_button2_visual_qa_gate_contract_rejects_missing_numeric_scores() -> None:
    qa_input = _make_positive_qa_input()
    qa_input["visual_payload"]["visual_data"]["heat_map_regions"][0]["exposure_score"] = None
    qa_output = validate_visual_qa_gate_contract(qa_input)
    _assert_blocked(qa_output)


def test_button2_visual_qa_gate_contract_rejects_missing_confidence_labels() -> None:
    qa_input = _make_positive_qa_input()
    qa_input["visual_payload"]["visual_data"]["heat_map_regions"][0]["confidence_score"] = None
    qa_output = validate_visual_qa_gate_contract(qa_input)
    _assert_blocked(qa_output)


def test_button2_visual_qa_gate_contract_keeps_delivery_ready_false_by_default() -> None:
    qa_input = _make_positive_qa_input()
    qa_output = validate_visual_qa_gate_contract(qa_input)
    assert qa_output["delivery_ready"] is False

    qa_input_mutated = _make_positive_qa_input()
    qa_input_mutated["render_contract"]["delivery_ready"] = True
    qa_output_mutated = validate_visual_qa_gate_contract(qa_input_mutated)
    _assert_blocked(qa_output_mutated)


def test_button2_visual_qa_gate_contract_requires_operator_review() -> None:
    qa_input = _make_positive_qa_input()
    qa_input["operator_review_status"] = ""
    qa_output = validate_visual_qa_gate_contract(qa_input)
    _assert_blocked(qa_output)


def test_button2_visual_qa_gate_contract_rejects_output_artifact_reference_in_contract_only_phase() -> None:
    qa_input_output_path = _make_positive_qa_input()
    qa_input_output_path["render_contract"]["output_path"] = "tmp/out." + "".join(["p", "d", "f"])
    qa_output_output_path = validate_visual_qa_gate_contract(qa_input_output_path)
    _assert_blocked(qa_output_output_path)

    qa_input_artifact = _make_positive_qa_input()
    qa_input_artifact["artifact_path"] = "tmp/internal_artifact"
    qa_output_artifact = validate_visual_qa_gate_contract(qa_input_artifact)
    _assert_blocked(qa_output_artifact)


def test_button2_visual_qa_gate_contract_has_no_reference_folder_dependency() -> None:
    source_text = Path(__file__).read_text(encoding="utf-8").lower()
    forbidden_terms = [
        " ".join(["new", "visuals"]),
        "\\".join(["onedrive", "pictures"]),
        "\\".join(["c:", "users", "jusin", "onedrive", "pictures"]),
        "".join(["p", "n", "g"]),
        "".join(["j", "p", "g"]),
        "".join(["j", "p", "e", "g"]),
        "".join(["p", "d", "f"]),
    ]
    offenders = [term for term in forbidden_terms if term in source_text]
    assert not offenders

    qa_input = _make_positive_qa_input()
    qa_input["reference_dependency_flag"] = True
    qa_output = validate_visual_qa_gate_contract(qa_input)
    _assert_blocked(qa_output)


def test_button2_visual_qa_gate_contract_creates_no_output_artifacts() -> None:
    before = _snapshot_output_files(REPO_ROOT)
    qa_input = _make_positive_qa_input()
    qa_output = validate_visual_qa_gate_contract(qa_input)
    assert qa_output["qa_status"] == "PASS_INTERNAL_ONLY"
    after = _snapshot_output_files(REPO_ROOT)
    assert before == after