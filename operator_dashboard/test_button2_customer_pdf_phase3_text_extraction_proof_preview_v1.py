"""Tests for Phase 3 text extraction proof preview module (v1)."""

import operator_dashboard.button2_customer_pdf_phase3_text_extraction_proof_preview_v1 as preview


def test_contract_shape_and_channel():
    result = preview.run_text_extraction_proof(b"%PDF-1.4")
    assert result["schema_version"] == "button2.phase3.text_extraction_proof.v1"
    assert result["proof_channel"] == "text_extraction"


def test_missing_pdf_bytes_fails_closed():
    result = preview.run_text_extraction_proof(None)
    assert result["proof_status"] == "failed_closed"
    assert "missing_pdf_bytes" in result["failure_reasons"]


def test_library_unavailable_fails_closed(monkeypatch):
    def _raise(_bytes):
        raise RuntimeError("extraction_library_unavailable")

    monkeypatch.setattr(preview, "_extract_text_with_pypdf", _raise)
    result = preview.run_text_extraction_proof(b"%PDF-1.4")
    assert result["proof_status"] == "failed_closed"
    assert "extraction_library_unavailable" in result["failure_reasons"]


def test_extraction_error_fails_closed(monkeypatch):
    def _raise(_bytes):
        raise RuntimeError("extraction_error")

    monkeypatch.setattr(preview, "_extract_text_with_pypdf", _raise)
    result = preview.run_text_extraction_proof(b"%PDF-1.4")
    assert result["proof_status"] == "failed_closed"
    assert "extraction_error" in result["failure_reasons"]


def test_missing_required_text_markers_fails_closed(monkeypatch):
    monkeypatch.setattr(preview, "_extract_text_with_pypdf", lambda _bytes: "Only header text")
    result = preview.run_text_extraction_proof(
        b"%PDF-1.4",
        required_text_markers=["AI-RISA Premium Fight Report", "Source Traceability"],
    )
    assert result["proof_status"] == "failed_closed"
    assert "missing_required_text_markers" in result["failure_reasons"]


def test_missing_required_section_markers_fails_closed(monkeypatch):
    monkeypatch.setattr(preview, "_extract_text_with_pypdf", lambda _bytes: "AI-RISA Premium Fight Report")
    result = preview.run_text_extraction_proof(
        b"%PDF-1.4",
        required_section_markers=["Source Traceability", "Visual QA"],
    )
    assert result["proof_status"] == "failed_closed"
    assert "missing_required_section_markers" in result["failure_reasons"]


def test_all_markers_present_passes(monkeypatch):
    extracted = "\n".join(
        [
            "AI-RISA Premium Fight Report",
            "Source Traceability",
            "Visual QA",
            "Visual certification:",
        ]
    )
    monkeypatch.setattr(preview, "_extract_text_with_pypdf", lambda _bytes: extracted)
    result = preview.run_text_extraction_proof(
        b"%PDF-1.4",
        required_text_markers=["AI-RISA Premium Fight Report", "Visual certification:"],
        required_section_markers=["Source Traceability", "Visual QA"],
    )
    assert result["proof_status"] == "passed"
    assert result["failure_reasons"] == []


def test_no_pdf_or_file_side_effects():
    result = preview.run_text_extraction_proof(None)
    assert result["pdf_generation_performed"] is False
    assert result["file_write_performed"] is False


def test_no_renderer_dashboard_delivery_or_certification_changes():
    result = preview.run_text_extraction_proof(None)
    assert result["renderer_behavior_changed"] is False
    assert result["dashboard_behavior_changed"] is False
    assert result["delivery_workflow_changed"] is False
    assert result["certification_automation_changed"] is False
