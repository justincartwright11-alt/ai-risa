# Button 2 PDF Render Gate — Integration Preview Tests (v1)
# Slice: button2-visual-intelligence-renderer-geometry-extractor-integration-preview-v1
#
# Purpose: Prove that the render call site module correctly:
#   - Guards extraction off by default (_visual_qa_enabled returns False)
#   - Guards extraction on when BUTTON2_VISUAL_QA=1
#   - Calls HTML(...).render() then document.write_pdf() in correct order
#   - Passes the rendered document to the geometry extractor when QA enabled
#   - Returns geometry_data when extractor succeeds
#   - Fails closed when extractor raises an exception
#   - Never calls extractor when guard is off
#   - Always returns pdf_bytes regardless of QA state
#
# No PDFs generated. No files written. No renderer layout changes.
# No dashboard changes. No report-generation behavior changes.

import sys
import os
from types import SimpleNamespace
from unittest.mock import MagicMock, patch, call

import pytest

from operator_dashboard.button2_pdf_render_gate_v1 import (
    _bootstrap_windows_weasyprint_runtime,
    _visual_qa_enabled,
    render_button2_pdf,
)


# ─── _visual_qa_enabled guard ────────────────────────────────────────────────

class TestVisualQaGuard:
    def test_guard_default_false_no_env(self):
        """Guard is False when BUTTON2_VISUAL_QA is not set."""
        env = {k: v for k, v in os.environ.items() if k != "BUTTON2_VISUAL_QA"}
        with patch.dict(os.environ, env, clear=True):
            assert _visual_qa_enabled() is False

    def test_guard_true_when_env_equals_one(self):
        """Guard is True when BUTTON2_VISUAL_QA=1."""
        with patch.dict(os.environ, {"BUTTON2_VISUAL_QA": "1"}):
            assert _visual_qa_enabled() is True

    def test_guard_false_when_env_zero(self):
        """Guard is False when BUTTON2_VISUAL_QA=0."""
        with patch.dict(os.environ, {"BUTTON2_VISUAL_QA": "0"}):
            assert _visual_qa_enabled() is False

    def test_guard_false_when_env_other_value(self):
        """Guard is False for any value other than '1'."""
        for val in ("true", "yes", "on", "2", ""):
            with patch.dict(os.environ, {"BUTTON2_VISUAL_QA": val}):
                assert _visual_qa_enabled() is False, f"expected False for '{val}'"

    def test_guard_handles_whitespace_in_env_value(self):
        """Guard strips whitespace before comparing."""
        with patch.dict(os.environ, {"BUTTON2_VISUAL_QA": " 1 "}):
            assert _visual_qa_enabled() is True


class TestWindowsRuntimeBootstrap:
    def test_registers_ucrt64_bin_from_path_when_available(self):
        add_calls = []

        with patch("operator_dashboard.button2_pdf_render_gate_v1.os.name", "nt"):
            with patch(
                "operator_dashboard.button2_pdf_render_gate_v1.os.add_dll_directory",
                side_effect=lambda path: add_calls.append(path),
                create=True,
            ):
                with patch(
                    "operator_dashboard.button2_pdf_render_gate_v1.os.path.isdir",
                    side_effect=lambda path: path == r"C:\msys64\ucrt64\bin",
                ):
                    with patch.dict(os.environ, {"PATH": r"C:\msys64\ucrt64\bin;C:\Windows\System32"}):
                        _bootstrap_windows_weasyprint_runtime()

        assert add_calls == [r"C:\msys64\ucrt64\bin"]

    def test_noops_outside_windows(self):
        with patch("operator_dashboard.button2_pdf_render_gate_v1.os.name", "posix"):
            with patch(
                "operator_dashboard.button2_pdf_render_gate_v1.os.add_dll_directory",
                side_effect=AssertionError("should not be called"),
                create=True,
            ):
                _bootstrap_windows_weasyprint_runtime()


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _make_mock_weasyprint():
    """Return a mock weasyprint module with controllable render/write_pdf."""
    mock_doc = MagicMock()
    mock_doc.write_pdf.return_value = b"%PDF-mock-bytes"

    mock_html_instance = MagicMock()
    mock_html_instance.render.return_value = mock_doc

    mock_wp = MagicMock()
    mock_wp.HTML.return_value = mock_html_instance

    return mock_wp, mock_doc, mock_html_instance


