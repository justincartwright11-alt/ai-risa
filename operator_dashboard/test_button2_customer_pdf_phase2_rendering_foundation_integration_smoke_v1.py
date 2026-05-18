"""
Button 2 Customer PDF - Phase 2 Slice 8 - Rendering Foundation Integration Smoke Tests

Purpose:
- Evidence-only smoke proof that all seven Phase 2 rendering foundation slices
  coexist with the full Phase 1 metadata stack.

Governance:
- Smoke proof only
- No implementation changes
- No renderer behavior changes
- No approval/output/file-write/dashboard/delivery changes
"""

import html as _html
import json
import re

from operator_dashboard.button2_html_composition_entry_point_v1 import (
    build_button2_report_html,
)


def _valid_ctx(**overrides):
    base = {
        "destination_marker": "button2_report_generation_preview",
        "report_context_kind": "dossier_handoff_report_context_preview",
        "fight_id": "fight_phase2_integration_smoke_001",
        "source_context_kind": "button1_dossier_handoff",
        "source_ingest_mode": "preview_only",
        "handoff_summary_preview": "Phase 2 Integration Smoke: Fighter A vs Fighter B",
        "hierarchy_markers": [
            {"level": "H0", "role": "report_identity_block"},
            {"level": "H1", "role": "analysis_block"},
            {"level": "H2", "role": "sources_calibration_block"},
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
            {
                "block_id": "meta_footer",
                "role": "footer_metadata_block",
                "break_policy": "keep_together",
                "can_split": False,
                "continuation_header_required": False,
                "min_lines_after_header": 2,
                "min_space_for_chart_in": 1.0,
                "approved_break_boundaries": ["never_split"],
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
            {"id": "SRC-001", "type": "official", "date": "2026-05-18"}
        ],
        "source_traceability_metadata": {
            "sources": [],
            "lineage_graph": {},
            "total_sources": 0,
            "corroboration_coverage": 0.0,
        },
        "overlap_proof": {"status": "present"},
        "off_page_text_proof": {"status": "present"},
        "visual_certification_status": "certified",
    }
    base.update(overrides)
    return base


def _extract_metadata_json(html_text, section_id):
    match = re.search(
        rf'<section\s+id="{section_id}".*?<pre[^>]*>(.*?)</pre>',
        html_text,
        re.DOTALL,
    )
    assert match is not None
    return json.loads(_html.unescape(match.group(1)))


class TestPhase2IntegrationSmoke:
    def test_composed_html_has_all_seven_render_facing_layers(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert 'class="typography-report-title"' in html
        assert 'id="button2-hierarchy-metadata"' in html
        assert 'id="button2-page-breaks-metadata"' in html
        assert 'id="button2-chart-scenario-metadata"' in html
        assert 'id="button2-header-footer-watermark-metadata"' in html
        assert 'id="button2-source-traceability-metadata"' in html
        assert 'id="button2-visual-qa-rollup-metadata"' in html

    def test_all_metadata_schema_versions_present(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert "button2.page_hierarchy.v1" in html
        assert "button2.page_breaks_and_blocks.v1" in html
        assert "button2.chart_and_scenario.v1" in html
        assert "button2.header_footer_watermark.v1" in html
        assert "button2.source_traceability.v1" in html
        assert "button2.visual_qa_rollup.v1" in html

    def test_metadata_sections_are_parseable_json(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert _extract_metadata_json(html, "button2-hierarchy-metadata")
        assert _extract_metadata_json(html, "button2-page-breaks-metadata")
        assert _extract_metadata_json(html, "button2-chart-scenario-metadata")
        assert _extract_metadata_json(html, "button2-header-footer-watermark-metadata")
        assert _extract_metadata_json(html, "button2-source-traceability-metadata")
        assert _extract_metadata_json(html, "button2-visual-qa-rollup-metadata")

    def test_rollup_metadata_is_render_facing_and_all_valid(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert 'data-visual-qa-rollup-status="all_valid"' in html
        assert 'data-certification-readiness="ready"' in html
        assert 'data-visual-completeness="100%"' in html
        assert 'data-visual-confidence="high"' in html
        assert "Visual QA rollup status: all_valid" in html
        assert "Overall visual confidence: high" in html

    def test_all_phase2_foundation_validation_rows_present(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert "Hierarchy validation: valid" in html
        assert "Page-break metadata validation: valid" in html
        assert "Chart/scenario metadata validation: valid" in html
        assert "Header/footer/watermark metadata validation: valid" in html
        assert "Source traceability metadata validation: valid" in html
        assert "Visual QA rollup status: all_valid" in html

    def test_no_external_css_or_scripts(self):
        html = build_button2_report_html(_valid_ctx())["html_content"].lower()
        assert "<script" not in html
        assert '<link rel="stylesheet"' not in html

    def test_no_interactive_dashboard_surface(self):
        html = build_button2_report_html(_valid_ctx())["html_content"].lower()
        assert "<button" not in html
        assert "<form" not in html

    def test_safety_flags_remain_locked(self):
        result = build_button2_report_html(_valid_ctx())
        assert result["preview_only"] is True
        assert result["pdf_generation_performed"] is False
        assert result["file_write_performed"] is False
        assert result["export_performed"] is False
        assert result["delivery_performed"] is False
        assert result["html_composition_performed"] is True

    def test_renderer_behavior_idempotent_and_deterministic(self):
        ctx = _valid_ctx()
        result_one = build_button2_report_html(ctx)
        result_two = build_button2_report_html(ctx)
        assert result_one["ok"] is True
        assert result_two["ok"] is True
        assert result_one["html_content"] == result_two["html_content"]

    def test_metadata_sections_not_duplicated(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert html.count('id="button2-hierarchy-metadata"') == 1
        assert html.count('id="button2-page-breaks-metadata"') == 1
        assert html.count('id="button2-chart-scenario-metadata"') == 1
        assert html.count('id="button2-header-footer-watermark-metadata"') == 1
        assert html.count('id="button2-source-traceability-metadata"') == 1
        assert html.count('id="button2-visual-qa-rollup-metadata"') == 1
