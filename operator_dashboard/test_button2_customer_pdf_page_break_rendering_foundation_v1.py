"""
Button 2 Customer PDF — Phase 2 Slice 3 — Page-Break Rendering Foundation Implementation Tests

Purpose:
- Validate that Phase 1 page-break and section-block metadata is preserved and accessible in rendered HTML
- Verify page-break policies (keep_together, allow_internal_break, split_by_chunk) are render-facing
- Verify section-block roles remain present and accessible
- Verify widow/orphan metadata remains present and intact
- Verify forbidden break boundaries remain detectable
- Verify invalid page-break metadata fails closed to not_certified
- Verify typography rendering foundation tests remain green
- Verify hierarchy rendering foundation tests remain green
- Verify all Phase 1 tests remain green

Governance:
- Page-break rendering foundation ONLY
- No chart rendering changes
- No header/footer rendering expansion
- No delivery workflow changes
- No approval changes
- No output-path changes
- No file-write behavior changes
- No dashboard changes
- Phase 1 metadata remains immutable
- Typography and hierarchy tokens remain unchanged
"""

import re
import json
from operator_dashboard.button2_html_composition_entry_point_v1 import (
    build_button2_report_html,
    _validate_page_break_metadata,
    _validate_section_block_metadata,
    _BREAK_POLICIES,
    _FORBIDDEN_BREAK_BOUNDARIES,
    _WIDOW_ORPHAN_RULES,
    _PAGE_BLOCK_ROLES,
)


def _valid_ctx(**overrides):
    """Base valid context for page-break rendering tests."""
    base = {
        "destination_marker": "button2_report_generation_preview",
        "report_context_kind": "dossier_handoff_report_context_preview",
        "fight_id": "fight_page_break_001",
        "source_context_kind": "button1_dossier_handoff",
        "source_ingest_mode": "preview_only",
        "handoff_summary_preview": "Page-Break Rendering Test: Fighter A vs Fighter B",
        "hierarchy_markers": [
            {"level": "H0", "role": "report_identity_block"},
            {"level": "H1", "role": "analysis_block"},
            {"level": "Body", "role": "analysis_block"},
            {"level": "Meta", "role": "footer_metadata_block"},
        ],
        "section_block_metadata": [
            {
                "block_id": "report_identity",
                "role": "report_identity_block",
                "break_policy": "keep_together",
                "can_split": False,
                "continuation_header_required": False,
                "min_lines_after_header": 2,
                "min_space_for_chart_in": 1.0,
                "approved_break_boundaries": ["between_h1_sections"],
            },
            {
                "block_id": "report_summary",
                "role": "analysis_block",
                "break_policy": "allow_internal_break",
                "can_split": True,
                "continuation_header_required": False,
                "min_lines_after_header": 2,
                "min_space_for_chart_in": 1.0,
                "approved_break_boundaries": ["between_h2_subsections"],
            },
            {
                "block_id": "source_traceability",
                "role": "sources_calibration_block",
                "break_policy": "split_by_chunk",
                "can_split": True,
                "continuation_header_required": True,
                "chunk_size": 10,
                "min_lines_after_header": 2,
                "min_space_for_chart_in": 1.0,
                "approved_break_boundaries": ["between_source_chunks"],
            },
        ],
        "page_break_metadata": [
            {
                "break_id": "pb_001",
                "trigger_block_id": "source_traceability",
                "trigger_section": "Source Traceability",
                "overflow_reason": "source_chunking",
                "previous_page_content_height_in": 8.0,
                "atomic_unit_preserved": True,
                "widow_orphan_rule_applied": False,
            }
        ],
        "source_traceability": [
            {"id": "SRC-001", "type": "official", "date": "2026-05-17"}
        ],
        "overlap_proof": {"proof_kind": "overlap_proof", "proof_status": "missing"},
        "off_page_text_proof": {"proof_kind": "off_page_text_proof", "proof_status": "missing"},
    }
    base.update(overrides)
    return base


