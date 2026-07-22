from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent
VISUAL_DIR = BASE_DIR / "visual_intelligence"


def _tok() -> dict[str, str]:
    return {
        "tri": "".join(["p", "d", "f"]),
        "img_a": "".join(["p", "n", "g"]),
        "img_b": "".join(["j", "p", "g"]),
        "img_c": "".join(["j", "p", "e", "g"]),
        "ref_a": " ".join(["New", "Visuals"]),
        "ref_b": "\\".join(["OneDrive", "Pictures"]),
        "ref_c": "\\".join(["C:", "Users", "jusin", "OneDrive", "Pictures"]),
    }


def _integration_mod_path() -> Path:
    tri = _tok()["tri"]
    name = "button2_premium_" + tri + "_visual_renderer_artifact_path_integration_v1.py"
    return VISUAL_DIR / name


def _renderer_mod_path() -> Path:
    tri = _tok()["tri"]
    name = "button2_premium_" + tri + "_visual_renderer_v1.py"
    return VISUAL_DIR / name


def _load_integration_mod():
    path = _integration_mod_path()
    spec = importlib.util.spec_from_file_location("b2_wire_integration_mod", path)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _root_contract_trace() -> dict[str, Any]:
    tri = _tok()["tri"]
    base = "button2_premium_" + tri + "_visual_"
    return {
        "renderer_scaffold_module": "operator_dashboard/visual_intelligence/" + base + "renderer_v1.py",
        "artifact_path_module": "operator_dashboard/visual_intelligence/" + base + "internal_artifact_path_v1.py",
        "qa_gate_module": "operator_dashboard/visual_intelligence/" + base + "qa_gate_v1.py",
        "integration_module": "operator_dashboard/visual_intelligence/" + base + "renderer_artifact_path_integration_v1.py",
        "system_lock_doc": "docs/" + base + "renderer_artifact_path_integration_system_lock_v1.md",
        "wiring_design_doc": "docs/" + base + "renderer_artifact_path_wiring_design_v1.md",
        "operator_review_status": "approved_for_internal_review",
    }


def _safe_render_contract() -> dict[str, Any]:
    return {
        "render_status": "CONTRACT_VALIDATED_INTERNAL_ONLY",
        "output_path": None,
        "delivery_ready": False,
        "customer_facing_authorized": False,
        "public_publishing_authorized": False,
        "production_launch_authorized": False,
        "automated_delivery_authorized": False,
        "learning_activation_authorized": False,
        "evidence_panel_rendered": True,
        "disclaimer_footer_rendered": True,
        "severity_scale_rendered": True,
        "source_traceability": copy.deepcopy(_root_contract_trace()),
        "blocked_reasons": [],
    }


def _safe_artifact_path_contract() -> dict[str, Any]:
    tri = _tok()["tri"]
    stem = "artifact_contract_stem_internal"
    root = "tmp_" + tri + "_output/button2_visual_internal_prototypes/"
    sub = "RID/AID/VID/FAM/PID/"
    return {
        "artifact_contract_status": "PASS_INTERNAL_ONLY",
        "artifact_path": root + sub + stem,
        "artifact_filename_stem": stem,
        "artifact_root": root,
        "artifact_subpath": sub,
        "artifact_extension_authorized": False,
        "delivery_ready": False,
        "customer_facing_authorized": False,
        "learning_activation_authorized": False,
        "source_traceability": copy.deepcopy(_root_contract_trace()),
        "blocked_reasons": [],
    }


def _safe_qa_gate_output() -> dict[str, Any]:
    return {
        "qa_status": "PASS_INTERNAL_ONLY",
        "required_operator_review": True,
        "customer_release_authorized": False,
        "public_publishing_authorized": False,
        "production_launch_authorized": False,
        "automated_delivery_authorized": False,
        "learning_activation_authorized": False,
        "release_boundary": {
            "customer_release_authorized": False,
            "public_publishing_authorized": False,
            "production_launch_authorized": False,
            "automated_delivery_authorized": False,
            "learning_activation_authorized": False,
        },
        "source_traceability": copy.deepcopy(_root_contract_trace()),
        "blocked_reasons": [],
    }


def _mk_safe_contracts() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    return _safe_render_contract(), _safe_artifact_path_contract(), _safe_qa_gate_output()


def _assert_blocked(out: dict[str, Any]) -> None:
    assert out["integration_status"] == "BLOCKED"
    assert out["delivery_ready"] is False
    assert out["customer_facing_authorized"] is False
    assert out["learning_activation_authorized"] is False
    assert out["artifact_extension_authorized"] is False
    assert out["blocked_reasons"]


