"""Smoke tests for Phase 3 text extraction proof helper (v1)."""

import operator_dashboard.button2_customer_pdf_phase3_text_extraction_proof_preview_v1 as preview


def test_valid_pdf_bytes_with_required_markers_pass(monkeypatch):
    extracted_text = "\n".join(
        [
            "AI-RISA Premium Fight Report",
            "Source Traceability",
            "Visual certification:",
        ]
    )
    monkeypatch.setattr(preview, "_extract_text_with_pypdf", lambda _bytes: extracted_text)

    result = preview.run_text_extraction_proof(
        b"%PDF-1.4\n%valid",
        required_text_markers=["AI-RISA Premium Fight Report", "Visual certification:"],
        required_section_markers=["Source Traceability"],
    )

    assert result["proof_status"] == "passed"
    assert result["failure_reasons"] == []


def test_missing_text_marker_fails_closed(monkeypatch):
    monkeypatch.setattr(preview, "_extract_text_with_pypdf", lambda _bytes: "Source Traceability")

    result = preview.run_text_extraction_proof(
        b"%PDF-1.4\n%valid",
        required_text_markers=["AI-RISA Premium Fight Report"],
        required_section_markers=["Source Traceability"],
    )

    assert result["proof_status"] == "failed_closed"
    assert "missing_required_text_markers" in result["failure_reasons"]


def test_missing_section_marker_fails_closed(monkeypatch):
    monkeypatch.setattr(preview, "_extract_text_with_pypdf", lambda _bytes: "AI-RISA Premium Fight Report")

    result = preview.run_text_extraction_proof(
        b"%PDF-1.4\n%valid",
        required_text_markers=["AI-RISA Premium Fight Report"],
        required_section_markers=["Source Traceability"],
    )

    assert result["proof_status"] == "failed_closed"
    assert "missing_required_section_markers" in result["failure_reasons"]


def test_malformed_pdf_bytes_fail_closed(monkeypatch):
    def _raise(_bytes):
        raise RuntimeError("extraction_error")

    monkeypatch.setattr(preview, "_extract_text_with_pypdf", _raise)
    result = preview.run_text_extraction_proof(b"not-a-pdf")

    assert result["proof_status"] == "failed_closed"
    assert "extraction_error" in result["failure_reasons"]


def test_empty_pdf_bytes_fail_closed():
    result = preview.run_text_extraction_proof(b"")

    assert result["proof_status"] == "failed_closed"
    assert "missing_pdf_bytes" in result["failure_reasons"]


def test_pypdf_unavailable_path_fails_closed(monkeypatch):
    def _raise(_bytes):
        raise RuntimeError("extraction_library_unavailable")

    monkeypatch.setattr(preview, "_extract_text_with_pypdf", _raise)
    result = preview.run_text_extraction_proof(b"%PDF-1.4\n%valid")

    assert result["proof_status"] == "failed_closed"
    assert "extraction_library_unavailable" in result["failure_reasons"]


def test_no_pdf_generation_and_no_file_writes():
    result = preview.run_text_extraction_proof(None)

    assert result["pdf_generation_performed"] is False
    assert result["file_write_performed"] is False


def test_no_renderer_dashboard_delivery_or_certification_changes():
    result = preview.run_text_extraction_proof(None)

    assert result["renderer_behavior_changed"] is False
    assert result["dashboard_behavior_changed"] is False
    assert result["delivery_workflow_changed"] is False
    assert result["certification_automation_changed"] is False
