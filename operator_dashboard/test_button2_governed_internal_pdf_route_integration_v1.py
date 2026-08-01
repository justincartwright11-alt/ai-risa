import copy
import hashlib
import json
from pathlib import Path

import pytest

from operator_dashboard.app import app


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "closed_loop_governed_local_fixture_v1.json"


def _request(fixture, **overrides):
    payload = {
        "fixture_id": fixture["fixture_id"],
        "report_id": fixture["button2"]["report_id"],
        "report_version": fixture["button2"]["report_version"],
        "internal_test_artifact_acknowledged": True,
    }
    payload.update(overrides)
    return payload


def _configure(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_RISA_LOCAL_FIXTURE_MODE", "1")
    monkeypatch.setenv("AI_RISA_BUTTON2_QUEUE_PATH", str(FIXTURE_PATH))
    monkeypatch.setenv("AI_RISA_INTERNAL_PDF_OUTPUT_ROOT", str(tmp_path))


def test_governed_internal_pdf_route_contract(tmp_path, monkeypatch):
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    original_fixture = copy.deepcopy(fixture)
    client = app.test_client()

    monkeypatch.delenv("AI_RISA_LOCAL_FIXTURE_MODE", raising=False)
    response = client.post("/api/button2/governed-internal-pdf/generate-v1", json=_request(fixture))
    assert response.status_code == 403
    assert response.get_json()["blocked_reason"] == "local_fixture_mode_required"

    _configure(monkeypatch, tmp_path)
    monkeypatch.delenv("AI_RISA_INTERNAL_PDF_OUTPUT_ROOT", raising=False)
    assert client.post("/api/button2/governed-internal-pdf/generate-v1", json=_request(fixture)).get_json()["status"] == "blocked"

    _configure(monkeypatch, tmp_path)
    for field, value, reason in (
        ("internal_test_artifact_acknowledged", False, "internal_test_artifact_acknowledgement_required"),
        ("fixture_id", "wrong_fixture", "fixture_id_mismatch"),
        ("report_id", "wrong_report", "report_id_mismatch"),
        ("report_version", "wrong_version", "report_version_mismatch"),
    ):
        response = client.post("/api/button2/governed-internal-pdf/generate-v1", json=_request(fixture, **{field: value}))
        assert response.status_code in (403, 422)
        assert response.get_json()["blocked_reason"] == reason
        assert response.get_json()["pdf_generation_count"] == 0

    fixture_before_valid = copy.deepcopy(fixture)
    response = client.post("/api/button2/governed-internal-pdf/generate-v1", json=_request(fixture))
    assert response.status_code == 200
    result = response.get_json()
    output = Path(result["output_path"])
    assert result["ok"] is True
    assert result["status"] == "generated_governed_internal_test_pdf" or result["status"] == "generated_internal_test_pdf"
    assert result["fixture_id"] == fixture["fixture_id"]
    assert result["report_id"] == fixture["button2"]["report_id"]
    assert result["report_version"] == fixture["button2"]["report_version"]
    assert result["artifact_classification"] == "governed_internal_test_pdf"
    assert result["internal_only"] is True and result["test_fixture_only"] is True
    assert result["customer_ready_possible"] is False
    assert result["customer_release_authorized"] is False
    assert result["queue_write_performed"] is False
    assert result["pdf_generation_count"] == 1
    assert result["pdf_signature_valid"] is True
    assert output.exists() and output.parent == tmp_path.resolve()
    content = output.read_bytes()
    assert content.startswith(b"%PDF-")
    assert result["sha256"] == hashlib.sha256(content).hexdigest()
    assert fixture == fixture_before_valid == original_fixture
    assert list(tmp_path.rglob("*.pdf")) == [output]

    before_collision = output.read_bytes()
    response = client.post("/api/button2/governed-internal-pdf/generate-v1", json=_request(fixture))
    assert response.status_code == 422
    assert response.get_json()["blocked_reason"] == "proposed_output_target_exists"
    assert output.read_bytes() == before_collision


def test_governed_internal_pdf_route_cleans_partial_artifact_on_render_failure(tmp_path, monkeypatch):
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    _configure(monkeypatch, tmp_path)
    monkeypatch.setattr(
        "operator_dashboard.button2_governed_internal_pdf_render_adapter_v1.render_button2_pdf",
        lambda _html: {"pdf_bytes": b"invalid"},
    )
    response = app.test_client().post(
        "/api/button2/governed-internal-pdf/generate-v1", json=_request(fixture)
    )
    assert response.status_code == 422
    assert response.get_json()["blocked_reason"] == "renderer_returned_invalid_pdf"
    assert response.get_json()["pdf_generation_performed"] is False
    assert list(tmp_path.rglob("*.pdf")) == []
