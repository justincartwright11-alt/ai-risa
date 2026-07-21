from __future__ import annotations

import copy
import pathlib
import typing


def list_visual_qa_required_fields() -> list[str]:
    return [
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
    ]


def list_visual_qa_output_fields() -> list[str]:
    return [
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
    ]


def _safe_release_boundary() -> dict[str, typing.Any]:
    return {
        "release_scope_decision": "INTERNAL_ONLY",
        "customer_release_authorized": False,
        "public_publishing_authorized": False,
        "production_launch_authorized": False,
        "automated_delivery_authorized": False,
        "learning_activation_authorized": False,
    }


def _stringify_scalar(value: typing.Any) -> str:
    if isinstance(value, pathlib.PurePath):
        return value.as_posix()
    return str(value)


def _iter_string_values(value: typing.Any) -> typing.Iterable[str]:
    if isinstance(value, str):
        yield value
        return

    if isinstance(value, pathlib.PurePath):
        yield value.as_posix()
        return

    if isinstance(value, dict):
        for nested in value.values():
            yield from _iter_string_values(nested)
        return

    if isinstance(value, (list, tuple, set)):
        for nested in value:
            yield from _iter_string_values(nested)
        return

    if value is None:
        return

    yield _stringify_scalar(value)


def _contains_reference_dependency(value: typing.Any) -> bool:
    token_a = " ".join(["New", "Visuals"]).lower()
    token_b = "\\".join(["OneDrive", "Pictures"]).lower()
    token_c = "\\".join(["C:", "Users", "jusin", "OneDrive", "Pictures"]).lower()
    for text in _iter_string_values(value):
        lowered = text.lower()
        if token_a in lowered or token_b in lowered or token_c in lowered:
            return True
    return False


def _contains_disallowed_medical_language(value: typing.Any) -> bool:
    allowed_negations = {
        "not medical diagnosis",
        "not a medical diagnosis",
        "not medical diagnostic determination",
        "not injury diagnosis",
        "not an injury diagnosis",
        "not an injury diagnostic determination",
        "tactical analysis not medical diagnosis",
    }
    blocked_terms = [
        "diagnosis",
        "diagnosed",
        "fracture",
        "concussion",
        "torn ligament",
        "treatment recommendation",
        "clinical conclusion",
        "medical claim",
    ]
    for text in _iter_string_values(value):
        lowered = text.lower().replace("_", " ")
        for phrase in allowed_negations:
            lowered = lowered.replace(phrase, "")
        if any(term in lowered for term in blocked_terms):
            return True
    return False


def _as_dict(value: typing.Any) -> dict[str, typing.Any]:
    if isinstance(value, dict):
        return value
    return {}


def _resolve_visual_family_id(qa_input: dict[str, typing.Any], visual_payload: dict[str, typing.Any]) -> str:
    direct = qa_input.get("visual_family_id")
    if isinstance(direct, str) and direct:
        return direct
    payload_value = visual_payload.get("visual_family_id")
    if isinstance(payload_value, str):
        return payload_value
    return ""


def _resolve_page_component_id(
    qa_input: dict[str, typing.Any],
    render_contract: dict[str, typing.Any],
) -> typing.Any:
    direct = qa_input.get("page_component_id")
    if isinstance(direct, str) and direct:
        return direct
    return render_contract.get("page_component_id")


def _has_required_heat_regions(visual_data: dict[str, typing.Any]) -> bool:
    regions = visual_data.get("heat_map_regions")
    if not isinstance(regions, list) or not regions:
        return False
    for region in regions:
        if not isinstance(region, dict):
            return False
        if not region.get("region_label"):
            return False
        score = region.get("exposure_score")
        if not isinstance(score, (int, float)):
            return False
        if not region.get("severity_band"):
            return False
        confidence = region.get("confidence_score")
        if not isinstance(confidence, (int, float)):
            return False
    return True