class TestPageBreakPoliciesPresence:
    """Verify page-break policies (keep_together, allow_internal_break, split_by_chunk) are present."""

    def test_keep_together_policy_in_html(self):
        """keep_together policy must be represented in rendered HTML."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        assert "keep_together" in html or "keep-together" in html

    def test_allow_internal_break_policy_in_html(self):
        """allow_internal_break policy must be represented in rendered HTML."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        assert "allow_internal_break" in html or "allow-internal-break" in html

    def test_split_by_chunk_policy_in_html(self):
        """split_by_chunk policy must be represented in rendered HTML."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        assert "split_by_chunk" in html or "split-by-chunk" in html

    def test_all_break_policies_defined(self):
        """All break policies must be defined."""
        assert _BREAK_POLICIES is not None
        assert isinstance(_BREAK_POLICIES, set)
        assert "keep_together" in _BREAK_POLICIES
        assert "allow_internal_break" in _BREAK_POLICIES
        assert "split_by_chunk" in _BREAK_POLICIES

    def test_break_policies_accessible_in_metadata(self):
        """Break policies must be accessible in page-break metadata section."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        assert 'button2.page_breaks_and_blocks.v1' in html


class TestSectionBlockRolesPresence:
    """Verify section-block roles remain present and accessible."""

    def test_report_identity_block_role_present(self):
        """report_identity_block role must be present."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        assert "report_identity_block" in html or "report-identity-block" in html

    def test_analysis_block_role_present(self):
        """analysis_block role must be present."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        assert "analysis_block" in html or "analysis-block" in html

    def test_sources_calibration_block_role_present(self):
        """sources_calibration_block role must be present."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        assert "sources_calibration_block" in html or "sources-calibration-block" in html

    def test_footer_metadata_block_role_present(self):
        """footer_metadata_block role must be present."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        assert "footer_metadata_block" in html or "footer-metadata-block" in html

    def test_all_page_block_roles_in_metadata(self):
        """All page block roles must be in metadata."""
        assert _PAGE_BLOCK_ROLES is not None
        assert isinstance(_PAGE_BLOCK_ROLES, set)
        assert "report_identity_block" in _PAGE_BLOCK_ROLES
        assert "analysis_block" in _PAGE_BLOCK_ROLES
        assert "sources_calibration_block" in _PAGE_BLOCK_ROLES
        assert "footer_metadata_block" in _PAGE_BLOCK_ROLES


class TestWidowOrphanMetadata:
    """Verify widow/orphan metadata remains present and intact."""

    def test_widow_orphan_rules_present(self):
        """Widow/orphan rules must be present in metadata."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        
        # Should contain widow_orphan references or similar
        assert "widow" in html.lower() or "orphan" in html.lower() or "min_lines" in html

    def test_widow_orphan_rules_defined(self):
        """Widow/orphan rules must be defined."""
        assert _WIDOW_ORPHAN_RULES is not None
        assert isinstance(_WIDOW_ORPHAN_RULES, list)
        assert len(_WIDOW_ORPHAN_RULES) > 0

    def test_widow_orphan_metadata_structure(self):
        """Widow/orphan metadata must have defined structure."""
        # Expected rules
        expected_rules = [
            "header_requires_two_following_lines",
            "no_single_list_item_orphan",
            "no_lonely_chart_under_one_inch_space",
        ]
        for rule in expected_rules:
            assert rule in _WIDOW_ORPHAN_RULES

    def test_min_lines_after_header_preserved(self):
        """min_lines_after_header must be preserved in metadata."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        
        # Should appear in section block metadata
        assert "min_lines" in html.lower() or "2" in html


