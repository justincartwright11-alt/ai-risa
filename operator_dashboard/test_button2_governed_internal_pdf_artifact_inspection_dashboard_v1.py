from pathlib import Path


TEMPLATE = Path(__file__).parent / "templates" / "index.html"


def test_governed_internal_pdf_inspection_dashboard_contract():
    html = TEMPLATE.read_text(encoding="utf-8")
    preview_start = html.index("Governed Internal Report Preview")
    preview_end = html.index('id="b2-internal-preview-details"', preview_start)
    preview = html[preview_start:preview_end]
    inspect_start = html.index("function button2InspectGovernedInternalPdf")
    inspect_end = html.index("function button2RenderInternalPreview", inspect_start)
    inspection = html[inspect_start:inspect_end]

    assert "Check Internal PDF Status" in preview
    assert "b2-governed-internal-pdf-inspection" in preview
    assert "This checks the existing internal test PDF only." in preview
    assert "Generate Internal Test PDF" in preview
    assert "button3" not in preview.lower()
    assert "b2-governed-internal-pdf-ack" not in preview[preview.index("b2-governed-internal-pdf-inspection"):]

    assert "window.button2GovernedInternalPdfInspectionState = 'idle'" in html
    assert "'checking'" in inspection
    assert "'absent'" in html
    assert "'present_valid'" in html
    assert "'blocked'" in html
    assert "button2GovernedInternalPdfRowIsValid(row)" in inspection
    assert "internalOutputRootConfigured !== 'true'" in inspection
    assert "Checking internal PDF status…" in html
    assert "window.button2GovernedInternalPdfInspectionIdentity" in html
    assert "button2ClearGovernedInternalPdfInspection" in html

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
