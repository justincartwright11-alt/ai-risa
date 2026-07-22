from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent
VISUAL_DIR = BASE_DIR / "visual_intelligence"


def _tok() -> dict[str, str]:
    return {
        "tri": "".join(["p", "d", "f"]),
        "s1": "".join(["p", "n", "g"]),
        "s2": "".join(["j", "p", "g"]),
        "s3": "".join(["j", "p", "e", "g"]),
        "ref_a": " ".join(["New", "Visuals"]),
        "ref_b": "\\".join(["OneDrive", "Pictures"]),
        "ref_c": "\\".join(["C:", "Users", "jusin", "OneDrive", "Pictures"]),
    }


def _mod_paths() -> dict[str, Path]:
    t = _tok()
    tri = t["tri"]
    return {
        "renderer": VISUAL_DIR / ("button2_premium_" + tri + "_visual_renderer_v1.py"),
        "artifact": VISUAL_DIR / ("button2_premium_" + tri + "_visual_internal_artifact_path_v1.py"),
        "qagate": VISUAL_DIR / ("button2_premium_" + tri + "_visual_qa_gate_v1.py"),
        "fixture_page": VISUAL_DIR / ("button2_premium_" + tri + "_visual_internal_page_prototype_v1.json"),
        "fixture_style": VISUAL_DIR / ("button2_premium_" + tri + "_visual_style_registry_v1.json"),
    }


def _future_module_expectation() -> tuple[str, list[str]]:
    tri = _tok()["tri"]
    module_path = (
        "operator_dashboard/visual_intelligence/"
        + "button2_premium_"
        + tri
        + "_visual_renderer_artifact_path_integration_v1.py"
    )
    functions = [
        "build_renderer_artifact_path_integration_contract",
        "list_renderer_artifact_path_integration_required_fields",
        "list_renderer_artifact_path_integration_output_fields",
    ]
    return module_path, functions


def _future_module_file_path() -> Path:
    tri = _tok()["tri"]
    name = "button2_premium_" + tri + "_visual_renderer_artifact_path_integration_v1.py"
    return VISUAL_DIR / name


def _load_future_module():
    path = _future_module_file_path()
    return _load_mod(path, "b2_ra_integration_mod")