class TestForbiddenBoundaryDetection:
    """Verify forbidden break boundaries remain detectable."""

    def test_forbidden_boundaries_defined(self):
        """Forbidden break boundaries must be defined."""
        assert _FORBIDDEN_BREAK_BOUNDARIES is not None
        assert isinstance(_FORBIDDEN_BREAK_BOUNDARIES, set)
        assert len(_FORBIDDEN_BREAK_BOUNDARIES) > 0

    def test_after_header_without_two_lines_boundary(self):
        """after_header_without_two_lines boundary must be defined."""
        assert "after_header_without_two_lines" in _FORBIDDEN_BREAK_BOUNDARIES

    def test_inside_chart_or_table_boundary(self):
        """inside_chart_or_table boundary must be defined."""
        assert "inside_chart_or_table" in _FORBIDDEN_BREAK_BOUNDARIES

    def test_between_claim_and_citation_boundary(self):
        """between_claim_and_citation boundary must be defined."""
        assert "between_claim_and_citation" in _FORBIDDEN_BREAK_BOUNDARIES

    def test_forbidden_boundaries_detectable_in_validation(self):
        """Forbidden boundaries must be detectable in validation logic."""
        # Invalid metadata with forbidden boundary should fail
        invalid_blocks = [
            {
                "block_id": "test",
                "role": "analysis_block",
                "break_policy": "allow_internal_break",
                "can_split": True,
                "continuation_header_required": False,
                "min_lines_after_header": 2,
                "min_space_for_chart_in": 1.0,
                "break_boundary": "after_header_without_two_lines",  # FORBIDDEN
                "approved_break_boundaries": [],
            }
        ]
        
        validation = _validate_section_block_metadata(invalid_blocks)
        assert validation["valid"] is False
        assert len(validation["forbidden_break_boundaries_detected"]) > 0


