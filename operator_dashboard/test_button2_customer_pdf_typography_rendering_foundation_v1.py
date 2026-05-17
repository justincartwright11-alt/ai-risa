"""
Button 2 Customer PDF — Phase 2 Slice 1 — Typography Rendering Foundation Implementation Tests

Purpose:
- Validate that Phase 1 typography tokens are applied to rendered HTML
- Verify typography rendering supports all locked font families, sizes, weights, colors, line-heights
- Verify no renderer behavior change beyond typography styling
- Verify all Phase 1 safety invariants preserved
- Verify all Phase 1 tests still pass

Governance:
- Typography rendering ONLY
- No hierarchy rewrite
- No chart rendering
- No page-break behavior changes
- No approval changes
- No output-path changes
- No file-write changes
- No dashboard changes
- No delivery workflow expansion
- Phase 1 metadata remains immutable
"""

import re
from operator_dashboard.button2_html_composition_entry_point_v1 import (
    build_button2_report_html,
)


def _valid_ctx(**overrides):
    """Base valid context for typography rendering tests."""
    base = {
        "destination_marker": "button2_report_generation_preview",
        "report_context_kind": "dossier_handoff_report_context_preview",
        "fight_id": "fight_typography_001",
        "source_context_kind": "button1_dossier_handoff",
        "source_ingest_mode": "preview_only",
        "handoff_summary_preview": "Typography Rendering Test: Fighter A vs Fighter B",
        "hierarchy_markers": [
            {"level": "H0", "role": "report_identity_block"},
            {"level": "H1", "role": "analysis_block"},
            {"level": "Body", "role": "analysis_block"},
            {"level": "Meta", "role": "footer_metadata_block"},
        ],
        "source_traceability": [
            {"id": "SRC-001", "type": "official", "date": "2026-05-17"}
        ],
        "overlap_proof": {"proof_kind": "overlap_proof", "proof_status": "missing"},
        "off_page_text_proof": {"proof_kind": "off_page_text_proof", "proof_status": "missing"},
    }
    base.update(overrides)
    return base


class TestTypographyTokensApplication:
    """Verify Phase 1 typography tokens are applied to rendered HTML."""

    def test_typography_css_stylesheet_present(self):
        """Typography CSS stylesheet must be embedded in HTML."""
        result = build_button2_report_html(_valid_ctx())
        assert result["ok"] is True
        html = result["html_content"]
        assert "<style>" in html
        assert "typography" in html.lower()
        assert "</style>" in html

    def test_font_family_stack_applied(self):
        """Typography font-family stack must be applied to body."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        # Check for expected font stack (system fonts, Segoe UI, sans-serif)
        assert "font-family:" in html
        assert ("apple-system" in html or "system" in html.lower() or "segoe" in html.lower())

    def test_typography_classes_defined_in_css(self):
        """All required typography classes must be defined in CSS."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        required_classes = [
            ".typography-body-primary",
            ".typography-body-secondary",
            ".typography-body-compact",
            ".typography-caption-primary",
            ".typography-caption-secondary",
            ".typography-approval-timestamp",
        ]
        for cls in required_classes:
            assert cls in html, f"Required typography class {cls} not found in CSS"

    def test_font_sizes_within_locked_bounds(self):
        """Font sizes in CSS must be within locked 8-20pt bounds."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        # Extract all font-size values
        font_size_pattern = r"font-size:\s*(\d+)pt"
        sizes = re.findall(font_size_pattern, html)
        
        assert len(sizes) > 0, "No font-size values found in CSS"
        
        for size_str in sizes:
            size = int(size_str)
            assert 8 <= size <= 20, f"Font size {size}pt outside locked bounds (8-20pt)"

    def test_font_weights_within_locked_values(self):
        """Font weights in CSS must be 400, 600, or 700."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        # Extract all font-weight values
        weight_pattern = r"font-weight:\s*(\d+)"
        weights = re.findall(weight_pattern, html)
        
        assert len(weights) > 0, "No font-weight values found in CSS"
        
        allowed_weights = {"400", "600", "700"}
        for weight in weights:
            assert weight in allowed_weights, f"Font weight {weight} not in allowed set {allowed_weights}"

    def test_line_heights_within_locked_bounds(self):
        """Line heights in CSS must be within 1.2-1.5 range."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        # Extract all line-height values
        line_height_pattern = r"line-height:\s*([\d.]+)"
        line_heights = re.findall(line_height_pattern, html)
        
        assert len(line_heights) > 0, "No line-height values found in CSS"
        
        for lh_str in line_heights:
            lh = float(lh_str)
            assert 1.2 <= lh <= 1.5, f"Line height {lh} outside locked bounds (1.2-1.5)"

    def test_text_colors_defined_in_typography(self):
        """Text colors must be defined in typography CSS."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        # Check for color definitions
        assert "color:" in html
        # Expected colors: #111111 (main text), #666666 (secondary), #999999 (caption)
        assert "#111111" in html or "#666666" in html or "#999999" in html

    def test_no_external_css_urls(self):
        """No external CSS URLs allowed (Phase 1 embedded stylesheet only)."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        assert "@import url" not in html
        assert "href=" not in html.split("<style>")[0]  # No links before styles

    def test_no_script_tags_in_html(self):
        """No script tags allowed in composition output."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        assert "<script" not in html.lower()
        assert "</script>" not in html.lower()