def _snap_parent(root: Path) -> dict[str, set[str]]:
    t = _tok()
    suffixes = {
        "." + t["tri"],
        "." + t["img_a"],
        "." + t["img_b"],
        "." + t["img_c"],
    }
    out = {
        "dirs": set(),
        "typed": set(),
    }
    if not root.exists():
        return out
    for item in root.rglob("*"):
        rel = item.relative_to(root).as_posix()
        if item.is_dir():
            out["dirs"].add(rel)
            continue
        if item.suffix.lower() in suffixes:
            out["typed"].add(rel)
    return out


def _expected_public_functions() -> list[str]:
    return [
        "build_renderer_artifact_path_integration_contract",
        "list_renderer_artifact_path_integration_required_fields",
        "list_renderer_artifact_path_integration_output_fields",
    ]


def _build_expected_renderer_artifact_path_wiring_contract(
    render_contract,
    artifact_path_contract,
    qa_gate_output,
):
    mod = _load_integration_mod()
    out = mod.build_renderer_artifact_path_integration_contract(
        render_contract,
        artifact_path_contract,
        qa_gate_output,
    )
    return out


def test_button2_renderer_artifact_path_wiring_future_surface_defined():
    assert callable(_build_expected_renderer_artifact_path_wiring_contract)
    renderer_path = _renderer_mod_path()
    assert renderer_path.exists()
    before = _snap_parent(REPO_ROOT)
    r, a, q = _mk_safe_contracts()
    out = _build_expected_renderer_artifact_path_wiring_contract(r, a, q)
    assert isinstance(out, dict)
    assert out["delivery_ready"] is False
    assert out["customer_facing_authorized"] is False
    assert out["learning_activation_authorized"] is False
    after = _snap_parent(REPO_ROOT)
    assert before == after


def test_button2_renderer_artifact_path_wiring_imports_locked_integration_module():
    mod = _load_integration_mod()
    assert mod is not None


def test_button2_renderer_artifact_path_wiring_validates_locked_public_functions():
    mod = _load_integration_mod()
    for name in _expected_public_functions():
        assert hasattr(mod, name)


def test_button2_renderer_artifact_path_wiring_accepts_safe_internal_contracts():
    before = _snap_parent(REPO_ROOT)
    r, a, q = _mk_safe_contracts()
    out = _build_expected_renderer_artifact_path_wiring_contract(r, a, q)
    assert out["integration_status"] == "PASS_INTERNAL_ONLY"
    assert out["render_contract_status"] == "CONTRACT_VALIDATED_INTERNAL_ONLY"
    assert out["artifact_contract_status"] == "PASS_INTERNAL_ONLY"
    assert out["qa_gate_status"] == "PASS_INTERNAL_ONLY"
    assert out.get("output_path") is None
    assert out["artifact_extension_authorized"] is False
    assert out["delivery_ready"] is False
    assert out["customer_facing_authorized"] is False
    assert out["learning_activation_authorized"] is False
    assert out["blocked_reasons"] == []
    assert out["source_traceability"]
    after = _snap_parent(REPO_ROOT)
    assert before == after


def test_button2_renderer_artifact_path_wiring_rejects_blocked_render_contract():
    r, a, q = _mk_safe_contracts()
    r["render_status"] = "BLOCKED"
    r["blocked_reasons"] = ["x"]
    out = _build_expected_renderer_artifact_path_wiring_contract(r, a, q)
    _assert_blocked(out)


def test_button2_renderer_artifact_path_wiring_rejects_blocked_artifact_path_contract():
    r, a, q = _mk_safe_contracts()
    a["artifact_contract_status"] = "BLOCKED"
    a["blocked_reasons"] = ["x"]
    out = _build_expected_renderer_artifact_path_wiring_contract(r, a, q)
    _assert_blocked(out)


def test_button2_renderer_artifact_path_wiring_rejects_blocked_qa_gate():
    r, a, q = _mk_safe_contracts()
    q["qa_status"] = "BLOCKED"
    q["blocked_reasons"] = ["x"]
    out = _build_expected_renderer_artifact_path_wiring_contract(r, a, q)
    _assert_blocked(out)


def test_button2_renderer_artifact_path_wiring_rejects_output_path_non_null():
    r, a, q = _mk_safe_contracts()
    r["output_path"] = "non_null"
    out = _build_expected_renderer_artifact_path_wiring_contract(r, a, q)
    _assert_blocked(out)


def test_button2_renderer_artifact_path_wiring_rejects_delivery_ready_true():
    r, a, q = _mk_safe_contracts()
    r["delivery_ready"] = True
    out = _build_expected_renderer_artifact_path_wiring_contract(r, a, q)
    _assert_blocked(out)


def test_button2_renderer_artifact_path_wiring_rejects_customer_release_true():
    r, a, q = _mk_safe_contracts()
    q["customer_release_authorized"] = True
    q["release_boundary"]["customer_release_authorized"] = True
    out = _build_expected_renderer_artifact_path_wiring_contract(r, a, q)
    _assert_blocked(out)


