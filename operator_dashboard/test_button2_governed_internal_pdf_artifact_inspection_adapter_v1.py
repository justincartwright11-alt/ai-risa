import copy
import hashlib
import json
import os
from pathlib import Path

import pytest

from operator_dashboard.button2_governed_internal_pdf_artifact_inspection_adapter_v1 import (
    inspect_button2_governed_internal_pdf_artifact_v1,
)
from operator_dashboard.button2_governed_internal_pdf_preflight_adapter_v1 import (
    build_button2_governed_internal_pdf_preflight_v1,
)
from operator_dashboard.button2_governed_internal_pdf_render_adapter_v1 import (
    render_button2_governed_internal_pdf_v1,
)
from operator_dashboard.button2_pdf_render_gate_v1 import render_button2_pdf


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "closed_loop_governed_local_fixture_v1.json"


def _row():
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    row = copy.deepcopy(fixture["button2"])
    row.update(fixture_id=fixture["fixture_id"], fixture_only=fixture["fixture_only"])
    return row


def _plan(tmp_path, row=None):
    return build_button2_governed_internal_pdf_preflight_v1(
        row or _row(), tmp_path / "internal-output", fixture_mode=True
    )


def _present_artifact(tmp_path):
    row = _row()
    root = tmp_path / "internal-output"
    root.mkdir()
    plan = build_button2_governed_internal_pdf_preflight_v1(row, root, fixture_mode=True)
    generated = render_button2_governed_internal_pdf_v1(plan, row)
    assert generated["ok"] is True
    return row, plan, Path(generated["output_path"])


def _custom_pdf(path, *, report_id, report_version, fixture_id, include_warning=True, claim=""):
    warning = "INTERNAL TEST FIXTURE NOT FOR CUSTOMER RELEASE" if include_warning else ""
    html = f"""
    <html><body>
    <h1>AI-RISA Premium Report Factory</h1>
    <p>{warning}</p>
    <p>fixture_id: {fixture_id}</p>
    <p>report_id: {report_id}</p>
    <p>report_version: {report_version}</p>
    <p>Fictional Fighter Alpha vs Fictional Fighter Beta</p>
    <p>classification: governed_internal_test_pdf</p>
    <p>customer release authorized: false</p>
    <p>{claim}</p>
    </body></html>
    """
    result = render_button2_pdf(html)
    path.write_bytes(result["pdf_bytes"])


def test_invalid_plans_relative_paths_filename_mismatch_and_absence(tmp_path):
    row = _row()
    plan = _plan(tmp_path, row)

    assert inspect_button2_governed_internal_pdf_artifact_v1({})["blocked_reason"] == "invalid_preflight_plan"
    relative = copy.deepcopy(plan)
    relative["proposed_output_directory"] = "relative-root"
    assert inspect_button2_governed_internal_pdf_artifact_v1(relative)["blocked_reason"] == "invalid_preflight_plan"
    escaped = copy.deepcopy(plan)
    escaped["proposed_output_directory"] = str(tmp_path / ".." / "escape")
    assert inspect_button2_governed_internal_pdf_artifact_v1(escaped)["blocked_reason"] == "invalid_preflight_plan"
    mismatch = copy.deepcopy(plan)
    mismatch["proposed_filename"] = "other.pdf"
    assert inspect_button2_governed_internal_pdf_artifact_v1(mismatch)["blocked_reason"] == "target_filename_mismatch"

    root = Path(plan["proposed_output_directory"])
    result = inspect_button2_governed_internal_pdf_artifact_v1(plan, row)
    assert result["ok"] is True
    assert result["status"] == "absent"
    assert result["artifact_exists"] is False
    assert result["artifact_state"] == "ABSENT"
    assert result["expected_filename"] == plan["proposed_filename"]
    assert not root.exists()
    assert result["pdf_generation_performed"] is False
    assert result["artifact_archived"] is False
    assert result["artifact_removed"] is False
    assert result["permanent_mutation_performed"] is False