def _page_density_ok(payload_density: typing.Any) -> bool:
    if not isinstance(payload_density, str):
        return False
    allowed = {
        "level_1_hero",
        "level_2_analytical",
        "level_3_evidence_panel",
    }
    if payload_density not in allowed:
        return False
    if "overload" in payload_density.lower():
        return False
    return True


def _build_output(
    qa_input: dict[str, typing.Any],
    visual_family_id: str,
    page_component_id: typing.Any,
    checks: list[str],
    failed_checks: list[str],
    warning_checks: list[str],
) -> dict[str, typing.Any]:
    qa_status = "PASS_INTERNAL_ONLY" if not failed_checks else "BLOCKED"
    blocked_reasons = [] if qa_status == "PASS_INTERNAL_ONLY" else sorted(set(failed_checks))
    return {
        "qa_status": qa_status,
        "qa_gate_id": qa_input.get("qa_gate_id"),
        "visual_family_id": visual_family_id,
        "page_component_id": page_component_id,
        "artifact_type": qa_input.get("artifact_type"),
        "delivery_ready": False,
        "release_boundary": _safe_release_boundary(),
        "checks": sorted(set(checks)),
        "failed_checks": blocked_reasons,
        "warning_checks": sorted(set(warning_checks)),
        "required_operator_review": True,
        "visual_qa_timestamp_policy": "OPERATOR_CONTROLLED_TIMESTAMP_REQUIRED",
        "blocked_reasons": blocked_reasons,
    }


