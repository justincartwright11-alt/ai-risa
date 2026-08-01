from pathlib import Path
import copy
import hashlib
import json

from operator_dashboard.app import app
from operator_dashboard.button2_governed_internal_pdf_preflight_adapter_v1 import build_button2_governed_internal_pdf_preflight_v1
from operator_dashboard.button2_governed_internal_pdf_render_adapter_v1 import render_button2_governed_internal_pdf_v1


TEMPLATE = Path(__file__).parent / "templates" / "index.html"
FIXTURE_PATH = Path(__file__).parent / "fixtures" / "closed_loop_governed_local_fixture_v1.json"
ROUTE = "/api/button2/governed-internal-pdf/inspect-v1"


def test_governed_internal_pdf_inspection_dashboard_contract():
    html = TEMPLATE.read_text(encoding="utf-8")
    preview_start = html.index("Governed Internal Report Preview")
    preview_end = html.index('id="b2-internal-preview-details"', preview_start)
    preview = html[preview_start:preview_end]
    inspection_control_start = html.index("function button2UpdateGovernedInternalPdfInspectionControl")
    inspection_control_end = html.index("function button2InspectionField", inspection_control_start)
    inspection_control = html[inspection_control_start:inspection_control_end]
    governed_control_start = html.index("function button2UpdateGovernedInternalPdfControl")
    governed_control_end = html.index("function button2SelectGovernedInternalPdfPreview", governed_control_start)
    governed_control = html[governed_control_start:governed_control_end]
    selection_start = html.index("function button2SelectGovernedInternalPdfPreview")
    selection_end = html.index("function button2RenderGovernedInternalPdfResult", selection_start)
    selection = html[selection_start:selection_end]
    refresh_start = html.index("function button2RefreshQueue")
    refresh_end = html.index("function button2ApplyEventFilter", refresh_start)
    refresh = html[refresh_start:refresh_end]
    inspect_start = html.index("function button2InspectGovernedInternalPdf")
    inspect_end = html.index("function button2RenderInternalPreview", inspect_start)
    inspection = html[inspect_start:inspect_end]
    render_start = html.index("function button2RenderGovernedInternalPdfInspection")
    present_start = html.index("payload.status === 'present_valid'", render_start)
    present_end = html.index("} else {", present_start)
    present = html[present_start:present_end]

    ids = {
        "b2-governed-internal-pdf-inspection",
        "b2-governed-internal-pdf-inspect",
        "b2-governed-internal-pdf-inspection-result",
    }
    assert all(preview.count(f'id="{element_id}"') == 1 for element_id in ids)
    assert html.index('id="b2-governed-internal-pdf-inspection"', preview_start) < html.index('id="b2-internal-preview-details"', preview_start)
    assert "Check Internal PDF Status" in preview
    assert "b2-governed-internal-pdf-inspection" in preview
    assert "This checks the existing internal test PDF only." in preview
    assert "Generate Internal Test PDF" in preview
    assert "button3" not in preview.lower()
    assert "b2-governed-internal-pdf-ack" not in preview[preview.index("b2-governed-internal-pdf-inspection"):]
    assert 'style="margin:10px 0;padding:12px;border:1px solid #6b7280;background:#171a21;display:none;"' in preview
    assert 'id="b2-governed-internal-pdf-inspect"' in preview and 'disabled>Check Internal PDF Status' in preview

    assert "window.button2GovernedInternalPdfInspectionState = 'idle'" in html
    assert "panel.style.display = button2GovernedInternalPdfRowIsValid(row) ? 'block' : 'none';" in inspection_control
    assert "button.disabled = !button2GovernedInternalPdfRowIsValid(row) || !configured || checking;" in inspection_control
    assert "ack" not in inspection_control
    assert "ack.checked" not in inspection_control
    assert "'checking'" in inspection
    assert "'absent'" in html
    assert "'present_valid'" in html
    assert "'blocked'" in html
    assert "button2GovernedInternalPdfRowIsValid(row)" in inspection
    assert "internalOutputRootConfigured !== 'true'" in inspection
    assert "Checking internal PDF status…" in html
    assert "window.button2GovernedInternalPdfInspectionIdentity" in html
    assert "button2ClearGovernedInternalPdfInspection" in html
    assert "button2UpdateGovernedInternalPdfInspectionControl();" in governed_control
    assert "!ack.checked" in governed_control
    assert governed_control.index("!ack.checked") < governed_control.index("button2UpdateGovernedInternalPdfInspectionControl();")
    assert selection.index("window.button2GovernedInternalPdfRow = row;") < selection.index("button2ClearGovernedInternalPdfInspection();")
    assert selection.index("button2ClearGovernedInternalPdfInspection();") < selection.index("button2UpdateGovernedInternalPdfControl();")
    assert selection.count("button2UpdateGovernedInternalPdfInspectionControl();") == 1
    assert "/api/button2/governed-internal-pdf/inspect-v1" not in selection
    assert "window.button2GovernedInternalPdfRow = null;" in refresh
    assert "button2ClearGovernedInternalPdfInspection();" in refresh
    assert "button2UpdateGovernedInternalPdfInspectionControl();" in refresh

    assert "fetch('/api/button2/governed-internal-pdf/inspect-v1'" in inspection
    inspection_call = html[inspect_start:html.index("function button2GenerateGovernedInternalPdf", inspect_start)]
    request_start = inspection.index("body: JSON.stringify({")
    request_end = inspection.index("})", request_start)
    request = inspection[request_start:request_end]
    assert "fixture_id: String(row.fixture_id)" in request
    assert "report_id: String(row.report_id)" in request
    assert "report_version: String(row.report_version)" in request
    for forbidden in (
        "output_root", "output_path", "path", "directory", "filename", "extension", "overwrite",
        "archive", "remove", "delete", "rename", "regenerate", "customer_ready", "customer_release",
        "internal_test_artifact_acknowledged",
    ):
        assert forbidden not in request
    assert "/api/button2/governed-internal-pdf/generate-v1" not in inspection_call

    assert "Internal test PDF not present" in html
    assert "Artifact state" in html
    assert "Expected filename" in html
    assert "Inspection completed: true" in html
    assert "PDF generated: false" in html
    assert "Internal test PDF present and valid" in html
    assert "payload.expected_filename" in present
    assert "payload.file_size_bytes" in present
    assert "Number.isInteger(payload.file_size_bytes)" in present
    assert "payload.file_size_bytes.toLocaleString('en-US') + ' bytes'" in present
    assert "boundedFilename" in present
    assert "boundedFileSize" in present
    assert "payload.filename" not in present
    assert "payload.output_filename" not in present
    assert "payload.file_size || payload.size_bytes" not in present
    assert "expected-file.pdf" not in present
    assert "11094" not in present
    assert "payload.sha256 || '—'" in present
    assert "payload.page_count || '—'" in present
    assert "boundedFilename" in present and "'—'" in present
    assert "boundedFileSize" in present and "'—'" in present
    assert "SHA-256" in html
    assert "Page count" in html
    assert "PDF signature verified" in html
    assert "Internal PDF inspection blocked" in html
    assert "Operator next action" in html
    assert "The expected internal artifact is not a valid PDF." in html
    assert "The expected internal PDF could not be read safely." in html
    assert "The artifact identity does not match the selected governed report." in html
    assert "target_outside_approved_root" in html

    assert "output_root" not in inspection
    assert "output_path" not in inspection
    assert "extracted" not in inspection.lower()
    assert "button2GovernedInternalPdfGenerated = true" in html
    assert "button2GovernedInternalPdfGenerated = false" in html
    assert "button2SelectedMatchupIds" not in inspection
    assert "button3" not in inspection.lower()
    assert "archive" in html
    assert "permanent_mutation_performed: false" in html


