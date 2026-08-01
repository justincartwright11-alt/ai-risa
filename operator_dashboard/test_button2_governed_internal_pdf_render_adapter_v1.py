import copy
import hashlib
import json
from pathlib import Path

from pypdf import PdfReader

from operator_dashboard.button2_governed_internal_pdf_preflight_adapter_v1 import (
    build_button2_governed_internal_pdf_preflight_v1,
)
from operator_dashboard.button2_governed_internal_pdf_render_adapter_v1 import (
    render_button2_governed_internal_pdf_v1,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "closed_loop_governed_local_fixture_v1.json"


def _row():
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    row = copy.deepcopy(fixture["button2"])
    row.update(fixture_id=fixture["fixture_id"], fixture_only=fixture["fixture_only"])
    return row


def _preflight(tmp_path, row=None):
    return build_button2_governed_internal_pdf_preflight_v1(
        row or _row(), tmp_path, fixture_mode=True
    )


def test_render_governed_internal_pdf_writes_one_verified_artifact(tmp_path):
    row = _row()
    original_row = copy.deepcopy(row)
    plan = _preflight(tmp_path, row)
    original_plan = copy.deepcopy(plan)
    result = render_button2_governed_internal_pdf_v1(plan, row)
    output = Path(result["output_path"])

    assert result["ok"] is True
    assert result["status"] == "generated_internal_test_pdf"
    assert output.exists() and output.parent == tmp_path.resolve()
    content = output.read_bytes()
    assert content.startswith(b"%PDF-")
    assert len(content) > 256
    assert result["sha256"] == hashlib.sha256(content).hexdigest()
    assert result["pdf_signature_valid"] is True
    text = "\n".join(page.extract_text() or "" for page in PdfReader(output).pages)
    assert "INTERNAL TEST FIXTURE" in text
    assert "NOT FOR CUSTOMER RELEASE" in text
    assert "Fictional Fighter Alpha" in text and "Fictional Fighter Beta" in text
    assert result["pdf_generation_count"] == 1
    assert result["controlled_artifact_write_performed"] is True
    assert result["customer_ready_possible"] is False
    assert result["customer_release_authorized"] is False
    assert result["queue_write_performed"] is False
    assert result["permanent_mutation_performed"] is False
    assert row == original_row and plan == original_plan
    assert list(tmp_path.rglob("*.pdf")) == [output]


def test_render_governed_internal_pdf_fails_closed_without_final_artifact(tmp_path, monkeypatch):
    row = _row()
    plan = _preflight(tmp_path, row)
    output = Path(plan["proposed_output_path"])

    assert render_button2_governed_internal_pdf_v1({**plan, "artifact_classification": "customer_ready_pdf"}, row)["blocked_reason"] == "invalid_internal_artifact_classification"
    assert render_button2_governed_internal_pdf_v1({**plan, "proposed_output_path": str(tmp_path / "other.pdf")}, row)["blocked_reason"] == "preflight_output_path_mismatch"
    mismatch = copy.deepcopy(row)
    mismatch["report_id"] = "different_report"
    assert render_button2_governed_internal_pdf_v1(plan, mismatch)["blocked_reason"] == "preflight_report_identity_mismatch"
    missing_prediction = copy.deepcopy(row)
    missing_prediction["structured_prediction"] = None
    assert render_button2_governed_internal_pdf_v1(plan, missing_prediction)["blocked_reason"] == "structured_prediction_missing"
    monkeypatch.setattr("operator_dashboard.button2_governed_internal_pdf_render_adapter_v1.render_button2_pdf", lambda _html: {"pdf_bytes": b"bad"})
    failed = render_button2_governed_internal_pdf_v1(plan, row)
    assert failed["ok"] is False
    assert failed["blocked_reason"] == "renderer_returned_invalid_pdf"
    assert not output.exists()

    output.parent.mkdir(exist_ok=True)
    output.write_bytes(b"existing")
    existing = render_button2_governed_internal_pdf_v1(plan, row)
    assert existing["blocked_reason"] == "approved_target_missing_or_exists"
    assert output.read_bytes() == b"existing"