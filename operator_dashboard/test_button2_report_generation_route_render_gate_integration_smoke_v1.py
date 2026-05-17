"""
Smoke Test: Button 2 Report Generation Route Render Gate Integration (v1)

Executable proof that the approval-gated Button 2 route integration:
  - Rejects unapproved requests with 403 before any side effects
  - Writes PDF to configured temp output root only after full approval + composition + render + path resolution
  - Fails closed on invalid fight_id, missing output root, composition failure, render failure, path resolution failure
  - Keeps visual QA optional and best-effort
  - Preserves existing Button 2 test coverage

This smoke test uses real file I/O (temp directories) to prove file write behavior.
"""

import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from operator_dashboard.button2_report_generation_route_render_gate_integration_v1 import (
    generate_button2_report_render_gate_integration,
)


# ---------------------------------------------------------------------------
# Smoke Test: Approval Guard + No Side Effects
# ---------------------------------------------------------------------------

class TestSmokeApprovalGuardNoSideEffects:
    """Prove no composition/render/write occurs without approval."""

    def test_no_approval_returns_403_no_composition_call(self, tmp_path):
        """No approval → 403 immediately, composition never called."""
        mock_compose = MagicMock()
        req = {
            "operator_approved": False,
            "fight_id": "test_fight",
            "ingest_payload": {"destination_marker": "button2_report_generation_preview"},
        }
        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_readonly_dossier_handoff_ingest_preview", mock_compose):
            result = generate_button2_report_render_gate_integration(req)
        assert result["ok"] is False
        assert result["error"] == "operator_approval_required"
        mock_compose.assert_not_called()

    def test_no_approval_returns_403_no_render_call(self, tmp_path):
        """No approval → 403 immediately, render never called."""
        mock_render = MagicMock()
        req = {
            "operator_approved": False,
            "fight_id": "test_fight",
            "ingest_payload": {},
        }
        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.render_button2_pdf", mock_render):
            result = generate_button2_report_render_gate_integration(req)
        mock_render.assert_not_called()

    def test_no_approval_returns_403_no_file_write(self, tmp_path):
        """No approval → 403 immediately, no file written anywhere."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        req = {
            "operator_approved": False,
            "fight_id": "test_fight",
            "ingest_payload": {},
        }
        result = generate_button2_report_render_gate_integration(req)
        assert result["ok"] is False
        # Verify no files were created
        assert len(list(output_dir.glob("**/*"))) == 0


# ---------------------------------------------------------------------------
# Smoke Test: Approval + Full Success Path with Real File I/O
# ---------------------------------------------------------------------------

class TestSmokeApprovedSuccessRealFileIO:
    """Prove approved request writes PDF to temp output root."""

    def _mock_all_with_valid_defaults(self):
        """Return dict of mocks for successful full flow."""
        return {
            "ingest": MagicMock(return_value={
                "ok": True,
                "button2_ingest_preview_context": {
                    "destination_marker": "button2_report_generation_preview",
                    "dossier_summary_preview": "Test summary.",
                }
            }),
            "context": MagicMock(return_value={
                "ok": True,
                "report_context_preview": {
                    "destination_marker": "button2_report_generation_preview",
                    "report_context_kind": "dossier_handoff_report_context_preview",
                    "handoff_summary_preview": "Test summary.",
                    "page_block_boundaries": [],
                    "hierarchy_markers": [],
                    "source_traceability": [],
                    "overlap_proof": "clear",
                    "off_page_text_proof": "clear",
                    "visual_certification_status": "not_certified",
                }
            }),
            "html": MagicMock(return_value={
                "ok": True,
                "html_content": "<html><body>Test PDF content</body></html>",
            }),
            "render": MagicMock(return_value={
                "pdf_bytes": b"FAKE_PDF_CONTENT_12345",
                "geometry_data": None,
            }),
        }

    def test_approved_request_writes_pdf_to_temp_root(self, tmp_path):
        """Approved request with valid fight_id writes PDF to configured temp root."""
        output_root = tmp_path / "pdf_output"
        output_root.mkdir()
        
        mocks = self._mock_all_with_valid_defaults()
        req = {
            "operator_approved": True,
            "fight_id": "my_test_fight_key",
            "ingest_payload": {"destination_marker": "button2_report_generation_preview"},
        }
        
        with patch.dict(os.environ, {"BUTTON2_PDF_OUTPUT_ROOT": str(output_root)}):
            with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_readonly_dossier_handoff_ingest_preview", mocks["ingest"]):
                with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_dossier_handoff_report_context_preview", mocks["context"]):
                    with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_report_html", mocks["html"]):
                        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.render_button2_pdf", mocks["render"]):
                            result = generate_button2_report_render_gate_integration(req)
        
        assert result["ok"] is True
        assert result["file_write_performed"] is True
        assert "my_test_fight_key_premium.pdf" in result["output_path"]
        
        # Verify file actually written
        output_file = output_root / "my_test_fight_key_premium.pdf"
        assert output_file.exists()
        assert output_file.read_bytes() == b"FAKE_PDF_CONTENT_12345"

    def test_approved_request_returns_output_path(self, tmp_path):
        """Approved request returns the output path in response."""
        output_root = tmp_path / "pdf_output"
        output_root.mkdir()
        
        mocks = self._mock_all_with_valid_defaults()
        req = {
            "operator_approved": True,
            "fight_id": "another_fight_key",
            "ingest_payload": {"destination_marker": "button2_report_generation_preview"},
        }
        
        with patch.dict(os.environ, {"BUTTON2_PDF_OUTPUT_ROOT": str(output_root)}):
            with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_readonly_dossier_handoff_ingest_preview", mocks["ingest"]):
                with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_dossier_handoff_report_context_preview", mocks["context"]):
                    with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_report_html", mocks["html"]):
                        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.render_button2_pdf", mocks["render"]):
                            result = generate_button2_report_render_gate_integration(req)
        
        assert "output_path" in result
        assert str(output_root) in result["output_path"]


# ---------------------------------------------------------------------------
# Smoke Test: Failure Modes (No Partial Writes)
# ---------------------------------------------------------------------------

class TestSmokeFailureModesNoDirtyState:
    """Prove failures at each stage prevent file write (no partial writes)."""

    def test_invalid_fight_id_no_file_write(self, tmp_path):
        """Invalid fight_id prevents path resolution and file write."""
        output_root = tmp_path / "pdf_output"
        output_root.mkdir()
        
        mocks = {
            "ingest": MagicMock(return_value={
                "ok": True,
                "button2_ingest_preview_context": {
                    "destination_marker": "button2_report_generation_preview",
                }
            }),
            "context": MagicMock(return_value={
                "ok": True,
                "report_context_preview": {
                    "destination_marker": "button2_report_generation_preview",
                    "report_context_kind": "dossier_handoff_report_context_preview",
                    "handoff_summary_preview": "Test.",
                    "page_block_boundaries": [],
                    "hierarchy_markers": [],
                    "source_traceability": [],
                    "overlap_proof": "clear",
                    "off_page_text_proof": "clear",
                    "visual_certification_status": "not_certified",
                }
            }),
            "html": MagicMock(return_value={
                "ok": True,
                "html_content": "<html><body>Test</body></html>",
            }),
            "render": MagicMock(return_value={
                "pdf_bytes": b"FAKE_PDF",
                "geometry_data": None,
            }),
        }
        
        req = {
            "operator_approved": True,
            "fight_id": "bad/path/key",  # Invalid: contains /
            "ingest_payload": {"destination_marker": "button2_report_generation_preview"},
        }
        
        with patch.dict(os.environ, {"BUTTON2_PDF_OUTPUT_ROOT": str(output_root)}):
            with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_readonly_dossier_handoff_ingest_preview", mocks["ingest"]):
                with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_dossier_handoff_report_context_preview", mocks["context"]):
                    with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_report_html", mocks["html"]):
                        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.render_button2_pdf", mocks["render"]):
                            result = generate_button2_report_render_gate_integration(req)
        
        assert result["ok"] is False
        assert result["error"] == "output_path_invalid"
        assert result["file_write_performed"] is False
        # Verify no files written
        assert len(list(output_root.glob("**/*"))) == 0

    def test_missing_output_root_no_file_write(self, tmp_path):
        """Missing output root configuration prevents file write."""
        mocks = {
            "ingest": MagicMock(return_value={
                "ok": True,
                "button2_ingest_preview_context": {
                    "destination_marker": "button2_report_generation_preview",
                }
            }),
            "context": MagicMock(return_value={
                "ok": True,
                "report_context_preview": {
                    "destination_marker": "button2_report_generation_preview",
                    "report_context_kind": "dossier_handoff_report_context_preview",
                    "handoff_summary_preview": "Test.",
                    "page_block_boundaries": [],
                    "hierarchy_markers": [],
                    "source_traceability": [],
                    "overlap_proof": "clear",
                    "off_page_text_proof": "clear",
                    "visual_certification_status": "not_certified",
                }
            }),
            "html": MagicMock(return_value={
                "ok": True,
                "html_content": "<html><body>Test</body></html>",
            }),
            "render": MagicMock(return_value={
                "pdf_bytes": b"FAKE_PDF",
                "geometry_data": None,
            }),
        }
        
        req = {
            "operator_approved": True,
            "fight_id": "valid_fight_key",
            "ingest_payload": {"destination_marker": "button2_report_generation_preview"},
        }
        
        # Clear the env var
        env_copy = {k: v for k, v in os.environ.items() if k != "BUTTON2_PDF_OUTPUT_ROOT"}
        with patch.dict(os.environ, env_copy, clear=True):
            with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_readonly_dossier_handoff_ingest_preview", mocks["ingest"]):
                with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_dossier_handoff_report_context_preview", mocks["context"]):
                    with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_report_html", mocks["html"]):
                        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.render_button2_pdf", mocks["render"]):
                            result = generate_button2_report_render_gate_integration(req)
        
        assert result["ok"] is False
        assert result["error"] == "output_path_invalid"
        assert result["file_write_performed"] is False

    def test_render_failure_no_file_write(self, tmp_path):
        """Render failure prevents path resolution and file write."""
        output_root = tmp_path / "pdf_output"
        output_root.mkdir()
        
        mocks = {
            "ingest": MagicMock(return_value={
                "ok": True,
                "button2_ingest_preview_context": {
                    "destination_marker": "button2_report_generation_preview",
                }
            }),
            "context": MagicMock(return_value={
                "ok": True,
                "report_context_preview": {
                    "destination_marker": "button2_report_generation_preview",
                    "report_context_kind": "dossier_handoff_report_context_preview",
                    "handoff_summary_preview": "Test.",
                    "page_block_boundaries": [],
                    "hierarchy_markers": [],
                    "source_traceability": [],
                    "overlap_proof": "clear",
                    "off_page_text_proof": "clear",
                    "visual_certification_status": "not_certified",
                }
            }),
            "html": MagicMock(return_value={
                "ok": True,
                "html_content": "<html><body>Test</body></html>",
            }),
            "render": MagicMock(side_effect=Exception("PDF render failed")),
        }
        
        req = {
            "operator_approved": True,
            "fight_id": "valid_fight_key",
            "ingest_payload": {"destination_marker": "button2_report_generation_preview"},
        }
        
        with patch.dict(os.environ, {"BUTTON2_PDF_OUTPUT_ROOT": str(output_root)}):
            with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_readonly_dossier_handoff_ingest_preview", mocks["ingest"]):
                with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_dossier_handoff_report_context_preview", mocks["context"]):
                    with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_report_html", mocks["html"]):
                        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.render_button2_pdf", mocks["render"]):
                            result = generate_button2_report_render_gate_integration(req)
        
        assert result["ok"] is False
        assert "pdf_render" in result["error"]
        assert result["file_write_performed"] is False
        # Verify no files written
        assert len(list(output_root.glob("**/*"))) == 0


# ---------------------------------------------------------------------------
# Smoke Test: Visual QA Optional and Best-Effort
# ---------------------------------------------------------------------------

class TestSmokeVisualQAOptional:
    """Prove visual QA is disabled by default and doesn't crash report generation."""

    def _mock_all_with_valid_defaults(self):
        """Return dict of mocks for successful full flow."""
        return {
            "ingest": MagicMock(return_value={
                "ok": True,
                "button2_ingest_preview_context": {
                    "destination_marker": "button2_report_generation_preview",
                    "dossier_summary_preview": "Test summary.",
                }
            }),
            "context": MagicMock(return_value={
                "ok": True,
                "report_context_preview": {
                    "destination_marker": "button2_report_generation_preview",
                    "report_context_kind": "dossier_handoff_report_context_preview",
                    "handoff_summary_preview": "Test summary.",
                    "page_block_boundaries": [],
                    "hierarchy_markers": [],
                    "source_traceability": [],
                    "overlap_proof": "clear",
                    "off_page_text_proof": "clear",
                    "visual_certification_status": "not_certified",
                }
            }),
            "html": MagicMock(return_value={
                "ok": True,
                "html_content": "<html><body>Test PDF content</body></html>",
            }),
            "render": MagicMock(return_value={
                "pdf_bytes": b"FAKE_PDF_CONTENT_12345",
                "geometry_data": None,
            }),
        }

    def test_visual_qa_disabled_by_default(self, tmp_path):
        """Visual QA is disabled by default, no qa_summary in response."""
        output_root = tmp_path / "pdf_output"
        output_root.mkdir()
        
        mocks = self._mock_all_with_valid_defaults()
        req = {
            "operator_approved": True,
            "fight_id": "test_fight_key",
            "ingest_payload": {"destination_marker": "button2_report_generation_preview"},
        }
        
        with patch.dict(os.environ, {"BUTTON2_PDF_OUTPUT_ROOT": str(output_root)}, clear=True):
            with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_readonly_dossier_handoff_ingest_preview", mocks["ingest"]):
                with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_dossier_handoff_report_context_preview", mocks["context"]):
                    with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_report_html", mocks["html"]):
                        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.render_button2_pdf", mocks["render"]):
                            result = generate_button2_report_render_gate_integration(req)
        
        assert result["ok"] is True
        assert result["visual_qa_enabled"] is False
        assert result["qa_summary"] is None

    def test_visual_qa_enabled_produces_qa_summary(self, tmp_path):
        """Visual QA enabled produces qa_summary in response."""
        output_root = tmp_path / "pdf_output"
        output_root.mkdir()
        
        mocks = self._mock_all_with_valid_defaults()
        mocks["render"] = MagicMock(return_value={
            "pdf_bytes": b"FAKE_PDF_CONTENT_12345",
            "geometry_data": {"blocks": []},  # Not None, triggers QA
        })
        
        req = {
            "operator_approved": True,
            "fight_id": "test_fight_key",
            "ingest_payload": {"destination_marker": "button2_report_generation_preview"},
        }
        
        with patch.dict(os.environ, {"BUTTON2_PDF_OUTPUT_ROOT": str(output_root), "BUTTON2_VISUAL_QA": "1"}):
            with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_readonly_dossier_handoff_ingest_preview", mocks["ingest"]):
                with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_dossier_handoff_report_context_preview", mocks["context"]):
                    with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_report_html", mocks["html"]):
                        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.render_button2_pdf", mocks["render"]):
                            with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.run_geometry_proof", return_value={
                                "overlap_proof": "clear",
                                "off_page_text_proof": "clear",
                                "visual_certification_status": "not_certified",
                            }):
                                result = generate_button2_report_render_gate_integration(req)
        
        assert result["ok"] is True
        assert result["visual_qa_enabled"] is True
        assert result["qa_summary"] is not None
        assert "overlap_proof" in result["qa_summary"]

    def test_visual_qa_failure_does_not_crash_report(self, tmp_path):
        """Visual QA failure is best-effort, doesn't crash report generation."""
        output_root = tmp_path / "pdf_output"
        output_root.mkdir()
        
        mocks = self._mock_all_with_valid_defaults()
        mocks["render"] = MagicMock(return_value={
            "pdf_bytes": b"FAKE_PDF_CONTENT_12345",
            "geometry_data": {"blocks": []},
        })
        
        req = {
            "operator_approved": True,
            "fight_id": "test_fight_key",
            "ingest_payload": {"destination_marker": "button2_report_generation_preview"},
        }
        
        with patch.dict(os.environ, {"BUTTON2_PDF_OUTPUT_ROOT": str(output_root), "BUTTON2_VISUAL_QA": "1"}):
            with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_readonly_dossier_handoff_ingest_preview", mocks["ingest"]):
                with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_dossier_handoff_report_context_preview", mocks["context"]):
                    with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_report_html", mocks["html"]):
                        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.render_button2_pdf", mocks["render"]):
                            with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.run_geometry_proof", side_effect=Exception("QA crashed")):
                                result = generate_button2_report_render_gate_integration(req)
        
        # Report generation still succeeds despite QA failure
        assert result["ok"] is True
        assert result["file_write_performed"] is True
        assert result["qa_summary"] is None  # QA failed, so no summary