def validate_visual_qa_gate_contract(qa_input: typing.Any) -> dict[str, typing.Any]:
    checks: list[str] = []
    failed_checks: list[str] = []
    warning_checks: list[str] = []

    if not isinstance(qa_input, dict):
        return _build_output({}, "", None, checks, ["qa_input_not_dict"], warning_checks)

    required_fields = list_visual_qa_required_fields()
    missing_fields = [field for field in required_fields if field not in qa_input]
    if missing_fields:
        failed_checks.append("missing_input_fields")
    else:
        checks.append("required_input_fields_present")

    release_boundary = _as_dict(qa_input.get("release_boundary"))
    expected_boundary = _safe_release_boundary()
    boundary_ok = all(release_boundary.get(k) == v for k, v in expected_boundary.items())
    if boundary_ok:
        checks.append("internal_only_release_boundary")
    else:
        failed_checks.append("unsafe_release_boundary")

    if _contains_reference_dependency(qa_input):
        failed_checks.append("reference_folder_dependency_detected")
    else:
        checks.append("reference_folder_dependency_not_detected")

    if qa_input.get("artifact_path") not in (None, ""):
        failed_checks.append("artifact_path_present_in_contract_only_phase")
    else:
        checks.append("artifact_path_not_present")

    render_contract = _as_dict(qa_input.get("render_contract"))
    if render_contract:
        checks.append("render_contract_present")
    else:
        failed_checks.append("render_contract_missing")

    render_required_values = {
        "render_status": "CONTRACT_VALIDATED_INTERNAL_ONLY",
        "output_type": "CONTRACT_OBJECT_ONLY",
        "output_path": None,
        "delivery_ready": False,
        "evidence_panel_rendered": True,
        "disclaimer_footer_rendered": True,
    }
    for key, expected in render_required_values.items():
        if render_contract.get(key) == expected:
            checks.append("render_contract_" + key + "_ok")
        else:
            failed_checks.append("render_contract_" + key + "_invalid")

    if render_contract.get("blocked_reasons") == []:
        checks.append("render_contract_not_blocked")
    else:
        failed_checks.append("render_contract_blocked_reasons_not_empty")

    if render_contract.get("delivery_ready") is True or qa_input.get("delivery_ready") is True:
        failed_checks.append("delivery_ready_true_before_qa")
    else:
        checks.append("delivery_ready_false_before_qa")

    visual_payload = _as_dict(qa_input.get("visual_payload"))
    if visual_payload:
        checks.append("visual_payload_present")
    else:
        failed_checks.append("visual_payload_missing")

    if visual_payload.get("delivery_ready") is True:
        failed_checks.append("visual_payload_delivery_ready_true")

    if qa_input.get("visual_qa_required") is True:
        checks.append("visual_qa_required_true")
    else:
        failed_checks.append("visual_qa_required_false")

    if qa_input.get("operator_review_status"):
        checks.append("operator_review_status_present")
    else:
        failed_checks.append("operator_review_status_missing")

    visual_data = _as_dict(visual_payload.get("visual_data"))
    visual_family_id = _resolve_visual_family_id(qa_input, visual_payload)
    page_component_id = _resolve_page_component_id(qa_input, render_contract)

    anatomical_family = "anatomical_target_exposure_heat_map"
    if visual_family_id == anatomical_family:
        if render_contract.get("severity_scale_rendered") is True:
            checks.append("severity_scale_rendered_for_anatomical")
        else:
            failed_checks.append("severity_scale_rendered_missing_for_anatomical")

        if visual_payload.get("disclaimer_variant") == "tactical_non_medical":
            checks.append("anatomical_disclaimer_variant_ok")
        else:
            failed_checks.append("anatomical_disclaimer_variant_invalid")

        if visual_data.get("severity_scale_present") is True:
            checks.append("visual_data_severity_scale_present")
        else:
            failed_checks.append("visual_data_severity_scale_missing")

        if _has_required_heat_regions(visual_data):
            checks.append("heat_regions_contract_ok")
        else:
            failed_checks.append("heat_regions_contract_invalid")

        if visual_payload.get("observed_vs_modelled"):
            checks.append("observed_vs_modelled_present")
        else:
            failed_checks.append("observed_vs_modelled_missing")

        confidence_value = visual_payload.get("confidence_score")
        if isinstance(confidence_value, (int, float)):
            checks.append("confidence_score_present")
        else:
            failed_checks.append("confidence_score_missing")

        if visual_payload.get("limitation_note"):
            checks.append("limitation_note_present")
        else:
            failed_checks.append("limitation_note_missing")

    density_value = visual_payload.get("page_density_level")
    if _page_density_ok(density_value):
        checks.append("page_density_level_allowed")
    else:
        failed_checks.append("page_density_level_invalid")

    colour_only_flag = visual_data.get("colour_only_meaning")
    if colour_only_flag is True:
        failed_checks.append("colour_only_meaning_true")
    else:
        checks.append("colour_only_meaning_not_true")

    if visual_data.get("accessibility_failure") is True:
        failed_checks.append("accessibility_failure_true")
    else:
        checks.append("accessibility_failure_not_true")

    if _contains_disallowed_medical_language(visual_payload):
        failed_checks.append("disallowed_medical_language_detected")
    else:
        checks.append("disallowed_medical_language_not_detected")

    output = _build_output(
        qa_input=copy.deepcopy(qa_input),
        visual_family_id=visual_family_id,
        page_component_id=page_component_id,
        checks=checks,
        failed_checks=failed_checks,
        warning_checks=warning_checks,
    )

    output_fields = list_visual_qa_output_fields()
    for field in output_fields:
        if field not in output:
            failed_checks.append("missing_output_field_" + field)
    if output["qa_status"] == "BLOCKED" and not output["blocked_reasons"]:
        failed_checks.append("blocked_without_reasons")

    if failed_checks and output["qa_status"] != "BLOCKED":
        output["qa_status"] = "BLOCKED"
        output["failed_checks"] = sorted(set(failed_checks))
        output["blocked_reasons"] = sorted(set(failed_checks))

    return output


def build_visual_qa_gate_output(qa_input: typing.Any) -> dict[str, typing.Any]:
    return validate_visual_qa_gate_contract(qa_input)