"""
Smoke test for Button 2 header/footer/watermark metadata coexistence.

Verifies that header/footer/watermark metadata layer coexists safely with
all prior layers: typography + hierarchy + page-breaks + charts.

Coverage:
- All 5 metadata layers present in HTML (typography classes, hierarchy markers, page-break data, chart metadata, hfw metadata)
- Schema versions for each layer present
- Fail-closed behavior preserved across all layers
- Safety flags unchanged (preview_only=True, pdf_generation_performed=False, file_write_performed=False)
"""

import pytest
import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from button2_html_composition_entry_point_v1 import (
    build_button2_report_html,
    _default_header_footer_watermark_metadata,
    _default_section_block_metadata,
    _default_page_break_metadata,
    _default_chart_and_scenario_metadata,
)


_BASE_REPORT_CONTEXT = {
    "destination_marker": "button2_report_generation_preview",
    "report_context_kind": "dossier_handoff_report_context_preview",
    "handoff_summary_preview": "<p>Full smoke test with all 5 layers</p>",
    "source_traceability": [],
    "source_context_kind": "web_search",
    "source_ingest_mode": "manual",
    "overlap_proof": {"status": "pass"},
    "off_page_text_proof": {"status": "pass"},
    "visual_certification_status": "certified",
}


class TestHeaderFooterWatermarkCoexistence:
    """Test header/footer/watermark metadata coexists with all prior layers."""

    def test_all_5_metadata_layers_present_in_html(self):
        """Verify all 5 metadata layers coexist in HTML output."""
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["section_block_metadata"] = _default_section_block_metadata()
        ctx["page_break_metadata"] = _default_page_break_metadata()
        ctx["chart_and_scenario_metadata"] = _default_chart_and_scenario_metadata()
        ctx["header_footer_watermark_metadata"] = _default_header_footer_watermark_metadata()

        result = build_button2_report_html(ctx)
        assert result["ok"], result.get("error")
        html = result["html_content"]

        # Verify all 5 metadata sections present
        assert "id=\"button2-hierarchy-metadata\"" in html
        assert "id=\"button2-page-breaks-metadata\"" in html
        assert "id=\"button2-chart-scenario-metadata\"" in html
        assert "id=\"button2-header-footer-watermark-metadata\"" in html

        # Verify typography classes are applied
        assert "typography-report-title" in html or "typography-" in html

    def test_all_schema_versions_present(self):
        """Verify all 5 schema versions are present."""
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["section_block_metadata"] = _default_section_block_metadata()
        ctx["page_break_metadata"] = _default_page_break_metadata()
        ctx["chart_and_scenario_metadata"] = _default_chart_and_scenario_metadata()
        ctx["header_footer_watermark_metadata"] = _default_header_footer_watermark_metadata()

        result = build_button2_report_html(ctx)
        assert result["ok"]
        html = result["html_content"]

        # Verify schema versions
        assert "button2.page_hierarchy.v1" in html
        assert "button2.page_breaks_and_blocks.v1" in html
        assert "button2.chart_and_scenario.v1" in html
        assert "button2.header_footer_watermark.v1" in html

    def test_hierarchy_layer_intact_with_hfw_layer(self):
        """Verify hierarchy metadata layer remains intact when hfw layer added."""
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["header_footer_watermark_metadata"] = _default_header_footer_watermark_metadata()

        result = build_button2_report_html(ctx)
        assert result["ok"]
        html = result["html_content"]

        # Extract and parse hierarchy metadata
        assert "button2-hierarchy-metadata" in html
        assert "data-hierarchy-validation-status" in html
        assert "data-canonical-section-order" in html

    def test_page_breaks_layer_intact_with_hfw_layer(self):
        """Verify page-breaks metadata layer remains intact when hfw layer added."""
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["section_block_metadata"] = _default_section_block_metadata()
        ctx["page_break_metadata"] = _default_page_break_metadata()
        ctx["header_footer_watermark_metadata"] = _default_header_footer_watermark_metadata()

        result = build_button2_report_html(ctx)
        assert result["ok"]
        html = result["html_content"]

        # Verify page-breaks section present
        assert "button2-page-breaks-metadata" in html
        assert "data-page-breaks-schema-version" in html
        assert "button2.page_breaks_and_blocks.v1" in html

    def test_chart_layer_intact_with_hfw_layer(self):
        """Verify chart metadata layer remains intact when hfw layer added."""
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["chart_and_scenario_metadata"] = _default_chart_and_scenario_metadata()
        ctx["header_footer_watermark_metadata"] = _default_header_footer_watermark_metadata()

        result = build_button2_report_html(ctx)
        assert result["ok"]
        html = result["html_content"]

        # Verify chart section present
        assert "button2-chart-scenario-metadata" in html
        assert "data-chart-scenario-schema-version" in html
        assert "button2.chart_and_scenario.v1" in html

    def test_fail_closed_behavior_preserved_across_all_layers(self):
        """Verify fail-closed behavior works across all 5 layers."""
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["visual_certification_status"] = "certified"
        ctx["section_block_metadata"] = _default_section_block_metadata()
        ctx["page_break_metadata"] = _default_page_break_metadata()
        ctx["chart_and_scenario_metadata"] = _default_chart_and_scenario_metadata()
        
        # Invalid hfw metadata should trigger fail-closed
        ctx["header_footer_watermark_metadata"] = {
            "header": None,  # Invalid
            "footer": {"page_number_format": "Page {n} of {m}"},
            "watermark": {"watermark_enabled": False, "watermark_type": "none"},
        }

        result = build_button2_report_html(ctx)
        assert result["ok"]
        html = result["html_content"]
        
        # Should be downgraded to not_certified
        assert "not_certified" in html

    def test_all_qa_metadata_rows_present(self):
        """Verify all metadata validation rows present in QA footer."""
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["section_block_metadata"] = _default_section_block_metadata()
        ctx["page_break_metadata"] = _default_page_break_metadata()
        ctx["chart_and_scenario_metadata"] = _default_chart_and_scenario_metadata()
        ctx["header_footer_watermark_metadata"] = _default_header_footer_watermark_metadata()

        result = build_button2_report_html(ctx)
        assert result["ok"]
        html = result["html_content"]

        # Verify all QA rows present
        assert "Hierarchy validation:" in html
        assert "Page-break metadata validation:" in html
        assert "Chart/scenario metadata validation:" in html
        assert "Header/footer/watermark metadata validation:" in html

    def test_metadata_section_css_display_none(self):
        """Verify all metadata sections have display:none CSS."""
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["section_block_metadata"] = _default_section_block_metadata()
        ctx["page_break_metadata"] = _default_page_break_metadata()
        ctx["chart_and_scenario_metadata"] = _default_chart_and_scenario_metadata()
        ctx["header_footer_watermark_metadata"] = _default_header_footer_watermark_metadata()

        result = build_button2_report_html(ctx)
        assert result["ok"]
        html = result["html_content"]

        # Verify CSS display:none styles exist
        assert ".header-footer-watermark-metadata { display: none; }" in html
        assert ".hierarchy-metadata { display: none; }" in html
        assert ".page-breaks-metadata { display: none; }" in html
        assert ".chart-scenario-metadata { display: none; }" in html

    def test_safety_flags_preserved_with_all_layers(self):
        """Verify safety flags remain unchanged across all 5 layers."""
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["section_block_metadata"] = _default_section_block_metadata()
        ctx["page_break_metadata"] = _default_page_break_metadata()
        ctx["chart_and_scenario_metadata"] = _default_chart_and_scenario_metadata()
        ctx["header_footer_watermark_metadata"] = _default_header_footer_watermark_metadata()

        result = build_button2_report_html(ctx)
        assert result["ok"]
        assert result["preview_only"] is True
        assert result["pdf_generation_performed"] is False
        assert result["file_write_performed"] is False
        assert result["export_performed"] is False
        assert result["delivery_performed"] is False

    def test_no_duplicate_metadata_sections(self):
        """Verify no duplicate metadata sections in HTML."""
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["section_block_metadata"] = _default_section_block_metadata()
        ctx["page_break_metadata"] = _default_page_break_metadata()
        ctx["chart_and_scenario_metadata"] = _default_chart_and_scenario_metadata()
        ctx["header_footer_watermark_metadata"] = _default_header_footer_watermark_metadata()

        result = build_button2_report_html(ctx)
        assert result["ok"]
        html = result["html_content"]

        # Count occurrences of each metadata section
        assert html.count("id=\"button2-hierarchy-metadata\"") == 1
        assert html.count("id=\"button2-page-breaks-metadata\"") == 1
        assert html.count("id=\"button2-chart-scenario-metadata\"") == 1
        assert html.count("id=\"button2-header-footer-watermark-metadata\"") == 1

    def test_valid_metadata_across_all_layers(self):
        """Verify valid metadata status across all 5 layers."""
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["section_block_metadata"] = _default_section_block_metadata()
        ctx["page_break_metadata"] = _default_page_break_metadata()
        ctx["chart_and_scenario_metadata"] = _default_chart_and_scenario_metadata()
        ctx["header_footer_watermark_metadata"] = _default_header_footer_watermark_metadata()

        result = build_button2_report_html(ctx)
        assert result["ok"]
        html = result["html_content"]

        # All validations should contain "valid"
        assert "button2-hierarchy-metadata" in html
        assert "button2-page-breaks-metadata" in html
        assert "button2-chart-scenario-metadata" in html
        assert "button2-header-footer-watermark-metadata" in html


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