# ---------------------------------------------------------------------------
# Smoke Test: Telemetry Flags Correct
# ---------------------------------------------------------------------------

class TestSmokeTelemetryFlags:
    """Prove telemetry flags are set correctly throughout flow."""

    def _mock_all_with_valid_defaults(self):
        """Return dict of mocks for successful full flow."""
        return {
            "ingest": MagicMock(return_value={
                "ok": True,
                "button2_ingest_preview_context": {
                    "destination_marker": "button2_report_generation_preview",
                    "dossier_summary_preview": "Test summary.",
                }
            }),
            "context": MagicMock(return_value={
                "ok": True,
                "report_context_preview": {
                    "destination_marker": "button2_report_generation_preview",
                    "report_context_kind": "dossier_handoff_report_context_preview",
                    "handoff_summary_preview": "Test summary.",
                    "page_block_boundaries": [],
                    "hierarchy_markers": [],
                    "source_traceability": [],
                    "overlap_proof": "clear",
                    "off_page_text_proof": "clear",
                    "visual_certification_status": "not_certified",
                }
            }),
            "html": MagicMock(return_value={
                "ok": True,
                "html_content": "<html><body>Test PDF content</body></html>",
            }),
            "render": MagicMock(return_value={
                "pdf_bytes": b"FAKE_PDF_CONTENT_12345",
                "geometry_data": None,
            }),
        }

    def test_success_telemetry_flags(self, tmp_path):
        """Successful request sets correct telemetry flags."""
        output_root = tmp_path / "pdf_output"
        output_root.mkdir()
        
        mocks = self._mock_all_with_valid_defaults()
        req = {
            "operator_approved": True,
            "fight_id": "test_fight_key",
            "ingest_payload": {"destination_marker": "button2_report_generation_preview"},
        }
        
        with patch.dict(os.environ, {"BUTTON2_PDF_OUTPUT_ROOT": str(output_root)}):
            with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_readonly_dossier_handoff_ingest_preview", mocks["ingest"]):
                with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_dossier_handoff_report_context_preview", mocks["context"]):
                    with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_report_html", mocks["html"]):
                        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.render_button2_pdf", mocks["render"]):
                            result = generate_button2_report_render_gate_integration(req)
        
        assert result["ok"] is True
        assert result["preview_only"] is False
        assert result["gate2_approval_required"] is True
        assert result["gate2_bypass_performed"] is False
        assert result["pdf_generation_performed"] is True
        assert result["file_write_performed"] is True

    def test_failure_telemetry_flags(self, tmp_path):
        """Failed request sets correct telemetry flags."""
        mocks = {
            "ingest": MagicMock(return_value={
                "ok": False,
                "error": "invalid_marker",
                "button2_ingest_preview_context": None,
            }),
        }
        
        req = {
            "operator_approved": True,
            "fight_id": "test_fight_key",
            "ingest_payload": {"destination_marker": "wrong_marker"},
        }
        
        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_readonly_dossier_handoff_ingest_preview", mocks["ingest"]):
            result = generate_button2_report_render_gate_integration(req)
        
        assert result["ok"] is False
        assert result["pdf_generation_performed"] is False
        assert result["file_write_performed"] is False
        assert result["gate2_approval_required"] is True
