from __future__ import annotations

import typing


def _mk_ref_tokens() -> tuple[str, str, str]:
    a = " ".join(["New", "Visuals"])
    b = "\\".join(["OneDrive", "Pictures"])
    c = "\\".join(["C:", "Users", "jusin", "OneDrive", "Pictures"])
    return a, b, c


def _as_map(value: typing.Any) -> dict[str, typing.Any]:
    if isinstance(value, dict):
        return value
    return {}


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
    norm = text.replace("\\", "/")
    return "../" in norm or "/.." in norm or norm.startswith("..")


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


def _normalized_blocked_reasons(value: typing.Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            text = str(item).strip()
            if text:
                out.append(text)
        return out
    text = str(value).strip()
    return [text] if text else []


def list_renderer_artifact_path_integration_required_fields() -> list[str]:
    return [
        "render_contract",
        "artifact_path_contract",
        "qa_gate_output",
        "render_status",
        "output_path",
        "delivery_ready",
        "evidence_panel_rendered",
        "disclaimer_footer_rendered",
        "severity_scale_rendered",
        "artifact_contract_status",
        "artifact_path",
        "artifact_filename_stem",
        "artifact_root",
        "artifact_subpath",
        "artifact_extension_authorized",
        "customer_facing_authorized",
        "learning_activation_authorized",
        "source_traceability",
        "blocked_reasons",
        "qa_status",
        "required_operator_review",
        "customer_release_authorized",
    ]


def list_renderer_artifact_path_integration_output_fields() -> list[str]:
    return [
        "integration_status",
        "artifact_contract_status",
        "render_contract_status",
        "qa_gate_status",
        "artifact_path",
        "artifact_filename_stem",
        "artifact_root",
        "artifact_subpath",
        "artifact_extension_authorized",
        "delivery_ready",
        "customer_facing_authorized",
        "learning_activation_authorized",
        "source_traceability",
        "blocked_reasons",
    ]


def build_renderer_artifact_path_integration_contract(render_contract, artifact_path_contract, qa_gate_output):
    blocked: list[str] = []

    r = _as_map(render_contract)
    a = _as_map(artifact_path_contract)
    q = _as_map(qa_gate_output)

    if not r:
        blocked.append("missing_render_contract")
    if not a:
        blocked.append("missing_artifact_path_contract")
    if not q:
        blocked.append("missing_qa_gate_output")

    if r.get("render_status") != "CONTRACT_VALIDATED_INTERNAL_ONLY":
        blocked.append("render_status_invalid")
    if r.get("output_path") is not None:
        blocked.append("render_output_path_non_null")
    if r.get("delivery_ready") is True:
        blocked.append("render_delivery_ready_true")
    if r.get("evidence_panel_rendered") is not True:
        blocked.append("evidence_panel_not_rendered")
    if r.get("disclaimer_footer_rendered") is not True:
        blocked.append("disclaimer_footer_not_rendered")
    if r.get("severity_scale_rendered") is not True:
        blocked.append("severity_scale_not_rendered")

    if q.get("qa_status") != "PASS_INTERNAL_ONLY":
        blocked.append("qa_status_not_pass_internal_only")
    if q.get("required_operator_review") is not True:
        blocked.append("qa_required_operator_review_false")

    q_blocked = _normalized_blocked_reasons(q.get("blocked_reasons"))
    if q_blocked:
        blocked.append("qa_blocked_reasons_non_empty")
        blocked.extend(q_blocked)

    if q.get("customer_release_authorized") is True:
        blocked.append("qa_customer_release_true")
    if q.get("learning_activation_authorized") is True:
        blocked.append("qa_learning_activation_true")

    q_boundary = _as_map(q.get("release_boundary"))
    if q_boundary.get("customer_release_authorized") is True:
        blocked.append("qa_release_boundary_customer_release_true")
    if q_boundary.get("public_publishing_authorized") is True:
        blocked.append("qa_release_boundary_public_publishing_true")
    if q_boundary.get("production_launch_authorized") is True:
        blocked.append("qa_release_boundary_production_launch_true")
    if q_boundary.get("automated_delivery_authorized") is True:
        blocked.append("qa_release_boundary_automated_delivery_true")
    if q_boundary.get("learning_activation_authorized") is True:
        blocked.append("qa_release_boundary_learning_activation_true")

    if a.get("artifact_contract_status") != "PASS_INTERNAL_ONLY":
        blocked.append("artifact_contract_not_pass_internal_only")
    if a.get("artifact_extension_authorized") is True:
        blocked.append("artifact_extension_authorized_true")
    if a.get("delivery_ready") is True:
        blocked.append("artifact_delivery_ready_true")
    if a.get("customer_facing_authorized") is True:
        blocked.append("artifact_customer_facing_authorized_true")
    if a.get("learning_activation_authorized") is True:
        blocked.append("artifact_learning_activation_authorized_true")

    a_blocked = _normalized_blocked_reasons(a.get("blocked_reasons"))
    if a_blocked:
        blocked.append("artifact_blocked_reasons_non_empty")
        blocked.extend(a_blocked)

    if a.get("artifact_path_override") not in (None, ""):
        blocked.append("unsafe_override_path_present")

    trace = a.get("source_traceability")
    if not isinstance(trace, dict) or not trace:
        blocked.append("missing_source_traceability")

    path_text = str(a.get("artifact_path", ""))
    if _is_abs_win_path(path_text):
        blocked.append("absolute_windows_path_present")
    if _has_ref_path(path_text):
        blocked.append("reference_folder_path_present")
    if _has_traversal(path_text):
        blocked.append("path_traversal_present")
    if _has_forbidden_path_zone(path_text):
        blocked.append("forbidden_path_zone_present")

    status = "PASS_INTERNAL_ONLY" if not blocked else "BLOCKED"

    return {
        "integration_status": status,
        "artifact_contract_status": a.get("artifact_contract_status"),
        "render_contract_status": r.get("render_status"),
        "qa_gate_status": q.get("qa_status"),
        "artifact_path": a.get("artifact_path"),
        "artifact_filename_stem": a.get("artifact_filename_stem"),
        "artifact_root": a.get("artifact_root"),
        "artifact_subpath": a.get("artifact_subpath"),
        "artifact_extension_authorized": False,
        "delivery_ready": False,
        "customer_facing_authorized": False,
        "learning_activation_authorized": False,
        "source_traceability": trace,
        "blocked_reasons": sorted(set(blocked)) if blocked else [],
    }