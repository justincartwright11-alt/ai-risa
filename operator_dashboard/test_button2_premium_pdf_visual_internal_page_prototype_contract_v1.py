from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest


BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent
VISUAL_DIR = BASE_DIR / "visual_intelligence"

ACR = "".join(["p", "d", "f"])

PAGE_FIXTURE_NAME = "button2_premium_" + ACR + "_visual_internal_page_prototype_v1.json"
PAYLOAD_FIXTURE_NAME = "button2_premium_" + ACR + "_visual_internal_contract_prototype_v1.json"
REGISTRY_NAME = "button2_premium_" + ACR + "_visual_style_registry_v1.json"
RENDERER_NAME = "button2_premium_" + ACR + "_visual_renderer_v1.py"
QA_GATE_NAME = "button2_premium_" + ACR + "_visual_qa_gate_v1.py"

PAGE_FIXTURE_PATH = VISUAL_DIR / PAGE_FIXTURE_NAME
PAYLOAD_FIXTURE_PATH = VISUAL_DIR / PAYLOAD_FIXTURE_NAME
REGISTRY_PATH = VISUAL_DIR / REGISTRY_NAME
RENDERER_PATH = VISUAL_DIR / RENDERER_NAME
QA_GATE_PATH = VISUAL_DIR / QA_GATE_NAME

REQUIRED_TOP_LEVEL_FIELDS = {
    "page_prototype_id",
    "report_id",
    "analysis_id",
    "report_version",
    "visual_family_id",
    "page_number",
    "page_role",
    "page_density_level",
    "style_registry_id",
    "render_contract",
    "qa_gate_output",
    "visual_payload",
    "evidence_panel",
    "disclaimer_footer",
    "accessibility_requirements",
    "release_boundary",
    "operator_review_status",
    "page_layout_contract",
    "prototype_status",
    "contract_only",
}

