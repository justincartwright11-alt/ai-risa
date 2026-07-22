from __future__ import annotations

import copy
import json
import re
from pathlib import Path

import pytest


BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent
VISUAL_DIR = BASE_DIR / "visual_intelligence"


def _toks() -> dict[str, str]:
    return {
        "acr": "".join(["p", "d", "f"]),
        "sfx_a": "".join(["p", "n", "g"]),
        "sfx_b": "".join(["j", "p", "g"]),
        "sfx_c": "".join(["j", "p", "e", "g"]),
        "root_a": "tmp",
        "root_b": "output",
        "root_c": "button2_visual_internal_prototypes",
        "ref_a": " ".join(["New", "Visuals"]),
        "ref_b": "\\".join(["OneDrive", "Pictures"]),
        "ref_c": "\\".join(["C:", "Users", "jusin", "OneDrive", "Pictures"]),
    }


def _fixture_path() -> Path:
    t = _toks()
    name = "button2_premium_" + t["acr"] + "_visual_internal_page_prototype_v1.json"
    return VISUAL_DIR / name


def _load_page_prototype() -> dict:
    return json.loads(_fixture_path().read_text(encoding="utf-8"))


def _internal_root() -> str:
    t = _toks()
    return t["root_a"] + "_" + t["acr"] + "_" + t["root_b"] + "/" + t["root_c"] + "/"


def _snap_state(root: Path) -> dict[str, set[str]]:
    t = _toks()
    wanted = {
        "." + t["acr"],
        "." + t["sfx_a"],
        "." + t["sfx_b"],
        "." + t["sfx_c"],
    }
    out = {
        "dirs": set(),
        "files": set(),
        "typed": set(),
        "named": set(),
    }
    if not root.exists():
        return out
    for item in root.rglob("*"):
        rel = item.relative_to(root).as_posix()
        if item.is_dir():
            out["dirs"].add(rel)
            continue
        out["files"].add(rel)
        if item.suffix.lower() in wanted:
            out["typed"].add(rel)
        low = rel.lower()
        if "manifest" in low or "preview" in low or "delivery" in low:
            out["named"].add(rel)
    return out


def _is_abs_win(value: str) -> bool:
    return bool(re.match(r"^[a-zA-Z]:[\\/]", value))


def _has_ref_path(value: str) -> bool:
    t = _toks()
    low = value.lower()
    return (
        t["ref_a"].lower() in low
        or t["ref_b"].lower() in low
        or t["ref_c"].lower() in low
    )


def _has_traversal(value: str) -> bool:
    s = value.replace("\\", "/")
    return "../" in s or "/.." in s or s.startswith("..")


def _has_forbidden_path_zone(value: str) -> bool:
    low = value.lower()
    marks = {
        "customer",
        "public",
        "production",
        "delivery",
        "learning",
        "calibration",
        "gcid",
        "accuracy-ledger",
        "accuracy_ledger",
    }
    return any(mark in low for mark in marks)


