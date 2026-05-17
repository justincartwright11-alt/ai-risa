# Button 2 HTML Composition Entry Point — Preview Tests (v1)
# Slice: button2-html-composition-entry-point-preview-v1
#
# Purpose: Verify that build_button2_report_html correctly:
#   - Produces a well-formed HTML document from a valid report_context_preview
#   - Routes all required content fields into the HTML output
#   - Validates destination_marker, report_context_kind, summary content, input type
#   - Escapes dynamic values (XSS safety)
#   - Places proof fields in the meta-footer only
#   - Renders proof dict values as status labels, not raw dicts
#   - Holds all safety invariants (no PDF, no file write, preview_only=True)
#
# No PDFs generated. No files written. No renderer changes. No dashboard changes.

import html as stdlib_html

import pytest

from operator_dashboard.button2_html_composition_entry_point_v1 import (
    build_button2_report_html,
)

# ─── Fixtures ─────────────────────────────────────────────────────────────────

def _valid_ctx(**overrides):
    base = {
        "destination_marker": "button2_report_generation_preview",
        "report_context_kind": "dossier_handoff_report_context_preview",
        "source_context_kind": "button1_dossier_handoff",
        "source_ingest_mode": "preview_only",
        "handoff_summary_preview": "Fighter: Test Fighter\nPromotion: UFC\nRecord: 10W-2L-0D",
        "hierarchy_markers": [
            {"block": "executive_summary", "order": 0}
        ],
        "source_traceability": [
            {"id": "SRC-001", "type": "button1_dossier_handoff", "date": "2026-05-17"}
        ],
        "overlap_proof": "unavailable",
        "off_page_text_proof": "unavailable",
        "visual_certification_status": "not_certified",
    }
    base.update(overrides)
    return base


# ─── Core path ────────────────────────────────────────────────────────────────

class TestCoreSuccess:
    def test_valid_input_returns_ok_true(self):
        result = build_button2_report_html(_valid_ctx())
        assert result["ok"] is True

    def test_valid_input_html_content_is_non_empty_string(self):
        result = build_button2_report_html(_valid_ctx())
        assert isinstance(result["html_content"], str)
        assert len(result["html_content"].strip()) > 0

    def test_html_content_starts_with_doctype(self):
        result = build_button2_report_html(_valid_ctx())
        assert result["html_content"].lstrip().startswith("<!DOCTYPE html>")

    def test_html_content_contains_html_root(self):
        result = build_button2_report_html(_valid_ctx())
        assert "<html" in result["html_content"]
        assert "</html>" in result["html_content"]

    def test_html_content_has_head_and_body(self):
        result = build_button2_report_html(_valid_ctx())
        assert "<head>" in result["html_content"]
        assert "<body>" in result["html_content"]

    def test_error_is_none_on_success(self):
        result = build_button2_report_html(_valid_ctx())
        assert result["error"] is None

    def test_html_composition_performed_true_on_success(self):
        result = build_button2_report_html(_valid_ctx())
        assert result["html_composition_performed"] is True


# ─── Content routing ──────────────────────────────────────────────────────────

class TestContentRouting:
    def test_summary_text_appears_in_html(self):
        ctx = _valid_ctx(handoff_summary_preview="Fighter: John Doe\nPromotion: Bellator")
        result = build_button2_report_html(ctx)
        assert "John Doe" in result["html_content"]
        assert "Bellator" in result["html_content"]

    def test_source_traceability_id_appears_in_html(self):
        ctx = _valid_ctx(source_traceability=[
            {"id": "SRC-XYZ", "type": "manual", "date": "2026-01-01"}
        ])
        result = build_button2_report_html(ctx)
        assert "SRC-XYZ" in result["html_content"]

    def test_source_traceability_type_appears_in_html(self):
        ctx = _valid_ctx(source_traceability=[
            {"id": "SRC-XYZ", "type": "manual_override", "date": "2026-01-01"}
        ])
        result = build_button2_report_html(ctx)
        assert "manual_override" in result["html_content"]

    def test_empty_source_traceability_renders_fallback(self):
        ctx = _valid_ctx(source_traceability=[])
        result = build_button2_report_html(ctx)
        assert "No source traceability data." in result["html_content"]

    def test_missing_source_traceability_renders_fallback(self):
        ctx = _valid_ctx()
        del ctx["source_traceability"]
        result = build_button2_report_html(ctx)
        assert "No source traceability data." in result["html_content"]

    def test_source_context_kind_in_meta_footer(self):
        ctx = _valid_ctx(source_context_kind="button1_dossier_handoff")
        result = build_button2_report_html(ctx)
        assert "button1_dossier_handoff" in result["html_content"]

    def test_ingest_mode_in_meta_footer(self):
        ctx = _valid_ctx(source_ingest_mode="preview_only")
        result = build_button2_report_html(ctx)
        assert "preview_only" in result["html_content"]


