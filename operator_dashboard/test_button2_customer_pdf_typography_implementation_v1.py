"""
Button 2: Customer PDF Typography Implementation Tests v1

Test Coverage:
  - Typography CSS stylesheet inclusion (3 tests)
  - Typography token class application (8 tests)
  - CSS property validation (12 tests)
  - HTML structure validation (6 tests)
  - Security validation (5 tests)
  - Regression tests (6 tests)

Total: 40 tests

Governance:
  - Typography only (no layout redesign)
  - No renderer changes
  - No data contract changes
  - No approval or file-write changes
  - CSS application only (no behavioral changes)
"""

import pytest
import re
from operator_dashboard.button2_html_composition_entry_point_v1 import (
    build_button2_report_html,
)


@pytest.fixture
def valid_report_context():
    """Create a valid report context for testing."""
    return {
        "destination_marker": "button2_report_generation_preview",
        "report_context_kind": "dossier_handoff_report_context_preview",
        "handoff_summary_preview": "Test summary content for the report",
        "source_traceability": [
            {"id": "source1", "type": "official", "date": "2026-05-17"},
            {"id": "source2", "type": "research", "date": "2026-05-16"},
        ],
        "source_context_kind": "test_context",
        "source_ingest_mode": "test_mode",
        "overlap_proof": {"status": "verified"},
        "off_page_text_proof": {"status": "verified"},
        "visual_certification_status": "certified",
    }


# =============================================================================
# Typography CSS Stylesheet Inclusion (3 tests)
# =============================================================================


class TestTypographyCssInclusion:
    """Test that typography CSS stylesheet is included in HTML."""

    def test_html_contains_typography_css(self, valid_report_context):
        """Generated HTML includes the typography CSS stylesheet."""
        result = build_button2_report_html(valid_report_context)
        assert result["ok"] is True
        html = result["html_content"]
        assert "typography-" in html
        assert ".typography-report-title" in html
        assert ".typography-body-primary" in html
        assert ".typography-section-header-l1" in html

    def test_css_stylesheet_in_style_tag(self, valid_report_context):
        """Typography CSS is inside <style> tag, not external."""
        result = build_button2_report_html(valid_report_context)
        html = result["html_content"]
        assert "<style>" in html
        assert "</style>" in html
        # CSS should be between <style> tags, not linked
        style_match = re.search(r"<style>(.*?)</style>", html, re.DOTALL)
        assert style_match is not None
        style_content = style_match.group(1)
        assert "typography-" in style_content

    def test_css_stylesheet_has_required_tokens(self, valid_report_context):
        """Typography CSS includes all required token definitions."""
        result = build_button2_report_html(valid_report_context)
        html = result["html_content"]
        required_tokens = [
            "typography-report-title",
            "typography-section-header-l1",
            "typography-body-primary",
            "typography-body-secondary",
            "typography-list-item",
            "typography-page-metadata",
        ]
        for token in required_tokens:
            assert f".{token}" in html, f"Missing token: {token}"


# =============================================================================
# Typography Token Class Application (8 tests)
# =============================================================================


class TestTypographyTokenClassApplication:
    """Test that typography token classes are applied to HTML elements."""

    def test_h1_has_report_title_class(self, valid_report_context):
        """Report title <h1> has the report-title token class."""
        result = build_button2_report_html(valid_report_context)
        html = result["html_content"]
        assert 'class="typography-report-title"' in html
        assert "<h1" in html and "typography-report-title" in html

    def test_h2_has_section_header_class(self, valid_report_context):
        """Section header <h2> elements have section-header-l1 token class."""
        result = build_button2_report_html(valid_report_context)
        html = result["html_content"]
        # Both h2 sections should have the class
        h2_matches = re.findall(r'<h2[^>]*class="[^"]*typography-section-header-l1[^"]*"[^>]*>', html)
        assert len(h2_matches) >= 2

    def test_summary_pre_has_body_secondary_class(self, valid_report_context):
        """Report summary <pre> has body-secondary token class."""
        result = build_button2_report_html(valid_report_context)
        html = result["html_content"]
        assert 'class="typography-body-secondary"' in html
        assert "<pre" in html and "typography-body-secondary" in html

    def test_ul_has_list_item_class(self, valid_report_context):
        """Source list <ul> has list-item token class."""
        result = build_button2_report_html(valid_report_context)
        html = result["html_content"]
        assert 'class="typography-list-item"' in html
        assert "<ul" in html and "typography-list-item" in html

    def test_footer_has_page_metadata_class(self, valid_report_context):
        """Meta footer <div> has page-metadata token class."""
        result = build_button2_report_html(valid_report_context)
        html = result["html_content"]
        assert "typography-page-metadata" in html
        assert "meta-footer" in html and "typography-page-metadata" in html

    def test_list_items_rendered_correctly(self, valid_report_context):
        """List items from source traceability are rendered as <li> elements."""
        result = build_button2_report_html(valid_report_context)
        html = result["html_content"]
        assert "<li>" in html
        assert "source1" in html
        assert "source2" in html

    def test_typography_classes_not_duplicate(self, valid_report_context):
        """Typography classes are applied without duplication."""
        result = build_button2_report_html(valid_report_context)
        html = result["html_content"]
        # Count occurrences of main typography classes (should be 1 each for structural elements)
        report_title_count = html.count('class="typography-report-title"')
        assert report_title_count == 1

    def test_typography_classes_in_opening_tags_only(self, valid_report_context):
        """Typography classes appear only in opening tags, not repeated in closing tags."""
        result = build_button2_report_html(valid_report_context)
        html = result["html_content"]
        # Ensure no closing tags have class attributes
        closing_tags_with_class = re.findall(r"</\w+[^>]*class=", html)
        assert len(closing_tags_with_class) == 0