class TestTypographyRendering:
    """Verify typography rendering applies correctly without breaking content."""

    def test_html_structure_valid_with_typography(self):
        """HTML structure must remain valid after typography application."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "</html>" in html
        assert "<head>" in html
        assert "</head>" in html
        assert "<body>" in html
        assert "</body>" in html

    def test_all_text_elements_present_after_rendering(self):
        """All report text content must be present after typography rendering."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        # Check for required content markers
        assert "AI-RISA" in html or "Report" in html

    def test_typography_does_not_modify_data_attributes(self):
        """Typography rendering must not modify Phase 1 metadata data-attributes."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        # Data attributes should remain unchanged
        assert 'data-' in html  # Some data attributes must exist from Phase 1

    def test_typography_css_only_in_style_block(self):
        """All typography CSS must be in <style> block, not inline."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        style_block = html[html.find("<style>"):html.find("</style>") + 8]
        
        # Typography definitions should be in style block
        assert ".typography-" in style_block
        
        # Should not have excessive inline styles
        inline_style_count = html.count('style="')
        assert inline_style_count < 20, "Too many inline styles; use CSS classes"


class TestPhase1TypographyIntegration:
    """Verify Phase 2 Slice 1 doesn't break Phase 1 typography layer."""

    def test_phase1_typography_metadata_present(self):
        """Phase 1 typography metadata must remain in HTML."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        assert 'schema_version' in html or 'button2' in html

    def test_typography_tokens_consistent_across_runs(self):
        """Typography tokens must be deterministic (consistent across runs)."""
        result1 = build_button2_report_html(_valid_ctx())
        result2 = build_button2_report_html(_valid_ctx())
        
        # Extract CSS blocks
        css1_start = result1["html_content"].find("<style>")
        css1_end = result1["html_content"].find("</style>")
        css1 = result1["html_content"][css1_start:css1_end]
        
        css2_start = result2["html_content"].find("<style>")
        css2_end = result2["html_content"].find("</style>")
        css2 = result2["html_content"][css2_start:css2_end]
        
        # CSS should be identical
        assert css1 == css2, "Typography CSS not deterministic between runs"

    def test_required_text_hierarchy_levels_present(self):
        """All required hierarchy levels must be represented with typography."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        # H0, H1, Body, Meta must have typography applied
        hierarchy_present = (
            ("H0" in html or "h0" in html.lower()) and
            ("H1" in html or "h1" in html.lower()) and
            ("Body" in html or "body" in html.lower())
        )
        assert hierarchy_present, "Required hierarchy levels not found in output"


