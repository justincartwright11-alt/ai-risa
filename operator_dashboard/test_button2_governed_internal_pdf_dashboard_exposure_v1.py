import json
from pathlib import Path

from operator_dashboard.app import app


TEMPLATE = Path(__file__).parent / "templates" / "index.html"
FIXTURE = Path(__file__).parent / "fixtures" / "closed_loop_governed_local_fixture_v1.json"


def test_governed_internal_dashboard_exposure_contract(tmp_path, monkeypatch):
    html = TEMPLATE.read_text(encoding="utf-8")
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    button2 = fixture["button2"]

    assert "Governed Internal Report Preview" in html
    assert "b2-governed-internal-pdf-control" in html
    assert "Generate Selected PDFs" in html
    assert "Generate Internal Test PDF" in html
    assert "INTERNAL TEST FIXTURE" in html
    assert "NOT FOR CUSTOMER RELEASE" in html
    assert "I acknowledge this will generate one fictional internal test PDF" in html
    assert "internal_test_artifact_acknowledged: true" in html
    assert "'/api/button2/governed-internal-pdf/generate-v1'" in html
    assert "output_path" not in html[html.index("function button2GenerateGovernedInternalPdf"):html.index("function button2GenerateGovernedInternalPdf") + 1800]
    request_start = html.index("body: JSON.stringify({ fixture_id:")
    request_end = html.index("})", request_start)
    request_contract = html[request_start:request_end]
    for forbidden in ("output_path", "filename", "overwrite", "customer_ready", "customer_release"):
        assert forbidden not in request_contract
    assert "window.button2GovernedInternalPdfInProgress" in html
    assert "window.button2SelectedMatchupIds" in html
    assert "button3SelectedGeneratedReportPreview" in html
    assert "button2/generate-selected-batch" in html
    assert "customer ready: false" in html
    assert "customer release authorised: false" in html
    assert "proposed_output_target_exists" in html
    assert "It was not overwritten" in html
    assert "button2GovernedInternalPdfRowIsValid" in html
    assert "fixture_only === true" in html
    assert "permanent_mutation_performed === false" in html
    assert "learning_applied" in html and "calibration_applied" in html
    assert "accuracy_ledger_written" in html and "gcid_written" in html
    assert "model_weights_changed" in html and "fighter_ratings_changed" in html
    assert "prediction_logic_changed" in html
    assert "No PDFs generated in last run." in html

    monkeypatch.setenv("AI_RISA_LOCAL_FIXTURE_MODE", "1")
    monkeypatch.setenv("AI_RISA_BUTTON2_QUEUE_PATH", str(FIXTURE))
    monkeypatch.setenv("AI_RISA_INTERNAL_PDF_OUTPUT_ROOT", str(tmp_path))
    client = app.test_client()
    payload = {
        "fixture_id": fixture["fixture_id"],
        "report_id": button2["report_id"],
        "report_version": button2["report_version"],
        "internal_test_artifact_acknowledged": True,
    }
    response = client.post("/api/button2/governed-internal-pdf/generate-v1", json=payload)
    assert response.status_code == 200
    generated = response.get_json()
    assert generated["customer_ready_possible"] is False
    assert generated["customer_release_authorized"] is False
    assert generated["queue_write_performed"] is False
    assert generated["artifact_overwritten"] is False
    assert generated["learning_applied"] is False
    assert generated["calibration_applied"] is False
    assert generated["accuracy_ledger_written"] is False
    assert generated["gcid_written"] is False
    assert generated["model_weights_changed"] is False
    assert generated["fighter_ratings_changed"] is False
    assert generated["prediction_logic_changed"] is False
    assert generated["permanent_mutation_performed"] is False

    collision = client.post("/api/button2/governed-internal-pdf/generate-v1", json=payload)
    assert collision.status_code == 422
    assert collision.get_json()["blocked_reason"] == "proposed_output_target_exists"