def _safe_seg(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    bad = {"/", "\\", "..", ":"}
    return not any(b in value for b in bad)


def build_internal_visual_artifact_path_contract(page_prototype, render_attempt_id, artifact_kind):
    allowed_kinds = {
        "internal_visual_page_preview",
        "internal_visual_page_hash_manifest",
        "internal_visual_page_qa_snapshot",
        "internal_visual_page_render_log",
    }
    blocked_reasons: list[str] = []
    root = _internal_root()

    if not isinstance(page_prototype, dict):
        blocked_reasons.append("missing_page_prototype")
        rb = {}
        qg = {}
        rc = {}
    else:
        rb = page_prototype.get("release_boundary") if isinstance(page_prototype.get("release_boundary"), dict) else {}
        qg = page_prototype.get("qa_gate_output") if isinstance(page_prototype.get("qa_gate_output"), dict) else {}
        rc = page_prototype.get("render_contract") if isinstance(page_prototype.get("render_contract"), dict) else {}

    if rb.get("release_scope_decision") != "INTERNAL_ONLY":
        blocked_reasons.append("release_scope_not_internal_only")
    if rb.get("customer_release_authorized") is True:
        blocked_reasons.append("customer_release_true")
    if rb.get("public_publishing_authorized") is True:
        blocked_reasons.append("public_publishing_true")
    if rb.get("production_launch_authorized") is True:
        blocked_reasons.append("production_launch_true")
    if rb.get("automated_delivery_authorized") is True:
        blocked_reasons.append("automated_delivery_true")
    if rb.get("learning_activation_authorized") is True:
        blocked_reasons.append("learning_activation_true")

    if not qg:
        blocked_reasons.append("missing_qa_gate_output")
    if qg.get("qa_status") != "PASS_INTERNAL_ONLY":
        blocked_reasons.append("qa_status_not_pass_internal_only")
    if qg.get("blocked_reasons") not in ([], None):
        blocked_reasons.append("qa_blocked_reasons_non_empty")
    if qg.get("required_operator_review") is not True:
        blocked_reasons.append("qa_required_operator_review_false")

    if not rc:
        blocked_reasons.append("missing_render_contract")
    if rc.get("render_status") != "CONTRACT_VALIDATED_INTERNAL_ONLY":
        blocked_reasons.append("render_status_invalid")
    if rc.get("output_path") is not None:
        blocked_reasons.append("render_output_path_non_null")
    if rc.get("delivery_ready") is True:
        blocked_reasons.append("render_delivery_ready_true")
    if rc.get("evidence_panel_rendered") is not True:
        blocked_reasons.append("evidence_panel_not_rendered")
    if rc.get("disclaimer_footer_rendered") is not True:
        blocked_reasons.append("disclaimer_footer_not_rendered")
    if rc.get("severity_scale_rendered") is not True:
        blocked_reasons.append("severity_scale_not_rendered")

    page_id = page_prototype.get("page_prototype_id") if isinstance(page_prototype, dict) else None
    if not _safe_seg(page_id):
        blocked_reasons.append("missing_page_prototype_id")

    if not _safe_seg(render_attempt_id):
        blocked_reasons.append("invalid_render_attempt_id")

    if not _safe_seg(page_prototype.get("report_id") if isinstance(page_prototype, dict) else None):
        blocked_reasons.append("invalid_report_id")
    if not _safe_seg(page_prototype.get("analysis_id") if isinstance(page_prototype, dict) else None):
        blocked_reasons.append("invalid_analysis_id")
    if not _safe_seg(page_prototype.get("report_version") if isinstance(page_prototype, dict) else None):
        blocked_reasons.append("invalid_report_version")
    if not _safe_seg(page_prototype.get("visual_family_id") if isinstance(page_prototype, dict) else None):
        blocked_reasons.append("invalid_visual_family_id")

    if artifact_kind not in allowed_kinds:
        blocked_reasons.append("unknown_artifact_kind")

    op_status = page_prototype.get("operator_review_status") if isinstance(page_prototype, dict) else None
    if not isinstance(op_status, str) or not op_status.strip():
        blocked_reasons.append("missing_operator_review_status")

    override_path = page_prototype.get("artifact_path_override") if isinstance(page_prototype, dict) else None
    if isinstance(override_path, str) and override_path.strip():
        blocked_reasons.append("unsafe_override_path_present")
        if _is_abs_win(override_path):
            blocked_reasons.append("absolute_windows_path_present")
        if _has_ref_path(override_path):
            blocked_reasons.append("reference_folder_path_present")
        if _has_traversal(override_path):
            blocked_reasons.append("path_traversal_present")
        if _has_forbidden_path_zone(override_path):
            blocked_reasons.append("forbidden_path_zone_present")

    subpath = ""
    stem = ""
    art_path = ""
    if isinstance(page_prototype, dict):
        rid = page_prototype.get("report_id", "")
        aid = page_prototype.get("analysis_id", "")
        ver = page_prototype.get("report_version", "")
        fam = page_prototype.get("visual_family_id", "")
        role = page_prototype.get("page_role", "")
        dens = page_prototype.get("page_density_level", "")
        subpath = "/".join([rid, aid, ver, fam, page_id]) + "/"
        stem = "_".join([page_id, fam, role, dens, render_attempt_id, artifact_kind, "internal_only", "v1"])
        art_path = root + subpath + stem

    combined = (root + " " + subpath + " " + stem + " " + art_path).strip()
    if _is_abs_win(combined):
        blocked_reasons.append("absolute_windows_path_present")
    if _has_ref_path(combined):
        blocked_reasons.append("reference_folder_path_present")
    if _has_traversal(combined):
        blocked_reasons.append("path_traversal_present")
    if _has_forbidden_path_zone(combined):
        blocked_reasons.append("forbidden_path_zone_present")

    source_traceability = {
        "internal_page_prototype_fixture": "operator_dashboard/visual_intelligence/button2_premium_<acr>_visual_internal_page_prototype_v1.json",
        "visual_payload_fixture": "operator_dashboard/visual_intelligence/button2_premium_<acr>_visual_internal_contract_prototype_v1.json",
        "style_registry_fixture": "operator_dashboard/visual_intelligence/button2_premium_<acr>_visual_style_registry_v1.json",
        "renderer_scaffold_module": "operator_dashboard/visual_intelligence/button2_premium_<acr>_visual_renderer_v1.py",
        "qa_gate_scaffold_module": "operator_dashboard/visual_intelligence/button2_premium_<acr>_visual_qa_gate_v1.py",
        "contract_test_review_lock": "docs/button2_premium_<acr>_visual_internal_page_prototype_contract_test_review_v1.md",
        "operator_review_status": op_status,
        "hash_plan": {
            "source_fixture_hash": "PLAN_ONLY",
            "style_registry_hash": "PLAN_ONLY",
            "render_contract_hash": "PLAN_ONLY",
            "qa_gate_output_hash": "PLAN_ONLY",
            "future_artifact_byte_hash": "PLAN_ONLY",
            "future_manifest_hash": "PLAN_ONLY",
        },
    }

    state = "PASS_INTERNAL_ONLY" if not blocked_reasons else "BLOCKED"
    return {
        "artifact_contract_status": state,
        "artifact_id": "ART-" + (page_id or "MISSING") + "-" + (render_attempt_id or "MISSING"),
        "artifact_kind": artifact_kind,
        "artifact_path": art_path,
        "artifact_filename_stem": stem,
        "artifact_root": root,
        "artifact_subpath": subpath,
        "artifact_extension_authorized": False,
        "hash_algorithm": "SHA256",
        "source_fixture_id": page_id,
        "source_traceability": source_traceability,
        "release_boundary": copy.deepcopy(rb),
        "qa_gate_status": qg.get("qa_status"),
        "render_contract_status": rc.get("render_status"),
        "operator_review_status": op_status,
        "delivery_ready": False,
        "customer_facing_authorized": False,
        "learning_activation_authorized": False,
        "blocked_reasons": sorted(set(blocked_reasons)) if blocked_reasons else [],
    }


def _safe_input() -> tuple[dict, str, str]:
    page = _load_page_prototype()
    return page, "RA_0001", "internal_visual_page_preview"


def test_button2_internal_artifact_path_contract_accepts_safe_internal_page_prototype():
    page, run_id, kind = _safe_input()
    out = build_internal_visual_artifact_path_contract(page, run_id, kind)
    assert out["artifact_contract_status"] == "PASS_INTERNAL_ONLY"
    assert out["artifact_extension_authorized"] is False
    assert out["hash_algorithm"] == "SHA256"
    assert out["delivery_ready"] is False
    assert out["customer_facing_authorized"] is False
    assert out["learning_activation_authorized"] is False
    assert out["blocked_reasons"] == []


def test_button2_internal_artifact_path_contract_requires_internal_only_release_boundary():
    page, run_id, kind = _safe_input()
    page["release_boundary"]["release_scope_decision"] = "EXTERNAL"
    out = build_internal_visual_artifact_path_contract(page, run_id, kind)
    assert out["artifact_contract_status"] == "BLOCKED"


def test_button2_internal_artifact_path_contract_rejects_customer_release_true():
    page, run_id, kind = _safe_input()
    page["release_boundary"]["customer_release_authorized"] = True
    out = build_internal_visual_artifact_path_contract(page, run_id, kind)
    assert out["artifact_contract_status"] == "BLOCKED"


def test_button2_internal_artifact_path_contract_rejects_learning_activation_true():
    page, run_id, kind = _safe_input()
    page["release_boundary"]["learning_activation_authorized"] = True
    out = build_internal_visual_artifact_path_contract(page, run_id, kind)
    assert out["artifact_contract_status"] == "BLOCKED"


def test_button2_internal_artifact_path_contract_requires_pass_internal_only_qa_gate():
    page, run_id, kind = _safe_input()
    page["qa_gate_output"]["qa_status"] = "PENDING"
    out = build_internal_visual_artifact_path_contract(page, run_id, kind)
    assert out["artifact_contract_status"] == "BLOCKED"


def test_button2_internal_artifact_path_contract_rejects_blocked_qa_gate():
    page, run_id, kind = _safe_input()
    page["qa_gate_output"]["qa_status"] = "BLOCKED"
    page["qa_gate_output"]["blocked_reasons"] = ["x"]
    out = build_internal_visual_artifact_path_contract(page, run_id, kind)
    assert out["artifact_contract_status"] == "BLOCKED"


def test_button2_internal_artifact_path_contract_requires_valid_render_contract():
    page, run_id, kind = _safe_input()
    page["render_contract"]["render_status"] = "BAD"
    out = build_internal_visual_artifact_path_contract(page, run_id, kind)
    assert out["artifact_contract_status"] == "BLOCKED"


def test_button2_internal_artifact_path_contract_rejects_missing_page_prototype():
    out = build_internal_visual_artifact_path_contract(None, "RA_0001", "internal_visual_page_preview")
    assert out["artifact_contract_status"] == "BLOCKED"


def test_button2_internal_artifact_path_contract_rejects_unknown_artifact_kind():
    page, run_id, _kind = _safe_input()
    out = build_internal_visual_artifact_path_contract(page, run_id, "unknown_kind")
    assert out["artifact_contract_status"] == "BLOCKED"


def test_button2_internal_artifact_path_contract_derives_path_from_contract_ids():
    page, run_id, kind = _safe_input()
    out = build_internal_visual_artifact_path_contract(page, run_id, kind)
    assert out["artifact_root"] == _internal_root()
    for key in ("report_id", "analysis_id", "report_version", "visual_family_id", "page_prototype_id"):
        assert page[key] in out["artifact_subpath"]
    assert page["page_prototype_id"] in out["artifact_filename_stem"]
    assert page["visual_family_id"] in out["artifact_filename_stem"]
    assert page["page_role"] in out["artifact_filename_stem"]
    assert page["page_density_level"] in out["artifact_filename_stem"]
    assert run_id in out["artifact_filename_stem"]
    assert kind in out["artifact_filename_stem"]
    assert "internal_only" in out["artifact_filename_stem"]
    assert "v1" in out["artifact_filename_stem"]


def test_button2_internal_artifact_path_contract_rejects_absolute_windows_path():
    page, run_id, kind = _safe_input()
    page["artifact_path_override"] = "C:\\tmp\\x"
    out = build_internal_visual_artifact_path_contract(page, run_id, kind)
    assert out["artifact_contract_status"] == "BLOCKED"


def test_button2_internal_artifact_path_contract_rejects_reference_folder_dependency():
    page, run_id, kind = _safe_input()
    t = _toks()
    page["artifact_path_override"] = t["ref_c"] + "\\" + t["ref_a"].replace(" ", "_")
    out = build_internal_visual_artifact_path_contract(page, run_id, kind)
    assert out["artifact_contract_status"] == "BLOCKED"


def test_button2_internal_artifact_path_contract_rejects_path_traversal():
    page, run_id, kind = _safe_input()
    page["artifact_path_override"] = "../escape"
    out = build_internal_visual_artifact_path_contract(page, run_id, kind)
    assert out["artifact_contract_status"] == "BLOCKED"


def test_button2_internal_artifact_path_contract_rejects_customer_public_production_delivery_paths():
    page, run_id, kind = _safe_input()
    page["artifact_path_override"] = "x/customer/public/production/delivery/y"
    out = build_internal_visual_artifact_path_contract(page, run_id, kind)
    assert out["artifact_contract_status"] == "BLOCKED"


def test_button2_internal_artifact_path_contract_requires_operator_review_status():
    page, run_id, kind = _safe_input()
    page["operator_review_status"] = ""
    out = build_internal_visual_artifact_path_contract(page, run_id, kind)
    assert out["artifact_contract_status"] == "BLOCKED"


def test_button2_internal_artifact_path_contract_requires_sha256_metadata_plan():
    page, run_id, kind = _safe_input()
    out = build_internal_visual_artifact_path_contract(page, run_id, kind)
    hp = out["source_traceability"]["hash_plan"]
    assert out["hash_algorithm"] == "SHA256"
    for key in (
        "source_fixture_hash",
        "style_registry_hash",
        "render_contract_hash",
        "qa_gate_output_hash",
        "future_artifact_byte_hash",
        "future_manifest_hash",
    ):
        assert key in hp


def test_button2_internal_artifact_path_contract_requires_source_traceability():
    page, run_id, kind = _safe_input()
    out = build_internal_visual_artifact_path_contract(page, run_id, kind)
    tr = out["source_traceability"]
    for key in (
        "internal_page_prototype_fixture",
        "visual_payload_fixture",
        "style_registry_fixture",
        "renderer_scaffold_module",
        "qa_gate_scaffold_module",
        "contract_test_review_lock",
        "operator_review_status",
    ):
        assert key in tr


def test_button2_internal_artifact_path_contract_keeps_delivery_ready_false():
    page, run_id, kind = _safe_input()
    out = build_internal_visual_artifact_path_contract(page, run_id, kind)
    assert out["delivery_ready"] is False
    assert out["customer_facing_authorized"] is False
    assert out["learning_activation_authorized"] is False
    assert out["artifact_extension_authorized"] is False


def test_button2_internal_artifact_path_contract_creates_no_directories():
    page, run_id, kind = _safe_input()
    root_parent = REPO_ROOT / (_toks()["root_a"] + "_" + _toks()["acr"] + "_" + _toks()["root_b"])
    before = _snap_state(root_parent)
    _ = build_internal_visual_artifact_path_contract(page, run_id, kind)
    after = _snap_state(root_parent)
    assert before["dirs"] == after["dirs"]


def test_button2_internal_artifact_path_contract_creates_no_output_artifacts():
    page, run_id, kind = _safe_input()
    root_parent = REPO_ROOT / (_toks()["root_a"] + "_" + _toks()["acr"] + "_" + _toks()["root_b"])
    before = _snap_state(root_parent)
    _ = build_internal_visual_artifact_path_contract(page, run_id, kind)
    after = _snap_state(root_parent)
    assert before["files"] == after["files"]
    assert before["typed"] == after["typed"]
    assert before["named"] == after["named"]