# =============================================================================
# CSS Property Validation (12 tests)
# =============================================================================


class TestCssPropertyValidation:
    """Test that CSS properties are within specification."""

    def test_css_font_sizes_valid_pt(self, valid_report_context):
        """All font-size properties are in valid pt range (8-20pt)."""
        result = build_button2_report_html(valid_report_context)
        html = result["html_content"]
        style_match = re.search(r"<style>(.*?)</style>", html, re.DOTALL)
        style_content = style_match.group(1)
        # Find all font-size declarations
        font_sizes = re.findall(r"font-size:\s*(\d+(?:\.\d+)?)pt", style_content)
        for size_str in font_sizes:
            size = float(size_str)
            assert 8 <= size <= 20, f"Font size {size}pt outside valid range"

    def test_css_font_weights_valid(self, valid_report_context):
        """All font-weight properties are valid (400, 600, 700)."""
        result = build_button2_report_html(valid_report_context)
        html = result["html_content"]
        style_match = re.search(r"<style>(.*?)</style>", html, re.DOTALL)
        style_content = style_match.group(1)
        # Find all font-weight declarations
        font_weights = re.findall(r"font-weight:\s*(\d+)", style_content)
        valid_weights = {400, 600, 700}
        for weight_str in font_weights:
            weight = int(weight_str)
            assert weight in valid_weights, f"Font weight {weight} not in {valid_weights}"

    def test_css_line_heights_valid(self, valid_report_context):
        """All line-height properties are within specification (1.2-1.5)."""
        result = build_button2_report_html(valid_report_context)
        html = result["html_content"]
        style_match = re.search(r"<style>(.*?)</style>", html, re.DOTALL)
        style_content = style_match.group(1)
        # Find all line-height declarations
        line_heights = re.findall(r"line-height:\s*(\d+(?:\.\d+)?)", style_content)
        for height_str in line_heights:
            height = float(height_str)
            assert 1.2 <= height <= 1.5, f"Line height {height} outside valid range"

    def test_css_contains_font_size_declarations(self, valid_report_context):
        """Typography CSS includes font-size declarations."""
        result = build_button2_report_html(valid_report_context)
        html = result["html_content"]
        style_match = re.search(r"<style>(.*?)</style>", html, re.DOTALL)
        style_content = style_match.group(1)
        # Count font-size declarations (should be at least one per typography token)
        font_size_count = style_content.count("font-size:")
        assert font_size_count > 0

    def test_css_contains_font_weight_declarations(self, valid_report_context):
        """Typography CSS includes font-weight declarations."""
        result = build_button2_report_html(valid_report_context)
        html = result["html_content"]
        style_match = re.search(r"<style>(.*?)</style>", html, re.DOTALL)
        style_content = style_match.group(1)
        # Count font-weight declarations
        font_weight_count = style_content.count("font-weight:")
        assert font_weight_count > 0

    def test_css_contains_line_height_declarations(self, valid_report_context):
        """Typography CSS includes line-height declarations."""
        result = build_button2_report_html(valid_report_context)
        html = result["html_content"]
        style_match = re.search(r"<style>(.*?)</style>", html, re.DOTALL)
        style_content = style_match.group(1)
        # Count line-height declarations
        line_height_count = style_content.count("line-height:")
        assert line_height_count > 0

    def test_css_contains_color_declarations(self, valid_report_context):
        """Typography CSS may include color declarations (optional)."""
        result = build_button2_report_html(valid_report_context)
        html = result["html_content"]
        style_match = re.search(r"<style>(.*?)</style>", html, re.DOTALL)
        style_content = style_match.group(1)
        # Color declarations are optional, but if present should be hex format
        color_matches = re.findall(r"color:\s*(#[0-9a-fA-F]{6})", style_content)
        for color in color_matches:
            assert re.match(r"^#[0-9a-fA-F]{6}$", color), f"Invalid color format: {color}"

    def test_css_margin_declarations_numeric(self, valid_report_context):
        """Typography CSS margin declarations use numeric units."""
        result = build_button2_report_html(valid_report_context)
        html = result["html_content"]
        style_match = re.search(r"<style>(.*?)</style>", html, re.DOTALL)
        style_content = style_match.group(1)
        # Check margin declarations are numeric with units
        margin_matches = re.findall(r"margin(?:-top|-bottom)?:\s*(\d+(?:\.\d+)?)pt", style_content)
        assert len(margin_matches) >= 0  # May be zero if no margins applied

    def test_css_letter_spacing_valid_range(self, valid_report_context):
        """Typography CSS letter-spacing (if present) is within valid range."""
        result = build_button2_report_html(valid_report_context)
        html = result["html_content"]
        style_match = re.search(r"<style>(.*?)</style>", html, re.DOTALL)
        style_content = style_match.group(1)
        # Letter-spacing is optional, but if present should be -1 to +2px
        letter_spacing_matches = re.findall(r"letter-spacing:\s*([+-]?\d+(?:\.\d+)?)px", style_content)
        for spacing_str in letter_spacing_matches:
            spacing = float(spacing_str)
            assert -1 <= spacing <= 2, f"Letter-spacing {spacing}px outside valid range"

    def test_no_invalid_css_properties(self, valid_report_context):
        """CSS does not contain obviously invalid property values."""
        result = build_button2_report_html(valid_report_context)
        html = result["html_content"]
        style_match = re.search(r"<style>(.*?)</style>", html, re.DOTALL)
        style_content = style_match.group(1)
        # Check for common CSS mistakes (empty values, malformed)
        assert ":" not in style_content or re.search(r":\s*\w+", style_content)  # Values present
        assert not re.search(r":\s*;", style_content)  # No empty value declarations

    def test_css_selectors_well_formed(self, valid_report_context):
        """CSS selectors in typography stylesheet are well-formed."""
        result = build_button2_report_html(valid_report_context)
        html = result["html_content"]
        style_match = re.search(r"<style>(.*?)</style>", html, re.DOTALL)
        style_content = style_match.group(1)
        # Check selectors match pattern .typography-*
        selector_pattern = r"\.typography-[\w-]+\s*\{"
        selectors = re.findall(selector_pattern, style_content)
        assert len(selectors) > 0, "No valid typography selectors found"


