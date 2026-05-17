"""
Button 2: Customer PDF Page Breaks and Section Blocks Smoke v1

Evidence-only smoke proof that typography, hierarchy, page-break metadata, and
section-block metadata work together in composed Button 2 HTML.
"""

from operator_dashboard.button2_html_composition_entry_point_v1 import (
    build_button2_report_html,
)


def _valid_ctx(**overrides):
    base = {
        "destination_marker": "button2_report_generation_preview",
        "report_context_kind": "dossier_handoff_report_context_preview",
        "fight_id": "smoke_breaks_001",
        "source_context_kind": "button1_dossier_handoff",
        "source_ingest_mode": "preview_only",
        "handoff_summary_preview": "Smoke summary for typography + hierarchy + breaks",
        "hierarchy_markers": [
            {"level": "H0", "role": "report_identity_block"},
            {"level": "H1", "role": "analysis_block"},
            {"level": "H2", "role": "sources_calibration_block"},
            {"level": "Body", "role": "analysis_block"},
            {"level": "Meta", "role": "footer_metadata_block"},
        ],
        "source_traceability": [
            {"id": "SRC-SMOKE-BREAKS", "type": "official", "date": "2026-05-17"}
        ],
        "overlap_proof": "unavailable",
        "off_page_text_proof": "unavailable",
        "visual_certification_status": "certified",
    }
    base.update(overrides)
    return base


class TestButton2PageBreaksAndSectionBlocksSmokeV1:
    def test_typography_token_classes_remain_applied(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert 'class="typography-report-title"' in html
        assert 'class="typography-section-header-l1"' in html
        assert 'class="typography-body-secondary"' in html
        assert 'class="typography-list-item"' in html
        assert "typography-page-metadata" in html

    def test_hierarchy_markers_remain_present(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        for level in ["H0", "H1", "H2", "Body", "Meta"]:
            assert f'data-hierarchy-level="{level}"' in html

    def test_section_block_and_page_break_metadata_exist(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert 'id="button2-hierarchy-metadata"' in html
        assert 'id="button2-page-breaks-metadata"' in html
        assert 'data-page-breaks-schema-version="button2.page_breaks_and_blocks.v1"' in html

    def test_break_policies_remain_represented(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert 'data-break-policy="keep_together"' in html
        assert 'data-break-policy="allow_internal_break"' in html
        assert 'data-break-policy="split_by_chunk"' in html

    def test_forbidden_boundaries_and_widow_orphan_rules_represented(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert "forbidden_break_boundaries" in html
        assert "inside_chart_or_table" in html
        assert "widow_orphan_rules" in html
        assert "header_requires_two_following_lines" in html

    def test_invalid_break_metadata_fails_closed_to_not_certified(self):
        html = build_button2_report_html(
            _valid_ctx(
                section_block_metadata=[
                    {
                        "block_id": "report_identity",
                        "role": "report_identity_block",
                        "break_policy": "invalid_policy",
                        "can_split": False,
                        "continuation_header_required": False,
                    }
                ],
                page_break_metadata=[
                    {
                        "break_id": "pb_001",
                        "trigger_block_id": "report_identity",
                        "trigger_section": "Report Identity",
                        "overflow_reason": "section_size",
                        "previous_page_content_height_in": 8.0,
                        "atomic_unit_preserved": True,
                        "widow_orphan_rule_applied": False,
                    }
                ],
                visual_certification_status="certified",
            )
        )["html_content"]
        assert "Page-break metadata validation: invalid" in html
        assert "Visual certification: not_certified" in html

    def test_missing_break_metadata_fails_closed_to_not_certified(self):
        html = build_button2_report_html(
            _valid_ctx(
                section_block_metadata=None,
                page_break_metadata=None,
                visual_certification_status="certified",
            )
        )["html_content"]
        assert "Page-break metadata validation: missing" in html
        assert "Visual certification: not_certified" in html

    def test_no_external_css_or_scripts_and_flags_unchanged(self):
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"].lower()
        assert "http://" not in html
        assert "https://" not in html
        assert "<script" not in html
        assert "<link rel=\"stylesheet\"" not in html
        assert result["preview_only"] is True
        assert result["pdf_generation_performed"] is False
        assert result["file_write_performed"] is False
        assert result["export_performed"] is False
        assert result["delivery_performed"] is False