# ─── render_button2_pdf — QA guard OFF ───────────────────────────────────────

class TestRenderGateQaDisabled:
    """Tests for render_button2_pdf when QA guard is off (default)."""

    def test_returns_pdf_bytes_when_qa_disabled(self):
        """pdf_bytes in result when QA disabled."""
        mock_wp, mock_doc, _ = _make_mock_weasyprint()
        with patch.dict(os.environ, {"BUTTON2_VISUAL_QA": "0"}):
            with patch.dict(sys.modules, {"weasyprint": mock_wp}):
                result = render_button2_pdf("<html><body>test</body></html>")
        assert result["pdf_bytes"] == b"%PDF-mock-bytes"

    def test_geometry_data_none_when_qa_disabled(self):
        """geometry_data is None when QA guard is off."""
        mock_wp, mock_doc, _ = _make_mock_weasyprint()
        with patch.dict(os.environ, {"BUTTON2_VISUAL_QA": "0"}):
            with patch.dict(sys.modules, {"weasyprint": mock_wp}):
                result = render_button2_pdf("<html></html>")
        assert result["geometry_data"] is None

    def test_extractor_not_called_when_qa_disabled(self):
        """Geometry extractor is never called when QA guard is off."""
        mock_wp, mock_doc, _ = _make_mock_weasyprint()
        extractor_target = (
            "operator_dashboard.button2_pdf_render_gate_v1"
            ".extract_weasyprint_page_geometry"
        )
        with patch.dict(os.environ, {"BUTTON2_VISUAL_QA": "0"}):
            with patch.dict(sys.modules, {"weasyprint": mock_wp}):
                with patch(extractor_target) as mock_extractor:
                    render_button2_pdf("<html></html>")
        mock_extractor.assert_not_called()

    def test_write_pdf_always_called_when_qa_disabled(self):
        """document.write_pdf() is always called even when QA is off."""
        mock_wp, mock_doc, _ = _make_mock_weasyprint()
        with patch.dict(os.environ, {"BUTTON2_VISUAL_QA": "0"}):
            with patch.dict(sys.modules, {"weasyprint": mock_wp}):
                render_button2_pdf("<html></html>")
        mock_doc.write_pdf.assert_called_once()

    def test_html_render_called_with_string_kwarg(self):
        """weasyprint.HTML is called with string= kwarg."""
        mock_wp, mock_doc, mock_html_instance = _make_mock_weasyprint()
        html_input = "<html><body>fight</body></html>"
        with patch.dict(os.environ, {"BUTTON2_VISUAL_QA": "0"}):
            with patch.dict(sys.modules, {"weasyprint": mock_wp}):
                render_button2_pdf(html_input)
        mock_wp.HTML.assert_called_once_with(string=html_input)
        mock_html_instance.render.assert_called_once()


# ─── render_button2_pdf — QA guard ON ────────────────────────────────────────