# ─── Proof field placement ────────────────────────────────────────────────────

class TestProofFieldPlacement:
    def test_overlap_proof_string_appears_in_meta_footer(self):
        ctx = _valid_ctx(overlap_proof="clear")
        result = build_button2_report_html(ctx)
        assert "clear" in result["html_content"]
        # Must be in the meta-footer div, not in a heading
        footer_start = result["html_content"].find('meta-footer')
        assert footer_start != -1
        assert "clear" in result["html_content"][footer_start:]

    def test_visual_certification_status_in_meta_footer(self):
        ctx = _valid_ctx(visual_certification_status="not_certified")
        result = build_button2_report_html(ctx)
        footer_start = result["html_content"].find('meta-footer')
        assert footer_start != -1
        assert "not_certified" in result["html_content"][footer_start:]

    def test_proof_dict_value_renders_status_label_not_raw_dict(self):
        """overlap_proof as dict → renders proof["status"], not the full dict repr."""
        ctx = _valid_ctx(overlap_proof={
            "status": "overlap_detected",
            "violations": [{"block_a": "div-p0-0", "block_b": "div-p0-1"}]
        })
        result = build_button2_report_html(ctx)
        assert "overlap_detected" in result["html_content"]
        # Raw dict keys/brackets must NOT appear in the HTML
        assert "violations" not in result["html_content"]
        assert '{"status"' not in result["html_content"]

    def test_off_page_proof_dict_renders_status_label(self):
        ctx = _valid_ctx(off_page_text_proof={"status": "off_page_detected", "violations": []})
        result = build_button2_report_html(ctx)
        assert "off_page_detected" in result["html_content"]
        assert "violations" not in result["html_content"]


# ─── Validation failures ──────────────────────────────────────────────────────

class TestValidationFailures:
    def test_non_dict_input_fails_with_invalid_input_type(self):
        for bad in (None, "string", 42, [], True):
            result = build_button2_report_html(bad)
            assert result["ok"] is False, f"Expected False for {bad!r}"
            assert result["error"] == "invalid_input_type"

    def test_missing_destination_marker_fails(self):
        ctx = _valid_ctx()
        del ctx["destination_marker"]
        result = build_button2_report_html(ctx)
        assert result["ok"] is False
        assert result["error"] == "invalid_destination_marker"

    def test_wrong_destination_marker_fails(self):
        ctx = _valid_ctx(destination_marker="wrong_marker")
        result = build_button2_report_html(ctx)
        assert result["ok"] is False
        assert result["error"] == "invalid_destination_marker"

    def test_missing_report_context_kind_fails(self):
        ctx = _valid_ctx()
        del ctx["report_context_kind"]
        result = build_button2_report_html(ctx)
        assert result["ok"] is False
        assert result["error"] == "invalid_report_context_kind"

    def test_wrong_report_context_kind_fails(self):
        ctx = _valid_ctx(report_context_kind="unknown_kind")
        result = build_button2_report_html(ctx)
        assert result["ok"] is False
        assert result["error"] == "invalid_report_context_kind"

    def test_missing_summary_content_fails(self):
        ctx = _valid_ctx(handoff_summary_preview="")
        result = build_button2_report_html(ctx)
        assert result["ok"] is False
        assert result["error"] == "missing_summary_content"

    def test_whitespace_only_summary_fails(self):
        ctx = _valid_ctx(handoff_summary_preview="   \n  ")
        result = build_button2_report_html(ctx)
        assert result["ok"] is False
        assert result["error"] == "missing_summary_content"

    def test_none_summary_fails(self):
        ctx = _valid_ctx(handoff_summary_preview=None)
        result = build_button2_report_html(ctx)
        assert result["ok"] is False
        assert result["error"] == "missing_summary_content"

    def test_html_content_none_on_failure(self):
        ctx = _valid_ctx(destination_marker="bad")
        result = build_button2_report_html(ctx)
        assert result["html_content"] is None

    def test_html_composition_performed_false_on_failure(self):
        ctx = _valid_ctx(destination_marker="bad")
        result = build_button2_report_html(ctx)
        assert result["html_composition_performed"] is False


