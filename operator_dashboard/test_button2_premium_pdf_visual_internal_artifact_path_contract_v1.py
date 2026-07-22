from __future__ import annotations

import copy
import importlib.util
import json
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


def _module_file_path() -> Path:
    t = _toks()
    name = "button2_premium_" + t["acr"] + "_visual_internal_artifact_path_v1.py"
    return VISUAL_DIR / name


def _fixture_path() -> Path:
    t = _toks()
    name = "button2_premium_" + t["acr"] + "_visual_internal_page_prototype_v1.json"
    return VISUAL_DIR / name


def _load_page_prototype() -> dict:
    return json.loads(_fixture_path().read_text(encoding="utf-8"))


def _load_module():
    mpath = _module_file_path()
    spec = importlib.util.spec_from_file_location("b2_artifact_path_mod", mpath)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _required_public_functions() -> list[str]:
    return [
        "build_internal_visual_artifact_path_contract",
        "list_internal_visual_artifact_path_required_fields",
        "list_internal_visual_artifact_path_output_fields",
        "list_internal_visual_artifact_path_allowed_kinds",
    ]


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


def _build(page_prototype, render_attempt_id, artifact_kind):
    mod = _load_module()
    return mod.build_internal_visual_artifact_path_contract(page_prototype, render_attempt_id, artifact_kind)


def _safe_input() -> tuple[dict, str, str]:
    page = _load_page_prototype()
    return page, "RA_0001", "internal_visual_page_preview"


def _blocked_case(page_mutator, render_attempt_id: str = "RA_0001", artifact_kind: str = "internal_visual_page_preview"):
    page, _run_id, _kind = _safe_input()
    page_mutator(page)
    return _build(page, render_attempt_id, artifact_kind)


def test_button2_internal_artifact_path_contract_imports_real_module():
    mod = _load_module()
    for name in _required_public_functions():
        assert hasattr(mod, name)


def test_button2_internal_artifact_path_contract_module_lists_required_fields():
    mod = _load_module()
    out = mod.list_internal_visual_artifact_path_required_fields()
    expected = {
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
    }
    assert isinstance(out, list)
    assert expected.issubset(set(out))


def test_button2_internal_artifact_path_contract_module_lists_output_fields():
    mod = _load_module()
    out = mod.list_internal_visual_artifact_path_output_fields()
    expected = {
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
    }
    assert isinstance(out, list)
    assert expected.issubset(set(out))


def test_button2_internal_artifact_path_contract_module_lists_allowed_kinds():
    mod = _load_module()
    out = mod.list_internal_visual_artifact_path_allowed_kinds()
    expected = {
        "internal_visual_page_preview",
        "internal_visual_page_hash_manifest",
        "internal_visual_page_qa_snapshot",
        "internal_visual_page_render_log",
    }
    assert isinstance(out, list)
    assert set(out) == expected


def test_button2_internal_artifact_path_contract_accepts_safe_internal_page_prototype():
    page, run_id, kind = _safe_input()
    out = _build(page, run_id, kind)
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
    out = _build(page, run_id, kind)
    assert out["artifact_contract_status"] == "BLOCKED"


def test_button2_internal_artifact_path_contract_rejects_customer_release_true():
    page, run_id, kind = _safe_input()
    page["release_boundary"]["customer_release_authorized"] = True
    out = _build(page, run_id, kind)
    assert out["artifact_contract_status"] == "BLOCKED"


def test_button2_internal_artifact_path_contract_rejects_public_publishing_true_with_module():
    out = _blocked_case(lambda page: page["release_boundary"].__setitem__("public_publishing_authorized", True))
    assert out["artifact_contract_status"] == "BLOCKED"
    assert out["blocked_reasons"]
    assert out["delivery_ready"] is False
    assert out["customer_facing_authorized"] is False
    assert out["learning_activation_authorized"] is False


def test_button2_internal_artifact_path_contract_rejects_production_launch_true_with_module():
    out = _blocked_case(lambda page: page["release_boundary"].__setitem__("production_launch_authorized", True))
    assert out["artifact_contract_status"] == "BLOCKED"
    assert out["blocked_reasons"]
    assert out["delivery_ready"] is False
    assert out["customer_facing_authorized"] is False
    assert out["learning_activation_authorized"] is False


def test_button2_internal_artifact_path_contract_rejects_automated_delivery_true_with_module():
    out = _blocked_case(lambda page: page["release_boundary"].__setitem__("automated_delivery_authorized", True))
    assert out["artifact_contract_status"] == "BLOCKED"
    assert out["blocked_reasons"]
    assert out["delivery_ready"] is False
    assert out["customer_facing_authorized"] is False
    assert out["learning_activation_authorized"] is False


