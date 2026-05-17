"""
Button 2: Customer PDF Page Hierarchy Implementation Tests v1

Purpose:
- Validate hierarchy markers and metadata emission in HTML composition
- Validate canonical section order representation
- Validate page-block role attachment
- Validate fail-closed certification downgrade for missing/invalid hierarchy

Governance:
- No renderer changes
- No layout redesign
- No approval changes
- No output path changes
- No file-write changes
- No dashboard or delivery changes
"""

import json
import re

from operator_dashboard.button2_html_composition_entry_point_v1 import (
    build_button2_report_html,
)


def _valid_ctx(**overrides):
    base = {
        "destination_marker": "button2_report_generation_preview",
        "report_context_kind": "dossier_handoff_report_context_preview",
        "fight_id": "fight_001",
        "source_context_kind": "button1_dossier_handoff",
        "source_ingest_mode": "preview_only",
        "handoff_summary_preview": "Fighter: Test Fighter A vs Test Fighter B",
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


class TestHierarchyMarkers:
    def test_hierarchy_levels_exist_in_html_annotations(self):
        result = build_button2_report_html(_valid_ctx())
        assert result["ok"] is True
        html = result["html_content"]
        for level in ["H0", "H1", "H2", "Body", "Meta"]:
            assert f'data-hierarchy-level="{level}"' in html

    def test_page_block_roles_attached(self):
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        required_roles = [
            "report_identity_block",
            "analysis_block",
            "sources_calibration_block",
            "footer_metadata_block",
        ]
        for role in required_roles:
            assert f'data-page-block-role="{role}"' in html


class TestCanonicalOrderRepresentation:
    def test_canonical_order_encoded_in_metadata_section(self):
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        expected = (
            "fighter_a_context|fighter_b_context|matchup_signal|"
            "detailed_analysis|sources_and_calibration"
        )
        assert f'data-canonical-section-order="{expected}"' in html


class TestHierarchyMetadataPayload:
    def test_hierarchy_metadata_section_present(self):
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        assert 'id="button2-hierarchy-metadata"' in html
        assert 'class="hierarchy-metadata"' in html

    def test_hierarchy_schema_version_present(self):
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        assert 'data-hierarchy-schema-version="button2.page_hierarchy.v1"' in html

    def test_embedded_json_contains_required_contract_fields(self):
        result = build_button2_report_html(_valid_ctx())
        html = result["html_content"]
        match = re.search(
            r'<section\s+id="button2-hierarchy-metadata".*?<pre[^>]*>(.*?)</pre>',
            html,
            re.DOTALL,
        )
        assert match is not None
        metadata_escaped = match.group(1)
        metadata = json.loads(metadata_escaped.replace("&quot;", '"'))
        assert metadata["schema_version"] == "button2.page_hierarchy.v1"
        assert metadata["canonical_section_order"] == [
            "fighter_a_context",
            "fighter_b_context",
            "matchup_signal",
            "detailed_analysis",
            "sources_and_calibration",
        ]
        assert metadata["required_levels"] == ["H0", "H1", "H2", "Body", "Meta"]
        assert isinstance(metadata["blocks"], list)
        assert len(metadata["blocks"]) > 0


class TestFailClosedHierarchyValidation:
    def test_missing_hierarchy_markers_downgrades_visual_certification(self):
        ctx = _valid_ctx(visual_certification_status="certified")
        del ctx["hierarchy_markers"]
        result = build_button2_report_html(ctx)
        html = result["html_content"]
        assert "Visual certification: not_certified" in html
        assert "Hierarchy validation: missing" in html

    def test_invalid_hierarchy_marker_level_downgrades_visual_certification(self):
        ctx = _valid_ctx(
            hierarchy_markers=[{"level": "H9", "role": "analysis_block"}],
            visual_certification_status="certified",
        )
        result = build_button2_report_html(ctx)
        html = result["html_content"]
        assert "Visual certification: not_certified" in html
        assert "Hierarchy validation: invalid" in html

    def test_invalid_hierarchy_marker_role_downgrades_visual_certification(self):
        ctx = _valid_ctx(
            hierarchy_markers=[{"level": "H1", "role": "unknown_role"}],
            visual_certification_status="certified",
        )
        result = build_button2_report_html(ctx)
        html = result["html_content"]
        assert "Visual certification: not_certified" in html
        assert "Hierarchy validation: invalid" in html

    def test_valid_hierarchy_preserves_visual_certification_value(self):
        result = build_button2_report_html(_valid_ctx(visual_certification_status="certified"))
        html = result["html_content"]
        assert "Hierarchy validation: valid" in html
        assert "Visual certification: certified" in html


class TestSafetyRegressionSignals:
    def test_preview_and_write_flags_unchanged(self):
        result = build_button2_report_html(_valid_ctx())
        assert result["preview_only"] is True
        assert result["pdf_generation_performed"] is False
        assert result["file_write_performed"] is False
        assert result["export_performed"] is False
        assert result["delivery_performed"] is False

    def test_no_external_urls_or_scripts_introduced(self):
        html = build_button2_report_html(_valid_ctx())["html_content"].lower()
        assert "http://" not in html
        assert "https://" not in html
        assert "<script" not in html