class TestRenderGateQaEnabled:
    """Tests for render_button2_pdf when QA guard is enabled."""

    def test_extractor_called_with_rendered_document_when_qa_enabled(self):
        """When QA enabled, extractor receives the rendered document object."""
        mock_wp, mock_doc, _ = _make_mock_weasyprint()
        mock_geometry = {"blocks": [], "page_width": 595.0, "page_height": 842.0,
                         "preview_only": True, "extraction_status": "no_content_blocks"}
        extractor_target = (
            "operator_dashboard.button2_pdf_render_gate_v1"
            ".extract_weasyprint_page_geometry"
        )
        with patch.dict(os.environ, {"BUTTON2_VISUAL_QA": "1"}):
            with patch.dict(sys.modules, {"weasyprint": mock_wp}):
                with patch(extractor_target, return_value=mock_geometry) as mock_extractor:
                    result = render_button2_pdf("<html></html>")
        mock_extractor.assert_called_once_with(mock_doc)
        assert result["geometry_data"] is mock_geometry

    def test_pdf_bytes_present_when_qa_enabled(self):
        """pdf_bytes is present even when QA extraction runs."""
        mock_wp, mock_doc, _ = _make_mock_weasyprint()
        extractor_target = (
            "operator_dashboard.button2_pdf_render_gate_v1"
            ".extract_weasyprint_page_geometry"
        )
        with patch.dict(os.environ, {"BUTTON2_VISUAL_QA": "1"}):
            with patch.dict(sys.modules, {"weasyprint": mock_wp}):
                with patch(extractor_target, return_value={"blocks": [], "preview_only": True,
                                                            "extraction_status": "ok",
                                                            "page_width": 595.0,
                                                            "page_height": 842.0}):
                    result = render_button2_pdf("<html></html>")
        assert result["pdf_bytes"] == b"%PDF-mock-bytes"

    def test_write_pdf_called_after_extraction(self):
        """document.write_pdf() is called after extraction — order preserved."""
        mock_wp, mock_doc, _ = _make_mock_weasyprint()
        call_order = []
        mock_doc.write_pdf.side_effect = lambda: call_order.append("write_pdf") or b"%PDF"
        extractor_target = (
            "operator_dashboard.button2_pdf_render_gate_v1"
            ".extract_weasyprint_page_geometry"
        )
        def mock_extract(doc):
            call_order.append("extract")
            return {"blocks": [], "preview_only": True,
                    "extraction_status": "ok",
                    "page_width": 595.0, "page_height": 842.0}
        with patch.dict(os.environ, {"BUTTON2_VISUAL_QA": "1"}):
            with patch.dict(sys.modules, {"weasyprint": mock_wp}):
                with patch(extractor_target, side_effect=mock_extract):
                    render_button2_pdf("<html></html>")
        assert call_order == ["extract", "write_pdf"], f"Unexpected order: {call_order}"


# ─── Fail-closed: extractor exception ────────────────────────────────────────

class TestRenderGateFailClosed:
    def test_geometry_none_when_extractor_raises_exception(self):
        """Any extractor exception → geometry_data=None (fail closed)."""
        mock_wp, mock_doc, _ = _make_mock_weasyprint()
        extractor_target = (
            "operator_dashboard.button2_pdf_render_gate_v1"
            ".extract_weasyprint_page_geometry"
        )
        with patch.dict(os.environ, {"BUTTON2_VISUAL_QA": "1"}):
            with patch.dict(sys.modules, {"weasyprint": mock_wp}):
                with patch(extractor_target, side_effect=RuntimeError("box tree corrupt")):
                    result = render_button2_pdf("<html></html>")
        assert result["geometry_data"] is None

    def test_pdf_bytes_present_even_when_extractor_raises(self):
        """pdf_bytes is always returned even when extraction fails."""
        mock_wp, mock_doc, _ = _make_mock_weasyprint()
        extractor_target = (
            "operator_dashboard.button2_pdf_render_gate_v1"
            ".extract_weasyprint_page_geometry"
        )
        with patch.dict(os.environ, {"BUTTON2_VISUAL_QA": "1"}):
            with patch.dict(sys.modules, {"weasyprint": mock_wp}):
                with patch(extractor_target, side_effect=AttributeError("no _page_box")):
                    result = render_button2_pdf("<html></html>")
        assert result["pdf_bytes"] == b"%PDF-mock-bytes"

    def test_geometry_none_when_extractor_raises_attribute_error(self):
        """AttributeError from box tree walk → geometry_data=None."""
        mock_wp, mock_doc, _ = _make_mock_weasyprint()
        extractor_target = (
            "operator_dashboard.button2_pdf_render_gate_v1"
            ".extract_weasyprint_page_geometry"
        )
        with patch.dict(os.environ, {"BUTTON2_VISUAL_QA": "1"}):
            with patch.dict(sys.modules, {"weasyprint": mock_wp}):
                with patch(extractor_target, side_effect=AttributeError):
                    result = render_button2_pdf("<html></html>")
        assert result["geometry_data"] is None

    def test_geometry_none_when_extractor_raises_value_error(self):
        """ValueError from extractor → geometry_data=None."""
        mock_wp, mock_doc, _ = _make_mock_weasyprint()
        extractor_target = (
            "operator_dashboard.button2_pdf_render_gate_v1"
            ".extract_weasyprint_page_geometry"
        )
        with patch.dict(os.environ, {"BUTTON2_VISUAL_QA": "1"}):
            with patch.dict(sys.modules, {"weasyprint": mock_wp}):
                with patch(extractor_target, side_effect=ValueError):
                    result = render_button2_pdf("<html></html>")
        assert result["geometry_data"] is None


