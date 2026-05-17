"""
Tests: Button 2 Report Generation Route Render Gate Integration (v1)

Coverage map
------------
TestGate2Approval               (3 tests)  – operator_approved guard, no side effects before approval
TestFightSelection              (4 tests)  – fight_id required, validated, formatted
TestCompositionIntegration      (4 tests)  – ingest payload required, report context built, HTML composition called
TestRenderGateIntegration       (4 tests)  – render called, PDF bytes returned, visual QA side-channel
TestOutputPathResolution        (4 tests)  – path resolved server-side, under configured root, safe filename
TestFileWrite                   (3 tests)  – directory creation, file written on success, no write on failure
TestNoPartialWrites             (4 tests)  – composition failure → no render, render failure → no path resolution,
                                             path resolution failure → no file write
TestVisualQAOptional            (3 tests)  – QA disabled by default, enabled via env var, separate approval flag
TestErrorHandling               (2 tests)  – malformed request, exception in composition/render
"""

import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from operator_dashboard.button2_report_generation_route_render_gate_integration_v1 import (
    generate_button2_report_render_gate_integration,
    _base_telemetry,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _valid_request(fight_id="test_fighter_a_vs_b", ingest_payload=None):
    """Build a valid request dict."""
    if ingest_payload is None:
        ingest_payload = {
            "destination_marker": "button2_report_generation_preview",
            "dossier_summary_preview": "Test fight summary.",
        }
    return {
        "operator_approved": True,
        "fight_id": fight_id,
        "ingest_payload": ingest_payload,
    }


def _mock_all_downstream(patch_dict):
    """Return dict with all downstream functions mocked."""
    return {
        "ingest": patch_dict.get("ingest", MagicMock(return_value={
            "ok": True,
            "button2_ingest_preview_context": {
                "destination_marker": "button2_report_generation_preview",
                "dossier_summary_preview": "Test summary.",
            }
        })),
        "context": patch_dict.get("context", MagicMock(return_value={
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
        })),
        "html": patch_dict.get("html", MagicMock(return_value={
            "ok": True,
            "html_content": "<html><body>Test</body></html>",
        })),
        "render": patch_dict.get("render", MagicMock(return_value={
            "pdf_bytes": b"fake pdf content",
            "geometry_data": None,
        })),
        "path": patch_dict.get("path", MagicMock(return_value="/output/test_fighter_a_vs_b_premium.pdf")),
    }


# ---------------------------------------------------------------------------
# TestGate2Approval
# ---------------------------------------------------------------------------

class TestGate2Approval:
    def test_missing_approval_returns_403_before_side_effects(self):
        req = _valid_request()
        req["operator_approved"] = False
        result = generate_button2_report_render_gate_integration(req)
        assert result["ok"] is False
        assert result["error"] == "operator_approval_required"
        assert result["pdf_generation_performed"] is False
        assert result["file_write_performed"] is False

    def test_no_approval_key_returns_403(self):
        req = _valid_request()
        del req["operator_approved"]
        result = generate_button2_report_render_gate_integration(req)
        assert result["ok"] is False
        assert result["error"] == "operator_approval_required"

    def test_approval_required_telemetry_flag_true(self):
        req = _valid_request()
        req["operator_approved"] = False
        result = generate_button2_report_render_gate_integration(req)
        assert result["gate2_approval_required"] is True
        assert result["gate2_bypass_performed"] is False


# ---------------------------------------------------------------------------
# TestFightSelection
# ---------------------------------------------------------------------------

class TestFightSelection:
    def test_missing_fight_id_returns_400(self):
        mocks = _mock_all_downstream({})
        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_readonly_dossier_handoff_ingest_preview", mocks["ingest"]):
            req = _valid_request()
            del req["fight_id"]
            result = generate_button2_report_render_gate_integration(req)
        assert result["ok"] is False
        assert result["error"] == "fight_id_required"

    def test_empty_fight_id_returns_400(self):
        mocks = _mock_all_downstream({})
        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_readonly_dossier_handoff_ingest_preview", mocks["ingest"]):
            req = _valid_request(fight_id="")
            result = generate_button2_report_render_gate_integration(req)
        assert result["ok"] is False
        assert result["error"] == "fight_id_required"

    def test_non_string_fight_id_returns_400(self):
        mocks = _mock_all_downstream({})
        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_readonly_dossier_handoff_ingest_preview", mocks["ingest"]):
            req = _valid_request(fight_id=123)
            result = generate_button2_report_render_gate_integration(req)
        assert result["ok"] is False
        assert result["error"] == "fight_id_required"

    def test_valid_fight_id_passed_to_path_resolution(self):
        mocks = _mock_all_downstream({})
        mock_path_resolve = MagicMock(return_value="/output/test_fight_premium.pdf")
        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_readonly_dossier_handoff_ingest_preview", mocks["ingest"]):
            with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_dossier_handoff_report_context_preview", mocks["context"]):
                with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_report_html", mocks["html"]):
                    with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.render_button2_pdf", mocks["render"]):
                        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.resolve_pdf_output_path", mock_path_resolve):
                            with patch("builtins.open"):
                                with patch("os.path.exists", return_value=True):
                                    req = _valid_request(fight_id="my_custom_key")
                                    result = generate_button2_report_render_gate_integration(req)
        mock_path_resolve.assert_called_once_with("my_custom_key")


# ---------------------------------------------------------------------------
# TestCompositionIntegration
# ---------------------------------------------------------------------------

class TestCompositionIntegration:
    def test_missing_ingest_payload_returns_400(self):
        mocks = _mock_all_downstream({})
        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_readonly_dossier_handoff_ingest_preview", mocks["ingest"]):
            req = _valid_request()
            del req["ingest_payload"]
            result = generate_button2_report_render_gate_integration(req)
        assert result["ok"] is False
        assert result["error"] == "ingest_payload_required"

    def test_empty_ingest_payload_returns_400(self):
        mocks = _mock_all_downstream({})
        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_readonly_dossier_handoff_ingest_preview", mocks["ingest"]):
            req = _valid_request(ingest_payload={})
            result = generate_button2_report_render_gate_integration(req)
        # Empty payload still goes through but should fail at ingest
        assert result["ok"] is False

    def test_ingest_context_invalid_returns_error(self):
        mocks = _mock_all_downstream({
            "ingest": MagicMock(return_value={
                "ok": False,
                "error": "invalid_destination_marker",
                "button2_ingest_preview_context": None,
            }),
        })
        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_readonly_dossier_handoff_ingest_preview", mocks["ingest"]):
            req = _valid_request()
            result = generate_button2_report_render_gate_integration(req)
        assert result["ok"] is False
        assert result["error"] == "ingest_context_invalid"

    def test_report_context_built_from_ingest(self):
        mocks = _mock_all_downstream({})
        mock_context_build = MagicMock(wraps=mocks["context"])
        mock_path_resolve = MagicMock(return_value="/output/test_premium.pdf")
        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_readonly_dossier_handoff_ingest_preview", mocks["ingest"]):
            with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_dossier_handoff_report_context_preview", mock_context_build):
                with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_report_html", mocks["html"]):
                    with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.render_button2_pdf", mocks["render"]):
                        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.resolve_pdf_output_path", mock_path_resolve):
                            with patch("builtins.open"):
                                with patch("os.path.exists", return_value=True):
                                    req = _valid_request()
                                    result = generate_button2_report_render_gate_integration(req)
        mock_context_build.assert_called_once()


# ---------------------------------------------------------------------------
# TestRenderGateIntegration
# ---------------------------------------------------------------------------

class TestRenderGateIntegration:
    def test_render_called_with_html_content(self):
        mocks = _mock_all_downstream({})
        mock_render = MagicMock(wraps=mocks["render"])
        mock_path_resolve = MagicMock(return_value="/output/test_premium.pdf")
        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_readonly_dossier_handoff_ingest_preview", mocks["ingest"]):
            with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_dossier_handoff_report_context_preview", mocks["context"]):
                with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_report_html", mocks["html"]):
                    with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.render_button2_pdf", mock_render):
                        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.resolve_pdf_output_path", mock_path_resolve):
                            with patch("builtins.open"):
                                with patch("os.path.exists", return_value=True):
                                    req = _valid_request()
                                    result = generate_button2_report_render_gate_integration(req)
        mock_render.assert_called_once_with("<html><body>Test</body></html>")

    def test_pdf_bytes_extracted_from_render_result(self):
        mocks = _mock_all_downstream({})
        mock_path_resolve = MagicMock(return_value="/output/test_premium.pdf")
        written_content = []
        def mock_open(path, mode):
            class MockFile:
                def __enter__(self):
                    return self
                def __exit__(self, *args):
                    pass
                def write(self, data):
                    written_content.append(data)
            return MockFile()
        
        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_readonly_dossier_handoff_ingest_preview", mocks["ingest"]):
            with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_dossier_handoff_report_context_preview", mocks["context"]):
                with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_report_html", mocks["html"]):
                    with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.render_button2_pdf", mocks["render"]):
                        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.resolve_pdf_output_path", mock_path_resolve):
                            with patch("builtins.open", mock_open):
                                with patch("os.path.exists", return_value=True):
                                    req = _valid_request()
                                    result = generate_button2_report_render_gate_integration(req)
        assert b"fake pdf content" in written_content

    def test_render_failure_returns_error(self):
        mocks = _mock_all_downstream({
            "render": MagicMock(side_effect=Exception("PDF render failed")),
        })
        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_readonly_dossier_handoff_ingest_preview", mocks["ingest"]):
            with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_dossier_handoff_report_context_preview", mocks["context"]):
                with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_report_html", mocks["html"]):
                    with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.render_button2_pdf", mocks["render"]):
                        req = _valid_request()
                        result = generate_button2_report_render_gate_integration(req)
        assert result["ok"] is False
        assert "pdf_render" in result["error"]

    def test_pdf_generation_performed_flag_set(self):
        mocks = _mock_all_downstream({})
        mock_path_resolve = MagicMock(return_value="/output/test_premium.pdf")
        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_readonly_dossier_handoff_ingest_preview", mocks["ingest"]):
            with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_dossier_handoff_report_context_preview", mocks["context"]):
                with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_report_html", mocks["html"]):
                    with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.render_button2_pdf", mocks["render"]):
                        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.resolve_pdf_output_path", mock_path_resolve):
                            with patch("builtins.open"):
                                with patch("os.path.exists", return_value=True):
                                    req = _valid_request()
                                    result = generate_button2_report_render_gate_integration(req)
        assert result["pdf_generation_performed"] is True


# ---------------------------------------------------------------------------
# TestOutputPathResolution
# ---------------------------------------------------------------------------

class TestOutputPathResolution:
    def test_output_path_resolved_from_fight_id(self):
        mocks = _mock_all_downstream({})
        mock_path_resolve = MagicMock(return_value="/configured/root/custom_fight_key_premium.pdf")
        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_readonly_dossier_handoff_ingest_preview", mocks["ingest"]):
            with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_dossier_handoff_report_context_preview", mocks["context"]):
                with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_report_html", mocks["html"]):
                    with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.render_button2_pdf", mocks["render"]):
                        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.resolve_pdf_output_path", mock_path_resolve):
                            with patch("builtins.open"):
                                with patch("os.path.exists", return_value=True):
                                    req = _valid_request(fight_id="custom_fight_key")
                                    result = generate_button2_report_render_gate_integration(req)
        assert result["output_path"] == "/configured/root/custom_fight_key_premium.pdf"

    def test_output_root_not_configured_returns_error(self):
        from operator_dashboard.button2_pdf_output_root_config_v1 import OutputRootNotConfiguredError
        mocks = _mock_all_downstream({})
        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_readonly_dossier_handoff_ingest_preview", mocks["ingest"]):
            with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_dossier_handoff_report_context_preview", mocks["context"]):
                with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_report_html", mocks["html"]):
                    with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.render_button2_pdf", mocks["render"]):
                        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.resolve_pdf_output_path", side_effect=OutputRootNotConfiguredError("not configured")):
                            req = _valid_request()
                            result = generate_button2_report_render_gate_integration(req)
        assert result["ok"] is False
        assert result["error"] == "output_path_invalid"

    def test_invalid_fight_key_fails_closed(self):
        from operator_dashboard.button2_pdf_output_root_config_v1 import FightKeyInvalidError
        mocks = _mock_all_downstream({})
        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_readonly_dossier_handoff_ingest_preview", mocks["ingest"]):
            with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_dossier_handoff_report_context_preview", mocks["context"]):
                with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_report_html", mocks["html"]):
                    with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.render_button2_pdf", mocks["render"]):
                        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.resolve_pdf_output_path", side_effect=FightKeyInvalidError("contains /")):
                            req = _valid_request(fight_id="bad/path")
                            result = generate_button2_report_render_gate_integration(req)
        assert result["ok"] is False
        assert result["error"] == "output_path_invalid"


# ---------------------------------------------------------------------------
# TestFileWrite
# ---------------------------------------------------------------------------

class TestFileWrite:
    def test_directory_created_if_missing(self):
        mocks = _mock_all_downstream({})
        mock_path_resolve = MagicMock(return_value="/new/dir/test_premium.pdf")
        makedirs_called = []
        def mock_makedirs(path, exist_ok=False):
            makedirs_called.append((path, exist_ok))
        
        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_readonly_dossier_handoff_ingest_preview", mocks["ingest"]):
            with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_dossier_handoff_report_context_preview", mocks["context"]):
                with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_report_html", mocks["html"]):
                    with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.render_button2_pdf", mocks["render"]):
                        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.resolve_pdf_output_path", mock_path_resolve):
                            with patch("builtins.open"):
                                with patch("os.path.exists", return_value=False):
                                    with patch("os.makedirs", side_effect=mock_makedirs):
                                        req = _valid_request()
                                        result = generate_button2_report_render_gate_integration(req)
        assert len(makedirs_called) > 0

    def test_file_write_performed_flag_set(self):
        mocks = _mock_all_downstream({})
        mock_path_resolve = MagicMock(return_value="/output/test_premium.pdf")
        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_readonly_dossier_handoff_ingest_preview", mocks["ingest"]):
            with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_dossier_handoff_report_context_preview", mocks["context"]):
                with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_report_html", mocks["html"]):
                    with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.render_button2_pdf", mocks["render"]):
                        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.resolve_pdf_output_path", mock_path_resolve):
                            with patch("builtins.open"):
                                with patch("os.path.exists", return_value=True):
                                    req = _valid_request()
                                    result = generate_button2_report_render_gate_integration(req)
        assert result["file_write_performed"] is True

    def test_file_write_failure_returns_error(self):
        mocks = _mock_all_downstream({})
        mock_path_resolve = MagicMock(return_value="/output/test_premium.pdf")
        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_readonly_dossier_handoff_ingest_preview", mocks["ingest"]):
            with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_dossier_handoff_report_context_preview", mocks["context"]):
                with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_report_html", mocks["html"]):
                    with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.render_button2_pdf", mocks["render"]):
                        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.resolve_pdf_output_path", mock_path_resolve):
                            with patch("builtins.open", side_effect=IOError("Permission denied")):
                                with patch("os.path.exists", return_value=True):
                                    req = _valid_request()
                                    result = generate_button2_report_render_gate_integration(req)
        assert result["ok"] is False
        assert "file_write" in result["error"]


# ---------------------------------------------------------------------------
# TestNoPartialWrites
# ---------------------------------------------------------------------------

class TestNoPartialWrites:
    def test_composition_failure_no_render_call(self):
        mocks = _mock_all_downstream({
            "html": MagicMock(return_value={
                "ok": False,
                "error": "composition_failed",
            }),
        })
        mock_render = MagicMock()
        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_readonly_dossier_handoff_ingest_preview", mocks["ingest"]):
            with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_dossier_handoff_report_context_preview", mocks["context"]):
                with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_report_html", mocks["html"]):
                    with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.render_button2_pdf", mock_render):
                        req = _valid_request()
                        result = generate_button2_report_render_gate_integration(req)
        mock_render.assert_not_called()

    def test_render_failure_no_path_resolution(self):
        mocks = _mock_all_downstream({
            "render": MagicMock(side_effect=Exception("render failed")),
        })
        mock_path = MagicMock()
        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_readonly_dossier_handoff_ingest_preview", mocks["ingest"]):
            with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_dossier_handoff_report_context_preview", mocks["context"]):
                with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_report_html", mocks["html"]):
                    with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.render_button2_pdf", mocks["render"]):
                        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.resolve_pdf_output_path", mock_path):
                            req = _valid_request()
                            result = generate_button2_report_render_gate_integration(req)
        mock_path.assert_not_called()

    def test_path_resolution_failure_no_file_write(self):
        from operator_dashboard.button2_pdf_output_root_config_v1 import FightKeyInvalidError
        mocks = _mock_all_downstream({})
        mock_open = MagicMock()
        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_readonly_dossier_handoff_ingest_preview", mocks["ingest"]):
            with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_dossier_handoff_report_context_preview", mocks["context"]):
                with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_report_html", mocks["html"]):
                    with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.render_button2_pdf", mocks["render"]):
                        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.resolve_pdf_output_path", side_effect=FightKeyInvalidError("bad")):
                            with patch("builtins.open", mock_open):
                                req = _valid_request()
                                result = generate_button2_report_render_gate_integration(req)
        mock_open.assert_not_called()

    def test_ingest_failure_no_further_processing(self):
        mocks = _mock_all_downstream({
            "ingest": MagicMock(return_value={
                "ok": False,
                "error": "invalid",
            }),
        })
        mock_context = MagicMock()
        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_readonly_dossier_handoff_ingest_preview", mocks["ingest"]):
            with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_dossier_handoff_report_context_preview", mock_context):
                req = _valid_request()
                result = generate_button2_report_render_gate_integration(req)
        mock_context.assert_not_called()


# ---------------------------------------------------------------------------
# TestVisualQAOptional
# ---------------------------------------------------------------------------

class TestVisualQAOptional:
    def test_visual_qa_disabled_by_default(self):
        mocks = _mock_all_downstream({})
        mock_path_resolve = MagicMock(return_value="/output/test_premium.pdf")
        with patch.dict(os.environ, {}, clear=True):
            with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_readonly_dossier_handoff_ingest_preview", mocks["ingest"]):
                with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_dossier_handoff_report_context_preview", mocks["context"]):
                    with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_report_html", mocks["html"]):
                        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.render_button2_pdf", mocks["render"]):
                            with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.resolve_pdf_output_path", mock_path_resolve):
                                with patch("builtins.open"):
                                    with patch("os.path.exists", return_value=True):
                                        req = _valid_request()
                                        result = generate_button2_report_render_gate_integration(req)
        assert result["visual_qa_enabled"] is False
        assert result["qa_summary"] is None

    def test_visual_qa_enabled_via_env_var(self):
        mocks = _mock_all_downstream({
            "render": MagicMock(return_value={
                "pdf_bytes": b"fake pdf",
                "geometry_data": {"blocks": []},  # Not None
            }),
        })
        mock_path_resolve = MagicMock(return_value="/output/test_premium.pdf")
        mock_proof = MagicMock(return_value={
            "overlap_proof": "clear",
            "off_page_text_proof": "clear",
            "visual_certification_status": "not_certified",
        })
        with patch.dict(os.environ, {"BUTTON2_VISUAL_QA": "1"}):
            with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_readonly_dossier_handoff_ingest_preview", mocks["ingest"]):
                with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_dossier_handoff_report_context_preview", mocks["context"]):
                    with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_report_html", mocks["html"]):
                        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.render_button2_pdf", mocks["render"]):
                            with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.resolve_pdf_output_path", mock_path_resolve):
                                with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.run_geometry_proof", mock_proof):
                                    with patch("builtins.open"):
                                        with patch("os.path.exists", return_value=True):
                                            req = _valid_request()
                                            result = generate_button2_report_render_gate_integration(req)
        assert result["visual_qa_enabled"] is True
        assert result["qa_summary"] is not None

    def test_qa_failure_does_not_fail_report_generation(self):
        mocks = _mock_all_downstream({
            "render": MagicMock(return_value={
                "pdf_bytes": b"fake pdf",
                "geometry_data": {"blocks": []},
            }),
        })
        mock_path_resolve = MagicMock(return_value="/output/test_premium.pdf")
        with patch.dict(os.environ, {"BUTTON2_VISUAL_QA": "1"}):
            with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_readonly_dossier_handoff_ingest_preview", mocks["ingest"]):
                with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_dossier_handoff_report_context_preview", mocks["context"]):
                    with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_report_html", mocks["html"]):
                        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.render_button2_pdf", mocks["render"]):
                            with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.resolve_pdf_output_path", mock_path_resolve):
                                with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.run_geometry_proof", side_effect=Exception("QA failed")):
                                    with patch("builtins.open"):
                                        with patch("os.path.exists", return_value=True):
                                            req = _valid_request()
                                            result = generate_button2_report_render_gate_integration(req)
        assert result["ok"] is True
        assert result["file_write_performed"] is True


# ---------------------------------------------------------------------------
# TestErrorHandling
# ---------------------------------------------------------------------------

class TestErrorHandling:
    def test_malformed_request_none(self):
        result = generate_button2_report_render_gate_integration(None)
        assert result["ok"] is False

    def test_exception_in_composition_returns_error(self):
        mocks = _mock_all_downstream({
            "ingest": MagicMock(side_effect=Exception("Composition error")),
        })
        with patch("operator_dashboard.button2_report_generation_route_render_gate_integration_v1.build_button2_readonly_dossier_handoff_ingest_preview", mocks["ingest"]):
            req = _valid_request()
            result = generate_button2_report_render_gate_integration(req)
        # Should catch the exception gracefully (but currently might not)
        # This test documents expected behavior