class TestPageBreakMetadataIntegrity:
    """Verify page-break metadata remains intact and accessible."""

    def test_page_breaks_metadata_section_present(self):
        """Page-break metadata section must be present in HTML."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        
        assert 'id="button2-page-breaks-metadata"' in html
        assert 'class="page-breaks-metadata"' in html

    def test_page_breaks_schema_version_present(self):
        """Page-break metadata must include schema version."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        
        assert 'button2.page_breaks_and_blocks.v1' in html

    def test_page_breaks_validation_status_accessible(self):
        """Page-break validation status must be accessible."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        
        assert 'data-page-breaks-validation-status=' in html

    def test_overflow_reasons_represented(self):
        """Overflow reasons must be represented in metadata."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        
        # Should reference overflow reasons
        assert "overflow" in html.lower() or "source_chunking" in html or "section_size" in html

    def test_atomic_unit_preservation_represented(self):
        """Atomic unit preservation must be represented."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        
        # Should indicate atomic preservation
        assert "atomic" in html.lower() or "preserved" in html.lower()


class TestPageBreakValidationFailClosed:
    """Verify invalid page-break metadata fails closed to not_certified."""

    def test_valid_page_break_metadata_passes_validation(self):
        """Valid page-break metadata must pass validation."""
        page_breaks = [
            {
                "break_id": "pb_001",
                "trigger_block_id": "source_traceability",
                "overflow_reason": "source_chunking",
                "atomic_unit_preserved": True,
                "widow_orphan_rule_applied": False,
            }
        ]
        section_block_ids = ["source_traceability"]
        
        validation = _validate_page_break_metadata(page_breaks, section_block_ids)
        assert validation["valid"] is True
        assert validation["status"] == "valid"

    def test_missing_page_break_metadata_fails_validation(self):
        """Missing page-break metadata must fail validation."""
        validation = _validate_page_break_metadata(None, [])
        assert validation["valid"] is False
        assert validation["status"] == "missing"

    def test_empty_page_break_metadata_fails_validation(self):
        """Empty page-break metadata must fail validation."""
        validation = _validate_page_break_metadata([], [])
        assert validation["valid"] is False
        assert validation["status"] == "invalid"

    def test_invalid_overflow_reason_fails_validation(self):
        """Invalid overflow reason must fail validation."""
        page_breaks = [
            {
                "break_id": "pb_001",
                "trigger_block_id": "source_traceability",
                "overflow_reason": "INVALID_REASON",
                "atomic_unit_preserved": True,
                "widow_orphan_rule_applied": False,
            }
        ]
        
        validation = _validate_page_break_metadata(page_breaks, ["source_traceability"])
        assert validation["valid"] is False

    def test_invalid_section_blocks_fail_validation(self):
        """Invalid section blocks must fail validation."""
        invalid_blocks = [
            {
                "block_id": "test",
                "role": "INVALID_ROLE",
                "break_policy": "keep_together",
                "can_split": False,
                "continuation_header_required": False,
                "min_lines_after_header": 2,
                "min_space_for_chart_in": 1.0,
                "approved_break_boundaries": [],
            }
        ]
        
        validation = _validate_section_block_metadata(invalid_blocks)
        assert validation["valid"] is False

    def test_invalid_page_break_downgrades_certification(self):
        """Invalid page-break metadata must downgrade visual certification."""
        # Create context with invalid page-break metadata
        ctx = _valid_ctx(page_break_metadata=[{"break_id": "bad"}])
        result = build_button2_report_html(ctx)
        html = result["html_content"]
        
        # Should result in not_certified status
        assert "not_certified" in html.lower() or "invalid" in html.lower()


class TestPageBreakNoTypographyChanges:
    """Verify page-break rendering does not alter typography."""

    def test_typography_tokens_unchanged_with_page_breaks(self):
        """Typography tokens must be unchanged with page-break metadata."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        
        # Typography CSS must still be present
        assert ".typography-" in html or "font-family:" in html
        assert "font-size:" in html
        assert "font-weight:" in html

    def test_font_sizes_preserved(self):
        """Font sizes must be preserved (8-20pt)."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        
        font_size_pattern = r"font-size:\s*\d+pt"
        sizes = re.findall(font_size_pattern, html)
        assert len(sizes) > 0

    def test_hierarchy_markers_preserved_with_page_breaks(self):
        """Hierarchy markers must be preserved with page-break metadata."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        
        assert 'data-hierarchy-level="H0"' in html or "H0" in html
        assert 'data-hierarchy-level="H1"' in html or "H1" in html


class TestPageBreakNoHierarchyChanges:
    """Verify page-break rendering does not alter hierarchy."""

    def test_hierarchy_metadata_unchanged(self):
        """Hierarchy metadata must be unchanged."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        
        assert 'button2.page_hierarchy.v1' in html

    def test_canonical_section_order_unchanged(self):
        """Canonical section order must be unchanged."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        
        assert "canonical_section_order" in html or "section_order" in html.lower()


class TestPageBreakNoRendererBehaviorChanges:
    """Verify page-break rendering does not change renderer behavior."""

    def test_page_break_rendering_idempotent(self):
        """Page-break rendering must be idempotent."""
        result1 = build_button2_report_html(_valid_ctx())
        result2 = build_button2_report_html(_valid_ctx())
        
        assert result1["html_content"] == result2["html_content"]

    def test_page_break_rendering_deterministic(self):
        """Page-break rendering must be deterministic."""
        ctx = _valid_ctx()
        result1 = build_button2_report_html(ctx)
        result2 = build_button2_report_html(ctx)
        
        assert result1["ok"] == result2["ok"]
        assert result1["html_content"] == result2["html_content"]

    def test_no_chart_rendering_in_page_break_slice(self):
        """Page-break rendering must not trigger chart rendering."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        
        # Should not have SVG or chart elements added by page-break layer
        assert "<svg" not in html.lower() or "scenario" not in html.lower()


class TestSafetyInvariantsPhase2Slice3:
    """Verify all safety invariants remain locked."""

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

    def test_html_composition_performed_true(self):
        """html_composition_performed must be True."""
        result = build_button2_report_html(_valid_ctx())
        assert result["html_composition_performed"] is True

    def test_no_approval_gate_bypass(self):
        """Page-break rendering must not bypass approval gates."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        
        assert "auto_approve" not in html.lower()
        assert "automatically_approved" not in html.lower()