# ─── XSS / escaping safety ───────────────────────────────────────────────────

class TestEscapingSafety:
    def test_xss_probe_in_source_context_kind_is_escaped(self):
        ctx = _valid_ctx(source_context_kind='<script>alert("xss")</script>')
        result = build_button2_report_html(ctx)
        assert "<script>" not in result["html_content"]
        assert "&lt;script&gt;" in result["html_content"]

    def test_xss_probe_in_source_traceability_id_is_escaped(self):
        ctx = _valid_ctx(source_traceability=[
            {"id": '<img src=x onerror=alert(1)>', "type": "test", "date": "n/a"}
        ])
        result = build_button2_report_html(ctx)
        assert "<img" not in result["html_content"]
        assert "&lt;img" in result["html_content"]

    def test_xss_probe_in_ingest_mode_is_escaped(self):
        ctx = _valid_ctx(source_ingest_mode='"><svg onload=alert(1)>')
        result = build_button2_report_html(ctx)
        assert "<svg" not in result["html_content"]

    def test_xss_probe_in_visual_certification_status_is_escaped(self):
        ctx = _valid_ctx(visual_certification_status='<b>injected</b>')
        result = build_button2_report_html(ctx)
        assert "<b>" not in result["html_content"]
        assert "&lt;b&gt;" in result["html_content"]


# ─── Safety invariants ───────────────────────────────────────────────────────

class TestSafetyInvariants:
    def test_preview_only_always_true_on_success(self):
        result = build_button2_report_html(_valid_ctx())
        assert result["preview_only"] is True

    def test_preview_only_always_true_on_failure(self):
        result = build_button2_report_html(_valid_ctx(destination_marker="bad"))
        assert result["preview_only"] is True

    def test_pdf_generation_performed_always_false_on_success(self):
        result = build_button2_report_html(_valid_ctx())
        assert result["pdf_generation_performed"] is False

    def test_pdf_generation_performed_always_false_on_failure(self):
        result = build_button2_report_html(_valid_ctx(destination_marker="bad"))
        assert result["pdf_generation_performed"] is False

    def test_file_write_performed_always_false_on_success(self):
        result = build_button2_report_html(_valid_ctx())
        assert result["file_write_performed"] is False

    def test_file_write_performed_always_false_on_failure(self):
        result = build_button2_report_html(_valid_ctx(destination_marker="bad"))
        assert result["file_write_performed"] is False

    def test_export_performed_always_false(self):
        result = build_button2_report_html(_valid_ctx())
        assert result["export_performed"] is False

    def test_delivery_performed_always_false(self):
        result = build_button2_report_html(_valid_ctx())
        assert result["delivery_performed"] is False

    def test_html_content_has_no_external_url_references(self):
        """HTML output must not reference any external URLs (fonts, images, stylesheets)."""
        result = build_button2_report_html(_valid_ctx())
        content = result["html_content"]
        assert "http://" not in content
        assert "https://" not in content
        assert "url(" not in content

    def test_html_content_has_no_script_tags(self):
        """HTML output must not contain any script elements."""
        result = build_button2_report_html(_valid_ctx())
        assert "<script" not in result["html_content"].lower()