# ─── Result shape contract ────────────────────────────────────────────────────

class TestRenderResultShape:
    def test_result_always_has_pdf_bytes_key(self):
        mock_wp, _, _ = _make_mock_weasyprint()
        with patch.dict(os.environ, {"BUTTON2_VISUAL_QA": "0"}):
            with patch.dict(sys.modules, {"weasyprint": mock_wp}):
                result = render_button2_pdf("<html></html>")
        assert "pdf_bytes" in result

    def test_result_always_has_geometry_data_key(self):
        mock_wp, _, _ = _make_mock_weasyprint()
        with patch.dict(os.environ, {"BUTTON2_VISUAL_QA": "0"}):
            with patch.dict(sys.modules, {"weasyprint": mock_wp}):
                result = render_button2_pdf("<html></html>")
        assert "geometry_data" in result

    def test_result_has_exactly_two_keys(self):
        """Result dict has exactly pdf_bytes and geometry_data."""
        mock_wp, _, _ = _make_mock_weasyprint()
        with patch.dict(os.environ, {"BUTTON2_VISUAL_QA": "0"}):
            with patch.dict(sys.modules, {"weasyprint": mock_wp}):
                result = render_button2_pdf("<html></html>")
        assert set(result.keys()) == {"pdf_bytes", "geometry_data"}


# ─── Proof chain integration: geometry_data flows to run_geometry_proof ───────

class TestGeometryFlowsToProofChain:
    """When QA is enabled and geometry is extracted, the data can be passed
    directly to run_geometry_proof — confirming end-to-end chain connectivity."""

    def test_geometry_data_flows_to_run_geometry_proof(self):
        """geometry_data returned from render_button2_pdf is accepted by run_geometry_proof."""
        from operator_dashboard.button2_visual_intelligence_overlap_offpage_proof_instrumentation_v1 import (
            run_geometry_proof,
        )
        # Simulate geometry_data as the extractor would return for a clean layout
        geometry_data = {
            "blocks": [
                {"id": "div-p0-0", "bounds": [10.0, 10.0, 100.0, 50.0], "page_index": 0},
            ],
            "page_width": 595.0,
            "page_height": 842.0,
            "preview_only": True,
            "extraction_status": "ok",
        }
        mock_wp, mock_doc, _ = _make_mock_weasyprint()
        extractor_target = (
            "operator_dashboard.button2_pdf_render_gate_v1"
            ".extract_weasyprint_page_geometry"
        )
        with patch.dict(os.environ, {"BUTTON2_VISUAL_QA": "1"}):
            with patch.dict(sys.modules, {"weasyprint": mock_wp}):
                with patch(extractor_target, return_value=geometry_data):
                    result = render_button2_pdf("<html></html>")

        proof = run_geometry_proof(result["geometry_data"])
        assert proof["overlap_proof"] == "clear"
        assert proof["off_page_text_proof"] == "clear"
        assert proof["visual_certification_status"] == "not_certified"