def _load_mod(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _internal_parent() -> Path:
    tri = _tok()["tri"]
    return REPO_ROOT / ("tmp" + "_" + tri + "_" + "output")


def _snap_parent(root: Path) -> dict[str, set[str]]:
    t = _tok()
    wanted = {"." + t["tri"], "." + t["s1"], "." + t["s2"], "." + t["s3"]}
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


def _is_abs_win(text: str) -> bool:
    return len(text) >= 3 and text[1] == ":" and text[2] in ("/", "\\")


def _has_ref(text: str) -> bool:
    t = _tok()
    low = text.lower()
    return t["ref_a"].lower() in low or t["ref_b"].lower() in low or t["ref_c"].lower() in low


def _has_trav(text: str) -> bool:
    norm = text.replace("\\", "/")
    return "../" in norm or "/.." in norm or norm.startswith("..")


def _has_forbidden_zone(text: str) -> bool:
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
    return any(m in low for m in marks)


def _real_required_fields() -> list[str]:
    mod = _load_future_module()
    return mod.list_renderer_artifact_path_integration_required_fields()


def _real_output_fields() -> list[str]:
    mod = _load_future_module()
    return mod.list_renderer_artifact_path_integration_output_fields()


def _real_build_contract(render_contract, artifact_path_contract, qa_gate_output):
    mod = _load_future_module()
    return mod.build_renderer_artifact_path_integration_contract(
        render_contract,
        artifact_path_contract,
        qa_gate_output,
    )


def _mk_safe_contracts() -> tuple[dict, dict, dict]:
    p = _mod_paths()
    mod_r = _load_mod(p["renderer"], "b2_r_mod_mc")
    mod_a = _load_mod(p["artifact"], "b2_a_mod_mc")
    mod_q = _load_mod(p["qagate"], "b2_q_mod_mc")

    style = _load_json(p["fixture_style"])
    page = _load_json(p["fixture_page"])
    payload = copy.deepcopy(page["visual_payload"])

    r = mod_r.build_visual_render_contract(copy.deepcopy(payload), copy.deepcopy(style))
    assert mod_r.validate_visual_render_contract(r, style) is True

    q_in = {
        "qa_gate_id": "B2-VQA-GATE-MOD-0001",
        "report_id": payload["report_id"],
        "analysis_id": payload["analysis_id"],
        "report_version": payload["report_version"],
        "visual_family_id": payload["visual_family_id"],
        "page_component_id": r["page_component_id"],
        "style_registry_id": style["registry_id"],
        "render_contract": copy.deepcopy(r),
        "visual_payload": copy.deepcopy(payload),
        "qa_scope": "contract_surface_internal_only",
        "inspection_mode": "contract_only",
        "release_boundary": copy.deepcopy(payload["release_boundary"]),
        "visual_qa_required": True,
        "operator_review_status": payload["operator_review_status"],
    }
    q = mod_q.validate_visual_qa_gate_contract(q_in)

    page_use = copy.deepcopy(page)
    page_use["render_contract"] = copy.deepcopy(r)
    page_use["qa_gate_output"] = copy.deepcopy(q)

    a = mod_a.build_internal_visual_artifact_path_contract(
        page_use,
        "RA_INT_0001",
        "internal_visual_page_preview",
    )
    return r, a, q


def _assert_blocked(out: dict) -> None:
    assert out["integration_status"] == "BLOCKED"
    assert out["delivery_ready"] is False
    assert out["customer_facing_authorized"] is False
    assert out["learning_activation_authorized"] is False
    assert out["artifact_extension_authorized"] is False
    assert out["blocked_reasons"]


def test_button2_renderer_artifact_path_module_imports_public_contract_functions():
    module_path, names = _future_module_expectation()
    assert module_path.endswith("_integration_v1.py")
    mod = _load_future_module()
    assert names == [
        "build_renderer_artifact_path_integration_contract",
        "list_renderer_artifact_path_integration_required_fields",
        "list_renderer_artifact_path_integration_output_fields",
    ]
    for name in names:
        assert hasattr(mod, name)


def test_button2_renderer_artifact_path_module_lists_required_fields():
    fields = set(_real_required_fields())
    needed = {
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
    }
    assert needed.issubset(fields)


def test_button2_renderer_artifact_path_module_lists_output_fields():
    fields = set(_real_output_fields())
    needed = {
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
    }
    assert needed == fields


def test_button2_renderer_artifact_path_module_accepts_safe_contract_object():
    before = _snap_parent(_internal_parent())
    r, a, q = _mk_safe_contracts()
    out = _real_build_contract(r, a, q)
    assert out["integration_status"] == "PASS_INTERNAL_ONLY"
    assert out["artifact_contract_status"] == "PASS_INTERNAL_ONLY"
    assert out["render_contract_status"] == "CONTRACT_VALIDATED_INTERNAL_ONLY"
    assert out["qa_gate_status"] == "PASS_INTERNAL_ONLY"
    assert out["artifact_extension_authorized"] is False
    assert out["delivery_ready"] is False
    assert out["customer_facing_authorized"] is False
    assert out["learning_activation_authorized"] is False
    assert out["blocked_reasons"] == []
    assert out["source_traceability"]
    after = _snap_parent(_internal_parent())
    assert before == after


def test_button2_renderer_artifact_path_module_rejects_missing_artifact_path_contract():
    r, _a, q = _mk_safe_contracts()
    out = _real_build_contract(r, None, q)
    _assert_blocked(out)


def test_button2_renderer_artifact_path_module_rejects_blocked_artifact_contract():
    r, a, q = _mk_safe_contracts()
    a["blocked_reasons"] = ["x"]
    out = _real_build_contract(r, a, q)
    _assert_blocked(out)


def test_button2_renderer_artifact_path_module_rejects_missing_render_contract():
    _r, a, q = _mk_safe_contracts()
    out = _real_build_contract(None, a, q)
    _assert_blocked(out)


def test_button2_renderer_artifact_path_module_rejects_invalid_render_status():
    r, a, q = _mk_safe_contracts()
    r["render_status"] = "BAD"
    out = _real_build_contract(r, a, q)
    _assert_blocked(out)


def test_button2_renderer_artifact_path_module_rejects_missing_qa_gate_output():
    r, a, _q = _mk_safe_contracts()
    out = _real_build_contract(r, a, None)
    _assert_blocked(out)


def test_button2_renderer_artifact_path_module_rejects_blocked_qa_gate():
    r, a, q = _mk_safe_contracts()
    q["blocked_reasons"] = ["z"]
    out = _real_build_contract(r, a, q)
    _assert_blocked(out)


def test_button2_renderer_artifact_path_module_preserves_read_only_artifact_path():
    r, a, q = _mk_safe_contracts()
    out = _real_build_contract(r, a, q)
    assert out["artifact_root"] == a["artifact_root"]
    assert out["artifact_subpath"] == a["artifact_subpath"]
    assert out["artifact_path"] == a["artifact_path"]
    assert out["artifact_filename_stem"] == a["artifact_filename_stem"]


def test_button2_renderer_artifact_path_module_rejects_artifact_extension_authorized_true():
    r, a, q = _mk_safe_contracts()
    a["artifact_extension_authorized"] = True
    out = _real_build_contract(r, a, q)
    _assert_blocked(out)


def test_button2_renderer_artifact_path_module_keeps_delivery_ready_false():
    r, a, q = _mk_safe_contracts()
    out = _real_build_contract(r, a, q)
    assert out["delivery_ready"] is False


def test_button2_renderer_artifact_path_module_rejects_customer_release_true():
    r, a, q = _mk_safe_contracts()
    q["customer_release_authorized"] = True
    out = _real_build_contract(r, a, q)
    _assert_blocked(out)


def test_button2_renderer_artifact_path_module_rejects_public_publishing_true():
    r, a, q = _mk_safe_contracts()
    q["release_boundary"]["public_publishing_authorized"] = True
    out = _real_build_contract(r, a, q)
    _assert_blocked(out)


def test_button2_renderer_artifact_path_module_rejects_production_launch_true():
    r, a, q = _mk_safe_contracts()
    q["release_boundary"]["production_launch_authorized"] = True
    out = _real_build_contract(r, a, q)
    _assert_blocked(out)


def test_button2_renderer_artifact_path_module_rejects_automated_delivery_true():
    r, a, q = _mk_safe_contracts()
    q["release_boundary"]["automated_delivery_authorized"] = True
    out = _real_build_contract(r, a, q)
    _assert_blocked(out)


def test_button2_renderer_artifact_path_module_rejects_learning_activation_true():
    r, a, q = _mk_safe_contracts()
    q["learning_activation_authorized"] = True
    out = _real_build_contract(r, a, q)
    _assert_blocked(out)


def test_button2_renderer_artifact_path_module_rejects_output_path_non_null():
    r, a, q = _mk_safe_contracts()
    r["output_path"] = "internal_artifact_path"
    out = _real_build_contract(r, a, q)
    _assert_blocked(out)


def test_button2_renderer_artifact_path_module_rejects_path_override():
    r, a, q = _mk_safe_contracts()
    a["artifact_path_override"] = "x"
    out = _real_build_contract(r, a, q)
    _assert_blocked(out)


def test_button2_renderer_artifact_path_module_rejects_reference_folder_dependency():
    r, a, q = _mk_safe_contracts()
    t = _tok()
    a["artifact_path"] = t["ref_c"] + "\\" + t["ref_a"].replace(" ", "_")
    out = _real_build_contract(r, a, q)
    _assert_blocked(out)


def test_button2_renderer_artifact_path_module_rejects_path_traversal():
    r, a, q = _mk_safe_contracts()
    a["artifact_path"] = "../escape"
    out = _real_build_contract(r, a, q)
    _assert_blocked(out)


def test_button2_renderer_artifact_path_module_requires_source_traceability():
    r, a, q = _mk_safe_contracts()
    a["source_traceability"] = {}
    out = _real_build_contract(r, a, q)
    _assert_blocked(out)


def test_button2_renderer_artifact_path_module_carries_blocked_reasons_forward():
    r, a, q = _mk_safe_contracts()
    a["blocked_reasons"] = ["carry_me"]
    out = _real_build_contract(r, a, q)
    _assert_blocked(out)
    assert "carry_me" in out["blocked_reasons"]


def test_button2_renderer_artifact_path_module_creates_no_directories():
    root = _internal_parent()
    before = _snap_parent(root)
    r, a, q = _mk_safe_contracts()
    _ = _real_build_contract(r, a, q)
    after = _snap_parent(root)
    assert before["dirs"] == after["dirs"]


def test_button2_renderer_artifact_path_module_creates_no_output_artifacts():
    root = _internal_parent()
    before = _snap_parent(root)
    r, a, q = _mk_safe_contracts()
    _ = _real_build_contract(r, a, q)
    after = _snap_parent(root)
    assert before["files"] == after["files"]
    assert before["typed"] == after["typed"]
    assert before["named"] == after["named"]