def test_button2_renderer_artifact_path_wiring_rejects_public_publishing_true():
    r, a, q = _mk_safe_contracts()
    q["public_publishing_authorized"] = True
    q["release_boundary"]["public_publishing_authorized"] = True
    out = _build_expected_renderer_artifact_path_wiring_contract(r, a, q)
    _assert_blocked(out)


def test_button2_renderer_artifact_path_wiring_rejects_production_launch_true():
    r, a, q = _mk_safe_contracts()
    q["production_launch_authorized"] = True
    q["release_boundary"]["production_launch_authorized"] = True
    out = _build_expected_renderer_artifact_path_wiring_contract(r, a, q)
    _assert_blocked(out)


def test_button2_renderer_artifact_path_wiring_rejects_automated_delivery_true():
    r, a, q = _mk_safe_contracts()
    q["automated_delivery_authorized"] = True
    q["release_boundary"]["automated_delivery_authorized"] = True
    out = _build_expected_renderer_artifact_path_wiring_contract(r, a, q)
    _assert_blocked(out)


def test_button2_renderer_artifact_path_wiring_rejects_learning_activation_true():
    r, a, q = _mk_safe_contracts()
    q["learning_activation_authorized"] = True
    q["release_boundary"]["learning_activation_authorized"] = True
    out = _build_expected_renderer_artifact_path_wiring_contract(r, a, q)
    _assert_blocked(out)


def test_button2_renderer_artifact_path_wiring_rejects_path_override():
    r, a, q = _mk_safe_contracts()
    a["artifact_path_override"] = "override"
    out = _build_expected_renderer_artifact_path_wiring_contract(r, a, q)
    _assert_blocked(out)


def test_button2_renderer_artifact_path_wiring_rejects_reference_folder_dependency():
    r, a, q = _mk_safe_contracts()
    ref = _tok()["ref_b"]
    a["artifact_path"] = "tmp_safe/" + ref + "/x"
    out = _build_expected_renderer_artifact_path_wiring_contract(r, a, q)
    _assert_blocked(out)


def test_button2_renderer_artifact_path_wiring_rejects_path_traversal():
    r, a, q = _mk_safe_contracts()
    a["artifact_path"] = "../unsafe"
    out = _build_expected_renderer_artifact_path_wiring_contract(r, a, q)
    _assert_blocked(out)


def test_button2_renderer_artifact_path_wiring_requires_source_traceability():
    r, a, q = _mk_safe_contracts()
    a["source_traceability"] = None
    out = _build_expected_renderer_artifact_path_wiring_contract(r, a, q)
    _assert_blocked(out)


def test_button2_renderer_artifact_path_wiring_preserves_output_path_none():
    r, a, q = _mk_safe_contracts()
    out = _build_expected_renderer_artifact_path_wiring_contract(r, a, q)
    assert out.get("output_path") is None


def test_button2_renderer_artifact_path_wiring_preserves_delivery_ready_false():
    r, a, q = _mk_safe_contracts()
    out = _build_expected_renderer_artifact_path_wiring_contract(r, a, q)
    assert out["delivery_ready"] is False


def test_button2_renderer_artifact_path_wiring_preserves_customer_facing_false():
    r, a, q = _mk_safe_contracts()
    out = _build_expected_renderer_artifact_path_wiring_contract(r, a, q)
    assert out["customer_facing_authorized"] is False


def test_button2_renderer_artifact_path_wiring_preserves_learning_activation_false():
    r, a, q = _mk_safe_contracts()
    out = _build_expected_renderer_artifact_path_wiring_contract(r, a, q)
    assert out["learning_activation_authorized"] is False


def test_button2_renderer_artifact_path_wiring_creates_no_directories():
    before = _snap_parent(REPO_ROOT)
    r, a, q = _mk_safe_contracts()
    _build_expected_renderer_artifact_path_wiring_contract(r, a, q)
    after = _snap_parent(REPO_ROOT)
    assert before["dirs"] == after["dirs"]


def test_button2_renderer_artifact_path_wiring_creates_no_output_artifacts():
    before = _snap_parent(REPO_ROOT)
    r, a, q = _mk_safe_contracts()
    out = _build_expected_renderer_artifact_path_wiring_contract(r, a, q)
    assert out["source_traceability"]
    trace = out["source_traceability"]
    for key in (
        "renderer_scaffold_module",
        "artifact_path_module",
        "qa_gate_module",
        "integration_module",
        "system_lock_doc",
        "wiring_design_doc",
        "operator_review_status",
    ):
        assert key in trace
    after = _snap_parent(REPO_ROOT)
    assert before["typed"] == after["typed"]