def test_governed_internal_pdf_inspection_present_filename_endpoint_contract(tmp_path, monkeypatch):
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    row = copy.deepcopy(fixture["button2"])
    row.update(fixture_id=fixture["fixture_id"], fixture_only=True)
    plan = build_button2_governed_internal_pdf_preflight_v1(row, tmp_path, fixture_mode=True)
    assert plan["ok"] is True
    generated = render_button2_governed_internal_pdf_v1(plan, row)
    assert generated["ok"] is True
    target = Path(generated["output_path"])
    expected_filename = target.name
    expected_size = target.stat().st_size
    expected_sha256 = hashlib.sha256(target.read_bytes()).hexdigest()

    monkeypatch.setenv("AI_RISA_LOCAL_FIXTURE_MODE", "1")
    monkeypatch.setenv("AI_RISA_BUTTON2_QUEUE_PATH", str(FIXTURE_PATH))
    monkeypatch.setenv("AI_RISA_INTERNAL_PDF_OUTPUT_ROOT", str(tmp_path))
    payload = {
        "fixture_id": fixture["fixture_id"],
        "report_id": row["report_id"],
        "report_version": row["report_version"],
    }
    before_bytes = target.read_bytes()
    response = app.test_client().post(ROUTE, json=payload)
    result = response.get_json()

    assert response.status_code == 200
    assert result["status"] == "present_valid"
    assert result["artifact_state"] == "ACTIVE_INTERNAL_TEST_ARTIFACT"
    assert result["expected_filename"] == expected_filename
    assert "/" not in result["expected_filename"] and "\\" not in result["expected_filename"]
    assert not Path(result["expected_filename"]).is_absolute()
    assert result["file_size_bytes"] == expected_size
    assert result["sha256"] == expected_sha256
    assert result["page_count"] == 1
    assert "proposed_output_path" not in result
    assert "proposed_output_directory" not in result
    assert target.read_bytes() == before_bytes
