"""
Button 2 Customer PDF - Phase 4 Source-Traceability Rendering Smoke v1

Evidence-only smoke proof that source-traceability rendering polish remains
CSS-only, preserves contracts, and introduces no operational behavior changes.
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
        "fight_id": "fight_phase4_source_traceability_smoke_001",
        "source_context_kind": "button1_dossier_handoff",
        "source_ingest_mode": "preview_only",
        "handoff_summary_preview": "Phase 4 source-traceability smoke keeps contracts stable.",
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
            "sources": [
                {
                    "source_type": "official",
                    "source_class": "tier_a",
                    "confidence_level": "high",
                    "citation_completeness": "complete",
                    "verification_status": "verified",
                    "source_url": "https://example.org/official",
                    "source_date": "2026-05-18",
                },
                {
                    "source_type": "research",
                    "source_class": "tier_b",
                    "confidence_level": "medium",
                    "citation_completeness": "partial",
                    "verification_status": "unverified",
                    "source_url": "https://example.org/research",
                    "source_date": "2026-05-17",
                },
                {
                    "source_type": "operator",
                    "source_class": "tier_c",
                    "confidence_level": "low",
                    "citation_completeness": "minimal",
                    "verification_status": "verified",
                    "source_url": "https://example.org/operator",
                    "source_date": "2026-05-16",
                },
            ],
            "lineage_graph": {},
            "total_sources": 3,
            "corroboration_coverage": 0.66,
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


def test_source_traceability_css_remains_present():
    html = build_button2_report_html(_valid_ctx())["html_content"]
    assert ".source-traceability-render-surface {" in html
    assert ".source-citation-row {" in html
    assert ".source-label," in html
    assert ".source-type-label {" in html


def test_citation_source_label_and_class_styling_remain_represented():
    html = build_button2_report_html(_valid_ctx())["html_content"]
    assert "grid-template-columns: minmax(7.2em, 10.5em) 1fr;" in html
    assert ".source-class-official {" in html
    assert ".source-class-research {" in html
    assert ".source-class-operator {" in html
    assert ".source-class-ai-risa {" in html


def test_source_footer_and_traceability_qa_styling_remain_represented():
    html = build_button2_report_html(_valid_ctx())["html_content"]
    assert ".source-traceability-footer {" in html
    assert "justify-content: space-between;" in html
    assert ".traceability-qa-row {" in html
    assert '.traceability-qa-row[data-traceability-status="clear"]' in html
    assert '.traceability-qa-row[data-traceability-status="watch"]' in html
    assert '.traceability-qa-row[data-traceability-status="escalated"]' in html


def test_locked_source_traceability_metadata_remains_intact():
    html = build_button2_report_html(_valid_ctx())["html_content"]
    metadata = _extract_metadata_json(html, "button2-source-traceability-metadata")
    payload = metadata["source_traceability"]
    assert metadata["schema_version"] == "button2.source_traceability.v1"
    assert metadata["validation_status"] == "valid"
    assert isinstance(payload["sources"], list)
    assert len(payload["sources"]) == 3


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


def test_no_delivery_certification_controls_or_mutation_endpoints():
    html = build_button2_report_html(_valid_ctx())["html_content"].lower()
    assert "deliver now" not in html
    assert "auto certify" not in html
    assert "certification automation" not in html
    assert "/api/" not in html


def test_no_approval_output_file_write_dashboard_changes():
    result = build_button2_report_html(_valid_ctx())
    html = result["html_content"].lower()
    assert result["preview_only"] is True
    assert result["pdf_generation_performed"] is False
    assert result["file_write_performed"] is False
    assert result["export_performed"] is False
    assert result["delivery_performed"] is False
    assert "<button" not in html
    assert "<form" not in html