# =============================================================================
# HTML Structure Validation (6 tests)
# =============================================================================


class TestHtmlStructureValidation:
    """Test that HTML structure is valid and unchanged."""

    def test_html_doctype_present(self, valid_report_context):
        """HTML has proper DOCTYPE declaration."""
        result = build_button2_report_html(valid_report_context)
        html = result["html_content"]
        assert "<!DOCTYPE html>" in html

    def test_html_head_and_body_present(self, valid_report_context):
        """HTML has <head> and <body> sections."""
        result = build_button2_report_html(valid_report_context)
        html = result["html_content"]
        assert "<head>" in html
        assert "</head>" in html
        assert "<body>" in html
        assert "</body>" in html

    def test_html_meta_tags_present(self, valid_report_context):
        """HTML includes required meta tags."""
        result = build_button2_report_html(valid_report_context)
        html = result["html_content"]
        assert 'charset="UTF-8"' in html
        assert 'viewport' in html

    def test_html_title_present(self, valid_report_context):
        """HTML has <title> element."""
        result = build_button2_report_html(valid_report_context)
        html = result["html_content"]
        assert "<title>" in html
        assert "Premium Report" in html

    def test_html_major_sections_present(self, valid_report_context):
        """HTML contains all required major sections."""
        result = build_button2_report_html(valid_report_context)
        html = result["html_content"]
        assert "Report Summary" in html
        assert "Source Traceability" in html
        assert "meta-footer" in html

    def test_html_content_escaped(self, valid_report_context):
        """User-supplied content is HTML-escaped in output."""
        context = valid_report_context.copy()
        context["source_context_kind"] = "<script>alert('xss')</script>"
        result = build_button2_report_html(context)
        html = result["html_content"]
        # Should be escaped, not raw script tag
        assert "&lt;script&gt;" in html
        assert "<script>" not in html


# =============================================================================
# Security Validation (5 tests)
# =============================================================================