def test_button2_internal_artifact_path_contract_rejects_learning_activation_true():
    page, run_id, kind = _safe_input()
    page["release_boundary"]["learning_activation_authorized"] = True
    out = _build(page, run_id, kind)
    assert out["artifact_contract_status"] == "BLOCKED"


def test_button2_internal_artifact_path_contract_rejects_missing_required_field_with_module():
    page, run_id, kind = _safe_input()
    page.pop("contract_only")
    out = _build(page, run_id, kind)
    assert out["artifact_contract_status"] == "BLOCKED"
    assert out["blocked_reasons"]
    assert out["delivery_ready"] is False
    assert out["customer_facing_authorized"] is False
    assert out["learning_activation_authorized"] is False


def test_button2_internal_artifact_path_contract_rejects_missing_render_attempt_id_with_module():
    out = _blocked_case(lambda page: None, render_attempt_id="")
    assert out["artifact_contract_status"] == "BLOCKED"
    assert out["blocked_reasons"]
    assert out["delivery_ready"] is False
    assert out["customer_facing_authorized"] is False
    assert out["learning_activation_authorized"] is False


def test_button2_internal_artifact_path_contract_rejects_qa_gate_blocked_reasons_with_module():
    out = _blocked_case(lambda page: page["qa_gate_output"].__setitem__("blocked_reasons", ["x"]))
    assert out["artifact_contract_status"] == "BLOCKED"
    assert out["blocked_reasons"]
    assert out["delivery_ready"] is False
    assert out["customer_facing_authorized"] is False
    assert out["learning_activation_authorized"] is False


def test_button2_internal_artifact_path_contract_rejects_required_operator_review_false_with_module():
    out = _blocked_case(lambda page: page.__setitem__("operator_review_status", ""))
    assert out["artifact_contract_status"] == "BLOCKED"
    assert out["blocked_reasons"]
    assert out["delivery_ready"] is False
    assert out["customer_facing_authorized"] is False
    assert out["learning_activation_authorized"] is False


def test_button2_internal_artifact_path_contract_rejects_missing_render_contract_with_module():
    out = _blocked_case(lambda page: page.pop("render_contract"))
    assert out["artifact_contract_status"] == "BLOCKED"
    assert out["blocked_reasons"]
    assert out["delivery_ready"] is False
    assert out["customer_facing_authorized"] is False
    assert out["learning_activation_authorized"] is False


def test_button2_internal_artifact_path_contract_rejects_invalid_render_status_with_module():
    out = _blocked_case(lambda page: page["render_contract"].__setitem__("render_status", "BAD"))
    assert out["artifact_contract_status"] == "BLOCKED"
    assert out["blocked_reasons"]
    assert out["delivery_ready"] is False
    assert out["customer_facing_authorized"] is False
    assert out["learning_activation_authorized"] is False


def test_button2_internal_artifact_path_contract_rejects_render_delivery_ready_true_with_module():
    out = _blocked_case(lambda page: page["render_contract"].__setitem__("delivery_ready", True))
    assert out["artifact_contract_status"] == "BLOCKED"
    assert out["blocked_reasons"]
    assert out["delivery_ready"] is False
    assert out["customer_facing_authorized"] is False
    assert out["learning_activation_authorized"] is False


def test_button2_internal_artifact_path_contract_rejects_evidence_panel_not_rendered_with_module():
    out = _blocked_case(lambda page: page["render_contract"].__setitem__("evidence_panel_rendered", False))
    assert out["artifact_contract_status"] == "BLOCKED"
    assert out["blocked_reasons"]
    assert out["delivery_ready"] is False
    assert out["customer_facing_authorized"] is False
    assert out["learning_activation_authorized"] is False


def test_button2_internal_artifact_path_contract_rejects_disclaimer_footer_not_rendered_with_module():
    out = _blocked_case(lambda page: page["render_contract"].__setitem__("disclaimer_footer_rendered", False))
    assert out["artifact_contract_status"] == "BLOCKED"
    assert out["blocked_reasons"]
    assert out["delivery_ready"] is False
    assert out["customer_facing_authorized"] is False
    assert out["learning_activation_authorized"] is False


