import copy
import hashlib
import json
from io import BytesIO
from pathlib import Path

from reportlab.pdfgen.canvas import Canvas

from operator_dashboard.app import app
from operator_dashboard.button2_governed_internal_pdf_preflight_adapter_v1 import (
    build_button2_governed_internal_pdf_inspection_plan_v1,
    build_button2_governed_internal_pdf_preflight_v1,
)
from operator_dashboard.button2_governed_internal_pdf_render_adapter_v1 import (
    render_button2_governed_internal_pdf_v1,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "closed_loop_governed_local_fixture_v1.json"
ROUTE = "/api/button2/governed-internal-pdf/inspect-v1"


def _fixture_and_request():
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    request = {
        "fixture_id": fixture["fixture_id"],
        "report_id": fixture["button2"]["report_id"],
        "report_version": fixture["button2"]["report_version"],
    }
    return fixture, request


def _configure(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_RISA_LOCAL_FIXTURE_MODE", "1")
    monkeypatch.setenv("AI_RISA_BUTTON2_QUEUE_PATH", str(FIXTURE_PATH))
    monkeypatch.setenv("AI_RISA_INTERNAL_PDF_OUTPUT_ROOT", str(tmp_path))


def _assert_safety(result):
    for field in (
        "customer_ready_possible", "customer_release_authorized", "queue_write_performed",
        "pdf_generation_performed", "learning_applied", "calibration_applied",
        "accuracy_ledger_written", "gcid_written", "model_weights_changed",
        "fighter_ratings_changed", "prediction_logic_changed", "artifact_archived",
        "artifact_removed", "artifact_overwritten", "permanent_mutation_performed",
    ):
        assert result[field] is False


def test_inspection_route_contract_and_read_only_states(tmp_path, monkeypatch):
    fixture, payload = _fixture_and_request()
    client = app.test_client()

    monkeypatch.delenv("AI_RISA_LOCAL_FIXTURE_MODE", raising=False)
    response = client.post(ROUTE, json=payload)
    assert response.status_code == 403
    assert response.get_json()["blocked_reason"] == "fixture_mode_disabled"
    _assert_safety(response.get_json())

    _configure(monkeypatch, tmp_path)
    monkeypatch.delenv("AI_RISA_INTERNAL_PDF_OUTPUT_ROOT", raising=False)
    response = client.post(ROUTE, json=payload)
    assert response.status_code == 422
    assert response.get_json()["blocked_reason"] == "internal_output_root_missing"

    _configure(monkeypatch, tmp_path)
    for bad_payload, reason, status in (
        (None, "request_json_required", 400),
        ({**payload, "unexpected": True}, "unexpected_request_fields", 400),
        ({"fixture_id": payload["fixture_id"], "report_id": payload["report_id"]}, "fixture_report_identity_required", 400),
        ({**payload, "fixture_id": "wrong_fixture"}, "fixture_identity_mismatch", 409),
        ({**payload, "report_id": "wrong_report"}, "report_identity_mismatch", 409),
        ({**payload, "report_version": "wrong_version"}, "report_version_mismatch", 409),
    ):
        response = client.post(ROUTE, json=bad_payload)
        assert response.status_code == status
        assert response.get_json()["blocked_reason"] == reason
        _assert_safety(response.get_json())

    fixture_before = copy.deepcopy(fixture)
    response = client.post(ROUTE, json=payload)
    result = response.get_json()
    assert response.status_code == 200
    assert result["ok"] is True
    assert result["status"] == "absent"
    assert result["artifact_state"] == "ABSENT"
    assert result["artifact_exists"] is False
    assert result["expected_filename"] == f'{payload["report_id"]}__{payload["report_version"]}.pdf'
    assert not list(tmp_path.iterdir())
    assert "proposed_output_path" not in result
    assert "proposed_output_directory" not in result
    _assert_safety(result)
    assert fixture == fixture_before


def test_inspection_route_present_corrupt_and_identity_states(tmp_path, monkeypatch):
    fixture, payload = _fixture_and_request()
    _configure(monkeypatch, tmp_path)
    root = tmp_path / "artifact-root"
    root.mkdir()
    row = copy.deepcopy(fixture["button2"])
    row.update(fixture_id=fixture["fixture_id"], fixture_only=True)
    plan = build_button2_governed_internal_pdf_inspection_plan_v1(row, root, fixture_mode=True)
    assert plan["status"] == "inspection_plan_ready"
    generated = render_button2_governed_internal_pdf_v1(plan, row)
    assert generated["ok"] is True
    target = Path(generated["output_path"])
    generation_plan = build_button2_governed_internal_pdf_preflight_v1(row, root, fixture_mode=True)
    assert generation_plan["blocked_reason"] == "proposed_output_target_exists"
    before_bytes = target.read_bytes()
    before_hash = hashlib.sha256(before_bytes).hexdigest()
    before_size = target.stat().st_size
    before_mtime = target.stat().st_mtime_ns

    monkeypatch.setenv("AI_RISA_INTERNAL_PDF_OUTPUT_ROOT", str(root))
    response = app.test_client().post(ROUTE, json=payload)
    result = response.get_json()
    assert response.status_code == 200
    assert result["status"] == "present_valid"
    assert result["artifact_state"] == "ACTIVE_INTERNAL_TEST_ARTIFACT"
    assert result["sha256"] == before_hash
    assert result["file_size_bytes"] == before_size
    assert result["page_count"] == 1
    assert result["artifact_classification"] == "governed_internal_test_pdf"
    assert result["text_validation"]["internal_warning_present"] is True
    assert "proposed_output_path" not in result
    _assert_safety(result)
    assert target.read_bytes() == before_bytes
    assert target.stat().st_size == before_size
    assert target.stat().st_mtime_ns == before_mtime

    target.write_bytes(b"not-a-pdf")
    response = app.test_client().post(ROUTE, json=payload)
    assert response.status_code == 422
    assert response.get_json()["blocked_reason"] == "pdf_signature_invalid"
    _assert_safety(response.get_json())

    forbidden_claim_pdf = BytesIO()
    canvas = Canvas(forbidden_claim_pdf)
    canvas.drawString(72, 740, "AI-RISA INTERNAL TEST FIXTURE")
    canvas.drawString(72, 720, "NOT FOR CUSTOMER RELEASE")
    canvas.drawString(72, 700, f"{payload['fixture_id']} {payload['report_id']} {payload['report_version']}")
    canvas.drawString(72, 680, f"{row['fighter_a']} {row['fighter_b']} governed_internal_test_pdf")
    canvas.drawString(72, 660, "customer released")
    canvas.save()
    target.write_bytes(forbidden_claim_pdf.getvalue())
    response = app.test_client().post(ROUTE, json=payload)
    assert response.status_code == 422
    assert response.get_json()["blocked_reason"] in {"forbidden_release_claim_present", "internal_warning_missing"}
    _assert_safety(response.get_json())


def test_inspection_route_does_not_invoke_renderer(tmp_path, monkeypatch):
    _, payload = _fixture_and_request()
    _configure(monkeypatch, tmp_path)
    monkeypatch.setattr(
        "operator_dashboard.button2_governed_internal_pdf_render_adapter_v1.render_button2_governed_internal_pdf_v1",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("inspection route invoked renderer")),
    )
    response = app.test_client().post(ROUTE, json=payload)
    assert response.status_code == 200
    assert response.get_json()["status"] == "absent"
