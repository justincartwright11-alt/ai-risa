"""
Button 2 Customer PDF - Phase 4 Chart/Scenario Rendering v1

Purpose:
- Validate first narrow chart/scenario rendering polish step is CSS-only and contract-safe.

Governance:
- No renderer rewrite
- No delivery workflow changes
- No certification automation
- No approval/output/file-write/dashboard changes
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
        "fight_id": "fight_phase4_chart_scenario_001",
        "source_context_kind": "button1_dossier_handoff",
        "source_ingest_mode": "preview_only",
        "handoff_summary_preview": "Phase 4 chart/scenario rendering polish remains metadata-locked.",
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


def test_chart_scenario_render_facing_css_rules_present():
    html = build_button2_report_html(_valid_ctx())["html_content"]
    assert ".chart-scenario-render-surface {" in html
    assert 'data-chart-module="scenario_tree"' in html
    assert 'data-chart-module="method_pathway"' in html
    assert 'data-chart-module="round_control"' in html
    assert 'data-chart-module="risk_collapse_markers"' in html


def test_scenario_tree_container_rules_represented():
    html = build_button2_report_html(_valid_ctx())["html_content"]
    assert '.chart-scenario-render-surface[data-chart-module="scenario_tree"] {' in html
    assert "border-left: 3px solid #d5dce8;" in html


def test_method_pathway_container_rules_represented():
    html = build_button2_report_html(_valid_ctx())["html_content"]
    assert '.chart-scenario-render-surface[data-chart-module="method_pathway"] {' in html
    assert "border-left: 3px solid #d7eadf;" in html


def test_round_control_visual_rules_represented():
    html = build_button2_report_html(_valid_ctx())["html_content"]
    assert '.chart-scenario-render-surface[data-chart-module="round_control"] {' in html
    assert "border-left: 3px solid #eadfbf;" in html


def test_risk_collapse_marker_visual_rules_represented():
    html = build_button2_report_html(_valid_ctx())["html_content"]
    assert '.chart-scenario-render-surface[data-chart-module="risk_collapse_markers"] {' in html
    assert '.risk-marker[data-risk-severity="watch"] {' in html
    assert '.risk-marker[data-risk-severity="elevated"] {' in html
    assert '.risk-marker[data-risk-severity="critical"] {' in html


def test_locked_chart_scenario_metadata_remains_intact():
    html = build_button2_report_html(_valid_ctx())["html_content"]
    metadata = _extract_metadata_json(html, "button2-chart-scenario-metadata")
    payload = metadata["chart_and_scenario"]
    assert metadata["schema_version"] == "button2.chart_and_scenario.v1"
    assert metadata["validation_status"] == "valid"
    assert payload["scenario_tree"]["root_node"]
    assert payload["method_pathways"][0]["method_type"]
    assert payload["round_control"][0]["round_range"]
    assert payload["risk_collapse_markers"][0]["risk_type"]


def test_no_proof_stack_or_html_data_contract_changes():
    html = build_button2_report_html(_valid_ctx())["html_content"]
    assert 'id="button2-hierarchy-metadata"' in html
    assert 'id="button2-page-breaks-metadata"' in html
    assert 'id="button2-chart-scenario-metadata"' in html
    assert 'id="button2-header-footer-watermark-metadata"' in html
    assert 'id="button2-source-traceability-metadata"' in html
    assert 'id="button2-visual-qa-rollup-metadata"' in html
    assert "Visual QA rollup status:" in html
    assert "Valid layers:" in html
    assert "Overall visual confidence:" in html


def test_no_approval_output_file_write_dashboard_delivery_changes():
    result = build_button2_report_html(_valid_ctx())
    html = result["html_content"].lower()
    assert result["preview_only"] is True
    assert result["pdf_generation_performed"] is False
    assert result["file_write_performed"] is False
    assert result["export_performed"] is False
    assert result["delivery_performed"] is False
    assert "<button" not in html
    assert "<form" not in html
    assert "/api/" not in html
    assert "deliver now" not in html
    assert "auto certify" not in html
