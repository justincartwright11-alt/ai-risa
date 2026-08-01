import copy
import json
from pathlib import Path

from operator_dashboard.button2_governed_internal_pdf_preflight_adapter_v1 import (
    INTERNAL_ARTIFACT_CLASSIFICATION,
    build_button2_governed_internal_pdf_preflight_v1,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "closed_loop_governed_local_fixture_v1.json"


def _row():
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    row = copy.deepcopy(fixture["button2"])
    row["fixture_id"] = fixture["fixture_id"]
    row["fixture_only"] = fixture["fixture_only"]
    return row


def _plan(tmp_path, row=None, **kwargs):
    return build_button2_governed_internal_pdf_preflight_v1(
        row or _row(), tmp_path / "internal-output", fixture_mode=True, **kwargs
    )


def test_governed_internal_pdf_preflight_is_non_writing_and_fail_closed(tmp_path):
    row = _row()
    original = copy.deepcopy(row)
    output_root = tmp_path / "internal-output"
    plan = _plan(tmp_path, row)

    assert plan["ok"] is True
    assert plan["preflight_only"] is True
    assert plan["artifact_classification"] == INTERNAL_ARTIFACT_CLASSIFICATION
    assert plan["artifact_labels"] == ["INTERNAL TEST FIXTURE", "NOT FOR CUSTOMER RELEASE"]
    assert plan["proposed_filename"] == "internal_fixture_report_closed_loop_v1__DRAFT_INTERNAL_FIXTURE_v1.pdf"
    assert Path(plan["proposed_output_path"]).parent == output_root.resolve()
    assert not Path(plan["proposed_output_path"]).exists()
    assert not output_root.exists()
    assert plan["customer_ready_possible"] is False
    assert plan["customer_release_authorized"] is False
    assert plan["queue_write_performed"] is False
    assert plan["pdf_generation_performed"] is False
    assert plan["permanent_mutation_performed"] is False
    assert row == original

    output_root.mkdir()
    Path(plan["proposed_output_path"]).touch()
    assert _plan(tmp_path, row)["blocked_reason"] == "proposed_output_target_exists"


def test_governed_internal_pdf_preflight_rejects_unsafe_or_incomplete_inputs(tmp_path):
    cases = [
        (_row(), {"fixture_mode": False}, "local_fixture_mode_required"),
        ({**_row(), "structured_prediction": None}, {}, "structured_prediction_contract_missing"),
        ({**_row(), "source_provenance": ""}, {}, "provenance_missing"),
        ({**_row(), "report_id": "../customer-ready"}, {}, "fixture_identity_incomplete_or_unsafe"),
    ]
    for row, overrides, reason in cases:
        result = build_button2_governed_internal_pdf_preflight_v1(
            row, tmp_path / "root", **({"fixture_mode": True} | overrides)
        )
        assert result["ok"] is False
        assert result["preflight_only"] is True
        assert result["blocked_reason"] == reason
        assert result["pdf_generation_performed"] is False
        assert result["queue_write_performed"] is False
        assert result["customer_release_authorized"] is False
        assert result["permanent_mutation_performed"] is False

    unsafe_root = build_button2_governed_internal_pdf_preflight_v1(
        _row(), tmp_path / ".." / "escape", fixture_mode=True
    )
    assert unsafe_root["blocked_reason"] == "approved_internal_output_root_invalid"
    overwrite_row = _row()
    overwrite_row["overwrite_requested"] = True
    overwrite = _plan(tmp_path, overwrite_row)
    assert overwrite["ok"] is False
    assert overwrite["blocked_reason"] == "overwrite_not_authorized"