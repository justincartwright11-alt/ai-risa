"""
Button 2: Customer PDF Page Breaks and Section Blocks Implementation Tests v1

Purpose:
- Validate page-break and section-block metadata in HTML composition
- Validate break policy representation and boundary detection
- Validate fail-closed downgrade for missing/invalid break metadata

Governance:
- Metadata and composition annotations only
- No renderer changes
- No output path changes
- No file-write changes
- No approval/dashboard/delivery changes
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
        "fight_id": "fight_pb_001",
        "source_context_kind": "button1_dossier_handoff",
        "source_ingest_mode": "preview_only",
        "handoff_summary_preview": "Report summary block content",
        "hierarchy_markers": [
            {"level": "H0", "role": "report_identity_block"},
            {"level": "H1", "role": "analysis_block"},
            {"level": "H2", "role": "sources_calibration_block"},
            {"level": "Body", "role": "analysis_block"},
            {"level": "Meta", "role": "footer_metadata_block"},
        ],
        "source_traceability": [
            {"id": "SRC-001", "type": "official", "date": "2026-05-17"}
        ],
        "overlap_proof": "unavailable",
        "off_page_text_proof": "unavailable",
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


class TestPageBreaksAndSectionBlocksMetadata:
    def test_section_block_metadata_exists(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        metadata = _extract_metadata_json(html, "button2-page-breaks-metadata")
        assert metadata["schema_version"] == "button2.page_breaks_and_blocks.v1"
        assert isinstance(metadata["section_blocks"], list)
        assert len(metadata["section_blocks"]) > 0

    def test_page_break_metadata_exists(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        metadata = _extract_metadata_json(html, "button2-page-breaks-metadata")
        assert isinstance(metadata["page_breaks"], list)
        assert len(metadata["page_breaks"]) > 0

    def test_block_roles_are_mapped_in_metadata(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        metadata = _extract_metadata_json(html, "button2-page-breaks-metadata")
        roles = {block["role"] for block in metadata["section_blocks"]}
        assert "report_identity_block" in roles
        assert "analysis_block" in roles
        assert "sources_calibration_block" in roles
        assert "footer_metadata_block" in roles

    def test_break_policies_are_represented(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        metadata = _extract_metadata_json(html, "button2-page-breaks-metadata")
        policies = {block["break_policy"] for block in metadata["section_blocks"]}
        assert "keep_together" in policies
        assert "allow_internal_break" in policies
        assert "split_by_chunk" in policies

    def test_widow_orphan_rules_are_represented(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        metadata = _extract_metadata_json(html, "button2-page-breaks-metadata")
        assert metadata["widow_orphan_rules"]
        assert "header_requires_two_following_lines" in metadata["widow_orphan_rules"]

    def test_page_breaks_metadata_section_and_schema_attrs_present(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert 'id="button2-page-breaks-metadata"' in html
        assert 'class="page-breaks-metadata"' in html
        assert 'data-page-breaks-schema-version="button2.page_breaks_and_blocks.v1"' in html


class TestBoundaryDetectionAndFailClosed:
    def test_forbidden_break_boundaries_are_detectable(self):
        section_blocks = [
            {
                "block_id": "report_identity",
                "role": "report_identity_block",
                "break_policy": "keep_together",
                "can_split": False,
                "continuation_header_required": False,
                "break_boundary": "inside_chart_or_table",
            }
        ]
        page_breaks = [
            {
                "break_id": "pb_001",
                "trigger_block_id": "report_identity",
                "trigger_section": "Report Identity",
                "overflow_reason": "section_size",
                "previous_page_content_height_in": 8.0,
                "atomic_unit_preserved": True,
                "widow_orphan_rule_applied": False,
            }
        ]
        html = build_button2_report_html(
            _valid_ctx(
                section_block_metadata=section_blocks,
                page_break_metadata=page_breaks,
                visual_certification_status="certified",
            )
        )["html_content"]
        metadata = _extract_metadata_json(html, "button2-page-breaks-metadata")
        assert metadata["validation_status"] == "invalid"
        assert "inside_chart_or_table" in metadata["forbidden_break_boundaries_detected"]
        assert "Page-break metadata validation: invalid" in html

    def test_missing_page_break_metadata_fails_closed(self):
        html = build_button2_report_html(
            _valid_ctx(page_break_metadata=None, visual_certification_status="certified")
        )["html_content"]
        assert "Page-break metadata validation: missing" in html
        assert "Visual certification: not_certified" in html

    def test_missing_section_block_metadata_fails_closed(self):
        html = build_button2_report_html(
            _valid_ctx(section_block_metadata=None, visual_certification_status="certified")
        )["html_content"]
        assert "Page-break metadata validation: missing" in html
        assert "Visual certification: not_certified" in html

    def test_invalid_break_policy_fails_closed(self):
        section_blocks = [
            {
                "block_id": "report_identity",
                "role": "report_identity_block",
                "break_policy": "unknown_policy",
                "can_split": False,
                "continuation_header_required": False,
            }
        ]
        page_breaks = [
            {
                "break_id": "pb_001",
                "trigger_block_id": "report_identity",
                "trigger_section": "Report Identity",
                "overflow_reason": "section_size",
                "previous_page_content_height_in": 8.0,
                "atomic_unit_preserved": True,
                "widow_orphan_rule_applied": False,
            }
        ]
        html = build_button2_report_html(
            _valid_ctx(
                section_block_metadata=section_blocks,
                page_break_metadata=page_breaks,
                visual_certification_status="certified",
            )
        )["html_content"]
        assert "Page-break metadata validation: invalid" in html
        assert "Visual certification: not_certified" in html


class TestNoBehaviorSurfaceExpansion:
    def test_safety_flags_unchanged(self):
        result = build_button2_report_html(_valid_ctx())
        assert result["preview_only"] is True
        assert result["pdf_generation_performed"] is False
        assert result["file_write_performed"] is False
        assert result["export_performed"] is False
        assert result["delivery_performed"] is False

    def test_no_external_css_or_scripts(self):
        html = build_button2_report_html(_valid_ctx())["html_content"].lower()
        assert "http://" not in html
        assert "https://" not in html
        assert "<script" not in html
        assert "<link rel=\"stylesheet\"" not in html
