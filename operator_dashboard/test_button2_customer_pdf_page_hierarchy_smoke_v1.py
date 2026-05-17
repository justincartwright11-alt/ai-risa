"""
Button 2: Customer PDF Page Hierarchy Smoke v1

Evidence-only smoke proof that typography + hierarchy metadata work together in
composed Button 2 HTML with no behavior-surface expansion.
"""

from operator_dashboard.button2_html_composition_entry_point_v1 import (
    build_button2_report_html,
)


def _valid_ctx(**overrides):
    base = {
        "destination_marker": "button2_report_generation_preview",
        "report_context_kind": "dossier_handoff_report_context_preview",
        "fight_id": "smoke_fight_001",
        "source_context_kind": "button1_dossier_handoff",
        "source_ingest_mode": "preview_only",
        "handoff_summary_preview": "Smoke summary: Fighter A vs Fighter B",
        "hierarchy_markers": [
            {"level": "H0", "role": "report_identity_block"},
            {"level": "H1", "role": "analysis_block"},
            {"level": "H2", "role": "sources_calibration_block"},
            {"level": "Body", "role": "analysis_block"},
            {"level": "Meta", "role": "footer_metadata_block"},
        ],
        "source_traceability": [
            {"id": "SRC-SMOKE-1", "type": "official", "date": "2026-05-17"}
        ],
        "overlap_proof": "unavailable",
        "off_page_text_proof": "unavailable",
        "visual_certification_status": "certified",
    }
    base.update(overrides)
    return base


class TestButton2PageHierarchySmokeV1:
    def test_typography_and_hierarchy_markers_render_together(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        assert 'class="typography-report-title"' in html
        assert 'class="typography-section-header-l1"' in html
        assert 'class="typography-body-secondary"' in html
        for level in ["H0", "H1", "H2", "Body", "Meta"]:
            assert f'data-hierarchy-level="{level}"' in html

    def test_canonical_section_order_is_stable(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        expected = (
            "fighter_a_context|fighter_b_context|matchup_signal|"
            "detailed_analysis|sources_and_calibration"
        )
        assert f'data-canonical-section-order="{expected}"' in html

    def test_page_block_roles_present(self):
        html = build_button2_report_html(_valid_ctx())["html_content"]
        for role in [
            "report_identity_block",
            "analysis_block",
            "sources_calibration_block",
            "footer_metadata_block",
        ]:
            assert f'data-page-block-role="{role}"' in html

    def test_invalid_hierarchy_fails_closed_to_not_certified(self):
        html = build_button2_report_html(
            _valid_ctx(
                hierarchy_markers=[{"level": "H9", "role": "analysis_block"}],
                visual_certification_status="certified",
            )
        )["html_content"]
        assert "Hierarchy validation: invalid" in html
        assert "Visual certification: not_certified" in html

    def test_legacy_hierarchy_marker_fixture_remains_compatible(self):
        html = build_button2_report_html(
            _valid_ctx(
                hierarchy_markers=[{"block": "executive_summary", "order": 0}],
                visual_certification_status="certified",
            )
        )["html_content"]
        assert "Hierarchy validation: valid" in html
        assert "Visual certification: certified" in html

    def test_no_external_css_or_scripts_in_composed_html(self):
        html = build_button2_report_html(_valid_ctx())["html_content"].lower()
        assert "http://" not in html
        assert "https://" not in html
        assert "<script" not in html
        assert "<link rel=\"stylesheet\"" not in html

    def test_output_and_write_behavior_flags_unchanged(self):
        result = build_button2_report_html(_valid_ctx())
        assert result["preview_only"] is True
        assert result["pdf_generation_performed"] is False
        assert result["file_write_performed"] is False
        assert result["export_performed"] is False
        assert result["delivery_performed"] is False
