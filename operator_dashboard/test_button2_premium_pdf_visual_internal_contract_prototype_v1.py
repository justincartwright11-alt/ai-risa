from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
BASE_DIR = Path(__file__).resolve().parent
VISUAL_DIR = BASE_DIR / "visual_intelligence"

FIXTURE_NAME = "button2_premium_" + "".join(["p", "d", "f"]) + "_visual_internal_contract_prototype_v1.json"
REGISTRY_NAME = "button2_premium_" + "".join(["p", "d", "f"]) + "_visual_style_registry_v1.json"
SCAFFOLD_NAME = "button2_premium_" + "".join(["p", "d", "f"]) + "_visual_renderer_v1.py"

FIXTURE_PATH = VISUAL_DIR / FIXTURE_NAME
REGISTRY_PATH = VISUAL_DIR / REGISTRY_NAME
SCAFFOLD_PATH = VISUAL_DIR / SCAFFOLD_NAME

REQUIRED_TOP_LEVEL_FIELDS = {
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

REQUIRED_REGION_FIELDS = {
    "region_id",
    "region_label",
    "exposure_score",
    "severity_band",
    "tactical_meaning",
    "evidence_basis",
    "observed_vs_modelled",
    "confidence_score",
    "uncertainty_flags",
}

ALLOWED_SEVERITY_BANDS = {
    "very_low",
    "low",
    "moderate",
    "high",
    "very_high",
    "critical_only_if_threshold_supported",
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


def _forbidden_terms() -> list[str]:
    return [
        " ".join(["New", "Visuals"]),
        "\\".join(["OneDrive", "Pictures"]),
        "\\".join(["C:", "Users", "jusin", "OneDrive", "Pictures"]),
        "".join(["p", "n", "g"]),
        "".join(["j", "p", "g"]),
        "".join(["j", "p", "e", "g"]),
        "".join(["p", "d", "f"]),
        "diagnosed",
        "fracture",
        "concussion",
        "torn ligament",
        "treatment recommendation",
        "clinical conclusion",
        "customer_release_authorized\": true",
        "learning_activation_authorized\": true",
    ]


def _load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _load_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def _load_scaffold_module():
    spec = importlib.util.spec_from_file_location("button2_visual_renderer_scaffold", SCAFFOLD_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _snapshot_output_files(root: Path) -> dict[str, set[str]]:
    snapshot: dict[str, set[str]] = {suffix: set() for suffix in OUTPUT_SUFFIXES}
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in snapshot:
            snapshot[path.suffix.lower()].add(path.relative_to(root).as_posix())
    return snapshot


def _assert_blocked(contract: dict) -> None:
    assert contract["render_status"] == "BLOCKED"
    assert contract["delivery_ready"] is False
    assert contract["blocked_reasons"]


def _build_contract(payload: dict) -> tuple[dict, dict, object]:
    module = _load_scaffold_module()
    registry = module.load_visual_style_registry(REGISTRY_PATH)
    contract = module.build_visual_render_contract(payload, registry)
    return contract, registry, module


def test_button2_visual_internal_contract_prototype_fixture_loads_as_json() -> None:
    payload = _load_fixture()
    assert isinstance(payload, dict)


def test_button2_visual_internal_contract_prototype_has_required_top_level_fields() -> None:
    payload = _load_fixture()
    missing = REQUIRED_TOP_LEVEL_FIELDS.difference(payload)
    assert not missing


def test_button2_visual_internal_contract_prototype_preserves_internal_only_release_boundary() -> None:
    payload = _load_fixture()
    release_boundary = payload["release_boundary"]
    assert release_boundary["release_scope_decision"] == "INTERNAL_ONLY"
    assert release_boundary["customer_release_authorized"] is False
    assert release_boundary["public_publishing_authorized"] is False
    assert release_boundary["production_launch_authorized"] is False
    assert release_boundary["automated_delivery_authorized"] is False
    assert release_boundary["learning_activation_authorized"] is False


def test_button2_visual_internal_contract_prototype_confirms_visual_family() -> None:
    payload = _load_fixture()
    assert payload["visual_family_id"] == "anatomical_target_exposure_heat_map"


def test_button2_visual_internal_contract_prototype_confirms_non_medical_disclaimer() -> None:
    payload = _load_fixture()
    assert payload["disclaimer_variant"] == "tactical_non_medical"


def test_button2_visual_internal_contract_prototype_confirms_visual_data_contract() -> None:
    payload = _load_fixture()
    visual_data = payload["visual_data"]
    assert payload["page_density_level"] == "level_1_hero"
    assert payload["visual_qa_required"] is True
    assert payload["observed_vs_modelled"] == "modelled"
    assert payload["operator_review_status"] == "INTERNAL_REVIEW_PENDING"
    assert visual_data["severity_scale_present"] is True
    assert visual_data["severity_scale_name"] == "default_0_100_scale"
    assert visual_data["contract_only"] is True
    assert visual_data["prototype_status"] == "INTERNAL_CONTRACT_ONLY"
    assert visual_data["non_medical_status"] == "TACTICAL_ANALYSIS_NOT_MEDICAL_DIAGNOSIS"
    assert isinstance(visual_data["labels"], list)
    assert visual_data["labels"]


def test_button2_visual_internal_contract_prototype_confirms_heat_map_region_contract() -> None:
    payload = _load_fixture()
    heat_map_regions = payload["visual_data"]["heat_map_regions"]
    assert len(heat_map_regions) >= 5

    for region in heat_map_regions:
        missing = REQUIRED_REGION_FIELDS.difference(region)
        assert not missing
        assert isinstance(region["exposure_score"], (int, float))
        assert 0 <= region["exposure_score"] <= 100
        assert region["severity_band"] in ALLOWED_SEVERITY_BANDS


def test_button2_visual_internal_contract_prototype_rejects_prohibited_content() -> None:
    fixture_text = FIXTURE_PATH.read_text(encoding="utf-8").lower()
    offenders = [term for term in _forbidden_terms() if term.lower() in fixture_text]
    assert not offenders


def test_button2_visual_internal_contract_prototype_passes_scaffold_contract() -> None:
    payload = _load_fixture()
    contract, registry, module = _build_contract(payload)
    assert contract["render_status"] == "CONTRACT_VALIDATED_INTERNAL_ONLY"
    assert contract["blocked_reasons"] == []
    assert module.validate_visual_render_contract(contract, registry) is True


def test_button2_visual_internal_contract_prototype_returns_contract_object_only() -> None:
    payload = _load_fixture()
    contract, _registry, _module = _build_contract(payload)
    assert contract["output_type"] == "CONTRACT_OBJECT_ONLY"


def test_button2_visual_internal_contract_prototype_keeps_output_path_null() -> None:
    payload = _load_fixture()
    contract, _registry, _module = _build_contract(payload)
    assert contract["output_path"] is None


def test_button2_visual_internal_contract_prototype_keeps_delivery_ready_false() -> None:
    payload = _load_fixture()
    contract, _registry, _module = _build_contract(payload)
    assert contract["delivery_ready"] is False


def test_button2_visual_internal_contract_prototype_keeps_visual_qa_pending() -> None:
    payload = _load_fixture()
    contract, _registry, _module = _build_contract(payload)
    assert contract["visual_qa_status"] == "PENDING"


def test_button2_visual_internal_contract_prototype_renders_no_output_artifacts() -> None:
    payload = _load_fixture()
    before = _snapshot_output_files(REPO_ROOT)
    contract, registry, module = _build_contract(payload)
    assert contract["render_status"] == "CONTRACT_VALIDATED_INTERNAL_ONLY"
    assert module.validate_visual_render_contract(contract, registry) is True
    after = _snapshot_output_files(REPO_ROOT)
    assert before == after


def test_button2_visual_internal_contract_prototype_has_no_reference_folder_dependency() -> None:
    source_text = Path(__file__).read_text(encoding="utf-8")
    fixture_text = FIXTURE_PATH.read_text(encoding="utf-8")
    combined_text = (source_text + "\n" + fixture_text).lower()
    offenders = [term for term in _forbidden_terms()[:3] if term.lower() in combined_text]
    assert not offenders


def test_button2_visual_internal_contract_prototype_rejects_customer_release_true_mutation() -> None:
    payload = copy.deepcopy(_load_fixture())
    payload["release_boundary"]["customer_release_authorized"] = True
    contract, _registry, _module = _build_contract(payload)
    _assert_blocked(contract)


def test_button2_visual_internal_contract_prototype_rejects_learning_activation_true_mutation() -> None:
    payload = copy.deepcopy(_load_fixture())
    payload["release_boundary"]["learning_activation_authorized"] = True
    contract, _registry, _module = _build_contract(payload)
    _assert_blocked(contract)


def test_button2_visual_internal_contract_prototype_rejects_missing_severity_scale_mutation() -> None:
    payload = copy.deepcopy(_load_fixture())
    payload["visual_data"]["severity_scale_present"] = False
    contract, _registry, _module = _build_contract(payload)
    _assert_blocked(contract)


def test_button2_visual_internal_contract_prototype_rejects_wrong_disclaimer_mutation() -> None:
    payload = copy.deepcopy(_load_fixture())
    payload["disclaimer_variant"] = "projected_modelled_estimate"
    contract, _registry, _module = _build_contract(payload)
    _assert_blocked(contract)


def test_button2_visual_internal_contract_prototype_rejects_delivery_ready_true_mutation() -> None:
    payload = copy.deepcopy(_load_fixture())
    payload["delivery_ready"] = True
    payload["visual_data"]["force_delivery_ready"] = True
    contract, _registry, _module = _build_contract(payload)
    _assert_blocked(contract)
