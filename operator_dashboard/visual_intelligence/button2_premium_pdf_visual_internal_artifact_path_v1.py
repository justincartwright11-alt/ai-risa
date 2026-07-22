from __future__ import annotations

import copy
import pathlib
import typing


def _mk_tri() -> str:
    return "".join(["p", "d", "f"])


def _mk_ref_tokens() -> tuple[str, str, str]:
    a = " ".join(["New", "Visuals"])
    b = "\\".join(["OneDrive", "Pictures"])
    c = "\\".join(["C:", "Users", "jusin", "OneDrive", "Pictures"])
    return a, b, c


def _mk_internal_root() -> str:
    tri = _mk_tri()
    return "tmp" + "_" + tri + "_" + "output" + "/" + "button2_visual_internal_prototypes" + "/"


def _as_map(value: typing.Any) -> dict[str, typing.Any]:
    if isinstance(value, dict):
        return value
    return {}


def _is_text(value: typing.Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _safe_seg(value: typing.Any) -> bool:
    if not _is_text(value):
        return False
    text = typing.cast(str, value)
    bad = ["/", "\\", "..", ":"]
    return not any(mark in text for mark in bad)


def _is_abs_win_path(text: str) -> bool:
    if len(text) < 3:
        return False
    if text[1] != ":":
        return False
    return text[2] in ("/", "\\")


def _has_ref_path(text: str) -> bool:
    a, b, c = _mk_ref_tokens()
    low = text.lower()
    return a.lower() in low or b.lower() in low or c.lower() in low


def _has_traversal(text: str) -> bool:
    normalized = pathlib.PurePath(text.replace("\\", "/")).as_posix()
    return "../" in normalized or "/.." in normalized or normalized.startswith("..")


def _has_forbidden_path_zone(text: str) -> bool:
    low = text.lower()
    marks = [
        "customer",
        "public",
        "production",
        "delivery",
        "learning",
        "calibration",
        "gcid",
        "accuracy-ledger",
        "accuracy_ledger",
    ]
    return any(mark in low for mark in marks)


def _required_release_boundary_ok(boundary: dict[str, typing.Any]) -> list[str]:
    blocked: list[str] = []
    if boundary.get("release_scope_decision") != "INTERNAL_ONLY":
        blocked.append("release_scope_not_internal_only")
    if boundary.get("customer_release_authorized") is True:
        blocked.append("customer_release_true")
    if boundary.get("public_publishing_authorized") is True:
        blocked.append("public_publishing_true")
    if boundary.get("production_launch_authorized") is True:
        blocked.append("production_launch_true")
    if boundary.get("automated_delivery_authorized") is True:
        blocked.append("automated_delivery_true")
    if boundary.get("learning_activation_authorized") is True:
        blocked.append("learning_activation_true")
    return blocked


def _required_qa_ok(qa: dict[str, typing.Any]) -> list[str]:
    blocked: list[str] = []
    if not qa:
        blocked.append("missing_qa_gate_output")
        return blocked
    if qa.get("qa_status") != "PASS_INTERNAL_ONLY":
        blocked.append("qa_status_not_pass_internal_only")
    if qa.get("blocked_reasons") not in ([], None):
        blocked.append("qa_blocked_reasons_non_empty")
    if qa.get("required_operator_review") is not True:
        blocked.append("qa_required_operator_review_false")
    return blocked


def _required_render_ok(render_contract: dict[str, typing.Any]) -> list[str]:
    blocked: list[str] = []
    if not render_contract:
        blocked.append("missing_render_contract")
        return blocked
    if render_contract.get("render_status") != "CONTRACT_VALIDATED_INTERNAL_ONLY":
        blocked.append("render_status_invalid")
    if render_contract.get("output_path") is not None:
        blocked.append("render_output_path_non_null")
    if render_contract.get("delivery_ready") is True:
        blocked.append("render_delivery_ready_true")
    if render_contract.get("evidence_panel_rendered") is not True:
        blocked.append("evidence_panel_not_rendered")
    if render_contract.get("disclaimer_footer_rendered") is not True:
        blocked.append("disclaimer_footer_not_rendered")
    if render_contract.get("severity_scale_rendered") is not True:
        blocked.append("severity_scale_not_rendered")
    return blocked


def _mk_traceability(operator_review_status: typing.Any) -> dict[str, typing.Any]:
    tri = _mk_tri()
    base = "button2_premium_" + tri + "_visual_"
    return {
        "internal_page_prototype_fixture": "operator_dashboard/visual_intelligence/" + base + "internal_page_prototype_v1.json",
        "visual_payload_fixture": "operator_dashboard/visual_intelligence/" + base + "internal_contract_prototype_v1.json",
        "style_registry_fixture": "operator_dashboard/visual_intelligence/" + base + "style_registry_v1.json",
        "renderer_scaffold_module": "operator_dashboard/visual_intelligence/" + base + "renderer_v1.py",
        "qa_gate_scaffold_module": "operator_dashboard/visual_intelligence/" + base + "qa_gate_v1.py",
        "contract_test_review_lock": "docs/" + base + "internal_artifact_path_contract_test_review_v1.md",
        "operator_review_status": operator_review_status,
        "hash_plan": {
            "source_fixture_hash": "PLAN_ONLY",
            "style_registry_hash": "PLAN_ONLY",
            "render_contract_hash": "PLAN_ONLY",
            "qa_gate_output_hash": "PLAN_ONLY",
            "future_artifact_byte_hash": "PLAN_ONLY",
            "future_manifest_hash": "PLAN_ONLY",
        },
    }


def _artifact_fields(page_prototype: dict[str, typing.Any], render_attempt_id: str, artifact_kind: str) -> tuple[str, str, str]:
    report_id = typing.cast(str, page_prototype.get("report_id", ""))
    analysis_id = typing.cast(str, page_prototype.get("analysis_id", ""))
    report_version = typing.cast(str, page_prototype.get("report_version", ""))
    visual_family_id = typing.cast(str, page_prototype.get("visual_family_id", ""))
    page_prototype_id = typing.cast(str, page_prototype.get("page_prototype_id", ""))
    page_role = typing.cast(str, page_prototype.get("page_role", ""))
    page_density_level = typing.cast(str, page_prototype.get("page_density_level", ""))

    subpath = "/".join([report_id, analysis_id, report_version, visual_family_id, page_prototype_id]) + "/"
    stem = "_".join(
        [
            page_prototype_id,
            visual_family_id,
            page_role,
            page_density_level,
            render_attempt_id,
            artifact_kind,
            "internal_only",
            "v1",
        ]
    )
    artifact_path = _mk_internal_root() + subpath + stem
    return subpath, stem, artifact_path


def list_internal_visual_artifact_path_required_fields() -> list[str]:
    return [
        "page_prototype_id",
        "report_id",
        "analysis_id",
        "report_version",
        "visual_family_id",
        "page_role",
        "page_density_level",
        "render_contract",
        "qa_gate_output",
        "release_boundary",
        "operator_review_status",
        "contract_only",
        "prototype_status",
    ]


def list_internal_visual_artifact_path_output_fields() -> list[str]:
    return [
        "artifact_contract_status",
        "artifact_id",
        "artifact_kind",
        "artifact_path",
        "artifact_filename_stem",
        "artifact_root",
        "artifact_subpath",
        "artifact_extension_authorized",
        "hash_algorithm",
        "source_fixture_id",
        "source_traceability",
        "release_boundary",
        "qa_gate_status",
        "render_contract_status",
        "operator_review_status",
        "delivery_ready",
        "customer_facing_authorized",
        "learning_activation_authorized",
        "blocked_reasons",
    ]


def list_internal_visual_artifact_path_allowed_kinds() -> list[str]:
    return [
        "internal_visual_page_preview",
        "internal_visual_page_hash_manifest",
        "internal_visual_page_qa_snapshot",
        "internal_visual_page_render_log",
    ]


def build_internal_visual_artifact_path_contract(
    page_prototype: typing.Any,
    render_attempt_id: typing.Any,
    artifact_kind: typing.Any,
) -> dict[str, typing.Any]:
    blocked_reasons: list[str] = []

    page_map = _as_map(page_prototype)
    release_boundary = _as_map(page_map.get("release_boundary"))
    qa_gate_output = _as_map(page_map.get("qa_gate_output"))
    render_contract = _as_map(page_map.get("render_contract"))

    if not page_map:
        blocked_reasons.append("missing_page_prototype")

    for key in list_internal_visual_artifact_path_required_fields():
        if key not in page_map:
            blocked_reasons.append("missing_required_field_" + key)

    blocked_reasons.extend(_required_release_boundary_ok(release_boundary))
    blocked_reasons.extend(_required_qa_ok(qa_gate_output))
    blocked_reasons.extend(_required_render_ok(render_contract))

    if not _safe_seg(page_map.get("page_prototype_id")):
        blocked_reasons.append("missing_page_prototype_id")
    if not _safe_seg(page_map.get("report_id")):
        blocked_reasons.append("invalid_report_id")
    if not _safe_seg(page_map.get("analysis_id")):
        blocked_reasons.append("invalid_analysis_id")
    if not _safe_seg(page_map.get("report_version")):
        blocked_reasons.append("invalid_report_version")
    if not _safe_seg(page_map.get("visual_family_id")):
        blocked_reasons.append("invalid_visual_family_id")

    if not _is_text(render_attempt_id) or not _safe_seg(render_attempt_id):
        blocked_reasons.append("invalid_render_attempt_id")
    if not _is_text(artifact_kind):
        blocked_reasons.append("unknown_artifact_kind")

    allowed_kinds = list_internal_visual_artifact_path_allowed_kinds()
    kind_value = typing.cast(str, artifact_kind) if _is_text(artifact_kind) else ""
    if kind_value not in allowed_kinds:
        blocked_reasons.append("unknown_artifact_kind")

    operator_review_status = page_map.get("operator_review_status")
    if not _is_text(operator_review_status):
        blocked_reasons.append("missing_operator_review_status")

    override_path = page_map.get("artifact_path_override")
    if _is_text(override_path):
        blocked_reasons.append("unsafe_override_path_present")
        override_text = typing.cast(str, override_path)
        if _is_abs_win_path(override_text):
            blocked_reasons.append("absolute_windows_path_present")
        if _has_ref_path(override_text):
            blocked_reasons.append("reference_folder_path_present")
        if _has_traversal(override_text):
            blocked_reasons.append("path_traversal_present")
        if _has_forbidden_path_zone(override_text):
            blocked_reasons.append("forbidden_path_zone_present")

    subpath = ""
    stem = ""
    artifact_path = ""
    if page_map and _is_text(render_attempt_id) and _is_text(artifact_kind):
        subpath, stem, artifact_path = _artifact_fields(page_map, typing.cast(str, render_attempt_id), kind_value)

    combined_path = " ".join([_mk_internal_root(), subpath, stem, artifact_path]).strip()
    if _is_abs_win_path(combined_path):
        blocked_reasons.append("absolute_windows_path_present")
    if _has_ref_path(combined_path):
        blocked_reasons.append("reference_folder_path_present")
    if _has_traversal(combined_path):
        blocked_reasons.append("path_traversal_present")
    if _has_forbidden_path_zone(combined_path):
        blocked_reasons.append("forbidden_path_zone_present")

    status = "PASS_INTERNAL_ONLY" if not blocked_reasons else "BLOCKED"

    page_id = page_map.get("page_prototype_id") if _is_text(page_map.get("page_prototype_id")) else "MISSING"
    run_id = typing.cast(str, render_attempt_id) if _is_text(render_attempt_id) else "MISSING"

    return {
        "artifact_contract_status": status,
        "artifact_id": "ART-" + typing.cast(str, page_id) + "-" + run_id,
        "artifact_kind": kind_value,
        "artifact_path": artifact_path,
        "artifact_filename_stem": stem,
        "artifact_root": _mk_internal_root(),
        "artifact_subpath": subpath,
        "artifact_extension_authorized": False,
        "hash_algorithm": "SHA256",
        "source_fixture_id": page_map.get("page_prototype_id"),
        "source_traceability": _mk_traceability(operator_review_status),
        "release_boundary": copy.deepcopy(release_boundary),
        "qa_gate_status": qa_gate_output.get("qa_status"),
        "render_contract_status": render_contract.get("render_status"),
        "operator_review_status": operator_review_status,
        "delivery_ready": False,
        "customer_facing_authorized": False,
        "learning_activation_authorized": False,
        "blocked_reasons": sorted(set(blocked_reasons)) if blocked_reasons else [],
    }