def test_valid_target_is_bounded_verified_and_unchanged(tmp_path, monkeypatch):
    row, plan, target = _present_artifact(tmp_path)
    decoy = target.parent / "not-the-deterministic-target.pdf"
    decoy.write_bytes(target.read_bytes())
    before_bytes = target.read_bytes()
    before_hash = hashlib.sha256(before_bytes).hexdigest()
    before_size = target.stat().st_size
    before_mtime = target.stat().st_mtime_ns
    original_plan = copy.deepcopy(plan)
    original_row = copy.deepcopy(row)

    def fail_scan(*_args, **_kwargs):
        raise AssertionError("directory scanning is forbidden")

    monkeypatch.setattr(Path, "iterdir", fail_scan)
    monkeypatch.setattr(Path, "rglob", fail_scan)
    result = inspect_button2_governed_internal_pdf_artifact_v1(plan, row)

    assert result["ok"] is True
    assert result["status"] == "present_valid"
    assert result["artifact_exists"] is True
    assert result["artifact_state"] == "ACTIVE_INTERNAL_TEST_ARTIFACT"
    assert result["regular_file"] is True
    assert result["path_contained"] is True
    assert result["filename_matches"] is True
    assert result["pdf_signature_valid"] is True
    assert result["file_size_bytes"] == before_size
    assert result["sha256"] == before_hash
    assert result["page_count"] == 1
    assert result["text_validation"]["internal_warning_present"] is True
    assert result["text_validation"]["release_warning_present"] is True
    assert result["text_validation"]["fixture_identity_present"] is True
    assert result["text_validation"]["report_id_present"] is True
    assert result["text_validation"]["report_version_present"] is True
    assert result["text_validation"]["fighter_a_present"] is True
    assert result["text_validation"]["fighter_b_present"] is True
    assert result["text_validation"]["classification_present"] is True
    assert result["customer_ready_possible"] is False
    assert result["customer_release_authorized"] is False
    assert result["queue_write_performed"] is False
    assert result["pdf_generation_performed"] is False
    assert result["artifact_archived"] is False
    assert result["artifact_removed"] is False
    assert result["artifact_overwritten"] is False
    assert result["permanent_mutation_performed"] is False
    assert target.read_bytes() == before_bytes
    assert target.stat().st_size == before_size
    assert target.stat().st_mtime_ns == before_mtime
    assert plan == original_plan
    assert row == original_row


def test_present_mismatches_and_corruption_fail_closed(tmp_path):
    row, plan, target = _present_artifact(tmp_path)
    cases = [
        ("wrong_report", {"report_id": "wrong-report"}, "artifact_identity_mismatch"),
        ("wrong_version", {"report_version": "WRONG_VERSION"}, "artifact_identity_mismatch"),
        ("missing_warning", {"include_warning": False}, "internal_warning_missing"),
        ("forbidden_claim", {"claim": "customer release authorized: true"}, "forbidden_release_claim_present"),
    ]
    for name, options, reason in cases:
        if name == "wrong_report":
            _custom_pdf(target, report_id=options["report_id"], report_version=plan["report_version"], fixture_id=plan["fixture_id"])
        elif name == "wrong_version":
            _custom_pdf(target, report_id=plan["report_id"], report_version=options["report_version"], fixture_id=plan["fixture_id"])
        else:
            _custom_pdf(target, report_id=plan["report_id"], report_version=plan["report_version"], fixture_id=plan["fixture_id"], **options)
        result = inspect_button2_governed_internal_pdf_artifact_v1(plan, row)
        assert result["ok"] is False, name
        assert result["blocked_reason"] == reason
        assert result["artifact_exists"] is True
        assert result["inspection_performed"] is True
        assert result["pdf_generation_performed"] is False
        assert result["artifact_removed"] is False
        assert result["artifact_overwritten"] is False
        assert result["permanent_mutation_performed"] is False

    target.write_bytes(b"not-a-pdf")
    signature = inspect_button2_governed_internal_pdf_artifact_v1(plan, row)
    assert signature["blocked_reason"] == "pdf_signature_invalid"

    target.write_bytes(b"%PDF-1.7\nthis is not parseable")
    parsed = inspect_button2_governed_internal_pdf_artifact_v1(plan, row)
    assert parsed["blocked_reason"] == "pdf_parse_failed"


def test_non_regular_and_link_targets_fail_closed(tmp_path):
    row = _row()
    root = tmp_path / "internal-output"
    root.mkdir()
    plan = build_button2_governed_internal_pdf_preflight_v1(row, root, fixture_mode=True)
    target = Path(plan["proposed_output_path"])
    target.mkdir()
    directory_result = inspect_button2_governed_internal_pdf_artifact_v1(plan, row)
    assert directory_result["blocked_reason"] == "target_is_not_regular_file"
    target.rmdir()

    external = tmp_path / "external.pdf"
    _custom_pdf(external, report_id=plan["report_id"], report_version=plan["report_version"], fixture_id=plan["fixture_id"])
    try:
        target.symlink_to(external)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"Windows link creation unavailable: {exc}")
    link_result = inspect_button2_governed_internal_pdf_artifact_v1(plan, row)
    assert link_result["ok"] is False
    assert link_result["blocked_reason"] in {
        "target_link_or_reparse_point_rejected",
        "target_outside_approved_root",
    }
    assert link_result["artifact_removed"] is False
    assert link_result["permanent_mutation_performed"] is False