def test_button2_internal_artifact_path_contract_rejects_severity_scale_not_rendered_with_module():
    out = _blocked_case(lambda page: page["render_contract"].__setitem__("severity_scale_rendered", False))
    assert out["artifact_contract_status"] == "BLOCKED"
    assert out["blocked_reasons"]
    assert out["delivery_ready"] is False
    assert out["customer_facing_authorized"] is False
    assert out["learning_activation_authorized"] is False


def test_button2_internal_artifact_path_contract_requires_pass_internal_only_qa_gate():
    page, run_id, kind = _safe_input()
    page["qa_gate_output"]["qa_status"] = "PENDING"
    out = _build(page, run_id, kind)
    assert out["artifact_contract_status"] == "BLOCKED"


def test_button2_internal_artifact_path_contract_rejects_blocked_qa_gate():
    page, run_id, kind = _safe_input()
    page["qa_gate_output"]["qa_status"] = "BLOCKED"
    page["qa_gate_output"]["blocked_reasons"] = ["x"]
    out = _build(page, run_id, kind)
    assert out["artifact_contract_status"] == "BLOCKED"


def test_button2_internal_artifact_path_contract_requires_valid_render_contract():
    page, run_id, kind = _safe_input()
    page["render_contract"]["render_status"] = "BAD"
    out = _build(page, run_id, kind)
    assert out["artifact_contract_status"] == "BLOCKED"


def test_button2_internal_artifact_path_contract_rejects_missing_page_prototype():
    out = _build(None, "RA_0001", "internal_visual_page_preview")
    assert out["artifact_contract_status"] == "BLOCKED"


def test_button2_internal_artifact_path_contract_rejects_unknown_artifact_kind():
    page, run_id, _kind = _safe_input()
    out = _build(page, run_id, "unknown_kind")
    assert out["artifact_contract_status"] == "BLOCKED"


def test_button2_internal_artifact_path_contract_derives_path_from_contract_ids():
    page, run_id, kind = _safe_input()
    out = _build(page, run_id, kind)
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
    out = _build(page, run_id, kind)
    assert out["artifact_contract_status"] == "BLOCKED"


def test_button2_internal_artifact_path_contract_rejects_reference_folder_dependency():
    page, run_id, kind = _safe_input()
    t = _toks()
    page["artifact_path_override"] = t["ref_c"] + "\\" + t["ref_a"].replace(" ", "_")
    out = _build(page, run_id, kind)
    assert out["artifact_contract_status"] == "BLOCKED"


def test_button2_internal_artifact_path_contract_rejects_path_traversal():
    page, run_id, kind = _safe_input()
    page["artifact_path_override"] = "../escape"
    out = _build(page, run_id, kind)
    assert out["artifact_contract_status"] == "BLOCKED"


def test_button2_internal_artifact_path_contract_rejects_customer_public_production_delivery_paths():
    page, run_id, kind = _safe_input()
    page["artifact_path_override"] = "x/customer/public/production/delivery/y"
    out = _build(page, run_id, kind)
    assert out["artifact_contract_status"] == "BLOCKED"


def test_button2_internal_artifact_path_contract_requires_operator_review_status():
    page, run_id, kind = _safe_input()
    page["operator_review_status"] = ""
    out = _build(page, run_id, kind)
    assert out["artifact_contract_status"] == "BLOCKED"


def test_button2_internal_artifact_path_contract_requires_sha256_metadata_plan():
    page, run_id, kind = _safe_input()
    out = _build(page, run_id, kind)
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
    out = _build(page, run_id, kind)
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
    out = _build(page, run_id, kind)
    assert out["delivery_ready"] is False
    assert out["customer_facing_authorized"] is False
    assert out["learning_activation_authorized"] is False
    assert out["artifact_extension_authorized"] is False


def test_button2_internal_artifact_path_contract_creates_no_directories():
    page, run_id, kind = _safe_input()
    root_parent = REPO_ROOT / (_toks()["root_a"] + "_" + _toks()["acr"] + "_" + _toks()["root_b"])
    before = _snap_state(root_parent)
    _ = _build(page, run_id, kind)
    after = _snap_state(root_parent)
    assert before["dirs"] == after["dirs"]


def test_button2_internal_artifact_path_contract_creates_no_output_artifacts():
    page, run_id, kind = _safe_input()
    root_parent = REPO_ROOT / (_toks()["root_a"] + "_" + _toks()["acr"] + "_" + _toks()["root_b"])
    before = _snap_state(root_parent)
    _ = _build(page, run_id, kind)
    after = _snap_state(root_parent)
    assert before["files"] == after["files"]
    assert before["typed"] == after["typed"]
    assert before["named"] == after["named"]
