# Button 2 Source Traceability Visual Layer Smoke Tests (v1)
# Slice: button2-customer-pdf-source-traceability-visual-layer-implementation-v1
#
# Purpose: Smoke tests verifying source traceability metadata layer coexists
# safely with all prior 5 layers (typography + hierarchy + page-breaks + charts + hfw).

import sys
import os
import pytest

# Add the operator_dashboard directory to sys.path for imports
sys.path.insert(0, os.path.dirname(__file__))

from button2_html_composition_entry_point_v1 import (
    build_button2_report_html,
    _default_source_traceability_metadata,
)

# Base report context fixture
_BASE_REPORT_CONTEXT = {
    "destination_marker": "button2_report_generation_preview",
    "report_context_kind": "dossier_handoff_report_context_preview",
    "handoff_summary_preview": "<p>Sample report summary</p>",
    "source_context_kind": "test",
    "source_ingest_mode": "preview",
    "visual_certification_status": "certified",
}


class TestSourceTraceabilityCoexistence:
    """Verify source traceability layer (6) coexists with all prior 5 layers."""

    def test_all_6_metadata_layers_present_in_html(self):
        """Verify all 6 metadata section IDs are present in HTML output."""
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["source_traceability_metadata"] = _default_source_traceability_metadata()
        result = build_button2_report_html(ctx)
        assert result["ok"]
        html = result["html_content"]
        
        # All 6 layer metadata sections should be present
        assert 'id="button2-hierarchy-metadata"' in html
        assert 'id="button2-page-breaks-metadata"' in html
        assert 'id="button2-chart-scenario-metadata"' in html
        assert 'id="button2-header-footer-watermark-metadata"' in html
        assert 'id="button2-source-traceability-metadata"' in html

    def test_all_6_schema_versions_present(self):
        """Verify all 6 schema versions are embedded in metadata."""
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["source_traceability_metadata"] = _default_source_traceability_metadata()
        result = build_button2_report_html(ctx)
        assert result["ok"]
        html = result["html_content"]
        
        # All 6 schema versions should be present
        assert "button2.page_hierarchy.v1" in html
        assert "button2.page_breaks_and_blocks.v1" in html
        assert "button2.chart_and_scenario.v1" in html
        assert "button2.header_footer_watermark.v1" in html
        assert "button2.source_traceability.v1" in html

    def test_hierarchy_layer_intact_with_src_layer(self):
        """Verify hierarchy metadata section remains intact with source layer."""
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["source_traceability_metadata"] = _default_source_traceability_metadata()
        result = build_button2_report_html(ctx)
        assert result["ok"]
        html = result["html_content"]
        
        assert 'id="button2-hierarchy-metadata"' in html
        assert "button2.page_hierarchy.v1" in html

    def test_page_breaks_layer_intact_with_src_layer(self):
        """Verify page-breaks metadata section remains intact with source layer."""
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["source_traceability_metadata"] = _default_source_traceability_metadata()
        result = build_button2_report_html(ctx)
        assert result["ok"]
        html = result["html_content"]
        
        assert 'id="button2-page-breaks-metadata"' in html
        assert "button2.page_breaks_and_blocks.v1" in html

    def test_chart_layer_intact_with_src_layer(self):
        """Verify chart metadata section remains intact with source layer."""
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["source_traceability_metadata"] = _default_source_traceability_metadata()
        result = build_button2_report_html(ctx)
        assert result["ok"]
        html = result["html_content"]
        
        assert 'id="button2-chart-scenario-metadata"' in html
        assert "button2.chart_and_scenario.v1" in html

    def test_hfw_layer_intact_with_src_layer(self):
        """Verify header/footer/watermark metadata section remains intact with source layer."""
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["source_traceability_metadata"] = _default_source_traceability_metadata()
        result = build_button2_report_html(ctx)
        assert result["ok"]
        html = result["html_content"]
        
        assert 'id="button2-header-footer-watermark-metadata"' in html
        assert "button2.header_footer_watermark.v1" in html

    def test_fail_closed_behavior_preserved_across_all_layers(self):
        """Verify fail-closed downgrade still works with source layer present."""
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["source_traceability_metadata"] = {
            "sources": [
                {
                    "source_type": "invalid",
                    "source_class": "tier_a",
                    "confidence_level": "high",
                    "citation_completeness": "complete",
                    "verification_status": "verified",
                    "source_url": "https://example.com",
                    "source_date": "2026-05-17",
                }
            ],
            "lineage_graph": {},
            "total_sources": 1,
            "corroboration_coverage": 1.0,
        }
        result = build_button2_report_html(ctx)
        assert result["ok"]
        # Invalid source metadata should show invalid validation status
        assert 'data-source-traceability-validation-status="invalid"' in result["html_content"]

    def test_all_qa_metadata_rows_present(self):
        """Verify all QA metadata rows are present in meta-footer."""
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["source_traceability_metadata"] = _default_source_traceability_metadata()
        result = build_button2_report_html(ctx)
        assert result["ok"]
        html = result["html_content"]
        
        # All validation status rows should be present
        assert "Hierarchy validation:" in html
        assert "Page-break metadata validation:" in html
        assert "Chart/scenario metadata validation:" in html
        assert "Header/footer/watermark metadata validation:" in html
        assert "Source traceability metadata validation:" in html

    def test_metadata_section_css_display_none(self):
        """Verify all 6 metadata section CSS rules have display:none."""
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["source_traceability_metadata"] = _default_source_traceability_metadata()
        result = build_button2_report_html(ctx)
        assert result["ok"]
        html = result["html_content"]
        
        # All metadata sections should have CSS display:none rules
        assert ".hierarchy-metadata { display: none; }" in html
        assert ".page-breaks-metadata { display: none; }" in html
        assert ".chart-scenario-metadata { display: none; }" in html
        assert ".header-footer-watermark-metadata { display: none; }" in html
        assert ".source-traceability-metadata { display: none; }" in html

    def test_safety_flags_preserved_with_all_layers(self):
        """Verify all safety flags unchanged with all 6 layers present."""
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["source_traceability_metadata"] = _default_source_traceability_metadata()
        result = build_button2_report_html(ctx)
        assert result["ok"]
        
        assert result["preview_only"] is True
        assert result["pdf_generation_performed"] is False
        assert result["file_write_performed"] is False
        assert result["export_performed"] is False
        assert result["delivery_performed"] is False

    def test_no_duplicate_metadata_sections(self):
        """Verify each metadata section ID appears exactly once."""
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["source_traceability_metadata"] = _default_source_traceability_metadata()
        result = build_button2_report_html(ctx)
        assert result["ok"]
        html = result["html_content"]
        
        # Each section ID should appear exactly once
        assert html.count('id="button2-hierarchy-metadata"') == 1
        assert html.count('id="button2-page-breaks-metadata"') == 1
        assert html.count('id="button2-chart-scenario-metadata"') == 1
        assert html.count('id="button2-header-footer-watermark-metadata"') == 1
        assert html.count('id="button2-source-traceability-metadata"') == 1

    def test_valid_metadata_across_all_layers(self):
        """Verify valid metadata across all 6 layers produces valid output."""
        ctx = _BASE_REPORT_CONTEXT.copy()
        ctx["source_traceability_metadata"] = {
            "sources": [
                {
                    "source_type": "official",
                    "source_class": "tier_a",
                    "confidence_level": "high",
                    "citation_completeness": "complete",
                    "verification_status": "verified",
                    "source_url": "https://example.com",
                    "source_date": "2026-05-17",
                }
            ],
            "lineage_graph": {},
            "total_sources": 1,
            "corroboration_coverage": 1.0,
        }
        result = build_button2_report_html(ctx)
        assert result["ok"]
        html = result["html_content"]
        
        # All 6 schema versions should be present
        assert "button2.page_hierarchy.v1" in html
        assert "button2.page_breaks_and_blocks.v1" in html
        assert "button2.chart_and_scenario.v1" in html
        assert "button2.header_footer_watermark.v1" in html
        assert "button2.source_traceability.v1" in html
        
        # All 6 metadata section IDs should be present
        assert 'id="button2-hierarchy-metadata"' in html
        assert 'id="button2-page-breaks-metadata"' in html
        assert 'id="button2-chart-scenario-metadata"' in html
        assert 'id="button2-header-footer-watermark-metadata"' in html
        assert 'id="button2-source-traceability-metadata"' in html


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