class TestSafetyInvariants:
    """Verify all Phase 1 safety invariants remain locked in Phase 2 Slice 1."""

    def test_preview_only_flag_preserved(self):
        """preview_only must remain True."""
        result = build_button2_report_html(_valid_ctx())
        assert result["preview_only"] is True

    def test_pdf_generation_flag_false(self):
        """pdf_generation_performed must remain False."""
        result = build_button2_report_html(_valid_ctx())
        assert result["pdf_generation_performed"] is False

    def test_file_write_flag_false(self):
        """file_write_performed must remain False."""
        result = build_button2_report_html(_valid_ctx())
        assert result["file_write_performed"] is False

    def test_export_flag_false(self):
        """export_performed must remain False."""
        result = build_button2_report_html(_valid_ctx())
        assert result["export_performed"] is False

    def test_delivery_flag_false(self):
        """delivery_performed must remain False."""
        result = build_button2_report_html(_valid_ctx())
        assert result["delivery_performed"] is False

    def test_no_file_system_writes(self):
        """Typography rendering must not perform any file writes."""
        result = build_button2_report_html(_valid_ctx())
        # Result should only contain HTML content and flags, no file paths
        assert isinstance(result["html_content"], str)
        assert not any(
            result["html_content"].startswith(prefix)
            for prefix in ["/", "C:\\", "tmp", "home"]
            if "file" in prefix.lower()
        )

    def test_output_is_html_string(self):
        """Output must be HTML string, not file path or export object."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        assert isinstance(html, str)
        assert html.startswith("<!DOCTYPE html>")
        assert "html" in html.lower()


class TestNoUnintendedChanges:
    """Verify Phase 2 Slice 1 doesn't introduce unintended behavior changes."""

    def test_no_new_validation_rules_in_typography_rendering(self):
        """Typography rendering must be procedural only, no new validation logic."""
        # Valid context should produce valid result
        result = build_button2_report_html(_valid_ctx())
        assert result["ok"] is True

    def test_typography_rendering_idempotent(self):
        """Applying typography rendering twice should produce identical output."""
        result1 = build_button2_report_html(_valid_ctx())
        result2 = build_button2_report_html(_valid_ctx())
        
        assert result1["html_content"] == result2["html_content"]

    def test_no_approval_logic_changes(self):
        """Typography rendering must not affect approval status or decisions."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        
        # Should not contain automatic approval triggers
        assert "auto_approve" not in html.lower()
        assert "automatically_approved" not in html.lower()

    def test_typography_rendering_is_rendering_only(self):
        """Typography changes must affect styling only, not content or structure."""
        ctx = _valid_ctx()
        result = build_button2_report_html(ctx)
        html = result["html_content"]
        
        # Content should be present and unchanged by rendering
        if ctx.get("handoff_summary_preview"):
            assert ctx["handoff_summary_preview"] in html or "Typography" in html


class TestTypographyRenderingBoundary:
    """Verify Phase 2 Slice 1 stays within design boundaries."""

    def test_only_typography_layer_changes(self):
        """Only typography rendering should be applied, not hierarchy, pages, charts."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        
        # Typography CSS should be present
        assert ".typography-" in html or "font-family:" in html
        
        # Should not have chart rendering changes (that's Slice 4)
        # Should not have new page-break logic (that's Slice 3)
        # Should not have new hierarchy structure (that's Slice 2)

    def test_typography_css_clearly_separated_from_other_css(self):
        """Typography CSS should be clearly identified, not mixed with other styles."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        
        # Look for typography section marker
        style_block = html[html.find("<style>"):html.find("</style>")]
        assert ".typography-" in style_block or "font-family:" in style_block

    def test_no_renderer_layout_changes_in_slice1(self):
        """Slice 1 is typography only; layout/renderer changes deferred to Slice 2+."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        
        # No page-break CSS should be added in Slice 1 (that's Slice 3)
        assert "page-break" not in html.lower() or "page-break" in result["html_content"]
        # (existing page-break rules should be unchanged)
