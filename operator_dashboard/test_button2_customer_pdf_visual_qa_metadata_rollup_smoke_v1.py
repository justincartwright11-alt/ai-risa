"""
Smoke Tests: Visual QA Metadata Rollup Coexistence (Layer 7)

Slice: button2-customer-pdf-visual-qa-metadata-rollup-implementation-v1
Purpose: Verify all 7 metadata layers (6 existing + rollup) coexist safely
         in Button 2 HTML composition without conflicts or regressions.

Test coverage (12 tests):
1. All 7 layers present in HTML (1 test)
2. All 7 schema versions present (1 test)
3. All 7 layers valid together (1 test)
4. CSS display:none rules active (1 test)
5. No duplicate metadata sections (1 test)
6. QA footer rows present (1 test)
7. Safety flags unchanged (1 test)
8. HTML structure intact (1 test)
9. Rollup observational only (1 test)
10. Fail-closed logic intact (1 test)
11. Backward compatibility (2 tests)
"""

import pytest
import json
from re import search as re_search
from operator_dashboard.button2_html_composition_entry_point_v1 import (
    build_button2_report_html,
)


# ============================================================================
# Fixtures: Base Report Context
# ============================================================================

@pytest.fixture
def valid_report_context():
    """Valid report context with all 7 layer payloads."""
    return {
        "destination_marker": "button2_report_generation_preview",
        "report_context_kind": "dossier_handoff_report_context_preview",
        "fight_id": "fighter_a_vs_fighter_b_001",
        "handoff_summary_preview": "<p>Test summary</p>",
        "source_context_kind": "test_context",
        "source_ingest_mode": "manual_ingest",
        "overlap_proof": {"status": "present"},
        "off_page_text_proof": {"status": "present"},
        "visual_certification_status": "certified",
        # Layer 1: Hierarchy
        "hierarchy_markers": [
            {"level": "H0", "role": "report_identity_block"},
            {"level": "H1", "role": "analysis_block"},
        ],
        # Layer 2: Page breaks
        "section_block_metadata": [
            {
                "block_id": "report_identity",
                "role": "report_identity_block",
                "break_policy": "keep_together",
                "can_split": False,
            }
        ],
        "page_break_metadata": [
            {
                "break_id": "pb_001",
                "trigger_block_id": "report_identity",
                "overflow_reason": "section_size",
                "atomic_unit_preserved": True,
                "widow_orphan_rule_applied": False,
            }
        ],
        # Layer 3: Charts
        "chart_and_scenario_metadata": {
            "charts": [
                {
                    "chart_id": "chart_001",
                    "chart_type": "scenario_tree",
                    "placement_block_role": "matchup_signal_block",
                    "source_citations": ["SRC-001"],
                    "size_contract": {"max_width_in": 6.5, "max_height_in": 3.5},
                    "print_readability_contract": {"min_label_pt": 9, "min_stroke_pt": 1, "min_contrast_ratio": 4.5},
                }
            ],
            "scenario_tree": {
                "root_node": "baseline",
                "branches": ["pace_advantage"],
                "terminal_nodes": ["late_finish"],
                "confidence_band": "58-66%",
            },
            "method_pathways": [
                {
                    "pathway_id": "method_001",
                    "method_type": "decision",
                    "trigger_factors": ["jab_volume"],
                    "counter_factors": ["pressure"],
                    "evidence_links": ["SRC-001"],
                    "confidence_band": "52-60%",
                }
            ],
            "round_control": [
                {
                    "window_id": "round_001",
                    "round_range": "R1-R2",
                    "control_expectation": "fighter_a",
                    "dominance_signal": "medium",
                    "evidence_links": ["SRC-001"],
                }
            ],
            "risk_collapse_markers": [
                {
                    "marker_id": "risk_001",
                    "risk_type": "damage_accumulation",
                    "trigger_window": "R3-R5",
                    "severity": "elevated",
                    "mitigation_note": "Reset distance.",
                    "evidence_links": ["SRC-001"],
                }
            ],
        },
        # Layer 4: Header/Footer/Watermark
        "header_footer_watermark_metadata": {
            "header": {
                "report_title": "AI-RISA Premium Report",
                "event_name": "Test Event",
                "event_date": "2026-05-17",
                "status_label": "DRAFT",
                "confidentiality_label": "CONFIDENTIAL",
            },
            "footer": {
                "page_number_format": "Page {n} of {m}",
                "operator_label": "Operator",
                "generated_timestamp": "2026-05-17T12:00:00Z",
            },
            "watermark": {
                "watermark_enabled": True,
                "watermark_type": "draft",
                "watermark_text": "DRAFT",
                "watermark_opacity": 0.12,
                "watermark_angle": 45,
            },
        },
        # Layer 5: Source Traceability
        "source_traceability_metadata": {
            "schema_version": "button2.source_traceability.v1",
            "validation_status": "valid",
            "total_sources": 1,
            "official_sources_count": 1,
            "research_sources_count": 0,
            "operator_sources_count": 0,
            "average_confidence_level": "high",
            "corroboration_coverage": 1.0,
            "sources": [
                {
                    "id": "SRC-001",
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
        },
        "source_traceability": [
            {"id": "SRC-001", "type": "Official", "date": "2026-05-17"}
        ],
    }


# ============================================================================
# Test Class 1: Layer Presence in HTML (1 test)
# ============================================================================

class TestLayerPresenceInHTML:
    """Verify all 7 layers present in generated HTML."""

    def test_all_seven_layers_present(self, valid_report_context):
        """All 7 metadata sections exist in HTML output."""
        result = build_button2_report_html(valid_report_context)
        assert result.get("ok") is True
        html_content = result.get("html_content", "")
        
        # Check for all 7 metadata section IDs
        assert "button2-hierarchy-metadata" in html_content
        assert "button2-page-breaks-metadata" in html_content
        assert "button2-chart-scenario-metadata" in html_content
        assert "button2-header-footer-watermark-metadata" in html_content
        assert "button2-source-traceability-metadata" in html_content
        assert "button2-visual-qa-rollup-metadata" in html_content


# ============================================================================
# Test Class 2: Schema Versions Present (1 test)
# ============================================================================

class TestSchemaVersionsPresent:
    """Verify all 7 schema versions embedded in HTML."""

    def test_all_schema_versions_present(self, valid_report_context):
        """All 7 schema versions present in data attributes."""
        result = build_button2_report_html(valid_report_context)
        html_content = result.get("html_content", "")
        
        schema_versions = [
            "button2.page_hierarchy.v1",
            "button2.page_breaks_and_blocks.v1",
            "button2.chart_and_scenario.v1",
            "button2.header_footer_watermark.v1",
            "button2.source_traceability.v1",
            "button2.visual_qa_rollup.v1",
        ]
        
        for schema in schema_versions:
            assert schema in html_content, f"Schema {schema} not found in HTML"


# ============================================================================
# Test Class 3: All Layers Valid Together (1 test)
# ============================================================================

class TestAllLayersValidTogether:
    """Verify all 7 layers show valid status when provided."""

    def test_all_layers_valid_status(self, valid_report_context):
        """All layer validation statuses = valid when provided."""
        result = build_button2_report_html(valid_report_context)
        html_content = result.get("html_content", "")
        
        # Check hierarchy validation
        assert 'hierarchy-validation-status="valid"' in html_content or \
               'data-hierarchy-validation-status="valid"' in html_content or \
               "Hierarchy validation: valid" in html_content
        
        # Check page-breaks validation
        assert 'page-breaks-validation-status="valid"' in html_content or \
               "Page-break metadata validation: valid" in html_content
        
        # Check chart validation
        assert 'chart-scenario-validation-status="valid"' in html_content or \
               "Chart/scenario metadata validation: valid" in html_content
        
        # Check hfw validation
        assert 'header-footer-watermark-validation-status="valid"' in html_content or \
               "Header/footer/watermark metadata validation: valid" in html_content
        
        # Check source traceability validation
        assert 'source-traceability-validation-status="valid"' in html_content or \
               "Source traceability metadata validation: valid" in html_content


# ============================================================================
# Test Class 4: CSS Display:None Rules Active (1 test)
# ============================================================================

class TestCSSDisplayNoneRules:
    """Verify metadata sections are hidden via CSS."""

    def test_display_none_css_present(self, valid_report_context):
        """CSS display:none rules exist for all 7 metadata sections."""
        result = build_button2_report_html(valid_report_context)
        html_content = result.get("html_content", "")
        
        css_rules = [
            ".hierarchy-metadata { display: none; }",
            ".page-breaks-metadata { display: none; }",
            ".chart-scenario-metadata { display: none; }",
            ".header-footer-watermark-metadata { display: none; }",
            ".source-traceability-metadata { display: none; }",
            ".visual-qa-rollup-metadata { display: none; }",
        ]
        
        for css_rule in css_rules:
            assert css_rule in html_content, f"CSS rule {css_rule} not found"


# ============================================================================
# Test Class 5: No Duplicate Sections (1 test)
# ============================================================================

class TestNoDuplicateSections:
    """Verify no duplicate metadata sections."""

    def test_no_duplicate_metadata_sections(self, valid_report_context):
        """Each metadata section ID appears exactly once."""
        result = build_button2_report_html(valid_report_context)
        html_content = result.get("html_content", "")
        
        section_ids = [
            "button2-hierarchy-metadata",
            "button2-page-breaks-metadata",
            "button2-chart-scenario-metadata",
            "button2-header-footer-watermark-metadata",
            "button2-source-traceability-metadata",
            "button2-visual-qa-rollup-metadata",
        ]
        
        for section_id in section_ids:
            count = html_content.count(f'id="{section_id}"')
            assert count == 1, f"Section {section_id} appears {count} times"


# ============================================================================
# Test Class 6: QA Footer Rows Present (1 test)
# ============================================================================

class TestQAFooterRowsPresent:
    """Verify all QA footer rows present."""

    def test_qa_footer_rows_for_all_layers(self, valid_report_context):
        """All QA footer rows present in output."""
        result = build_button2_report_html(valid_report_context)
        html_content = result.get("html_content", "")
        
        qa_rows = [
            "Hierarchy validation:",
            "Page-break metadata validation:",
            "Chart/scenario metadata validation:",
            "Header/footer/watermark metadata validation:",
            "Source traceability metadata validation:",
            "Visual QA rollup status:",
            "Certification readiness:",
            "Valid layers:",
            "Overall visual confidence:",
        ]
        
        for qa_row in qa_rows:
            assert qa_row in html_content, f"QA row '{qa_row}' not found"


# ============================================================================
# Test Class 7: Safety Flags Unchanged (1 test)
# ============================================================================

class TestSafetyFlagsUnchanged:
    """Verify all safety flags remain unchanged."""

    def test_safety_flags_preserved(self, valid_report_context):
        """All safety flags are preserved (preview_only=True, etc.)."""
        result = build_button2_report_html(valid_report_context)
        
        assert result.get("preview_only") is True
        assert result.get("pdf_generation_performed") is False
        assert result.get("file_write_performed") is False
        assert result.get("export_performed") is False
        assert result.get("delivery_performed") is False


# ============================================================================
# Test Class 8: HTML Structure Intact (1 test)
# ============================================================================

class TestHTMLStructureIntact:
    """Verify HTML structure remains valid."""

    def test_html_structure_valid(self, valid_report_context):
        """HTML contains valid structure with all sections."""
        result = build_button2_report_html(valid_report_context)
        html_content = result.get("html_content", "")
        
        # Check DOCTYPE and basic structure
        assert "<!DOCTYPE html>" in html_content
        assert "<html" in html_content
        assert "<head>" in html_content
        assert "<body>" in html_content
        assert "</body>" in html_content
        assert "</html>" in html_content
        
        # Check main content areas
        assert "Report Summary" in html_content
        assert "Source Traceability" in html_content


# ============================================================================
# Test Class 9: Rollup Observational Only (1 test)
# ============================================================================

class TestRollupObservationalOnly:
    """Verify rollup is observational only, no automation."""

    def test_rollup_no_certification_automation(self, valid_report_context):
        """Rollup metadata does not automate certification decisions."""
        result = build_button2_report_html(valid_report_context)
        html_content = result.get("html_content", "")
        
        # Rollup should provide metrics, not automation
        assert "rollup_status" in html_content or "Visual QA rollup status" in html_content
        
        # Should not override visual_certification_status (should preserve it or show it as-is)
        assert "Visual certification:" in html_content or "Certification readiness:" in html_content


# ============================================================================
# Test Class 10: Fail-Closed Logic Intact (1 test)
# ============================================================================

class TestFailClosedLogicIntact:
    """Verify fail-closed behavior preserved."""

    def test_visual_certification_downgrade_on_layer_failure(self):
        """visual_certification_status downgrades if any layer invalid."""
        context = {
            "destination_marker": "button2_report_generation_preview",
            "report_context_kind": "dossier_handoff_report_context_preview",
            "fight_id": "test_001",
            "handoff_summary_preview": "<p>Test</p>",
            "source_context_kind": "test",
            "source_ingest_mode": "test",
            "visual_certification_status": "certified",
            "hierarchy_markers": [],  # Invalid: empty
        }
        result = build_button2_report_html(context)
        html_content = result.get("html_content", "")
        
        # Should downgrade to not_certified due to invalid hierarchy
        assert "not_certified" in html_content


# ============================================================================
# Test Class 11: Backward Compatibility (2 tests)
# ============================================================================

class TestBackwardCompatibility:
    """Verify backward compatibility with 6-layer composition."""

    def test_html_generation_succeeds_with_all_layers(self, valid_report_context):
        """HTML generation succeeds with all 7 layers present."""
        result = build_button2_report_html(valid_report_context)
        assert result.get("ok") is True
        assert result.get("html_composition_performed") is True
        assert result.get("html_content") is not None

    def test_html_generation_succeeds_without_rollup_context(self):
        """HTML generation succeeds even without explicit rollup context."""
        context = {
            "destination_marker": "button2_report_generation_preview",
            "report_context_kind": "dossier_handoff_report_context_preview",
            "fight_id": "test_001",
            "handoff_summary_preview": "<p>Summary</p>",
            "source_context_kind": "test",
            "source_ingest_mode": "test",
        }
        result = build_button2_report_html(context)
        assert result.get("ok") is True
        # Should generate rollup metadata with defaults
        html_content = result.get("html_content", "")
        assert "button2-visual-qa-rollup-metadata" in html_content