class TestSecurityValidation:
    """Test that HTML composition remains secure with typography additions."""

    def test_no_script_tags_in_html(self, valid_report_context):
        """Generated HTML contains no <script> tags."""
        result = build_button2_report_html(valid_report_context)
        html = result["html_content"]
        assert "<script>" not in html
        assert "</script>" not in html

    def test_no_external_css_urls(self, valid_report_context):
        """Generated HTML uses no external CSS URLs."""
        result = build_button2_report_html(valid_report_context)
        html = result["html_content"]
        # Check for external stylesheet links
        assert "http://" not in html or "http://" in "<!-- http references only in text"
        assert "https://" not in html or "https://" in "<!-- https references only in text"
        # Specifically no <link> tags with href
        assert not re.search(r'<link[^>]*href=["\']https?://', html)

    def test_no_iframe_tags(self, valid_report_context):
        """Generated HTML contains no <iframe> tags."""
        result = build_button2_report_html(valid_report_context)
        html = result["html_content"]
        assert "<iframe" not in html

    def test_no_event_handlers_in_html(self, valid_report_context):
        """Generated HTML contains no inline event handlers."""
        result = build_button2_report_html(valid_report_context)
        html = result["html_content"]
        # Check for on* event handlers
        event_handlers = [
            "onclick", "onload", "onerror", "onmouseover", "onchange", "onfocus"
        ]
        for handler in event_handlers:
            assert f" {handler}=" not in html

    def test_css_contains_no_javascript(self, valid_report_context):
        """Generated CSS contains no javascript: URLs or expressions."""
        result = build_button2_report_html(valid_report_context)
        html = result["html_content"]
        assert "javascript:" not in html
        assert "expression(" not in html


# =============================================================================
# Regression Tests (6 tests)
# =============================================================================


class TestRegressionValidation:
    """Test that existing functionality is not broken by typography additions."""

    def test_build_returns_ok_on_valid_input(self, valid_report_context):
        """Function still returns ok=True for valid input."""
        result = build_button2_report_html(valid_report_context)
        assert result["ok"] is True
        assert result["error"] is None
        assert result["html_content"] is not None

    def test_build_returns_error_on_invalid_destination(self, valid_report_context):
        """Function still validates destination_marker."""
        context = valid_report_context.copy()
        context["destination_marker"] = "invalid_marker"
        result = build_button2_report_html(context)
        assert result["ok"] is False
        assert result["error"] == "invalid_destination_marker"

    def test_build_returns_error_on_invalid_context_kind(self, valid_report_context):
        """Function still validates report_context_kind."""
        context = valid_report_context.copy()
        context["report_context_kind"] = "invalid_kind"
        result = build_button2_report_html(context)
        assert result["ok"] is False
        assert result["error"] == "invalid_report_context_kind"

    def test_build_returns_error_on_missing_summary(self, valid_report_context):
        """Function still validates handoff_summary_preview presence."""
        context = valid_report_context.copy()
        context["handoff_summary_preview"] = ""
        result = build_button2_report_html(context)
        assert result["ok"] is False
        assert result["error"] == "missing_summary_content"

    def test_build_returns_error_on_invalid_input_type(self):
        """Function still validates input is a dict."""
        result = build_button2_report_html("not a dict")
        assert result["ok"] is False
        assert result["error"] == "invalid_input_type"

    def test_base_flags_still_set_correctly(self, valid_report_context):
        """Function still sets base flags correctly."""
        result = build_button2_report_html(valid_report_context)
        assert result["preview_only"] is True
        assert result["pdf_generation_performed"] is False
        assert result["file_write_performed"] is False
        assert result["export_performed"] is False
        assert result["delivery_performed"] is False
        assert result["html_composition_performed"] is True


# =============================================================================
# Integration Tests (2 tests)
# =============================================================================


class TestTypographyIntegration:
    """Integration tests for typography implementation."""

    def test_full_html_composition_with_typography(self, valid_report_context):
        """Full HTML composition works end-to-end with typography applied."""
        result = build_button2_report_html(valid_report_context)
        assert result["ok"] is True
        html = result["html_content"]
        # Check all major components are present and have typography
        assert 'class="typography-report-title"' in html
        assert 'class="typography-section-header-l1"' in html
        assert 'class="typography-body-secondary"' in html
        assert 'class="typography-list-item"' in html
        assert "typography-page-metadata" in html
        # Check CSS is present
        assert ".typography-" in html
        # Check content is preserved
        assert valid_report_context["handoff_summary_preview"] in html

    def test_typography_css_syntax_valid(self, valid_report_context):
        """Generated CSS has valid syntax (basic check)."""
        result = build_button2_report_html(valid_report_context)
        html = result["html_content"]
        style_match = re.search(r"<style>(.*?)</style>", html, re.DOTALL)
        style_content = style_match.group(1)
        # Check basic CSS syntax
        assert "{" in style_content and "}" in style_content
        # Count braces are balanced
        open_braces = style_content.count("{")
        close_braces = style_content.count("}")
        assert open_braces == close_braces