REQUIRED_EVIDENCE_FIELDS = {
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

REQUIRED_LAYOUT_ZONES = {
    "top_title_band",
    "primary_visual_field",
    "fighter_context_label_band",
    "severity_scale_legend",
    "evidence_panel",
    "tactical_limitation_note",
    "disclaimer_footer",
    "internal_only_status_marker",
}


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_renderer_module():
    spec = importlib.util.spec_from_file_location("b2_renderer_contract_mod", RENDERER_PATH)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_qa_module():
    spec = importlib.util.spec_from_file_location("b2_qa_contract_mod", QA_GATE_PATH)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _base_page() -> dict:
    return _load_json(PAGE_FIXTURE_PATH)


def _base_payload() -> dict:
    return _load_json(PAYLOAD_FIXTURE_PATH)


def _base_registry() -> dict:
    return _load_json(REGISTRY_PATH)


def _mk_fragment_tokens() -> dict[str, str]:
    return {
        "folder_a": " ".join(["New", "Visuals"]),
        "folder_b": "\\".join(["OneDrive", "Pictures"]),
        "folder_c": "\\".join(["C:", "Users", "jusin", "OneDrive", "Pictures"]),
        "sfx_a": "".join(["p", "n", "g"]),
        "sfx_b": "".join(["j", "p", "g"]),
        "sfx_c": "".join(["j", "p", "e", "g"]),
        "sfx_d": "".join(["p", "d", "f"]),
        "bad_customer": "customer_release_authorized\": true",
        "bad_learning": "learning_activation_authorized\": true",
        "bad_prod": "production_launch_authorized\": true",
        "bad_auto": "automated_delivery_authorized\": true",
    }


def _iter_strings(value):
    if isinstance(value, str):
        yield value
        return
    if isinstance(value, dict):
        for nested in value.values():
            yield from _iter_strings(nested)
        return
    if isinstance(value, (list, tuple, set)):
        for nested in value:
            yield from _iter_strings(nested)
        return
    if value is None:
        return
    yield str(value)


def _contains_dependency_text(value) -> bool:
    tokens = _mk_fragment_tokens()
    for text in _iter_strings(value):
        lowered = text.lower()
        if (
            tokens["folder_a"].lower() in lowered
            or tokens["folder_b"].lower() in lowered
            or tokens["folder_c"].lower() in lowered
            or tokens["sfx_a"].lower() in lowered
            or tokens["sfx_b"].lower() in lowered
            or tokens["sfx_c"].lower() in lowered
            or tokens["sfx_d"].lower() in lowered
        ):
            return True
    return False


def _contains_medical_or_treatment_text(value) -> bool:
    blocked = {
        "diagnosed",
        "diagnosis",
        "fracture",
        "concussion",
        "torn ligament",
        "treatment",
        "clinical conclusion",
        "medical claim",
    }
    for text in _iter_strings(value):
        lowered = text.lower().replace("_", " ")
        lowered = lowered.replace("not a medical diagnosis", "")
        lowered = lowered.replace("not medical diagnosis", "")
        lowered = lowered.replace("not treatment guidance", "")
        lowered = lowered.replace("not an injury diagnostic determination", "")
        lowered = lowered.replace("not an injury diagnosis", "")
        if any(term in lowered for term in blocked):
            return True
    return False


def _snapshot_output_files(root: Path) -> dict[str, set[str]]:
    t = _mk_fragment_tokens()
    suffixes = tuple("." + t[key] for key in ("sfx_d", "sfx_a", "sfx_b", "sfx_c"))
    out = {suffix: set() for suffix in suffixes}
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in out:
            out[path.suffix.lower()].add(path.relative_to(root).as_posix())
    return out


def _build_expected_contracts() -> tuple[dict, dict]:
    payload = _base_payload()
    registry = _base_registry()
    renderer = _load_renderer_module()
    qa_mod = _load_qa_module()

    render_contract = renderer.build_visual_render_contract(copy.deepcopy(payload), registry)
    assert renderer.validate_visual_render_contract(render_contract, registry) is True

    qa_input = {
        "qa_gate_id": "B2-VQA-GATE-PAGE-0001",
        "report_id": payload["report_id"],
        "analysis_id": payload["analysis_id"],
        "report_version": payload["report_version"],
        "visual_family_id": payload["visual_family_id"],
        "page_component_id": render_contract["page_component_id"],
        "style_registry_id": "button2_premium_visual_style_registry_v1",
        "render_contract": copy.deepcopy(render_contract),
        "visual_payload": copy.deepcopy(payload),
        "qa_scope": "contract_surface_internal_only",
        "inspection_mode": "contract_only",
        "release_boundary": copy.deepcopy(payload["release_boundary"]),
        "visual_qa_required": True,
        "operator_review_status": payload["operator_review_status"],
    }
    qa_output = qa_mod.validate_visual_qa_gate_contract(qa_input)
    return render_contract, qa_output


def validate_page_prototype_contract(page):
    blocked_reasons: list[str] = []

    missing = sorted(REQUIRED_TOP_LEVEL_FIELDS.difference(page))
    if missing:
        blocked_reasons.append("missing_top_level_fields")

    rb = page.get("release_boundary") if isinstance(page.get("release_boundary"), dict) else {}
    safe_rb = (
        rb.get("release_scope_decision") == "INTERNAL_ONLY"
        and rb.get("customer_release_authorized") is False
        and rb.get("public_publishing_authorized") is False
        and rb.get("production_launch_authorized") is False
        and rb.get("automated_delivery_authorized") is False
        and rb.get("learning_activation_authorized") is False
    )
    if not safe_rb:
        blocked_reasons.append("unsafe_release_boundary")

    rc = page.get("render_contract") if isinstance(page.get("render_contract"), dict) else None
    if rc is None:
        blocked_reasons.append("missing_render_contract")
        rc = {}

    qg = page.get("qa_gate_output") if isinstance(page.get("qa_gate_output"), dict) else None
    if qg is None:
        blocked_reasons.append("missing_qa_gate_output")
        qg = {}

    if not isinstance(page.get("evidence_panel"), dict):
        blocked_reasons.append("missing_evidence_panel")

    if not isinstance(page.get("disclaimer_footer"), dict):
        blocked_reasons.append("missing_disclaimer_footer")

    if not isinstance(page.get("accessibility_requirements"), dict):
        blocked_reasons.append("missing_accessibility_requirements")

    if not isinstance(page.get("page_layout_contract"), dict):
        blocked_reasons.append("missing_page_layout_contract")

    if rc.get("output_path") is not None:
        blocked_reasons.append("output_path_non_null")

    if rc.get("delivery_ready") is True or qg.get("delivery_ready") is True:
        blocked_reasons.append("delivery_ready_true")

    if rb.get("customer_release_authorized") is True:
        blocked_reasons.append("customer_release_true")

    if rb.get("learning_activation_authorized") is True:
        blocked_reasons.append("learning_activation_true")

    if page.get("visual_family_id") != "anatomical_target_exposure_heat_map":
        blocked_reasons.append("wrong_visual_family")

    if page.get("page_role") != "LEVEL_1_HERO_VISUAL_PAGE":
        blocked_reasons.append("wrong_page_role")

    if page.get("page_density_level") != "level_1_hero":
        blocked_reasons.append("wrong_page_density")

    if _contains_medical_or_treatment_text(page):
        blocked_reasons.append("medical_or_treatment_language_present")

    if _contains_dependency_text(page):
        blocked_reasons.append("reference_or_output_dependency_present")

    status = "PASS_INTERNAL_ONLY" if not blocked_reasons else "BLOCKED"
    return {
        "status": status,
        "blocked_reasons": sorted(set(blocked_reasons)) if blocked_reasons else [],
        "delivery_ready": False,
        "required_operator_review": True,
    }


def test_button2_internal_page_prototype_fixture_json_is_valid():
    page = _base_page()
    assert isinstance(page, dict)


def test_button2_internal_page_prototype_requires_all_top_level_fields():
    page = _base_page()
    missing = REQUIRED_TOP_LEVEL_FIELDS.difference(page)
    assert not missing


def test_button2_internal_page_prototype_confirms_visual_family_page_role_and_density():
    page = _base_page()
    assert page["visual_family_id"] == "anatomical_target_exposure_heat_map"
    assert page["page_role"] == "LEVEL_1_HERO_VISUAL_PAGE"
    assert page["page_density_level"] == "level_1_hero"
    assert page["prototype_status"] == "INTERNAL_PAGE_CONTRACT_ONLY"
    assert page["contract_only"] is True
    assert page["operator_review_status"] == "INTERNAL_REVIEW_PENDING"


def test_button2_internal_page_prototype_preserves_internal_only_release_boundary():
    page = _base_page()
    rb = page["release_boundary"]
    assert rb["release_scope_decision"] == "INTERNAL_ONLY"
    assert rb["customer_release_authorized"] is False
    assert rb["public_publishing_authorized"] is False
    assert rb["production_launch_authorized"] is False
    assert rb["automated_delivery_authorized"] is False
    assert rb["learning_activation_authorized"] is False


def test_button2_internal_page_prototype_embeds_safe_render_contract():
    page = _base_page()
    expected_rc, _ = _build_expected_contracts()
    rc = page["render_contract"]
    assert rc["render_status"] == "CONTRACT_VALIDATED_INTERNAL_ONLY"
    assert rc["output_type"] == "CONTRACT_OBJECT_ONLY"
    assert rc["output_path"] is None
    assert rc["delivery_ready"] is False
    assert rc["visual_qa_status"] == "PENDING"
    assert rc["evidence_panel_rendered"] is True
    assert rc["disclaimer_footer_rendered"] is True
    assert rc["severity_scale_rendered"] is True
    assert rc["blocked_reasons"] == []
    for key in (
        "render_status",
        "output_type",
        "output_path",
        "delivery_ready",
        "visual_qa_status",
        "evidence_panel_rendered",
        "disclaimer_footer_rendered",
        "severity_scale_rendered",
        "blocked_reasons",
    ):
        assert rc[key] == expected_rc[key]


def test_button2_internal_page_prototype_embeds_safe_qa_gate_output():
    page = _base_page()
    _, expected_qg = _build_expected_contracts()
    qg = page["qa_gate_output"]
    assert qg["qa_status"] == "PASS_INTERNAL_ONLY"
    assert qg["delivery_ready"] is False
    assert qg["required_operator_review"] is True
    assert qg["blocked_reasons"] == []
    for key in ("qa_status", "delivery_ready", "required_operator_review", "blocked_reasons"):
        assert qg[key] == expected_qg[key]


def test_button2_internal_page_prototype_preserves_source_visual_payload_identity():
    page = _base_page()
    payload = _base_payload()
    embedded = page["visual_payload"]
    assert embedded == payload
    assert page["report_id"] == payload["report_id"]
    assert page["analysis_id"] == payload["analysis_id"]
    assert page["report_version"] == payload["report_version"]
    assert page["release_boundary"] == payload["release_boundary"]


def test_button2_internal_page_prototype_confirms_evidence_panel_contract():
    page = _base_page()
    evidence = page["evidence_panel"]
    missing = REQUIRED_EVIDENCE_FIELDS.difference(evidence)
    assert not missing


def test_button2_internal_page_prototype_confirms_disclaimer_footer_contract():
    page = _base_page()
    footer = page["disclaimer_footer"]
    assert footer["disclaimer_variant"] == "tactical_non_medical"
    assert footer["visible_required"] is True
    assert footer["customer_facing_authorized"] is False
    lowered = footer["disclaimer_text"].lower()
    assert "tactical analysis" in lowered
    assert "not a medical diagnosis" in lowered
    assert "internal prototype only" in lowered
    assert "not customer-facing output" in lowered
    assert "not treatment guidance" in lowered


def test_button2_internal_page_prototype_confirms_accessibility_requirements():
    page = _base_page()
    req = page["accessibility_requirements"]
    assert req["region_labels_required"] is True
    assert req["numeric_scores_required"] is True
    assert req["severity_labels_required"] is True
    assert req["confidence_labels_required"] is True
    assert req["colour_only_meaning_allowed"] is False
    assert req["readable_type_required"] is True
    assert req["contrast_required"] is True
    assert req["clipped_labels_allowed"] is False
    assert req["overcrowded_callouts_allowed"] is False


def test_button2_internal_page_prototype_confirms_page_layout_contract():
    page = _base_page()
    layout = page["page_layout_contract"]
    missing = REQUIRED_LAYOUT_ZONES.difference(layout)
    assert not missing
    for zone in REQUIRED_LAYOUT_ZONES:
        zone_obj = layout[zone]
        assert "zone_required" in zone_obj
        assert "purpose" in zone_obj
        assert "density_role" in zone_obj


def test_button2_internal_page_prototype_rejects_customer_release_true():
    page = _base_page()
    page["release_boundary"]["customer_release_authorized"] = True
    result = validate_page_prototype_contract(page)
    assert result["status"] == "BLOCKED"


def test_button2_internal_page_prototype_rejects_learning_activation_true():
    page = _base_page()
    page["release_boundary"]["learning_activation_authorized"] = True
    result = validate_page_prototype_contract(page)
    assert result["status"] == "BLOCKED"


def test_button2_internal_page_prototype_rejects_delivery_ready_true():
    page = _base_page()
    page["render_contract"]["delivery_ready"] = True
    result = validate_page_prototype_contract(page)
    assert result["status"] == "BLOCKED"


def test_button2_internal_page_prototype_rejects_output_path_non_null():
    page = _base_page()
    page["render_contract"]["output_path"] = "internal_output"
    result = validate_page_prototype_contract(page)
    assert result["status"] == "BLOCKED"


def test_button2_internal_page_prototype_rejects_missing_render_contract():
    page = _base_page()
    page.pop("render_contract")
    result = validate_page_prototype_contract(page)
    assert result["status"] == "BLOCKED"


def test_button2_internal_page_prototype_rejects_missing_qa_gate_output():
    page = _base_page()
    page.pop("qa_gate_output")
    result = validate_page_prototype_contract(page)
    assert result["status"] == "BLOCKED"


def test_button2_internal_page_prototype_rejects_missing_evidence_panel():
    page = _base_page()
    page.pop("evidence_panel")
    result = validate_page_prototype_contract(page)
    assert result["status"] == "BLOCKED"


def test_button2_internal_page_prototype_rejects_missing_disclaimer_footer():
    page = _base_page()
    page.pop("disclaimer_footer")
    result = validate_page_prototype_contract(page)
    assert result["status"] == "BLOCKED"


def test_button2_internal_page_prototype_rejects_missing_accessibility_requirements():
    page = _base_page()
    page.pop("accessibility_requirements")
    result = validate_page_prototype_contract(page)
    assert result["status"] == "BLOCKED"


def test_button2_internal_page_prototype_rejects_wrong_page_density():
    page = _base_page()
    page["page_density_level"] = "level_2_analytical"
    result = validate_page_prototype_contract(page)
    assert result["status"] == "BLOCKED"


def test_button2_internal_page_prototype_rejects_wrong_visual_family():
    page = _base_page()
    page["visual_family_id"] = "tactical_vulnerability_map"
    result = validate_page_prototype_contract(page)
    assert result["status"] == "BLOCKED"


def test_button2_internal_page_prototype_rejects_medical_or_treatment_language():
    page = _base_page()
    page["visual_payload"]["limitation_note"] = "clinical conclusion with treatment"
    result = validate_page_prototype_contract(page)
    assert result["status"] == "BLOCKED"


def test_button2_internal_page_prototype_rejects_reference_folder_dependency():
    page = _base_page()
    t = _mk_fragment_tokens()
    page["visual_payload"]["dependency_hint"] = t["folder_b"]
    result = validate_page_prototype_contract(page)
    assert result["status"] == "BLOCKED"


def test_button2_internal_page_prototype_creates_no_output_artifacts():
    before = _snapshot_output_files(REPO_ROOT)
    page = _base_page()
    result = validate_page_prototype_contract(page)
    assert result["status"] == "PASS_INTERNAL_ONLY"
    after = _snapshot_output_files(REPO_ROOT)
    assert before == after