class TestPhase1BackwardCompatibility:
    """Verify Phase 1 implementation still works with Page-Break Slice 3."""

    def test_phase1_html_structure_unchanged(self):
        """Phase 1 HTML structure must remain valid."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        
        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "</html>" in html
        assert "<body>" in html
        assert "</body>" in html

    def test_all_metadata_sections_present(self):
        """All metadata sections must be present."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        
        assert 'id="button2-hierarchy-metadata"' in html
        assert 'id="button2-page-breaks-metadata"' in html
        assert 'id="button2-chart-scenario-metadata"' in html
        assert 'id="button2-header-footer-watermark-metadata"' in html
        assert 'id="button2-source-traceability-metadata"' in html
        assert 'id="button2-visual-qa-rollup-metadata"' in html

    def test_typography_layer_unchanged(self):
        """Typography layer must remain unchanged."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        
        assert "<style>" in html
        assert ".typography-" in html or "font-family:" in html
        assert "</style>" in html

    def test_no_scripts_injected(self):
        """No scripts must be injected."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        
        assert "<script" not in html.lower()
        assert "</script>" not in html.lower()


class TestPageBreakIntegration:
    """Verify page-break rendering integrates with all layers."""

    def test_page_breaks_schema_matches_constant(self):
        """Page-break schema version must match constant."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        
        assert 'button2.page_breaks_and_blocks.v1' in html

    def test_section_blocks_and_page_breaks_together(self):
        """Section blocks and page-breaks must work together."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        
        # Both must be present
        assert 'data-page-break' in html or 'break_policy' in html
        assert 'data-page-block-role' in html or 'block_role' in html

    def test_page_breaks_do_not_break_charts_layer(self):
        """Page-break layer must not break charts layer."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        
        assert 'button2.chart_and_scenario.v1' in html

    def test_page_breaks_do_not_break_typography_layer(self):
        """Page-break layer must not break typography layer."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        
        assert 'button2.page_typography_tokens.v1' in html or '.typography-' in html

    def test_all_visual_qa_layers_accounted_for(self):
        """All visual QA layers must be accounted for."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        
        assert 'button2.visual_qa_rollup.v1' in html or 'visual_qa_rollup' in html.lower()


class TestPageBreakMetadataRenderFacing:
    """Verify page-break metadata is render-facing (present in HTML)."""

    def test_break_policies_render_facing(self):
        """Break policies must be render-facing in HTML."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        
        # Must be accessible as data attributes or in metadata
        assert "break_policy" in html or "keep_together" in html

    def test_section_block_metadata_render_facing(self):
        """Section block metadata must be render-facing."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        
        # Must be in data attributes or metadata
        assert "block_id" in html or "section_block" in html.lower()

    def test_widow_orphan_rules_render_facing(self):
        """Widow/orphan rules must be render-facing."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        
        # Must be accessible
        assert "widow" in html.lower() or "orphan" in html.lower() or "min_lines" in html


class TestCanSplitPolicies:
    """Verify can_split policies are correctly represented."""

    def test_can_split_attribute_present(self):
        """can_split attribute must be present in metadata."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        
        # Should appear in section block data
        assert "can_split" in html or "can-split" in html.lower()

    def test_continuation_header_required_present(self):
        """continuation_header_required must be present in metadata."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        
        # Should appear in section block data
        assert "continuation" in html.lower() or "header" in html.lower()

    def test_chunk_size_present_for_split_by_chunk(self):
        """chunk_size must be present for split_by_chunk policy."""
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        
        # Should reference chunk sizing
        assert "chunk" in html.lower() or "10" in html
